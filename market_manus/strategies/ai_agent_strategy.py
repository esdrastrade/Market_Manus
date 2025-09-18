"""
AI Agent Strategy - Multi-Armed Bandit com Tiny-Memory
Sistema de aprendizagem progressiva para trading algorítmico

Características:
- Multi-armed bandit (UCB1) para seleção de estratégias
- Tiny-memory persistente (SQLite + Parquet)
- Walk-forward validation
- Sub-estratégias: EMA Crossover, RSI Mean Reversion, Breakout
- Otimização automática de hiperparâmetros
- Recompensa baseada em Sharpe, Drawdown e Turnover
"""

import json
import logging
import sqlite3
import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# Configurar logging
logger = logging.getLogger(__name__)


class BaseStrategy:
    """Classe base para estratégias (compatibilidade)"""

    def __init__(self, **params):
        self.params = params
        self.name = "Base Strategy"
        self.risk_level = "medium"
        self.best_timeframes = ["15m", "1h"]
        self.market_conditions = "Any"

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Calcula sinais de trading"""
        return pd.Series(0, index=data.index)


class StrategyConfig:
    """Configuração de estratégia (compatibilidade)"""

    def __init__(
        self,
        name: str,
        risk_level: str,
        best_timeframes: List[str],
        market_conditions: str,
        **params,
    ):
        self.name = name
        self.risk_level = risk_level
        self.best_timeframes = best_timeframes
        self.market_conditions = market_conditions
        self.params = params


class UCB1Bandit:
    """Multi-Armed Bandit usando algoritmo UCB1"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.ensure_database()

    def ensure_database(self):
        """Garante que o banco de dados existe com a estrutura correta"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

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
                UNIQUE(strategy, params_json)
            )
        """
        )

        conn.commit()
        conn.close()

    def ensure_arms(self, strategy_seeds: List[Dict]):
        """Garante que todos os braços iniciais existem"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for seed in strategy_seeds:
            strategy = seed["strategy"]
            params = seed["params"]
            params_json = json.dumps(params, sort_keys=True)

            cursor.execute(
                """
                INSERT OR IGNORE INTO arms (strategy, params_json, last_ts)
                VALUES (?, ?, ?)
            """,
                (strategy, params_json, datetime.now().timestamp()),
            )

        conn.commit()
        conn.close()

    def select_arm(self) -> Dict:
        """Seleciona um braço usando UCB1"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Buscar todos os braços
        cursor.execute(
            """
            SELECT strategy, params_json, pulls, mean_reward
            FROM arms
            ORDER BY id
        """
        )

        arms = cursor.fetchall()
        conn.close()

        if not arms:
            raise ValueError("Nenhum braço disponível")

        # Calcular total de pulls
        total_pulls = sum(arm[2] for arm in arms)

        # Encontrar braços não explorados (pulls = 0)
        unexplored = [arm for arm in arms if arm[2] == 0]
        if unexplored:
            # Selecionar primeiro braço não explorado
            selected = unexplored[0]
            return {"strategy": selected[0], "params": json.loads(selected[1])}

        # Calcular UCB1 scores
        best_arm = None
        best_score = float("-inf")

        for arm in arms:
            strategy, params_json, pulls, mean_reward = arm

            if pulls == 0:
                ucb_score = float("inf")
            else:
                confidence = np.sqrt(2 * np.log(total_pulls) / pulls)
                ucb_score = mean_reward + confidence

            if ucb_score > best_score:
                best_score = ucb_score
                best_arm = arm

        if best_arm is None:
            # Fallback para primeiro braço
            best_arm = arms[0]

        return {"strategy": best_arm[0], "params": json.loads(best_arm[1])}

    def update_arm(self, strategy: str, params: Dict, reward: float):
        """Atualiza estatísticas de um braço"""
        params_json = json.dumps(params, sort_keys=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Buscar braço atual
        cursor.execute(
            """
            SELECT pulls, total_reward FROM arms
            WHERE strategy = ? AND params_json = ?
        """,
            (strategy, params_json),
        )

        result = cursor.fetchone()
        if result is None:
            # Braço não existe, criar
            cursor.execute(
                """
                INSERT INTO arms (strategy, params_json, pulls, total_reward, mean_reward, last_ts)
                VALUES (?, ?, 1, ?, ?, ?)
            """,
                (strategy, params_json, reward, reward, datetime.now().timestamp()),
            )
        else:
            # Atualizar braço existente
            pulls, total_reward = result
            new_pulls = pulls + 1
            new_total_reward = total_reward + reward
            new_mean_reward = new_total_reward / new_pulls

            cursor.execute(
                """
                UPDATE arms 
                SET pulls = ?, total_reward = ?, mean_reward = ?, last_ts = ?
                WHERE strategy = ? AND params_json = ?
            """,
                (
                    new_pulls,
                    new_total_reward,
                    new_mean_reward,
                    datetime.now().timestamp(),
                    strategy,
                    params_json,
                ),
            )

        conn.commit()
        conn.close()

    def get_stats(self) -> List[Dict]:
        """Retorna estatísticas de todos os braços"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT strategy, params_json, pulls, mean_reward, last_ts
            FROM arms
            ORDER BY mean_reward DESC
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
                    "last_ts": row[4],
                }
            )

        conn.close()
        return results


class BacktestEngine:
    """Engine de backtesting para validação de estratégias"""

    @staticmethod
    def backtest_signals(
        df: pd.DataFrame, signals: pd.Series, fee_bps: float = 1.5
    ) -> Dict:
        """
        Executa backtest de sinais

        Args:
            df: DataFrame com OHLCV
            signals: Series com sinais (-1, 0, 1)
            fee_bps: Taxa em basis points

        Returns:
            Dict com métricas de performance
        """
        if len(df) != len(signals):
            raise ValueError("DataFrame e signals devem ter mesmo tamanho")

        # Calcular retornos
        returns = df["close"].pct_change().fillna(0)

        # Posições (shift para simular execução no próximo bar)
        positions = signals.shift(1).fillna(0)

        # PnL bruto
        strategy_returns = positions * returns

        # Calcular custos de transação
        position_changes = positions.diff().abs().fillna(0)
        transaction_costs = position_changes * (fee_bps / 10000)

        # PnL líquido
        net_returns = strategy_returns - transaction_costs

        # Métricas
        total_return = (1 + net_returns).prod() - 1

        # Sharpe ratio (anualizado)
        if net_returns.std() > 0:
            sharpe = (net_returns.mean() / net_returns.std()) * np.sqrt(252)
        else:
            sharpe = 0

        # Maximum drawdown
        cumulative = (1 + net_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = abs(drawdown.min())

        # Win rate
        winning_trades = net_returns[net_returns > 0]
        losing_trades = net_returns[net_returns < 0]
        total_trades = len(winning_trades) + len(losing_trades)
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0

        # Turnover (frequência de mudança de posição)
        turnover = position_changes.sum() / len(df)

        return {
            "ret_total": total_return,
            "sharpe": sharpe,
            "max_dd": max_drawdown,
            "winrate": win_rate,
            "turnover": turnover,
            "trades": total_trades,
        }

    @staticmethod
    def walkforward(
        df: pd.DataFrame,
        signal_fn,
        params: Dict,
        train_size: int,
        test_size: int,
        fee_bps: float = 1.5,
    ) -> Dict:
        """
        Executa walk-forward validation

        Args:
            df: DataFrame com dados
            signal_fn: Função que gera sinais
            params: Parâmetros da estratégia
            train_size: Tamanho da janela de treino
            test_size: Tamanho da janela de teste
            fee_bps: Taxa de transação

        Returns:
            Dict com métricas agregadas
        """
        if len(df) < train_size + test_size:
            # Dados insuficientes, usar backtest simples
            signals = signal_fn(df, **params)
            return BacktestEngine.backtest_signals(df, signals, fee_bps)

        metrics_list = []

        # Walk-forward windows
        for start in range(0, len(df) - train_size - test_size + 1, test_size):
            train_end = start + train_size
            test_end = min(train_end + test_size, len(df))

            # Dados de teste
            test_df = df.iloc[train_end:test_end].copy()

            if len(test_df) < 10:  # Mínimo de barras para teste
                continue

            # Gerar sinais para período de teste
            signals = signal_fn(test_df, **params)

            # Backtest
            metrics = BacktestEngine.backtest_signals(test_df, signals, fee_bps)
            metrics_list.append(metrics)

        if not metrics_list:
            # Fallback para backtest simples
            signals = signal_fn(df, **params)
            return BacktestEngine.backtest_signals(df, signals, fee_bps)

        # Agregar métricas (média)
        aggregated = {}
        for key in metrics_list[0].keys():
            values = [m[key] for m in metrics_list if not np.isnan(m[key])]
            aggregated[key] = np.mean(values) if values else 0

        return aggregated


class MemoryManager:
    """Gerenciador de tiny-memory para experimentos"""

    def __init__(self, memory_dir: str):
        self.memory_dir = Path(memory_dir)
        self.ensure_dirs()

    def ensure_dirs(self):
        """Garante que diretórios existem"""
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def log_experiment(self, experiment: Dict):
        """Registra experimento em arquivo Parquet"""
        parquet_file = self.memory_dir / "experiments.parquet"

        # Converter para DataFrame
        df_new = pd.DataFrame([experiment])

        # Adicionar timestamp se não existir
        if "ts" not in df_new.columns:
            df_new["ts"] = datetime.now().timestamp()

        try:
            if parquet_file.exists():
                # Carregar dados existentes
                df_existing = pd.read_parquet(parquet_file)
                # Concatenar
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            else:
                df_combined = df_new

            # Salvar
            df_combined.to_parquet(parquet_file, index=False)

        except Exception as e:
            logger.warning(f"Erro ao salvar experimento: {e}")
            # Fallback: salvar apenas novo experimento
            df_new.to_parquet(parquet_file, index=False)

    def get_experiments(self, limit: int = None) -> pd.DataFrame:
        """Recupera experimentos salvos"""
        parquet_file = self.memory_dir / "experiments.parquet"

        if not parquet_file.exists():
            return pd.DataFrame()

        try:
            df = pd.read_parquet(parquet_file)
            if limit:
                df = df.tail(limit)
            return df
        except Exception as e:
            logger.warning(f"Erro ao carregar experimentos: {e}")
            return pd.DataFrame()


class SignalHelpers:
    """Funções auxiliares para geração de sinais"""

    @staticmethod
    def ema_crossover(df: pd.DataFrame, fast: int, slow: int) -> pd.Series:
        """Estratégia EMA Crossover"""
        ema_fast = df["close"].ewm(span=fast).mean()
        ema_slow = df["close"].ewm(span=slow).mean()

        signals = pd.Series(0, index=df.index)
        signals[ema_fast > ema_slow] = 1
        signals[ema_fast < ema_slow] = -1

        return signals

    @staticmethod
    def rsi_mean_reversion(
        df: pd.DataFrame, period: int, lo: float, hi: float
    ) -> pd.Series:
        """Estratégia RSI Mean Reversion"""
        # Calcular RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        signals = pd.Series(0, index=df.index)
        signals[rsi < lo] = 1  # Oversold -> Buy
        signals[rsi > hi] = -1  # Overbought -> Sell

        return signals

    @staticmethod
    def breakout(df: pd.DataFrame, lookback: int, buffer_bps: float) -> pd.Series:
        """Estratégia Breakout"""
        # Calcular máximas e mínimas móveis
        high_max = df["high"].rolling(window=lookback).max()
        low_min = df["low"].rolling(window=lookback).min()

        # Níveis de breakout com buffer
        breakout_high = high_max * (1 + buffer_bps / 10000)
        breakout_low = low_min * (1 - buffer_bps / 10000)

        signals = pd.Series(0, index=df.index)
        signals[df["high"] > breakout_high] = 1  # Breakout para cima
        signals[df["low"] < breakout_low] = -1  # Breakout para baixo

        return signals


class AIAgentStrategy(BaseStrategy):
    """
    Estratégia AI Agent com Multi-Armed Bandit e Tiny-Memory

    Características:
    - Seleção dinâmica de sub-estratégias via UCB1
    - Otimização automática de hiperparâmetros
    - Aprendizagem walk-forward
    - Memória persistente entre execuções
    - Recompensa baseada em Sharpe, Drawdown e Turnover
    """

    def __init__(
        self,
        fee_bps: float = 1.5,
        lam_dd: float = 0.5,
        lam_cost: float = 0.1,
        train: int = 1000,
        test: int = 250,
        **kwargs,
    ):
        super().__init__(**kwargs)

        # Parâmetros
        self.fee_bps = fee_bps
        self.lam_dd = lam_dd  # Penalização por drawdown
        self.lam_cost = lam_cost  # Penalização por turnover
        self.train_size = train
        self.test_size = test

        # Configuração da estratégia
        self.name = "AI Agent (Bandit)"
        self.risk_level = "variable"
        self.best_timeframes = ["1m", "5m", "15m"]
        self.market_conditions = "Qualquer (com detecção de regime)"

        # Inicializar componentes
        self._setup_components()

        # Garantir braços iniciais
        self._ensure_initial_arms()

    def _setup_components(self):
        """Configura componentes do AI Agent"""
        # Diretório de memória
        memory_dir = Path("./memory")
        memory_dir.mkdir(parents=True, exist_ok=True)

        # Bandit e memória
        self.bandit = UCB1Bandit(str(memory_dir / "tiny_memory.db"))
        self.memory = MemoryManager(str(memory_dir))

        # Engine de backtest
        self.backtest_engine = BacktestEngine()

        logger.info("AI Agent components initialized")

    def _ensure_initial_arms(self):
        """Garante que braços iniciais existem"""
        strategy_seeds = [
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

        self.bandit.ensure_arms(strategy_seeds)

    def _generate_signals_for_strategy(
        self, df: pd.DataFrame, strategy: str, params: Dict
    ) -> pd.Series:
        """Gera sinais para uma estratégia específica"""
        if strategy == "ema_cross":
            return SignalHelpers.ema_crossover(df, params["fast"], params["slow"])
        elif strategy == "rsi_mr":
            return SignalHelpers.rsi_mean_reversion(
                df, params["period"], params["lo"], params["hi"]
            )
        elif strategy == "breakout":
            return SignalHelpers.breakout(df, params["lookback"], params["buffer_bps"])
        else:
            # Fallback: sem sinal
            return pd.Series(0, index=df.index)

    def _calculate_reward(self, metrics: Dict) -> float:
        """
        Calcula recompensa baseada em métricas

        Formula: reward = sharpe - lam_dd * max_dd - lam_cost * turnover
        """
        sharpe = metrics.get("sharpe", 0)
        max_dd = metrics.get("max_dd", 0)
        turnover = metrics.get("turnover", 0)

        reward = sharpe - (self.lam_dd * max_dd) - (self.lam_cost * turnover)

        return reward

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Método principal: calcula sinais usando AI Agent

        Processo:
        1. Seleciona braço (estratégia + parâmetros) via UCB1
        2. Gera sinais para todo o DataFrame
        3. Executa walk-forward validation
        4. Calcula recompensa
        5. Atualiza bandit
        6. Registra experimento
        7. Retorna sinal para última barra
        """
        try:
            # Validar dados
            if len(data) < 50:
                logger.warning("Dados insuficientes para AI Agent")
                return pd.Series(0, index=data.index)

            # Garantir colunas necessárias
            required_cols = ["open", "high", "low", "close", "volume"]
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                logger.error(f"Colunas faltando: {missing_cols}")
                return pd.Series(0, index=data.index)

            # 1. Selecionar braço via UCB1
            selected_arm = self.bandit.select_arm()
            strategy = selected_arm["strategy"]
            params = selected_arm["params"]

            logger.info(f"AI Agent selected: {strategy} with params {params}")

            # 2. Gerar sinais para todo o DataFrame
            signals = self._generate_signals_for_strategy(data, strategy, params)

            # 3. Executar walk-forward validation
            if len(data) >= self.train_size + self.test_size:
                metrics = self.backtest_engine.walkforward(
                    data,
                    self._generate_signals_for_strategy,
                    {"strategy": strategy, **params},
                    self.train_size,
                    self.test_size,
                    self.fee_bps,
                )
            else:
                # Fallback para backtest simples
                metrics = self.backtest_engine.backtest_signals(
                    data, signals, self.fee_bps
                )

            # 4. Calcular recompensa
            reward = self._calculate_reward(metrics)

            # 5. Atualizar bandit
            self.bandit.update_arm(strategy, params, reward)

            # 6. Registrar experimento
            experiment = {
                "ts": datetime.now().timestamp(),
                "symbol": "UNKNOWN",  # Será preenchido externamente se disponível
                "strategy": strategy,
                "params_json": json.dumps(params, sort_keys=True),
                "ret_total": metrics.get("ret_total", 0),
                "sharpe": metrics.get("sharpe", 0),
                "max_dd": metrics.get("max_dd", 0),
                "winrate": metrics.get("winrate", 0),
                "turnover": metrics.get("turnover", 0),
                "trades": metrics.get("trades", 0),
                "reward": reward,
            }

            self.memory.log_experiment(experiment)

            logger.info(
                f"AI Agent experiment logged: reward={reward:.3f}, sharpe={metrics.get('sharpe', 0):.3f}"
            )

            # 7. Retornar sinais (compatibilidade com BaseStrategy)
            return signals

        except Exception as e:
            logger.error(f"Erro no AI Agent: {e}")
            # Fallback: sem sinal
            return pd.Series(0, index=data.index)

    def get_bandit_stats(self) -> List[Dict]:
        """Retorna estatísticas do bandit"""
        return self.bandit.get_stats()

    def get_recent_experiments(self, limit: int = 10) -> pd.DataFrame:
        """Retorna experimentos recentes"""
        return self.memory.get_experiments(limit)

    def reset_memory(self):
        """Reset completo da memória (CUIDADO!)"""
        memory_dir = Path("./memory")

        # Remover banco de dados
        db_file = memory_dir / "tiny_memory.db"
        if db_file.exists():
            db_file.unlink()

        # Remover experimentos
        parquet_file = memory_dir / "experiments.parquet"
        if parquet_file.exists():
            parquet_file.unlink()

        # Reinicializar
        self._setup_components()
        self._ensure_initial_arms()

        logger.info("AI Agent memory reset completed")


# Configuração para registro automático (compatibilidade com o sistema)
STRATEGY_CONFIG = {
    "key": "ai_agent_bandit",
    "class": AIAgentStrategy,
    "factory": lambda **params: AIAgentStrategy(**params),
    "default_params": {
        "fee_bps": 1.5,
        "lam_dd": 0.5,
        "lam_cost": 0.1,
        "train": 1000,
        "test": 250,
    },
}


def create_ai_agent_strategy(**params) -> AIAgentStrategy:
    """Factory function para criar AI Agent Strategy"""
    return AIAgentStrategy(**params)


if __name__ == "__main__":
    # Teste básico
    print("🤖 AI Agent Strategy - Teste Básico")

    # Criar dados sintéticos
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=1000, freq="1H")

    # Simular dados OHLCV
    base_price = 50000
    returns = np.random.normal(0, 0.02, 1000)
    prices = base_price * (1 + returns).cumprod()

    data = pd.DataFrame(
        {
            "open": prices * (1 + np.random.normal(0, 0.001, 1000)),
            "high": prices * (1 + np.abs(np.random.normal(0, 0.005, 1000))),
            "low": prices * (1 - np.abs(np.random.normal(0, 0.005, 1000))),
            "close": prices,
            "volume": np.random.uniform(100, 1000, 1000),
        },
        index=dates,
    )

    # Criar AI Agent
    ai_agent = AIAgentStrategy()

    # Gerar sinais
    print("🔄 Gerando sinais...")
    signals = ai_agent.calculate_signals(data)

    print(f"✅ Sinais gerados: {len(signals)} pontos")
    print(
        f"📊 Distribuição: Long={sum(signals==1)}, Short={sum(signals==-1)}, Neutro={sum(signals==0)}"
    )

    # Estatísticas do bandit
    stats = ai_agent.get_bandit_stats()
    print(f"\n🤖 Estatísticas do Bandit:")
    for stat in stats[:3]:  # Top 3
        print(
            f"   {stat['strategy']}: {stat['pulls']} pulls, reward={stat['mean_reward']:.3f}"
        )

    # Experimentos recentes
    experiments = ai_agent.get_recent_experiments(5)
    if not experiments.empty:
        print(f"\n📊 Últimos experimentos:")
        for _, exp in experiments.iterrows():
            print(
                f"   {exp['strategy']}: reward={exp['reward']:.3f}, sharpe={exp['sharpe']:.3f}"
            )

    print("\n🎉 Teste concluído com sucesso!")
