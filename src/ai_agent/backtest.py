"""
Backtest Engine para AI Agent Strategy
Sistema de validação de estratégias com walk-forward analysis

Características:
- Backtest de sinais com custos de transação
- Walk-forward validation
- Métricas completas: Sharpe, Drawdown, Win Rate, Turnover
- Suporte a diferentes frequências de dados
- Tratamento robusto de bordas e dados faltantes
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Callable, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Engine de backtesting para validação de estratégias
    
    Funcionalidades:
    - Backtest simples com custos de transação
    - Walk-forward validation
    - Cálculo de métricas de performance
    - Tratamento de dados faltantes
    - Suporte a diferentes tipos de sinais
    """
    
    @staticmethod
    def validate_data(df: pd.DataFrame) -> bool:
        """
        Valida se DataFrame tem estrutura correta para backtest
        
        Args:
            df: DataFrame com dados OHLCV
        
        Returns:
            True se dados são válidos
        """
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        
        # Verificar colunas
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Colunas faltando: {missing_cols}")
            return False
        
        # Verificar se há dados suficientes
        if len(df) < 10:
            logger.error(f"Dados insuficientes: {len(df)} barras")
            return False
        
        # Verificar valores válidos
        for col in required_cols:
            if df[col].isna().all():
                logger.error(f"Coluna {col} contém apenas NaN")
                return False
        
        # Verificar consistência OHLC
        invalid_ohlc = (
            (df['high'] < df['low']) |
            (df['high'] < df['open']) |
            (df['high'] < df['close']) |
            (df['low'] > df['open']) |
            (df['low'] > df['close'])
        ).any()
        
        if invalid_ohlc:
            logger.warning("Dados OHLC inconsistentes detectados")
        
        return True
    
    @staticmethod
    def backtest_signals(df: pd.DataFrame, signals: pd.Series, fee_bps: float = 1.5) -> Dict:
        """
        Executa backtest de sinais de trading
        
        Args:
            df: DataFrame com dados OHLCV
            signals: Series com sinais (-1, 0, 1)
            fee_bps: Taxa de transação em basis points
        
        Returns:
            Dict com métricas de performance
        """
        try:
            # Validar dados
            if not BacktestEngine.validate_data(df):
                return BacktestEngine._empty_metrics()
            
            if len(df) != len(signals):
                logger.error(f"Tamanhos incompatíveis: df={len(df)}, signals={len(signals)}")
                return BacktestEngine._empty_metrics()
            
            # Calcular retornos dos preços
            returns = df['close'].pct_change().fillna(0)
            
            # Posições (shift para simular execução no próximo bar)
            positions = signals.shift(1).fillna(0)
            
            # Limitar posições a [-1, 0, 1]
            positions = positions.clip(-1, 1)
            
            # Retornos da estratégia (brutos)
            strategy_returns = positions * returns
            
            # Calcular custos de transação
            position_changes = positions.diff().abs().fillna(0)
            transaction_costs = position_changes * (fee_bps / 10000)
            
            # Retornos líquidos
            net_returns = strategy_returns - transaction_costs
            
            # Calcular métricas
            metrics = BacktestEngine._calculate_metrics(net_returns, positions)
            
            # Adicionar informações extras
            metrics.update({
                'total_bars': len(df),
                'position_changes': position_changes.sum(),
                'total_transaction_costs': transaction_costs.sum(),
                'gross_return': strategy_returns.sum(),
                'net_return': net_returns.sum()
            })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Erro no backtest: {e}")
            return BacktestEngine._empty_metrics()
    
    @staticmethod
    def _calculate_metrics(returns: pd.Series, positions: pd.Series) -> Dict:
        """
        Calcula métricas de performance
        
        Args:
            returns: Series com retornos líquidos
            positions: Series com posições
        
        Returns:
            Dict com métricas
        """
        # Retorno total
        total_return = (1 + returns).prod() - 1
        
        # Sharpe ratio (anualizado assumindo dados horários)
        if returns.std() > 0:
            # Assumir 24*365 = 8760 períodos por ano para dados horários
            # Ajustar baseado na frequência real se necessário
            periods_per_year = 8760  # Default para dados horários
            sharpe = (returns.mean() / returns.std()) * np.sqrt(periods_per_year)
        else:
            sharpe = 0
        
        # Maximum drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = abs(drawdown.min()) if len(drawdown) > 0 else 0
        
        # Win rate e trade statistics
        non_zero_returns = returns[returns != 0]
        if len(non_zero_returns) > 0:
            winning_trades = non_zero_returns[non_zero_returns > 0]
            losing_trades = non_zero_returns[non_zero_returns < 0]
            
            total_trades = len(non_zero_returns)
            win_rate = len(winning_trades) / total_trades
            
            # Profit factor
            gross_profit = winning_trades.sum() if len(winning_trades) > 0 else 0
            gross_loss = abs(losing_trades.sum()) if len(losing_trades) > 0 else 0
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            # Average win/loss
            avg_win = winning_trades.mean() if len(winning_trades) > 0 else 0
            avg_loss = losing_trades.mean() if len(losing_trades) > 0 else 0
        else:
            total_trades = 0
            win_rate = 0
            profit_factor = 0
            avg_win = 0
            avg_loss = 0
        
        # Turnover (frequência de mudança de posição)
        position_changes = positions.diff().abs().fillna(0)
        turnover = position_changes.sum() / len(positions) if len(positions) > 0 else 0
        
        # Volatilidade anualizada
        volatility = returns.std() * np.sqrt(8760) if returns.std() > 0 else 0
        
        # Sortino ratio (usando apenas downside deviation)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            sortino = (returns.mean() / downside_returns.std()) * np.sqrt(8760)
        else:
            sortino = 0
        
        return {
            'ret_total': total_return,
            'sharpe': sharpe,
            'sortino': sortino,
            'max_dd': max_drawdown,
            'winrate': win_rate,
            'turnover': turnover,
            'trades': total_trades,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'volatility': volatility
        }
    
    @staticmethod
    def _empty_metrics() -> Dict:
        """Retorna métricas vazias para casos de erro"""
        return {
            'ret_total': 0.0,
            'sharpe': 0.0,
            'sortino': 0.0,
            'max_dd': 0.0,
            'winrate': 0.0,
            'turnover': 0.0,
            'trades': 0,
            'profit_factor': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'volatility': 0.0
        }
    
    @staticmethod
    def walkforward(df: pd.DataFrame, signal_fn: Callable, params: Dict,
                   train_size: int, test_size: int, fee_bps: float = 1.5) -> Dict:
        """
        Executa walk-forward validation
        
        Args:
            df: DataFrame com dados OHLCV
            signal_fn: Função que gera sinais (df, **params) -> Series
            params: Parâmetros para função de sinais
            train_size: Tamanho da janela de treino
            test_size: Tamanho da janela de teste
            fee_bps: Taxa de transação
        
        Returns:
            Dict com métricas agregadas
        """
        try:
            # Validar dados
            if not BacktestEngine.validate_data(df):
                return BacktestEngine._empty_metrics()
            
            if len(df) < train_size + test_size:
                logger.warning(f"Dados insuficientes para walk-forward: {len(df)} < {train_size + test_size}")
                # Fallback para backtest simples
                signals = signal_fn(df, **params)
                return BacktestEngine.backtest_signals(df, signals, fee_bps)
            
            metrics_list = []
            windows_processed = 0
            
            # Walk-forward windows
            step_size = max(1, test_size // 2)  # Overlap de 50%
            
            for start in range(0, len(df) - train_size - test_size + 1, step_size):
                train_end = start + train_size
                test_end = min(train_end + test_size, len(df))
                
                # Dados de treino e teste
                train_df = df.iloc[start:train_end].copy()
                test_df = df.iloc[train_end:test_end].copy()
                
                if len(test_df) < 10:  # Mínimo de barras para teste válido
                    continue
                
                try:
                    # Gerar sinais para período de teste
                    # Nota: Em implementação real, poderia usar dados de treino para otimização
                    signals = signal_fn(test_df, **params)
                    
                    # Backtest do período de teste
                    window_metrics = BacktestEngine.backtest_signals(test_df, signals, fee_bps)
                    
                    # Adicionar informações da janela
                    window_metrics.update({
                        'window_start': start,
                        'window_train_end': train_end,
                        'window_test_end': test_end,
                        'window_test_size': len(test_df)
                    })
                    
                    metrics_list.append(window_metrics)
                    windows_processed += 1
                    
                except Exception as e:
                    logger.warning(f"Erro na janela {start}-{test_end}: {e}")
                    continue
            
            if not metrics_list:
                logger.warning("Nenhuma janela processada com sucesso")
                # Fallback para backtest simples
                signals = signal_fn(df, **params)
                return BacktestEngine.backtest_signals(df, signals, fee_bps)
            
            # Agregar métricas
            aggregated = BacktestEngine._aggregate_walkforward_metrics(metrics_list)
            
            # Adicionar informações do walk-forward
            aggregated.update({
                'walkforward_windows': windows_processed,
                'walkforward_train_size': train_size,
                'walkforward_test_size': test_size,
                'walkforward_total_bars': len(df)
            })
            
            logger.info(f"Walk-forward completed: {windows_processed} windows processed")
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Erro no walk-forward: {e}")
            return BacktestEngine._empty_metrics()
    
    @staticmethod
    def _aggregate_walkforward_metrics(metrics_list: List[Dict]) -> Dict:
        """
        Agrega métricas de múltiplas janelas walk-forward
        
        Args:
            metrics_list: Lista de dicts com métricas de cada janela
        
        Returns:
            Dict com métricas agregadas
        """
        if not metrics_list:
            return BacktestEngine._empty_metrics()
        
        # Métricas que devem ser somadas
        sum_metrics = ['trades', 'total_bars', 'position_changes']
        
        # Métricas que devem ser calculadas como média ponderada
        weighted_metrics = ['ret_total', 'sharpe', 'sortino', 'max_dd', 'winrate', 
                          'turnover', 'profit_factor', 'volatility']
        
        # Métricas que devem ser calculadas como média simples
        simple_avg_metrics = ['avg_win', 'avg_loss']
        
        aggregated = {}
        
        # Somar métricas apropriadas
        for metric in sum_metrics:
            values = [m.get(metric, 0) for m in metrics_list]
            aggregated[metric] = sum(values)
        
        # Média ponderada por tamanho da janela
        total_weight = sum(m.get('window_test_size', 1) for m in metrics_list)
        
        for metric in weighted_metrics:
            if total_weight > 0:
                weighted_sum = sum(
                    m.get(metric, 0) * m.get('window_test_size', 1) 
                    for m in metrics_list
                )
                aggregated[metric] = weighted_sum / total_weight
            else:
                aggregated[metric] = 0
        
        # Média simples
        for metric in simple_avg_metrics:
            values = [m.get(metric, 0) for m in metrics_list if not np.isnan(m.get(metric, 0))]
            aggregated[metric] = np.mean(values) if values else 0
        
        # Métricas especiais
        # Max drawdown: pior caso entre todas as janelas
        max_dd_values = [m.get('max_dd', 0) for m in metrics_list]
        aggregated['max_dd'] = max(max_dd_values) if max_dd_values else 0
        
        # Sharpe: média ponderada já calculada acima
        # Win rate: média ponderada já calculada acima
        
        return aggregated
    
    @staticmethod
    def optimize_parameters(df: pd.DataFrame, signal_fn: Callable, 
                          param_grid: Dict, metric: str = 'sharpe',
                          train_size: int = 1000, test_size: int = 250,
                          fee_bps: float = 1.5) -> Tuple[Dict, Dict]:
        """
        Otimização de parâmetros usando grid search com walk-forward
        
        Args:
            df: DataFrame com dados
            signal_fn: Função que gera sinais
            param_grid: Dict com ranges de parâmetros
            metric: Métrica para otimização ('sharpe', 'ret_total', etc.)
            train_size: Tamanho da janela de treino
            test_size: Tamanho da janela de teste
            fee_bps: Taxa de transação
        
        Returns:
            Tuple com (melhores_params, melhores_metrics)
        """
        try:
            # Gerar combinações de parâmetros
            param_combinations = BacktestEngine._generate_param_combinations(param_grid)
            
            if not param_combinations:
                logger.error("Nenhuma combinação de parâmetros gerada")
                return {}, BacktestEngine._empty_metrics()
            
            best_params = None
            best_metrics = None
            best_score = float('-inf')
            
            logger.info(f"Otimizando {len(param_combinations)} combinações de parâmetros")
            
            for i, params in enumerate(param_combinations):
                try:
                    # Executar walk-forward para esta combinação
                    metrics = BacktestEngine.walkforward(
                        df, signal_fn, params, train_size, test_size, fee_bps
                    )
                    
                    # Avaliar score
                    score = metrics.get(metric, float('-inf'))
                    
                    if score > best_score:
                        best_score = score
                        best_params = params.copy()
                        best_metrics = metrics.copy()
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"Processadas {i + 1}/{len(param_combinations)} combinações")
                
                except Exception as e:
                    logger.warning(f"Erro na combinação {params}: {e}")
                    continue
            
            if best_params is None:
                logger.error("Nenhuma combinação válida encontrada")
                return {}, BacktestEngine._empty_metrics()
            
            logger.info(f"Melhor combinação: {best_params} (score={best_score:.3f})")
            
            return best_params, best_metrics
            
        except Exception as e:
            logger.error(f"Erro na otimização: {e}")
            return {}, BacktestEngine._empty_metrics()
    
    @staticmethod
    def _generate_param_combinations(param_grid: Dict) -> List[Dict]:
        """
        Gera todas as combinações de parâmetros do grid
        
        Args:
            param_grid: Dict com listas de valores para cada parâmetro
        
        Returns:
            Lista de dicts com combinações de parâmetros
        """
        import itertools
        
        if not param_grid:
            return []
        
        # Extrair nomes e valores dos parâmetros
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        
        # Gerar produto cartesiano
        combinations = []
        for combination in itertools.product(*param_values):
            param_dict = dict(zip(param_names, combination))
            combinations.append(param_dict)
        
        return combinations


