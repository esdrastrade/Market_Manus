"""
Multi-Armed Bandit (UCB1) para AI Agent Strategy
Sistema de aprendizagem para seleção dinâmica de estratégias

Características:
- Algoritmo UCB1 (Upper Confidence Bound)
- Persistência em SQLite
- Exploração vs Exploração balanceada
- Suporte a múltiplas estratégias e hiperparâmetros
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class UCB1Bandit:
    """
    Multi-Armed Bandit usando algoritmo UCB1

    UCB1 Formula: mean_reward + sqrt(2 * ln(total_pulls) / arm_pulls)

    Características:
    - Exploração automática de braços não testados
    - Balanceamento exploração vs exploração
    - Persistência em banco SQLite
    - Suporte a parâmetros JSON ordenados
    """

    def __init__(self, db_path: str):
        """
        Inicializa bandit com banco de dados

        Args:
            db_path: Caminho para arquivo SQLite
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ensure_database()
        logger.info(f"UCB1 Bandit initialized: {self.db_path}")

    def ensure_database(self):
        """Garante que o banco de dados existe com estrutura correta"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Criar tabela de braços
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS arms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy TEXT NOT NULL,
                params_json TEXT NOT NULL,
                pulls INTEGER DEFAULT 0,
                total_reward REAL DEFAULT 0.0,
                mean_reward REAL DEFAULT 0.0,
                ucb_score REAL DEFAULT 0.0,
                last_ts REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(strategy, params_json)
            )
        """
        )

        # Índices para performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_strategy ON arms(strategy)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_mean_reward ON arms(mean_reward DESC)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pulls ON arms(pulls)")

        conn.commit()
        conn.close()

    def ensure_arms(self, strategy_seeds: List[Dict]):
        """
        Garante que braços iniciais existem no banco

        Args:
            strategy_seeds: Lista de dicts com 'strategy' e 'params'
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        added_count = 0
        for seed in strategy_seeds:
            strategy = seed["strategy"]
            params = seed["params"]

            # Ordenar parâmetros para hash estável
            params_json = json.dumps(params, sort_keys=True)

            # Inserir se não existir
            cursor.execute(
                """
                INSERT OR IGNORE INTO arms (strategy, params_json, last_ts)
                VALUES (?, ?, ?)
            """,
                (strategy, params_json, datetime.now().timestamp()),
            )

            if cursor.rowcount > 0:
                added_count += 1

        conn.commit()
        conn.close()

        if added_count > 0:
            logger.info(f"Added {added_count} new arms to bandit")

    def select_arm(self) -> Dict:
        """
        Seleciona braço usando algoritmo UCB1

        Returns:
            Dict com 'strategy' e 'params' do braço selecionado
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Buscar todos os braços
        cursor.execute(
            """
            SELECT id, strategy, params_json, pulls, mean_reward
            FROM arms
            ORDER BY id
        """
        )

        arms = cursor.fetchall()
        conn.close()

        if not arms:
            raise ValueError("Nenhum braço disponível no bandit")

        # Calcular total de pulls
        total_pulls = sum(arm[3] for arm in arms)  # arm[3] = pulls

        # Priorizar braços não explorados (pulls = 0)
        unexplored = [arm for arm in arms if arm[3] == 0]
        if unexplored:
            # Selecionar primeiro braço não explorado
            selected = unexplored[0]
            logger.info(f"Selected unexplored arm: {selected[1]} (id={selected[0]})")
            return {"strategy": selected[1], "params": json.loads(selected[2])}

        # Calcular UCB1 scores para braços explorados
        best_arm = None
        best_score = float("-inf")

        for arm in arms:
            arm_id, strategy, params_json, pulls, mean_reward = arm

            if pulls == 0:
                # Não deveria acontecer (já tratado acima)
                ucb_score = float("inf")
            else:
                # UCB1 formula
                confidence_interval = np.sqrt(2 * np.log(total_pulls) / pulls)
                ucb_score = mean_reward + confidence_interval

            if ucb_score > best_score:
                best_score = ucb_score
                best_arm = arm

        if best_arm is None:
            # Fallback para primeiro braço
            best_arm = arms[0]
            logger.warning("Fallback to first arm")

        # Atualizar UCB score no banco
        self._update_ucb_score(best_arm[0], best_score)

        logger.info(f"Selected arm: {best_arm[1]} (UCB1={best_score:.3f})")

        return {"strategy": best_arm[1], "params": json.loads(best_arm[2])}

    def update_arm(self, strategy: str, params: Dict, reward: float):
        """
        Atualiza estatísticas de um braço após observar recompensa

        Args:
            strategy: Nome da estratégia
            params: Parâmetros da estratégia
            reward: Recompensa observada
        """
        # Ordenar parâmetros para hash estável
        params_json = json.dumps(params, sort_keys=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Buscar braço atual
        cursor.execute(
            """
            SELECT id, pulls, total_reward FROM arms
            WHERE strategy = ? AND params_json = ?
        """,
            (strategy, params_json),
        )

        result = cursor.fetchone()

        if result is None:
            # Braço não existe, criar novo
            cursor.execute(
                """
                INSERT INTO arms (strategy, params_json, pulls, total_reward, mean_reward, last_ts, updated_at)
                VALUES (?, ?, 1, ?, ?, ?, ?)
            """,
                (
                    strategy,
                    params_json,
                    reward,
                    reward,
                    datetime.now().timestamp(),
                    datetime.now().isoformat(),
                ),
            )

            logger.info(f"Created new arm: {strategy} with reward {reward:.3f}")
        else:
            # Atualizar braço existente
            arm_id, pulls, total_reward = result
            new_pulls = pulls + 1
            new_total_reward = total_reward + reward
            new_mean_reward = new_total_reward / new_pulls

            cursor.execute(
                """
                UPDATE arms 
                SET pulls = ?, total_reward = ?, mean_reward = ?, last_ts = ?, updated_at = ?
                WHERE id = ?
            """,
                (
                    new_pulls,
                    new_total_reward,
                    new_mean_reward,
                    datetime.now().timestamp(),
                    datetime.now().isoformat(),
                    arm_id,
                ),
            )

            logger.info(
                f"Updated arm {strategy}: pulls={new_pulls}, mean_reward={new_mean_reward:.3f}"
            )

        conn.commit()
        conn.close()

    def _update_ucb_score(self, arm_id: int, ucb_score: float):
        """Atualiza UCB score de um braço"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE arms SET ucb_score = ? WHERE id = ?
        """,
            (ucb_score, arm_id),
        )

        conn.commit()
        conn.close()

    def get_stats(self) -> List[Dict]:
        """
        Retorna estatísticas de todos os braços

        Returns:
            Lista de dicts com estatísticas ordenadas por mean_reward
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT strategy, params_json, pulls, mean_reward, total_reward, ucb_score, last_ts, updated_at
            FROM arms
            ORDER BY mean_reward DESC, pulls DESC
        """
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "strategy": row[0],
                    "params": json.loads(row[1]),
                    "pulls": row[2],
                    "mean_reward": row[3],
                    "total_reward": row[4],
                    "ucb_score": row[5],
                    "last_ts": row[6],
                    "updated_at": row[7],
                }
            )

        conn.close()
        return results

    def get_best_arms(self, limit: int = 5) -> List[Dict]:
        """
        Retorna os melhores braços por mean_reward

        Args:
            limit: Número máximo de braços a retornar

        Returns:
            Lista dos melhores braços
        """
        stats = self.get_stats()
        return stats[:limit]

    def get_arm_count(self) -> int:
        """Retorna número total de braços"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM arms")
        count = cursor.fetchone()[0]

        conn.close()
        return count

    def get_total_pulls(self) -> int:
        """Retorna número total de pulls em todos os braços"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT SUM(pulls) FROM arms")
        result = cursor.fetchone()[0]

        conn.close()
        return result or 0

    def reset_all_arms(self):
        """
        Reset completo de todos os braços (CUIDADO!)
        Remove todos os dados de aprendizagem
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM arms")
        conn.commit()
        conn.close()

        logger.warning("All arms reset - learning data cleared")

    def export_arms_data(self) -> Dict:
        """
        Exporta dados dos braços para backup/análise

        Returns:
            Dict com todos os dados dos braços
        """
        stats = self.get_stats()

        export_data = {
            "timestamp": datetime.now().isoformat(),
            "total_arms": len(stats),
            "total_pulls": self.get_total_pulls(),
            "arms": stats,
        }

        return export_data

    def import_arms_data(self, data: Dict):
        """
        Importa dados dos braços de backup

        Args:
            data: Dict com dados exportados
        """
        if "arms" not in data:
            raise ValueError("Invalid import data format")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        imported_count = 0
        for arm_data in data["arms"]:
            strategy = arm_data["strategy"]
            params_json = json.dumps(arm_data["params"], sort_keys=True)
            pulls = arm_data["pulls"]
            total_reward = arm_data["total_reward"]
            mean_reward = arm_data["mean_reward"]

            cursor.execute(
                """
                INSERT OR REPLACE INTO arms 
                (strategy, params_json, pulls, total_reward, mean_reward, last_ts, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    strategy,
                    params_json,
                    pulls,
                    total_reward,
                    mean_reward,
                    datetime.now().timestamp(),
                    datetime.now().isoformat(),
                ),
            )

            imported_count += 1

        conn.commit()
        conn.close()

        logger.info(f"Imported {imported_count} arms from backup")


