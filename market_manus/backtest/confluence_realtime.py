"""
Real-time Confluence Execution
Rate-limited (1 decisão por candle fechado), reenvio só em mudança de estado
"""

import pandas as pd
import time
from datetime import datetime
from typing import Optional, Callable
import yaml
from market_manus.strategies.smc.patterns import confluence_decision
from market_manus.core.signal import Signal


class RealTimeConfluenceEngine:
    """
    Motor de confluência em tempo real com rate-limiting.
    Executa 1 decisão por candle fechado e só reenvia ordem em mudança de estado.
    """
    
    def __init__(self, config_path: str = None, config: dict = None):
        """
        Args:
            config_path: Caminho para YAML de config
            config: Dict de config direto (prioritário)
        """
        if config is None:
            if config_path is None:
                config_path = "config/confluence.yaml"
            
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = config
        
        self.last_processed_timestamp = None  # Timestamp do último candle processado
        self.last_signal = None
        self.running = False
        self.stats = {
            'signals_generated': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'hold_signals': 0,
            'state_changes': 0
        }
    
    def _is_new_candle(self, candle_timestamp) -> bool:
        """
        Verifica se é um novo candle baseado no timestamp do último candle do stream.
        Data-driven gating em vez de wall-clock.
        
        Args:
            candle_timestamp: Timestamp do último candle do stream
        
        Returns:
            True se é novo candle (timestamp diferente do último processado)
        """
        if self.last_processed_timestamp is None:
            return True
        
        # Compara timestamps: só processa se mudou
        return candle_timestamp != self.last_processed_timestamp
    
    def process_candle(
        self,
        candles: pd.DataFrame,
        symbol: str,
        timeframe: str,
        callback: Optional[Callable] = None
    ) -> Optional[Signal]:
        """
        Processa novo candle e gera decisão de confluência.
        Rate-limited: só executa se é novo candle.
        Só notifica se houver mudança de estado.
        
        Args:
            candles: DataFrame OHLCV histórico + candle atual
            symbol: Símbolo (ex: "BTCUSDT")
            timeframe: Timeframe (ex: "5m")
            callback: Função callback(signal) para executar ordem (opcional)
        
        Returns:
            Signal se houver mudança de estado, None caso contrário
        """
        # Extrai timestamp do último candle do stream
        if 'timestamp' in candles.columns:
            candle_timestamp = candles['timestamp'].iloc[-1]
        elif isinstance(candles.index[-1], (pd.Timestamp, datetime)):
            candle_timestamp = candles.index[-1]
        else:
            candle_timestamp = len(candles)  # Fallback: usa índice
        
        # Rate limiting: só processa se é novo candle (data-driven)
        if not self._is_new_candle(candle_timestamp):
            return None
        
        # Atualiza timestamp do último candle processado
        self.last_processed_timestamp = candle_timestamp
        
        # Gera decisão de confluência
        signal = confluence_decision(
            candles=candles,
            symbol=symbol,
            timeframe=timeframe,
            config=self.config
        )
        
        self.stats['signals_generated'] += 1
        
        if signal.action == "BUY":
            self.stats['buy_signals'] += 1
        elif signal.action == "SELL":
            self.stats['sell_signals'] += 1
        else:
            self.stats['hold_signals'] += 1
        
        # Verifica mudança de estado
        state_changed = False
        
        if self.last_signal is None:
            # Primeiro sinal: conta como mudança se não for HOLD
            if signal.action != "HOLD":
                state_changed = True
                self.stats['state_changes'] += 1
        else:
            # Compara com sinal anterior
            if signal.action != self.last_signal.action:
                state_changed = True
                self.stats['state_changes'] += 1
        
        # Só executa callback se houver mudança de estado
        if state_changed and callback is not None:
            callback(signal)
        
        # Atualiza último sinal
        self.last_signal = signal
        
        return signal if state_changed else None
    
    def get_stats(self) -> dict:
        """Retorna estatísticas da sessão"""
        return self.stats.copy()
    
    def reset(self):
        """Reseta estado do engine"""
        self.last_processed_timestamp = None
        self.last_signal = None
        self.stats = {
            'signals_generated': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'hold_signals': 0,
            'state_changes': 0
        }


def realtime_confluence(
    data_stream: Callable,
    config_path: str = None,
    config: dict = None,
    broker_callback: Optional[Callable] = None,
    symbol: str = "BTCUSDT",
    timeframe: str = "5m",
    max_iterations: Optional[int] = None
) -> dict:
    """
    Executa confluência em tempo real com rate-limiting.
    
    Args:
        data_stream: Callable que retorna DataFrame OHLCV atualizado a cada chamada
        config_path: Caminho para YAML de config
        config: Dict de config direto
        broker_callback: Função(signal) para executar ordens (opcional)
        symbol: Símbolo para trading
        timeframe: Timeframe
        max_iterations: Máximo de iterações (None = infinito)
    
    Returns:
        Dict com estatísticas da sessão
    """
    engine = RealTimeConfluenceEngine(config_path, config)
    
    iteration = 0
    
    try:
        while True:
            # Obtém dados atualizados
            candles = data_stream()
            
            if candles is None or len(candles) == 0:
                time.sleep(1)
                continue
            
            # Processa candle
            signal = engine.process_candle(
                candles=candles,
                symbol=symbol,
                timeframe=timeframe,
                callback=broker_callback
            )
            
            # Log se houver mudança
            if signal is not None:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                      f"🔔 MUDANÇA DE ESTADO: {signal.action} "
                      f"(confidence: {signal.confidence:.2f})")
                print(f"   Razões: {signal.reasons[:3]}")  # Primeiras 3 razões
            
            iteration += 1
            
            # Verifica limite de iterações
            if max_iterations is not None and iteration >= max_iterations:
                break
            
            # Aguarda próximo tick (ajustável)
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n⏹️  Real-time confluence interrompido pelo usuário")
    
    return engine.get_stats()