def create_sample_data(n_bars: int = 1000, base_price: float = 50000, 
                      volatility: float = 0.02, seed: int = 42) -> pd.DataFrame:
    """
    Cria dados sintéticos para teste
    
    Args:
        n_bars: Número de barras
        base_price: Preço base
        volatility: Volatilidade diária
        seed: Seed para reprodutibilidade
    
    Returns:
        DataFrame com dados OHLCV sintéticos
    """
    np.random.seed(seed)
    
    # Gerar retornos
    returns = np.random.normal(0, volatility, n_bars)
    prices = base_price * (1 + returns).cumprod()
    
    # Gerar OHLC com ruído
    noise_factor = 0.001
    
    data = pd.DataFrame({
        'open': prices * (1 + np.random.normal(0, noise_factor, n_bars)),
        'high': prices * (1 + np.abs(np.random.normal(0, noise_factor * 2, n_bars))),
        'low': prices * (1 - np.abs(np.random.normal(0, noise_factor * 2, n_bars))),
        'close': prices,
        'volume': np.random.uniform(100, 1000, n_bars)
    })
    
    # Garantir consistência OHLC
    data['high'] = data[['open', 'high', 'close']].max(axis=1)
    data['low'] = data[['open', 'low', 'close']].min(axis=1)
    
    # Adicionar timestamp
    data.index = pd.date_range('2024-01-01', periods=n_bars, freq='1H')
    
    return data