def create_default_bandit(memory_dir: str = "./memory") -> UCB1Bandit:
    """
    Cria bandit com configuração padrão

    Args:
        memory_dir: Diretório para arquivos de memória

    Returns:
        UCB1Bandit configurado
    """
    db_path = Path(memory_dir) / "tiny_memory.db"
    bandit = UCB1Bandit(str(db_path))

    # Estratégias padrão
    default_arms = [
        # EMA Crossover variations
        {"strategy": "ema_cross", "params": {"fast": 9, "slow": 21}},
        {"strategy": "ema_cross", "params": {"fast": 12, "slow": 26}},
        {"strategy": "ema_cross", "params": {"fast": 20, "slow": 50}},
        # RSI Mean Reversion variations
        {"strategy": "rsi_mr", "params": {"period": 14, "lo": 30, "hi": 70}},
        {"strategy": "rsi_mr", "params": {"period": 8, "lo": 25, "hi": 75}},
        {"strategy": "rsi_mr", "params": {"period": 21, "lo": 35, "hi": 65}},
        # Breakout variations
        {"strategy": "breakout", "params": {"lookback": 20, "buffer_bps": 2}},
        {"strategy": "breakout", "params": {"lookback": 55, "buffer_bps": 3}},
        {"strategy": "breakout", "params": {"lookback": 10, "buffer_bps": 1}},
    ]

    bandit.ensure_arms(default_arms)
    return bandit


