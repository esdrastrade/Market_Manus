#!/usr/bin/env python3
"""
CONTRATO ÚNICO DAS ESTRATÉGIAS - Market Manus
Padronização de entrada e saída para todas as estratégias
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Callable
from abc import ABC, abstractmethod


class StrategyContract:
    """
    Contrato único para padronização de estratégias
    
    ENTRADA: DataFrame com ['open', 'high', 'low', 'close', 'volume', 'timestamp'] (UTC)
    SAÍDA: DataFrame com ['signal', 'entry', 'strength'] + colunas de indicadores
    """
    
    REQUIRED_INPUT_COLUMNS = ['open', 'high', 'low', 'close', 'volume', 'timestamp']
    REQUIRED_OUTPUT_COLUMNS = ['signal', 'entry', 'strength']
    
    @staticmethod
    def validate_input(df: pd.DataFrame) -> bool:
        """
        Valida se o DataFrame de entrada possui as colunas obrigatórias
        
        Args:
            df: DataFrame de entrada
            
        Returns:
            True se válido, False caso contrário
            
        Raises:
            ValueError: Se colunas obrigatórias estiverem faltando
        """
        missing_columns = [col for col in StrategyContract.REQUIRED_INPUT_COLUMNS if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Colunas obrigatórias faltando: {missing_columns}")
        
        if len(df) == 0:
            raise ValueError("DataFrame não pode estar vazio")
            
        return True
    
    @staticmethod
    def validate_output(df: pd.DataFrame) -> bool:
        """
        Valida se o DataFrame de saída possui as colunas obrigatórias
        
        Args:
            df: DataFrame de saída
            
        Returns:
            True se válido, False caso contrário
            
        Raises:
            ValueError: Se colunas obrigatórias estiverem faltando
        """
        missing_columns = [col for col in StrategyContract.REQUIRED_OUTPUT_COLUMNS if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Colunas de saída obrigatórias faltando: {missing_columns}")
        
        # Validar valores de signal
        if not df['signal'].isin([-1, 0, 1]).all():
            raise ValueError("Coluna 'signal' deve conter apenas valores -1, 0, 1")
        
        # Validar valores de strength
        if not ((df['strength'] >= 0) & (df['strength'] <= 1)).all():
            raise ValueError("Coluna 'strength' deve conter valores entre 0 e 1")
            
        return True
    
    @staticmethod
    def normalize_strength(values: pd.Series, method: str = 'minmax') -> pd.Series:
        """
        Normaliza valores de força para o intervalo [0, 1]
        
        Args:
            values: Série de valores a normalizar
            method: Método de normalização ('minmax', 'zscore')
            
        Returns:
            Série normalizada entre 0 e 1
        """
        if method == 'minmax':
            min_val = values.min()
            max_val = values.max()
            if max_val == min_val:
                return pd.Series(0.5, index=values.index)
            return (values - min_val) / (max_val - min_val)
        
        elif method == 'zscore':
            # Z-score normalizado e clampado para [0, 1]
            mean_val = values.mean()
            std_val = values.std()
            if std_val == 0:
                return pd.Series(0.5, index=values.index)
            zscore = (values - mean_val) / std_val
            # Clampar entre -3 e 3, depois normalizar para [0, 1]
            zscore_clamped = np.clip(zscore, -3, 3)
            return (zscore_clamped + 3) / 6
        
        else:
            raise ValueError(f"Método de normalização desconhecido: {method}")


class BaseStrategyV2(ABC):
    """
    Classe base para estratégias seguindo o contrato único
    """
    
    def __init__(self, name: str, min_periods: int = 20):
        """
        Inicializa estratégia
        
        Args:
            name: Nome da estratégia
            min_periods: Número mínimo de períodos necessários
        """
        self.name = name
        self.min_periods = min_periods
    
    @abstractmethod
    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Executa a estratégia seguindo o contrato único
        
        Args:
            df: DataFrame com ['open', 'high', 'low', 'close', 'volume', 'timestamp']
            params: Parâmetros da estratégia
            
        Returns:
            DataFrame com ['signal', 'entry', 'strength'] + colunas de indicadores
        """
        pass
    
    def validate_and_run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Valida entrada, executa estratégia e valida saída
        
        Args:
            df: DataFrame de entrada
            params: Parâmetros da estratégia
            
        Returns:
            DataFrame de saída validado
        """
        # Validar entrada
        StrategyContract.validate_input(df)
        
        # Verificar se há dados suficientes
        if len(df) < self.min_periods:
            raise ValueError(f"Dados insuficientes: {len(df)} < {self.min_periods} (min_periods)")
        
        # Executar estratégia
        result = self.run(df, params)
        
        # Validar saída
        StrategyContract.validate_output(result)
        
        return result


# Implementações das estratégias seguindo o contrato único

class RSIMeanReversionV2(BaseStrategyV2):
    """RSI Mean Reversion Strategy seguindo contrato único"""
    
    def __init__(self):
        super().__init__("RSI Mean Reversion", min_periods=14)
    
    def calculate_rsi_wilder(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calcula RSI usando suavização de Wilder"""
        delta = prices.diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        
        # EWMA com alpha=1/period (equivalente à suavização de Wilder)
        roll_up = up.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        roll_down = down.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        
        rs = roll_up / roll_down
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Executa estratégia RSI Mean Reversion
        
        Args:
            df: DataFrame com OHLCV
            params: {'period': 14, 'buy_threshold': 30, 'sell_threshold': 70}
            
        Returns:
            DataFrame com sinais RSI
        """
        result = df.copy()
        
        # Parâmetros
        period = params.get('period', 14)
        buy_threshold = params.get('buy_threshold', 30)
        sell_threshold = params.get('sell_threshold', 70)
        
        # Calcular RSI
        result['rsi'] = self.calculate_rsi_wilder(result['close'], period)
        
        # Gerar sinais
        result['signal'] = 0
        result.loc[result['rsi'] < buy_threshold, 'signal'] = 1   # Compra (sobrevendido)
        result.loc[result['rsi'] > sell_threshold, 'signal'] = -1  # Venda (sobrecomprado)
        
        # Calcular entry (mudanças de posição)
        result['entry'] = result['signal'].diff().fillna(0)
        
        # Calcular strength baseado na distância dos thresholds
        strength_buy = np.where(result['rsi'] < buy_threshold, 
                               (buy_threshold - result['rsi']) / buy_threshold, 0)
        strength_sell = np.where(result['rsi'] > sell_threshold,
                                (result['rsi'] - sell_threshold) / (100 - sell_threshold), 0)
        
        result['strength'] = np.maximum(strength_buy, strength_sell)
        result['strength'] = np.clip(result['strength'], 0, 1)
        
        return result


class EMACrossoverV2(BaseStrategyV2):
    """EMA Crossover Strategy seguindo contrato único"""
    
    def __init__(self):
        super().__init__("EMA Crossover", min_periods=26)
    
    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Executa estratégia EMA Crossover
        
        Args:
            df: DataFrame com OHLCV
            params: {'fast_period': 12, 'slow_period': 26}
            
        Returns:
            DataFrame com sinais EMA
        """
        result = df.copy()
        
        # Parâmetros
        fast_period = params.get('fast_period', 12)
        slow_period = params.get('slow_period', 26)
        
        # Calcular EMAs
        result['ema_fast'] = result['close'].ewm(span=fast_period, min_periods=fast_period).mean()
        result['ema_slow'] = result['close'].ewm(span=slow_period, min_periods=slow_period).mean()
        
        # Gerar sinais
        result['signal'] = 0
        result.loc[result['ema_fast'] > result['ema_slow'], 'signal'] = 1   # Compra
        result.loc[result['ema_fast'] < result['ema_slow'], 'signal'] = -1  # Venda
        
        # Calcular entry (mudanças de posição)
        result['entry'] = result['signal'].diff().fillna(0)
        
        # Calcular strength baseado na diferença percentual entre EMAs
        ema_diff = abs(result['ema_fast'] - result['ema_slow']) / result['ema_slow']
        result['strength'] = StrategyContract.normalize_strength(ema_diff, method='minmax')
        
        return result