if __name__ == "__main__":
    # Teste básico do backtest engine
    print("📊 Backtest Engine - Teste Básico")
    
    # Criar dados sintéticos
    data = create_sample_data(1000)
    print(f"✅ Dados criados: {len(data)} barras")
    
    # Estratégia simples: buy and hold
    signals = pd.Series(1, index=data.index)  # Sempre long
    
    # Executar backtest
    print("\n🔄 Executando backtest...")
    metrics = BacktestEngine.backtest_signals(data, signals, fee_bps=1.5)
    
    print(f"📊 Métricas:")
    print(f"   Retorno total: {metrics['ret_total']:.2%}")
    print(f"   Sharpe ratio: {metrics['sharpe']:.2f}")
    print(f"   Max drawdown: {metrics['max_dd']:.2%}")
    print(f"   Win rate: {metrics['winrate']:.1%}")
    print(f"   Total trades: {metrics['trades']}")
    
    # Teste walk-forward
    print("\n🔄 Testando walk-forward...")
    
    def simple_ma_strategy(df, period=20):
        """Estratégia simples de média móvel"""
        ma = df['close'].rolling(period).mean()
        signals = pd.Series(0, index=df.index)
        signals[df['close'] > ma] = 1
        signals[df['close'] < ma] = -1
        return signals
    
    wf_metrics = BacktestEngine.walkforward(
        data, simple_ma_strategy, {'period': 20}, 
        train_size=500, test_size=100
    )
    
    print(f"📊 Walk-forward metrics:")
    print(f"   Retorno total: {wf_metrics['ret_total']:.2%}")
    print(f"   Sharpe ratio: {wf_metrics['sharpe']:.2f}")
    print(f"   Janelas processadas: {wf_metrics.get('walkforward_windows', 0)}")
    
    print("\n✅ Teste concluído com sucesso!")