if __name__ == "__main__":
    # Teste básico do bandit
    print("🤖 UCB1 Bandit - Teste Básico")

    # Criar bandit
    bandit = create_default_bandit("./test_memory")

    print(f"📊 Braços disponíveis: {bandit.get_arm_count()}")
    print(f"📊 Total pulls: {bandit.get_total_pulls()}")

    # Simular algumas seleções e atualizações
    print("\n🔄 Simulando aprendizagem...")

    for i in range(20):
        # Selecionar braço
        arm = bandit.select_arm()

        # Simular recompensa (aleatória para teste)
        reward = np.random.normal(0.1, 0.3)  # Média 0.1, desvio 0.3

        # Atualizar bandit
        bandit.update_arm(arm["strategy"], arm["params"], reward)

        if i % 5 == 0:
            print(f"   Iteração {i+1}: {arm['strategy']} -> reward={reward:.3f}")

    # Mostrar estatísticas finais
    print(f"\n📊 Estatísticas finais:")
    stats = bandit.get_best_arms(3)

    for i, stat in enumerate(stats, 1):
        print(
            f"   {i}. {stat['strategy']}: {stat['pulls']} pulls, reward={stat['mean_reward']:.3f}"
        )

    print(f"\n📊 Total pulls após simulação: {bandit.get_total_pulls()}")
    print("✅ Teste concluído com sucesso!")