class BollingerBreakoutV2(BaseStrategyV2):
    """Bollinger Bands Breakout Strategy seguindo contrato único"""
    
    def __init__(self):
        super().__init__("Bollinger Breakout", min_periods=20)
    
    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Executa estratégia Bollinger Breakout
        
        Args:
            df: DataFrame com OHLCV
            params: {'period': 20, 'std_dev': 2}
            
        Returns:
            DataFrame com sinais Bollinger
        """
        result = df.copy()
        
        # Parâmetros
        period = params.get('period', 20)
        std_dev = params.get('std_dev', 2)
        
        # Calcular Bollinger Bands
        result['bb_middle'] = result['close'].rolling(window=period, min_periods=period).mean()
        bb_std = result['close'].rolling(window=period, min_periods=period).std()
        result['bb_upper'] = result['bb_middle'] + (bb_std * std_dev)
        result['bb_lower'] = result['bb_middle'] - (bb_std * std_dev)
        
        # Gerar sinais
        result['signal'] = 0
        result.loc[result['close'] > result['bb_upper'], 'signal'] = 1   # Breakout para cima
        result.loc[result['close'] < result['bb_lower'], 'signal'] = -1  # Breakout para baixo
        
        # Calcular entry (mudanças de posição)
        result['entry'] = result['signal'].diff().fillna(0)
        
        # Calcular strength baseado na distância das bandas
        upper_distance = (result['close'] - result['bb_upper']) / result['bb_upper']
        lower_distance = (result['bb_lower'] - result['close']) / result['bb_lower']
        
        strength_values = np.maximum(
            np.where(result['close'] > result['bb_upper'], upper_distance, 0),
            np.where(result['close'] < result['bb_lower'], lower_distance, 0)
        )
        
        result['strength'] = StrategyContract.normalize_strength(pd.Series(strength_values), method='minmax')
        
        return result


class MACDStrategyV2(BaseStrategyV2):
    """MACD Strategy seguindo contrato único"""
    
    def __init__(self):
        super().__init__("MACD Strategy", min_periods=26)
    
    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Executa estratégia MACD
        
        Args:
            df: DataFrame com OHLCV
            params: {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}
            
        Returns:
            DataFrame com sinais MACD
        """
        result = df.copy()
        
        # Parâmetros
        fast_period = params.get('fast_period', 12)
        slow_period = params.get('slow_period', 26)
        signal_period = params.get('signal_period', 9)
        
        # Calcular MACD
        ema_fast = result['close'].ewm(span=fast_period, min_periods=fast_period).mean()
        ema_slow = result['close'].ewm(span=slow_period, min_periods=slow_period).mean()
        
        result['macd'] = ema_fast - ema_slow
        result['macd_signal'] = result['macd'].ewm(span=signal_period, min_periods=signal_period).mean()
        result['macd_histogram'] = result['macd'] - result['macd_signal']
        
        # Gerar sinais
        result['signal'] = 0
        result.loc[result['macd'] > result['macd_signal'], 'signal'] = 1   # Compra
        result.loc[result['macd'] < result['macd_signal'], 'signal'] = -1  # Venda
        
        # Calcular entry (mudanças de posição)
        result['entry'] = result['signal'].diff().fillna(0)
        
        # Calcular strength baseado no histograma MACD
        result['strength'] = StrategyContract.normalize_strength(
            abs(result['macd_histogram']), method='minmax'
        )
        
        return result


