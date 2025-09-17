#!/usr/bin/env python3
"""
Market Analysis Agent para Sistema de Scalping Automatizado
Responsável por análise OHLC, cálculo de indicadores e geração de sinais
Autor: Manus AI
Data: 17 de Julho de 2025
"""

import json
import os
import sys
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Adicionar diretório pai ao path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent, SuggestionType, AlertSeverity

class MarketAnalysisAgent(BaseAgent):
    """
    Agente de Análise de Mercado
    
    Responsabilidades:
    - Coleta dados OHLC em tempo real
    - Calcula indicadores técnicos (EMA, RSI, Bollinger Bands, Volume)
    - Implementa estratégias de scalping
    - Gera sinais ponderados com níveis de confiança
    - Analisa performance histórica dos sinais
    - Sugere ajustes automáticos de parâmetros
    
    Frequência: A cada 5 minutos via PowerShell scheduled task
    """
    
    def __init__(self):
        super().__init__("MarketAnalysisAgent")
        
        # Histórico de sinais para análise de performance
        self.signals_history = []
        self.performance_window = self.config.get("monitoring", {}).get("performance_window_trades", 100)
        
        # Cache de dados de mercado
        self.market_data_cache = {}
        self.cache_duration = 300  # 5 minutos
        
        # Métricas de performance
        self.performance_metrics = {
            "total_signals": 0,
            "signals_by_strategy": {},
            "avg_confidence": 0.0,
            "last_signal_time": None
        }
        
        self.logger.info("MarketAnalysisAgent inicializado")
    
    def fetch_market_data(self, symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
        """
        Busca dados de mercado OHLC
        
        Em produção, conectaria com CCXT ou API real da exchange
        Para demonstração, gera dados simulados realistas
        
        Args:
            symbol: Par de trading (ex: BTC/USDT)
            timeframe: Timeframe (5m, 15m, 1h)
            limit: Número de candles
            
        Returns:
            pd.DataFrame: Dados OHLC com timestamp
        """
        cache_key = f"{symbol}_{timeframe}_{limit}"
        current_time = time.time()
        
        # Verificar cache
        if cache_key in self.market_data_cache:
            cached_data, cache_time = self.market_data_cache[cache_key]
            if current_time - cache_time < self.cache_duration:
                self.logger.debug(f"Usando dados em cache para {symbol}")
                return cached_data
        
        try:
            # Simular dados realistas baseados no símbolo
            base_prices = {
                "BTC/USDT": 45000,
                "ETH/USDT": 3000,
                "BNB/USDT": 300,
                "ADA/USDT": 0.5,
                "DOT/USDT": 8.0
            }
            
            base_price = base_prices.get(symbol, 1000)
            
            # Gerar timestamps
            if timeframe == "5m":
                freq = "5T"
            elif timeframe == "15m":
                freq = "15T"
            elif timeframe == "1h":
                freq = "1H"
            else:
                freq = "5T"
            
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=limit * 5)  # Aproximação
            dates = pd.date_range(start=start_time, end=end_time, freq=freq)[:limit]
            
            # Gerar dados OHLC realistas
            data = []
            price = base_price
            
            for i, date in enumerate(dates):
                # Simular movimento de preço com tendência e volatilidade
                trend = np.sin(i * 0.1) * 0.001  # Tendência suave
                volatility = np.random.normal(0, 0.005)  # Volatilidade
                
                price_change = trend + volatility
                new_price = price * (1 + price_change)
                
                # Gerar OHLC
                high_factor = 1 + abs(np.random.normal(0, 0.002))
                low_factor = 1 - abs(np.random.normal(0, 0.002))
                
                open_price = price
                close_price = new_price
                high_price = max(open_price, close_price) * high_factor
                low_price = min(open_price, close_price) * low_factor
                
                # Volume baseado na volatilidade
                base_volume = 1000
                volume_factor = 1 + abs(price_change) * 10
                volume = base_volume * volume_factor * np.random.uniform(0.5, 2.0)
                
                data.append({
                    'timestamp': date,
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'volume': round(volume, 2)
                })
                
                price = new_price
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            
            # Armazenar em cache
            self.market_data_cache[cache_key] = (df, current_time)
            
            self.logger.debug(f"Dados de mercado obtidos para {symbol}: {len(df)} candles")
            return df
            
        except Exception as e:
            self.handle_error(e, f"fetch_market_data({symbol})")
            return pd.DataFrame()
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calcula Média Móvel Exponencial"""
        return prices.ewm(span=period, adjust=False).mean()
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calcula Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calcula Bollinger Bands"""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper, middle, lower
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula todos os indicadores técnicos necessários
        
        Args:
            df: DataFrame com dados OHLC
            
        Returns:
            pd.DataFrame: DataFrame com indicadores adicionados
        """
        if df.empty or len(df) < 50:
            self.logger.warning("Dados insuficientes para calcular indicadores")
            return df
        
        try:
            # EMAs para estratégia Triple EMA
            ema_periods = self.config["strategies"]["ema_triple"]["periods"]
            for period in ema_periods:
                df[f'ema_{period}'] = self.calculate_ema(df['close'], period)
            
            # RSI
            rsi_period = self.config["strategies"]["bollinger_rsi"]["rsi_period"]
            df['rsi'] = self.calculate_rsi(df['close'], rsi_period)
            
            # Bollinger Bands
            bb_period = self.config["strategies"]["bollinger_rsi"]["bb_period"]
            bb_std = self.config["strategies"]["bollinger_rsi"].get("bb_std", 2.0)
            df['bb_upper'], df['bb_middle'], df['bb_lower'] = self.calculate_bollinger_bands(
                df['close'], bb_period, bb_std
            )
            
            # Indicadores de Volume
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            
            # ATR para stop loss dinâmico
            df['tr'] = np.maximum(
                df['high'] - df['low'],
                np.maximum(
                    abs(df['high'] - df['close'].shift(1)),
                    abs(df['low'] - df['close'].shift(1))
                )
            )
            df['atr'] = df['tr'].rolling(window=14).mean()
            
            # Volatilidade
            df['volatility'] = df['close'].pct_change().rolling(window=20).std()
            
            self.logger.debug("Indicadores calculados com sucesso")
            return df
            
        except Exception as e:
            self.handle_error(e, "calculate_indicators")
            return df
    
    def analyze_ema_triple_strategy(self, df: pd.DataFrame) -> Dict:
        """
        Analisa estratégia EMA Triple Crossover
        
        Args:
            df: DataFrame com indicadores
            
        Returns:
            Dict: Resultado da análise
        """
        if len(df) < 30:
            return {'signal': 'HOLD', 'confidence': 0, 'reason': 'Dados insuficientes'}
        
        try:
            latest = df.iloc[-1]
            ema_8, ema_13, ema_21 = latest['ema_8'], latest['ema_13'], latest['ema_21']
            
            # Verificar alinhamento bullish
            if ema_8 > ema_13 > ema_21:
                # Calcular força do sinal baseado na separação das EMAs
                separation = ((ema_8 - ema_21) / ema_21) * 100
                confidence = min(0.9, 0.6 + (separation * 10))  # Base 60%, max 90%
                
                return {
                    'signal': 'BUY',
                    'confidence': confidence,
                    'reason': f'EMA bullish alignment (sep: {separation:.3f}%)',
                    'ema_values': {'ema_8': ema_8, 'ema_13': ema_13, 'ema_21': ema_21}
                }
            
            # Verificar alinhamento bearish
            elif ema_8 < ema_13 < ema_21:
                separation = ((ema_21 - ema_8) / ema_21) * 100
                confidence = min(0.9, 0.6 + (separation * 10))
                
                return {
                    'signal': 'SELL',
                    'confidence': confidence,
                    'reason': f'EMA bearish alignment (sep: {separation:.3f}%)',
                    'ema_values': {'ema_8': ema_8, 'ema_13': ema_13, 'ema_21': ema_21}
                }
            
            else:
                return {
                    'signal': 'HOLD',
                    'confidence': 0.3,
                    'reason': 'EMAs não alinhadas',
                    'ema_values': {'ema_8': ema_8, 'ema_13': ema_13, 'ema_21': ema_21}
                }
                
        except Exception as e:
            self.handle_error(e, "analyze_ema_triple_strategy")
            return {'signal': 'HOLD', 'confidence': 0, 'reason': 'Erro no cálculo'}
    
    def analyze_bollinger_rsi_strategy(self, df: pd.DataFrame) -> Dict:
        """
        Analisa estratégia Bollinger Bands + RSI
        
        Args:
            df: DataFrame com indicadores
            
        Returns:
            Dict: Resultado da análise
        """
        if len(df) < 30:
            return {'signal': 'HOLD', 'confidence': 0, 'reason': 'Dados insuficientes'}
        
        try:
            latest = df.iloc[-1]
            price = latest['close']
            bb_upper, bb_lower = latest['bb_upper'], latest['bb_lower']
            rsi = latest['rsi']
            
            # Calcular posição dentro das Bollinger Bands
            bb_range = bb_upper - bb_lower
            if bb_range == 0:
                bb_position = 0.5
            else:
                bb_position = (price - bb_lower) / bb_range
            
            rsi_oversold = self.config["strategies"]["bollinger_rsi"]["rsi_oversold"]
            rsi_overbought = self.config["strategies"]["bollinger_rsi"]["rsi_overbought"]
            
            # Sinal de compra: preço próximo à banda inferior + RSI oversold
            if bb_position < 0.2 and rsi < rsi_oversold:
                confidence = 0.9 - (bb_position * 2) + ((rsi_oversold - rsi) / 100)
                confidence = min(0.95, max(0.7, confidence))
                
                return {
                    'signal': 'BUY',
                    'confidence': confidence,
                    'reason': f'Oversold: BB pos {bb_position:.2f}, RSI {rsi:.1f}',
                    'indicators': {'bb_position': bb_position, 'rsi': rsi}
                }
            
            # Sinal de venda: preço próximo à banda superior + RSI overbought
            elif bb_position > 0.8 and rsi > rsi_overbought:
                confidence = 0.9 - ((1 - bb_position) * 2) + ((rsi - rsi_overbought) / 100)
                confidence = min(0.95, max(0.7, confidence))
                
                return {
                    'signal': 'SELL',
                    'confidence': confidence,
                    'reason': f'Overbought: BB pos {bb_position:.2f}, RSI {rsi:.1f}',
                    'indicators': {'bb_position': bb_position, 'rsi': rsi}
                }
            
            else:
                return {
                    'signal': 'HOLD',
                    'confidence': 0.4,
                    'reason': f'Neutro: BB pos {bb_position:.2f}, RSI {rsi:.1f}',
                    'indicators': {'bb_position': bb_position, 'rsi': rsi}
                }
                
        except Exception as e:
            self.handle_error(e, "analyze_bollinger_rsi_strategy")
            return {'signal': 'HOLD', 'confidence': 0, 'reason': 'Erro no cálculo'}
    
    def analyze_breakout_strategy(self, df: pd.DataFrame) -> Dict:
        """
        Analisa estratégia Volume Breakout
        
        Args:
            df: DataFrame com indicadores
            
        Returns:
            Dict: Resultado da análise
        """
        if len(df) < 20:
            return {'signal': 'HOLD', 'confidence': 0, 'reason': 'Dados insuficientes'}
        
        try:
            latest = df.iloc[-1]
            volume_threshold = self.config["strategies"]["breakout"]["volume_threshold"]
            lookback = self.config["strategies"]["breakout"].get("lookback_periods", 10)
            
            # Verificar volume anômalo
            volume_ratio = latest['volume_ratio']
            if volume_ratio < volume_threshold:
                return {
                    'signal': 'HOLD',
                    'confidence': 0.2,
                    'reason': f'Volume baixo: {volume_ratio:.2f}x',
                    'volume_ratio': volume_ratio
                }
            
            # Analisar breakout de preço
            recent_data = df.tail(lookback)
            recent_high = recent_data['high'].max()
            recent_low = recent_data['low'].min()
            current_price = latest['close']
            
            # Breakout bullish
            if current_price > recent_high:
                breakout_strength = (current_price - recent_high) / recent_high
                confidence = min(0.9, 0.7 + (breakout_strength * 20) + ((volume_ratio - volume_threshold) * 0.1))
                
                return {
                    'signal': 'BUY',
                    'confidence': confidence,
                    'reason': f'Bullish breakout: {breakout_strength:.3f}%, vol {volume_ratio:.1f}x',
                    'breakout_data': {
                        'strength': breakout_strength,
                        'volume_ratio': volume_ratio,
                        'recent_high': recent_high
                    }
                }
            
            # Breakout bearish
            elif current_price < recent_low:
                breakout_strength = (recent_low - current_price) / recent_low
                confidence = min(0.9, 0.7 + (breakout_strength * 20) + ((volume_ratio - volume_threshold) * 0.1))
                
                return {
                    'signal': 'SELL',
                    'confidence': confidence,
                    'reason': f'Bearish breakout: {breakout_strength:.3f}%, vol {volume_ratio:.1f}x',
                    'breakout_data': {
                        'strength': breakout_strength,
                        'volume_ratio': volume_ratio,
                        'recent_low': recent_low
                    }
                }
            
            else:
                return {
                    'signal': 'HOLD',
                    'confidence': 0.5,
                    'reason': f'Volume alto mas sem breakout: {volume_ratio:.1f}x',
                    'volume_ratio': volume_ratio
                }
                
        except Exception as e:
            self.handle_error(e, "analyze_breakout_strategy")
            return {'signal': 'HOLD', 'confidence': 0, 'reason': 'Erro no cálculo'}
    
    def generate_combined_signal(self, symbol: str, df: pd.DataFrame) -> Dict:
        """
        Combina sinais de todas as estratégias em um sinal final ponderado
        
        Args:
            symbol: Par de trading
            df: DataFrame com indicadores
            
        Returns:
            Dict: Sinal final combinado
        """
        try:
            individual_signals = []
            
            # Analisar cada estratégia habilitada
            strategies = self.config["strategies"]
            
            if strategies["ema_triple"]["enabled"]:
                ema_result = self.analyze_ema_triple_strategy(df)
                ema_result["strategy"] = "ema_triple"
                ema_result["weight"] = strategies["ema_triple"]["weight"]
                individual_signals.append(ema_result)
            
            if strategies["bollinger_rsi"]["enabled"]:
                bb_rsi_result = self.analyze_bollinger_rsi_strategy(df)
                bb_rsi_result["strategy"] = "bollinger_rsi"
                bb_rsi_result["weight"] = strategies["bollinger_rsi"]["weight"]
                individual_signals.append(bb_rsi_result)
            
            if strategies["breakout"]["enabled"]:
                breakout_result = self.analyze_breakout_strategy(df)
                breakout_result["strategy"] = "breakout"
                breakout_result["weight"] = strategies["breakout"]["weight"]
                individual_signals.append(breakout_result)
            
            # Calcular scores ponderados
            buy_score = sum(
                s['confidence'] * s['weight'] 
                for s in individual_signals 
                if s['signal'] == 'BUY'
            )
            
            sell_score = sum(
                s['confidence'] * s['weight'] 
                for s in individual_signals 
                if s['signal'] == 'SELL'
            )
            
            hold_score = sum(
                s['confidence'] * s['weight'] 
                for s in individual_signals 
                if s['signal'] == 'HOLD'
            )
            
            # Determinar sinal final
            min_confidence = 0.6  # Confiança mínima para gerar sinal
            
            if buy_score > sell_score and buy_score > hold_score and buy_score >= min_confidence:
                final_signal = 'BUY'
                final_confidence = buy_score
            elif sell_score > buy_score and sell_score > hold_score and sell_score >= min_confidence:
                final_signal = 'SELL'
                final_confidence = sell_score
            else:
                final_signal = 'HOLD'
                final_confidence = max(buy_score, sell_score, hold_score)
            
            # Construir sinal final
            latest = df.iloc[-1]
            signal = {
                'symbol': symbol,
                'signal': final_signal,
                'confidence': round(final_confidence, 3),
                'price': round(latest['close'], 2),
                'timestamp': datetime.now().isoformat(),
                'individual_signals': individual_signals,
                'scores': {
                    'buy_score': round(buy_score, 3),
                    'sell_score': round(sell_score, 3),
                    'hold_score': round(hold_score, 3)
                },
                'market_data': {
                    'volume': latest['volume'],
                    'volatility': latest.get('volatility', 0),
                    'atr': latest.get('atr', 0)
                }
            }
            
            return signal
            
        except Exception as e:
            self.handle_error(e, f"generate_combined_signal({symbol})")
            return {
                'symbol': symbol,
                'signal': 'HOLD',
                'confidence': 0,
                'price': 0,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def save_signal(self, signal: Dict):
        """
        Salva sinal gerado em arquivo JSON
        
        Args:
            signal: Dicionário com dados do sinal
        """
        try:
            # Criar nome do arquivo com timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            symbol_clean = signal['symbol'].replace('/', '_')
            filename = f"signal_{symbol_clean}_{timestamp}.json"
            filepath = Path("data/signals") / filename
            
            # Salvar sinal
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(signal, f, indent=2, ensure_ascii=False)
            
            # Adicionar ao histórico
            self.signals_history.append(signal)
            
            # Manter apenas últimos sinais na memória
            if len(self.signals_history) > self.performance_window:
                self.signals_history = self.signals_history[-self.performance_window:]
            
            self.logger.info(f"Sinal salvo: {signal['symbol']} {signal['signal']} (conf: {signal['confidence']:.2f})")
            
        except Exception as e:
            self.handle_error(e, "save_signal")
    
    def analyze_performance(self) -> Dict:
        """
        Analisa performance dos sinais gerados
        
        Returns:
            Dict: Métricas de performance
        """
        try:
            # Carregar histórico de sinais se necessário
            if not self.signals_history:
                self.signals_history = self.get_performance_window_data("signals", self.performance_window)
            
            if len(self.signals_history) < 10:
                return {
                    'status': 'insufficient_data',
                    'total_signals': len(self.signals_history),
                    'message': 'Dados insuficientes para análise'
                }
            
            recent_signals = self.signals_history[-self.performance_window:]
            
            # Métricas básicas
            total_signals = len(recent_signals)
            buy_signals = [s for s in recent_signals if s['signal'] == 'BUY']
            sell_signals = [s for s in recent_signals if s['signal'] == 'SELL']
            hold_signals = [s for s in recent_signals if s['signal'] == 'HOLD']
            
            # Simular win rate baseado na confiança (em produção, usaria dados reais)
            total_trades = len(buy_signals) + len(sell_signals)
            if total_trades > 0:
                avg_confidence = np.mean([s['confidence'] for s in recent_signals if s['signal'] != 'HOLD'])
                simulated_win_rate = min(0.8, avg_confidence * 0.9)  # Aproximação
            else:
                avg_confidence = 0
                simulated_win_rate = 0
            
            # Análise por estratégia
            strategy_performance = {}
            for strategy in ['ema_triple', 'bollinger_rsi', 'breakout']:
                strategy_signals = []
                for signal in recent_signals:
                    for individual in signal.get('individual_signals', []):
                        if individual.get('strategy') == strategy:
                            strategy_signals.append(individual)
                
                if strategy_signals:
                    strategy_performance[strategy] = {
                        'signal_count': len(strategy_signals),
                        'avg_confidence': np.mean([s['confidence'] for s in strategy_signals]),
                        'buy_signals': len([s for s in strategy_signals if s['signal'] == 'BUY']),
                        'sell_signals': len([s for s in strategy_signals if s['signal'] == 'SELL']),
                        'estimated_win_rate': min(0.8, np.mean([s['confidence'] for s in strategy_signals]) * 0.9)
                    }
            
            # Métricas de distribuição de confiança
            confidences = [s['confidence'] for s in recent_signals]
            confidence_stats = self.calculate_basic_stats(confidences)
            
            performance = {
                'total_signals': total_signals,
                'signal_distribution': {
                    'buy': len(buy_signals),
                    'sell': len(sell_signals),
                    'hold': len(hold_signals)
                },
                'total_trades': total_trades,
                'avg_confidence': round(avg_confidence, 3),
                'simulated_win_rate': round(simulated_win_rate, 3),
                'confidence_stats': confidence_stats,
                'strategy_performance': strategy_performance,
                'last_analysis': datetime.now().isoformat(),
                'analysis_window': self.performance_window
            }
            
            return performance
            
        except Exception as e:
            self.handle_error(e, "analyze_performance")
            return {'status': 'error', 'message': str(e)}
    
    def suggest_improvements(self) -> List[Dict]:
        """
        Sugere melhorias baseadas na análise de performance
        
        Returns:
            List[Dict]: Lista de sugestões de melhoria
        """
        try:
            performance = self.analyze_performance()
            suggestions = []
            
            if performance.get('status') == 'insufficient_data':
                return suggestions
            
            # Sugestão 1: Ajustar RSI se win rate baixo
            if performance.get('simulated_win_rate', 0) < 0.6:
                current_rsi_oversold = self.config["strategies"]["bollinger_rsi"]["rsi_oversold"]
                suggested_rsi = max(20, current_rsi_oversold - 5)
                
                suggestions.append({
                    "type": SuggestionType.PARAMETER_ADJUSTMENT,
                    "priority": "high",
                    "current_metrics": {
                        "win_rate": performance['simulated_win_rate'],
                        "total_trades": performance['total_trades']
                    },
                    "suggested_changes": {
                        "file": "config/trading_config.json",
                        "line_range": [15, 20],
                        "parameter": "strategies.bollinger_rsi.rsi_oversold",
                        "current_value": current_rsi_oversold,
                        "suggested_value": suggested_rsi,
                        "reason": f"Win rate {performance['simulated_win_rate']:.1%} abaixo do target 60% - ajustar RSI para sinais mais conservadores",
                        "expected_improvement": "Reduzir falsos positivos em condições de sobrevenda"
                    }
                })
            
            # Sugestão 2: Ajustar períodos EMA se estratégia com baixa performance
            ema_perf = performance['strategy_performance'].get('ema_triple', {})
            if ema_perf.get('estimated_win_rate', 0) < 0.55:
                current_periods = self.config["strategies"]["ema_triple"]["periods"]
                suggested_periods = [p + 1 for p in current_periods]  # Períodos mais longos
                
                suggestions.append({
                    "type": SuggestionType.STRATEGY_OPTIMIZATION,
                    "priority": "medium",
                    "current_metrics": ema_perf,
                    "suggested_changes": {
                        "file": "config/trading_config.json",
                        "line_range": [8, 12],
                        "parameter": "strategies.ema_triple.periods",
                        "current_value": current_periods,
                        "suggested_value": suggested_periods,
                        "reason": f"EMA strategy win rate {ema_perf.get('estimated_win_rate', 0):.1%} - ajustar períodos para melhor responsividade",
                        "expected_improvement": "Melhor alinhamento com volatilidade atual do mercado"
                    }
                })
            
            # Sugestão 3: Ajustar threshold de volume se muitos sinais fracos
            if performance['avg_confidence'] < 0.7:
                current_threshold = self.config["strategies"]["breakout"]["volume_threshold"]
                suggested_threshold = current_threshold + 0.3
                
                suggestions.append({
                    "type": SuggestionType.PARAMETER_ADJUSTMENT,
                    "priority": "medium",
                    "current_metrics": {"avg_confidence": performance['avg_confidence']},
                    "suggested_changes": {
                        "file": "config/trading_config.json",
                        "line_range": [25, 30],
                        "parameter": "strategies.breakout.volume_threshold",
                        "current_value": current_threshold,
                        "suggested_value": suggested_threshold,
                        "reason": f"Confiança média {performance['avg_confidence']:.1%} baixa - aumentar threshold de volume para sinais mais fortes",
                        "expected_improvement": "Filtrar breakouts falsos e melhorar qualidade dos sinais"
                    }
                })
            
            # Sugestão 4: Desabilitar estratégia com performance muito baixa
            for strategy, perf in performance['strategy_performance'].items():
                if perf.get('estimated_win_rate', 0) < 0.4 and perf.get('signal_count', 0) > 10:
                    suggestions.append({
                        "type": SuggestionType.STRATEGY_OPTIMIZATION,
                        "priority": "high",
                        "current_metrics": perf,
                        "suggested_changes": {
                            "file": "config/trading_config.json",
                            "line_range": [1, 50],
                            "parameter": f"strategies.{strategy}.enabled",
                            "current_value": True,
                            "suggested_value": False,
                            "reason": f"Estratégia {strategy} com win rate muito baixo ({perf['estimated_win_rate']:.1%}) - considerar desabilitar temporariamente",
                            "expected_improvement": "Melhorar performance geral removendo estratégia problemática"
                        }
                    })
            
            return suggestions
            
        except Exception as e:
            self.handle_error(e, "suggest_improvements")
            return []
    
    def run(self):
        """
        Executa ciclo principal do agente de análise de mercado
        """
        self.logger.info("Iniciando ciclo de análise de mercado")
        
        try:
            symbols = self.config["trading"]["symbols"]
            timeframe = self.config["trading"]["timeframe"]
            
            signals_generated = 0
            
            # Processar cada símbolo configurado
            for symbol in symbols:
                self.logger.info(f"Analisando {symbol}")
                
                # Buscar dados de mercado
                df = self.fetch_market_data(symbol, timeframe)
                
                if df.empty:
                    self.logger.warning(f"Não foi possível obter dados para {symbol}")
                    continue
                
                # Calcular indicadores técnicos
                df = self.calculate_indicators(df)
                
                # Gerar sinal combinado
                signal = self.generate_combined_signal(symbol, df)
                
                # Salvar sinal se configurado
                if self.config.get("monitoring", {}).get("save_signals", True):
                    self.save_signal(signal)
                
                signals_generated += 1
                
                self.logger.info(
                    f"Sinal gerado para {symbol}: {signal['signal']} "
                    f"(confiança: {signal['confidence']:.2f})"
                )
            
            # Analisar performance e gerar sugestões
            performance = self.analyze_performance()
            self.save_metrics(performance)
            
            suggestions = self.suggest_improvements()
            for suggestion in suggestions:
                self.save_suggestion(suggestion)
            
            # Atualizar métricas de performance
            self.performance_metrics.update({
                "total_signals": self.performance_metrics["total_signals"] + signals_generated,
                "last_signal_time": datetime.now().isoformat()
            })
            
            self.logger.info(
                f"Ciclo de análise concluído: {signals_generated} sinais gerados, "
                f"{len(suggestions)} sugestões criadas"
            )
            
        except Exception as e:
            self.handle_error(e, "run")
            raise

def main():
    """Função principal para execução standalone"""
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Modo de teste
        agent = MarketAnalysisAgent()
        print("Executando teste do MarketAnalysisAgent...")
        agent.run()
        print("Teste concluído com sucesso!")
    else:
        # Execução normal
        agent = MarketAnalysisAgent()
        agent.run_with_error_handling()

if __name__ == "__main__":
    main()

