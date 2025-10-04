"""
Market Context Analyzer
Analisa últimos 60 dias para identificar regime de mercado (BULLISH/BEARISH/CORREÇÃO)
Usado para ajustar estratégias baseado no contexto macro
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class MarketContext:
    """Representa o contexto atual do mercado"""
    regime: str  # "BULLISH", "BEARISH", "CORRECTION"
    confidence: float  # 0.0 a 1.0
    trend_strength: float  # ADX value
    volatility: float  # ATR normalized
    price_change_pct: float  # % change over period
    recommendations: Dict[str, float]  # Strategy weight adjustments
    analysis_period: str  # Period analyzed
    
    def __str__(self):
        emoji = "📈" if self.regime == "BULLISH" else ("📉" if self.regime == "BEARISH" else "🔄")
        return f"{emoji} {self.regime} (Confiança: {self.confidence:.1%})"


class MarketContextAnalyzer:
    """
    Analisa contexto de mercado dos últimos 60 dias
    Identifica regime e ajusta estratégias
    """
    
    def __init__(self, lookback_days: int = 60):
        """
        Args:
            lookback_days: Número de dias para análise (padrão 60)
        """
        self.lookback_days = lookback_days
        
        # Thresholds para classificação
        self.adx_strong_threshold = 25  # ADX > 25 = tendência forte
        self.ma_slope_threshold = 0.001  # Inclinação mínima para tendência
        
    def analyze(
        self,
        data_provider,
        symbol: str,
        timeframe: str = "1h"
    ) -> Optional[MarketContext]:
        """
        Analisa contexto de mercado
        
        Args:
            data_provider: Provider de dados (Binance/Bybit)
            symbol: Símbolo do ativo
            timeframe: Timeframe para análise
            
        Returns:
            MarketContext com análise completa ou None se falhar
        """
        try:
            # Buscar dados dos últimos 60 dias
            df = self._fetch_context_data(data_provider, symbol, timeframe)
            
            if df is None or len(df) < 50:
                print(f"⚠️ Dados insuficientes para análise de contexto ({len(df) if df is not None else 0} candles)")
                return None
            
            # Calcular indicadores
            ma_slope = self._calculate_ma_slope(df)
            adx = self._calculate_adx(df)
            atr_normalized = self._calculate_normalized_atr(df)
            price_change_pct = ((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100
            
            # Determinar regime
            regime, confidence = self._determine_regime(ma_slope, adx, price_change_pct)
            
            # Gerar recomendações de ajuste de estratégias
            recommendations = self._generate_strategy_adjustments(regime, confidence, adx)
            
            # Criar período de análise
            start_date = df.index[0].strftime("%d/%m/%Y")
            end_date = df.index[-1].strftime("%d/%m/%Y")
            analysis_period = f"{start_date} → {end_date}"
            
            return MarketContext(
                regime=regime,
                confidence=confidence,
                trend_strength=adx,
                volatility=atr_normalized,
                price_change_pct=price_change_pct,
                recommendations=recommendations,
                analysis_period=analysis_period
            )
            
        except Exception as e:
            print(f"❌ Erro ao analisar contexto de mercado: {e}")
            return None
    
    def _fetch_context_data(
        self,
        data_provider,
        symbol: str,
        timeframe: str
    ) -> Optional[pd.DataFrame]:
        """Busca dados históricos para análise de contexto"""
        try:
            # Converter timeframe para formato da API
            timeframe_map = {
                "1m": "1", "5m": "5", "15m": "15",
                "30m": "30", "1h": "60", "4h": "240", "1d": "D"
            }
            api_timeframe = timeframe_map.get(timeframe, "60")
            
            # Calcular timestamps
            end_time = datetime.now()
            start_time = end_time - timedelta(days=self.lookback_days)
            
            start_ts = int(start_time.timestamp() * 1000)
            end_ts = int(end_time.timestamp() * 1000)
            
            # Buscar dados
            all_klines = []
            current_start = start_ts
            
            while current_start < end_ts:
                klines = data_provider.get_kline(
                    category='spot',
                    symbol=symbol,
                    interval=api_timeframe,
                    limit=500,
                    start=current_start,
                    end=end_ts
                )
                
                if not klines:
                    break
                
                all_klines.extend(klines)
                last_ts = int(klines[-1][0])
                current_start = last_ts + (60 * 1000)
            
            if not all_klines:
                return None
            
            # Converter para DataFrame
            df = pd.DataFrame(all_klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            print(f"❌ Erro ao buscar dados de contexto: {e}")
            return None
    
    def _calculate_ma_slope(self, df: pd.DataFrame, period: int = 50) -> float:
        """Calcula inclinação da MA para identificar tendência"""
        ma = df['close'].rolling(window=period).mean()
        
        # Calcular slope usando últimos 20 períodos
        recent_ma = ma.iloc[-20:]
        if len(recent_ma) < 2:
            return 0.0
        
        # Regressão linear simples
        x = np.arange(len(recent_ma))
        y = recent_ma.values
        slope = np.polyfit(x, y, 1)[0]
        
        # Normalizar pelo preço médio
        avg_price = df['close'].mean()
        normalized_slope = slope / avg_price if avg_price > 0 else 0
        
        return normalized_slope
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calcula ADX (Average Directional Index)"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Directional Movement
        up_move = high - high.shift()
        down_move = low.shift() - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # Smoothed indicators
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * pd.Series(plus_dm).rolling(window=period).mean() / atr
        minus_di = 100 * pd.Series(minus_dm).rolling(window=period).mean() / atr
        
        # ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 0.0
    
    def _calculate_normalized_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calcula ATR normalizado como % do preço"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.rolling(window=period).mean()
        
        # Normalizar pelo preço atual
        current_price = df['close'].iloc[-1]
        normalized_atr = (atr.iloc[-1] / current_price) * 100 if current_price > 0 else 0
        
        return normalized_atr
    
    def _determine_regime(
        self,
        ma_slope: float,
        adx: float,
        price_change_pct: float
    ) -> Tuple[str, float]:
        """
        Determina regime de mercado e confiança
        
        Returns:
            (regime, confidence)
        """
        # Tendência forte (ADX > 25)
        if adx > self.adx_strong_threshold:
            if ma_slope > self.ma_slope_threshold and price_change_pct > 5:
                # Bullish forte
                confidence = min((adx / 50) * (abs(ma_slope) / 0.01), 1.0)
                return "BULLISH", confidence
            elif ma_slope < -self.ma_slope_threshold and price_change_pct < -5:
                # Bearish forte
                confidence = min((adx / 50) * (abs(ma_slope) / 0.01), 1.0)
                return "BEARISH", confidence
        
        # Correção ou lateral
        if abs(price_change_pct) < 3 or adx < 20:
            confidence = 1.0 - (adx / 30)  # Menor ADX = maior confiança em lateral
            return "CORRECTION", confidence
        
        # Tendência fraca
        if ma_slope > 0 and price_change_pct > 0:
            confidence = 0.5 + (adx / 50) * 0.3
            return "BULLISH", confidence
        elif ma_slope < 0 and price_change_pct < 0:
            confidence = 0.5 + (adx / 50) * 0.3
            return "BEARISH", confidence
        
        # Default: Correção com baixa confiança
        return "CORRECTION", 0.3
    
    def _generate_strategy_adjustments(
        self,
        regime: str,
        confidence: float,
        adx: float
    ) -> Dict[str, float]:
        """
        Gera ajustes de peso para estratégias baseado no regime
        
        Returns:
            Dict com multiplicadores de peso (1.0 = sem mudança)
        """
        adjustments = {}
        
        if regime == "BULLISH":
            # Favorecer estratégias de momentum e trend-following
            adjustments = {
                "ema_crossover": 1.3,
                "macd": 1.2,
                "adx": 1.3,
                "bos": 1.2,  # SMC Break of Structure
                "rsi_mean_reversion": 0.8,  # Reduzir counter-trend
                "bollinger_breakout": 1.1,
                "stochastic": 0.9,
                "choch": 0.7,  # Reduzir reversão
            }
        
        elif regime == "BEARISH":
            # Favorecer estratégias de reversão e proteção
            adjustments = {
                "rsi_mean_reversion": 1.2,
                "choch": 1.3,  # SMC Change of Character
                "macd": 1.1,
                "ema_crossover": 0.8,
                "bos": 0.7,  # Reduzir continuação
                "bollinger_breakout": 1.0,
                "stochastic": 1.1,
            }
        
        else:  # CORRECTION
            # Favorecer estratégias de range e mean reversion
            adjustments = {
                "rsi_mean_reversion": 1.4,
                "bollinger_breakout": 1.3,
                "stochastic": 1.2,
                "order_blocks": 1.2,  # SMC Order Blocks
                "fvg": 1.1,  # Fair Value Gap
                "ema_crossover": 0.7,
                "adx": 0.6,  # Reduzir trend-following
                "bos": 0.5,
            }
        
        # Ajustar baseado na confiança
        for key in adjustments:
            # Suavizar ajustes se confiança baixa
            adjustment = adjustments[key]
            if adjustment > 1.0:
                adjustments[key] = 1.0 + (adjustment - 1.0) * confidence
            else:
                adjustments[key] = 1.0 - (1.0 - adjustment) * confidence
        
        return adjustments
    
    def display_context(self, context: MarketContext):
        """Exibe análise de contexto formatada"""
        print("\n" + "=" * 70)
        print("📊 ANÁLISE DE CONTEXTO DE MERCADO (ÚLTIMOS 60 DIAS)")
        print("=" * 70)
        
        # Regime
        regime_emoji = "📈" if context.regime == "BULLISH" else ("📉" if context.regime == "BEARISH" else "🔄")
        print(f"\n🎯 Regime: {regime_emoji} {context.regime}")
        print(f"   Confiança: {context.confidence:.1%}")
        print(f"   Período: {context.analysis_period}")
        
        # Métricas
        print(f"\n📊 Métricas:")
        print(f"   Força da Tendência (ADX): {context.trend_strength:.1f}")
        print(f"   Volatilidade (ATR%): {context.volatility:.2f}%")
        print(f"   Variação de Preço: {context.price_change_pct:+.2f}%")
        
        # Recomendações
        print(f"\n💡 Ajustes Recomendados de Estratégias:")
        sorted_recs = sorted(
            context.recommendations.items(),
            key=lambda x: x[1],
            reverse=True
        )
        for strategy, weight in sorted_recs[:5]:  # Top 5
            emoji = "📈" if weight > 1.0 else "📉"
            print(f"   {emoji} {strategy}: {weight:.2f}x")
        
        print("=" * 70)
