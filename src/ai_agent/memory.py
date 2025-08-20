"""
Memory Manager para AI Agent Strategy
Sistema de tiny-memory persistente para experimentos e aprendizagem

Características:
- Persistência em arquivos Parquet (eficiente e compacto)
- Backup automático e rotação de arquivos
- Indexação por timestamp e estratégia
- Compressão automática para economia de espaço
- Análise estatística dos experimentos
"""

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Gerenciador de tiny-memory para experimentos do AI Agent
    
    Funcionalidades:
    - Armazenamento eficiente em Parquet
    - Indexação por timestamp e estratégia
    - Backup automático
    - Análise estatística
    - Limpeza automática de dados antigos
    """
    
    def __init__(self, memory_dir: str, max_experiments: int = 10000, 
                 backup_frequency: int = 100):
        """
        Inicializa gerenciador de memória
        
        Args:
            memory_dir: Diretório para arquivos de memória
            max_experiments: Máximo de experimentos antes da limpeza
            backup_frequency: Frequência de backup (a cada N experimentos)
        """
        self.memory_dir = Path(memory_dir)
        self.max_experiments = max_experiments
        self.backup_frequency = backup_frequency
        self.experiments_file = self.memory_dir / "experiments.parquet"
        self.backup_dir = self.memory_dir / "backups"
        
        self.ensure_dirs()
        self._experiment_count = 0
        
        logger.info(f"Memory Manager initialized: {self.memory_dir}")
    
    def ensure_dirs(self):
        """Garante que diretórios necessários existem"""
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def log_experiment(self, experiment: Dict):
        """
        Registra um experimento na tiny-memory
        
        Args:
            experiment: Dict com dados do experimento
        """
        try:
            # Validar experimento
            if not self._validate_experiment(experiment):
                logger.warning("Experimento inválido, pulando...")
                return
            
            # Adicionar timestamp se não existir
            if 'ts' not in experiment:
                experiment['ts'] = datetime.now().timestamp()
            
            # Adicionar ID único
            experiment['experiment_id'] = self._generate_experiment_id()
            
            # Converter para DataFrame
            df_new = pd.DataFrame([experiment])
            
            # Carregar dados existentes se existirem
            if self.experiments_file.exists():
                try:
                    df_existing = pd.read_parquet(self.experiments_file)
                    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                except Exception as e:
                    logger.warning(f"Erro ao carregar experimentos existentes: {e}")
                    df_combined = df_new
            else:
                df_combined = df_new
            
            # Salvar com compressão
            df_combined.to_parquet(
                self.experiments_file, 
                index=False, 
                compression='snappy'
            )
            
            self._experiment_count += 1
            
            # Backup periódico
            if self._experiment_count % self.backup_frequency == 0:
                self._create_backup()
            
            # Limpeza se necessário
            if len(df_combined) > self.max_experiments:
                self._cleanup_old_experiments()
            
            logger.debug(f"Experimento registrado: {experiment.get('strategy', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Erro ao registrar experimento: {e}")
    
    def _validate_experiment(self, experiment: Dict) -> bool:
        """
        Valida estrutura do experimento
        
        Args:
            experiment: Dict com dados do experimento
        
        Returns:
            True se experimento é válido
        """
        required_fields = ['strategy', 'params_json', 'reward']
        
        for field in required_fields:
            if field not in experiment:
                logger.warning(f"Campo obrigatório faltando: {field}")
                return False
        
        # Validar tipos
        if not isinstance(experiment['reward'], (int, float)):
            logger.warning("Campo 'reward' deve ser numérico")
            return False
        
        # Validar JSON
        try:
            if isinstance(experiment['params_json'], str):
                json.loads(experiment['params_json'])
        except json.JSONDecodeError:
            logger.warning("Campo 'params_json' não é JSON válido")
            return False
        
        return True
    
    def _generate_experiment_id(self) -> str:
        """Gera ID único para experimento"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = np.random.randint(1000, 9999)
        return f"exp_{timestamp}_{random_suffix}"
    
    def get_experiments(self, limit: Optional[int] = None, 
                       strategy: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Recupera experimentos da memória
        
        Args:
            limit: Número máximo de experimentos
            strategy: Filtrar por estratégia específica
            start_date: Data de início
            end_date: Data de fim
        
        Returns:
            DataFrame com experimentos
        """
        try:
            if not self.experiments_file.exists():
                return pd.DataFrame()
            
            df = pd.read_parquet(self.experiments_file)
            
            if df.empty:
                return df
            
            # Converter timestamp para datetime se necessário
            if 'ts' in df.columns and df['ts'].dtype in ['int64', 'float64']:
                df['datetime'] = pd.to_datetime(df['ts'], unit='s')
            
            # Filtros
            if strategy:
                df = df[df['strategy'] == strategy]
            
            if start_date and 'datetime' in df.columns:
                df = df[df['datetime'] >= start_date]
            
            if end_date and 'datetime' in df.columns:
                df = df[df['datetime'] <= end_date]
            
            # Ordenar por timestamp (mais recentes primeiro)
            if 'ts' in df.columns:
                df = df.sort_values('ts', ascending=False)
            
            # Limitar resultados
            if limit:
                df = df.head(limit)
            
            return df
            
        except Exception as e:
            logger.error(f"Erro ao recuperar experimentos: {e}")
            return pd.DataFrame()
    
    def get_strategy_stats(self, strategy: Optional[str] = None, 
                          days: int = 30) -> Dict:
        """
        Calcula estatísticas de estratégia(s)
        
        Args:
            strategy: Estratégia específica (None para todas)
            days: Número de dias para análise
        
        Returns:
            Dict com estatísticas
        """
        try:
            # Filtrar por período
            start_date = datetime.now() - timedelta(days=days)
            df = self.get_experiments(start_date=start_date, strategy=strategy)
            
            if df.empty:
                return {'error': 'Nenhum experimento encontrado'}
            
            stats = {}
            
            if strategy:
                # Estatísticas para estratégia específica
                stats = self._calculate_single_strategy_stats(df)
            else:
                # Estatísticas para todas as estratégias
                stats = self._calculate_all_strategies_stats(df)
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
            return {'error': str(e)}
    
    def _calculate_single_strategy_stats(self, df: pd.DataFrame) -> Dict:
        """Calcula estatísticas para uma estratégia"""
        if df.empty:
            return {}
        
        stats = {
            'total_experiments': len(df),
            'mean_reward': df['reward'].mean(),
            'std_reward': df['reward'].std(),
            'min_reward': df['reward'].min(),
            'max_reward': df['reward'].max(),
            'median_reward': df['reward'].median(),
        }
        
        # Adicionar métricas específicas se disponíveis
        for metric in ['sharpe', 'ret_total', 'max_dd', 'winrate', 'turnover']:
            if metric in df.columns:
                stats[f'mean_{metric}'] = df[metric].mean()
                stats[f'std_{metric}'] = df[metric].std()
        
        # Tendência (regressão linear simples no reward)
        if len(df) > 1:
            x = np.arange(len(df))
            y = df['reward'].values
            slope = np.polyfit(x, y, 1)[0]
            stats['reward_trend'] = slope
        
        return stats
    
    def _calculate_all_strategies_stats(self, df: pd.DataFrame) -> Dict:
        """Calcula estatísticas para todas as estratégias"""
        if df.empty:
            return {}
        
        stats = {
            'total_experiments': len(df),
            'unique_strategies': df['strategy'].nunique(),
            'strategies': {}
        }
        
        # Estatísticas por estratégia
        for strategy in df['strategy'].unique():
            strategy_df = df[df['strategy'] == strategy]
            stats['strategies'][strategy] = self._calculate_single_strategy_stats(strategy_df)
        
        # Ranking de estratégias por reward médio
        strategy_rewards = []
        for strategy, strategy_stats in stats['strategies'].items():
            strategy_rewards.append({
                'strategy': strategy,
                'mean_reward': strategy_stats.get('mean_reward', 0),
                'experiments': strategy_stats.get('total_experiments', 0)
            })
        
        stats['strategy_ranking'] = sorted(
            strategy_rewards, 
            key=lambda x: x['mean_reward'], 
            reverse=True
        )
        
        return stats
    
    def get_best_experiments(self, limit: int = 10, 
                           metric: str = 'reward') -> pd.DataFrame:
        """
        Retorna os melhores experimentos por métrica
        
        Args:
            limit: Número de experimentos
            metric: Métrica para ordenação
        
        Returns:
            DataFrame com melhores experimentos
        """
        try:
            df = self.get_experiments()
            
            if df.empty or metric not in df.columns:
                return pd.DataFrame()
            
            # Ordenar por métrica (descendente)
            df_sorted = df.sort_values(metric, ascending=False)
            
            return df_sorted.head(limit)
            
        except Exception as e:
            logger.error(f"Erro ao buscar melhores experimentos: {e}")
            return pd.DataFrame()
    
    def analyze_parameter_impact(self, strategy: str, 
                               parameter: str, days: int = 30) -> Dict:
        """
        Analisa impacto de um parâmetro específico na performance
        
        Args:
            strategy: Nome da estratégia
            parameter: Nome do parâmetro
            days: Período de análise
        
        Returns:
            Dict com análise do parâmetro
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            df = self.get_experiments(strategy=strategy, start_date=start_date)
            
            if df.empty:
                return {'error': 'Nenhum experimento encontrado'}
            
            # Extrair valores do parâmetro
            param_values = []
            rewards = []
            
            for _, row in df.iterrows():
                try:
                    params = json.loads(row['params_json'])
                    if parameter in params:
                        param_values.append(params[parameter])
                        rewards.append(row['reward'])
                except:
                    continue
            
            if not param_values:
                return {'error': f'Parâmetro {parameter} não encontrado'}
            
            # Análise estatística
            param_df = pd.DataFrame({
                'param_value': param_values,
                'reward': rewards
            })
            
            # Correlação
            correlation = param_df['param_value'].corr(param_df['reward'])
            
            # Agrupamento por valor do parâmetro
            grouped = param_df.groupby('param_value')['reward'].agg([
                'count', 'mean', 'std', 'min', 'max'
            ]).reset_index()
            
            # Melhor valor
            best_value = grouped.loc[grouped['mean'].idxmax(), 'param_value']
            
            return {
                'parameter': parameter,
                'strategy': strategy,
                'correlation': correlation,
                'best_value': best_value,
                'value_analysis': grouped.to_dict('records'),
                'total_experiments': len(param_values)
            }
            
        except Exception as e:
            logger.error(f"Erro na análise de parâmetro: {e}")
            return {'error': str(e)}
    
    def _create_backup(self):
        """Cria backup dos experimentos"""
        try:
            if not self.experiments_file.exists():
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"experiments_backup_{timestamp}.parquet"
            
            # Copiar arquivo
            df = pd.read_parquet(self.experiments_file)
            df.to_parquet(backup_file, index=False, compression='snappy')
            
            logger.info(f"Backup criado: {backup_file.name}")
            
            # Limpar backups antigos (manter apenas 10)
            self._cleanup_old_backups()
            
        except Exception as e:
            logger.error(f"Erro ao criar backup: {e}")
    
    def _cleanup_old_backups(self, keep: int = 10):
        """Remove backups antigos"""
        try:
            backup_files = sorted(
                self.backup_dir.glob("experiments_backup_*.parquet"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Remover backups excedentes
            for backup_file in backup_files[keep:]:
                backup_file.unlink()
                logger.debug(f"Backup removido: {backup_file.name}")
                
        except Exception as e:
            logger.error(f"Erro ao limpar backups: {e}")
    
    def _cleanup_old_experiments(self):
        """Remove experimentos antigos para manter limite"""
        try:
            df = pd.read_parquet(self.experiments_file)
            
            if len(df) <= self.max_experiments:
                return
            
            # Manter apenas os mais recentes
            df_sorted = df.sort_values('ts', ascending=False)
            df_trimmed = df_sorted.head(self.max_experiments)
            
            # Salvar
            df_trimmed.to_parquet(
                self.experiments_file, 
                index=False, 
                compression='snappy'
            )
            
            removed_count = len(df) - len(df_trimmed)
            logger.info(f"Removidos {removed_count} experimentos antigos")
            
        except Exception as e:
            logger.error(f"Erro ao limpar experimentos antigos: {e}")
    
    def export_experiments(self, format: str = 'csv', 
                          filename: Optional[str] = None) -> str:
        """
        Exporta experimentos para arquivo
        
        Args:
            format: Formato ('csv', 'json', 'parquet')
            filename: Nome do arquivo (opcional)
        
        Returns:
            Caminho do arquivo exportado
        """
        try:
            df = self.get_experiments()
            
            if df.empty:
                raise ValueError("Nenhum experimento para exportar")
            
            # Gerar nome do arquivo se não fornecido
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"experiments_export_{timestamp}.{format}"
            
            export_path = self.memory_dir / filename
            
            # Exportar no formato solicitado
            if format == 'csv':
                df.to_csv(export_path, index=False)
            elif format == 'json':
                df.to_json(export_path, orient='records', indent=2)
            elif format == 'parquet':
                df.to_parquet(export_path, index=False, compression='snappy')
            else:
                raise ValueError(f"Formato não suportado: {format}")
            
            logger.info(f"Experimentos exportados: {export_path}")
            return str(export_path)
            
        except Exception as e:
            logger.error(f"Erro ao exportar experimentos: {e}")
            raise
    
    def reset_memory(self):
        """
        Reset completo da memória (CUIDADO!)
        Remove todos os experimentos e backups
        """
        try:
            # Criar backup final antes do reset
            if self.experiments_file.exists():
                final_backup = self.backup_dir / f"final_backup_before_reset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
                df = pd.read_parquet(self.experiments_file)
                df.to_parquet(final_backup, index=False, compression='snappy')
                logger.info(f"Backup final criado: {final_backup}")
            
            # Remover arquivo principal
            if self.experiments_file.exists():
                self.experiments_file.unlink()
            
            # Reset contador
            self._experiment_count = 0
            
            logger.warning("Memory reset completed - all experiments cleared")
            
        except Exception as e:
            logger.error(f"Erro no reset da memória: {e}")
            raise
    
    def get_memory_info(self) -> Dict:
        """
        Retorna informações sobre o estado da memória
        
        Returns:
            Dict com informações da memória
        """
        try:
            info = {
                'memory_dir': str(self.memory_dir),
                'experiments_file_exists': self.experiments_file.exists(),
                'max_experiments': self.max_experiments,
                'backup_frequency': self.backup_frequency
            }
            
            if self.experiments_file.exists():
                df = pd.read_parquet(self.experiments_file)
                info.update({
                    'total_experiments': len(df),
                    'unique_strategies': df['strategy'].nunique() if not df.empty else 0,
                    'file_size_mb': self.experiments_file.stat().st_size / (1024 * 1024),
                    'oldest_experiment': df['ts'].min() if not df.empty and 'ts' in df.columns else None,
                    'newest_experiment': df['ts'].max() if not df.empty and 'ts' in df.columns else None
                })
            else:
                info.update({
                    'total_experiments': 0,
                    'unique_strategies': 0,
                    'file_size_mb': 0
                })
            
            # Informações de backup
            backup_files = list(self.backup_dir.glob("*.parquet"))
            info['backup_count'] = len(backup_files)
            info['total_backup_size_mb'] = sum(f.stat().st_size for f in backup_files) / (1024 * 1024)
            
            return info
            
        except Exception as e:
            logger.error(f"Erro ao obter informações da memória: {e}")
            return {'error': str(e)}


def create_readme_content() -> str:
    """Cria conteúdo do README para o diretório ai_agent"""
    return """# AI Agent - Tiny Memory System

## Visão Geral

O sistema de tiny-memory do AI Agent é responsável por armazenar e gerenciar todos os experimentos de aprendizagem da estratégia de IA. Utiliza arquivos Parquet para armazenamento eficiente e SQLite para o sistema de bandit.

## Estrutura de Arquivos

```
memory/
├── tiny_memory.db          # Banco SQLite com dados do bandit UCB1
├── experiments.parquet     # Experimentos de aprendizagem
└── backups/               # Backups automáticos
    ├── experiments_backup_20250116_1200.parquet
    └── ...
```

## Como Funciona

### 1. Multi-Armed Bandit (UCB1)
- Armazenado em `tiny_memory.db`
- Cada "braço" representa uma combinação estratégia + parâmetros
- Algoritmo UCB1 balanceia exploração vs exploração
- Persistente entre execuções

### 2. Experimentos
- Armazenados em `experiments.parquet`
- Cada experimento contém métricas de performance
- Backup automático a cada 100 experimentos
- Limpeza automática mantém últimos 10.000 experimentos

### 3. Aprendizagem
- AI Agent seleciona estratégia via UCB1
- Executa backtest e calcula recompensa
- Atualiza bandit com resultado
- Registra experimento na memória

## Campos dos Experimentos

- `ts`: Timestamp do experimento
- `strategy`: Nome da estratégia (ema_cross, rsi_mr, breakout)
- `params_json`: Parâmetros da estratégia em JSON
- `ret_total`: Retorno total
- `sharpe`: Sharpe ratio
- `max_dd`: Maximum drawdown
- `winrate`: Taxa de acerto
- `turnover`: Frequência de trades
- `trades`: Número total de trades
- `reward`: Recompensa calculada

## Fórmula da Recompensa

```
reward = sharpe - (lam_dd * max_dd) - (lam_cost * turnover)
```

Onde:
- `lam_dd = 0.5`: Penalização por drawdown
- `lam_cost = 0.1`: Penalização por turnover

## Como Resetar

Para resetar completamente a memória do AI Agent:

1. **Via código:**
   ```python
   ai_agent = AIAgentStrategy()
   ai_agent.reset_memory()
   ```

2. **Manualmente:**
   ```bash
   rm -rf memory/
   ```

3. **Via CLI:**
   - Advanced Settings → AI Agent Settings → Reset Memory

## Backup e Recuperação

- Backups automáticos a cada 100 experimentos
- Mantém últimos 10 backups
- Backup final antes de reset
- Exportação em CSV/JSON/Parquet disponível

## Monitoramento

Use o CLI para monitorar:
- Performance Analysis → AI Agent Statistics
- Advanced Settings → AI Agent Settings
- Strategy Explorer → AI Agent details

## Troubleshooting

### Arquivo corrompido
```bash
rm memory/experiments.parquet
# AI Agent recriará automaticamente
```

### Banco SQLite corrompido
```bash
rm memory/tiny_memory.db
# Bandit será reinicializado com braços padrão
```

### Espaço em disco
- Arquivos Parquet são comprimidos (Snappy)
- Limpeza automática remove experimentos antigos
- Backups antigos são removidos automaticamente

## Desenvolvimento

Para adicionar novas métricas aos experimentos:

1. Modifique `BacktestEngine._calculate_metrics()`
2. Atualize `MemoryManager._validate_experiment()`
3. Adicione análise em `get_strategy_stats()`

---

**Importante:** A tiny-memory é essencial para o aprendizado do AI Agent. Não remova sem necessidade, pois todo o conhecimento acumulado será perdido.
"""


if __name__ == "__main__":
    # Teste básico do memory manager
    print("🧠 Memory Manager - Teste Básico")
    
    # Criar memory manager
    memory = MemoryManager("./test_memory")
    
    # Simular alguns experimentos
    print("\n📊 Simulando experimentos...")
    
    strategies = ['ema_cross', 'rsi_mr', 'breakout']
    
    for i in range(20):
        strategy = np.random.choice(strategies)
        
        experiment = {
            'strategy': strategy,
            'params_json': json.dumps({'param1': np.random.randint(10, 50)}, sort_keys=True),
            'ret_total': np.random.normal(0.05, 0.15),
            'sharpe': np.random.normal(0.8, 0.5),
            'max_dd': np.random.uniform(0.02, 0.20),
            'winrate': np.random.uniform(0.4, 0.7),
            'turnover': np.random.uniform(0.1, 0.5),
            'trades': np.random.randint(10, 100),
            'reward': np.random.normal(0.1, 0.3)
        }
        
        memory.log_experiment(experiment)
    
    # Recuperar experimentos
    print(f"\n📊 Experimentos registrados:")
    df = memory.get_experiments(limit=5)
    print(f"   Total: {len(memory.get_experiments())}")
    print(f"   Últimos 5: {df['strategy'].tolist() if not df.empty else 'Nenhum'}")
    
    # Estatísticas
    stats = memory.get_strategy_stats()
    if 'strategies' in stats:
        print(f"\n📊 Estatísticas por estratégia:")
        for strategy, strategy_stats in stats['strategies'].items():
            print(f"   {strategy}: {strategy_stats.get('total_experiments', 0)} exp, "
                  f"reward={strategy_stats.get('mean_reward', 0):.3f}")
    
    # Informações da memória
    info = memory.get_memory_info()
    print(f"\n💾 Informações da memória:")
    print(f"   Experimentos: {info.get('total_experiments', 0)}")
    print(f"   Estratégias únicas: {info.get('unique_strategies', 0)}")
    print(f"   Tamanho do arquivo: {info.get('file_size_mb', 0):.2f} MB")
    
    print("\n✅ Teste concluído com sucesso!")
    
    # Criar README
    readme_path = Path("./test_memory") / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(create_readme_content())
    
    print(f"📄 README criado: {readme_path}")