# Registry de estratégias seguindo contrato único
STRATEGY_REGISTRY_V2 = {
    'rsi_mean_reversion': {
        'class': RSIMeanReversionV2,
        'default_params': {'period': 14, 'buy_threshold': 30, 'sell_threshold': 70},
        'description': 'RSI Mean Reversion com suavização de Wilder',
        'risk_level': 'medium',
        'best_timeframes': ['5m', '15m', '30m', '1h']
    },
    'ema_crossover': {
        'class': EMACrossoverV2,
        'default_params': {'fast_period': 12, 'slow_period': 26},
        'description': 'Cruzamento de médias móveis exponenciais',
        'risk_level': 'low',
        'best_timeframes': ['15m', '30m', '1h', '4h']
    },
    'bollinger_breakout': {
        'class': BollingerBreakoutV2,
        'default_params': {'period': 20, 'std_dev': 2},
        'description': 'Breakout das Bandas de Bollinger',
        'risk_level': 'high',
        'best_timeframes': ['5m', '15m', '30m']
    },
    'macd_strategy': {
        'class': MACDStrategyV2,
        'default_params': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9},
        'description': 'Estratégia baseada no indicador MACD',
        'risk_level': 'medium',
        'best_timeframes': ['15m', '30m', '1h', '4h']
    }
}


def get_strategy(strategy_key: str) -> BaseStrategyV2:
    """
    Cria instância de estratégia pelo nome
    
    Args:
        strategy_key: Chave da estratégia
        
    Returns:
        Instância da estratégia
        
    Raises:
        ValueError: Se estratégia não encontrada
    """
    if strategy_key not in STRATEGY_REGISTRY_V2:
        available = list(STRATEGY_REGISTRY_V2.keys())
        raise ValueError(f"Estratégia '{strategy_key}' não encontrada. Disponíveis: {available}")
    
    strategy_config = STRATEGY_REGISTRY_V2[strategy_key]
    return strategy_config['class']()


def run_strategy(strategy_key: str, df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """
    Executa estratégia com validação completa
    
    Args:
        strategy_key: Chave da estratégia
        df: DataFrame com OHLCV
        params: Parâmetros personalizados (opcional)
        
    Returns:
        DataFrame com sinais validados
    """
    strategy = get_strategy(strategy_key)
    
    # Usar parâmetros padrão se não fornecidos
    if params is None:
        params = STRATEGY_REGISTRY_V2[strategy_key]['default_params']
    else:
        # Mesclar com parâmetros padrão
        default_params = STRATEGY_REGISTRY_V2[strategy_key]['default_params'].copy()
        default_params.update(params)
        params = default_params
    
    return strategy.validate_and_run(df, params)


def list_available_strategies() -> dict:
    """
    Lista todas as estratégias disponíveis
    
    Returns:
        Dicionário com informações das estratégias
    """
    return {
        key: {
            'description': config['description'],
            'risk_level': config['risk_level'],
            'best_timeframes': config['best_timeframes'],
            'default_params': config['default_params']
        }
        for key, config in STRATEGY_REGISTRY_V2.items()
    }


if __name__ == "__main__":
    # Teste básico do contrato
    import datetime
    
    # Criar dados de teste
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    test_data = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100)
    })
    
    print("🧪 Testando contrato único das estratégias...")
    
    # Testar cada estratégia
    for strategy_key in STRATEGY_REGISTRY_V2.keys():
        try:
            result = run_strategy(strategy_key, test_data)
            print(f"✅ {strategy_key}: {len(result)} registros, {result['signal'].sum()} sinais")
        except Exception as e:
            print(f"❌ {strategy_key}: {e}")
    
    print("\\n📋 Estratégias disponíveis:")
    for key, info in list_available_strategies().items():
        print(f"   {key}: {info['description']} ({info['risk_level']} risk)")
