"""
Real-Time Strategy Execution Engine
Integrates WebSocket data with parallel strategy execution and live UI
"""

import asyncio
from collections import deque
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
import pandas as pd
import numpy as np
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from market_manus.data_providers.market_data_ws import BinanceUSWebSocket
from market_manus.strategies.classic_analysis import (
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_adx,
    fibonacci_signal
)
from market_manus.strategies.smc.patterns import (
    detect_bos,
    detect_choch,
    detect_order_blocks,
    detect_fvg,
    detect_liquidity_sweep
)
from market_manus.core.signal import Signal
from market_manus.analysis.market_context_analyzer import MarketContextAnalyzer


class RealtimeStrategyEngine:
    """Engine for real-time strategy execution with WebSocket data"""
    
    def __init__(
        self,
        symbol: str,
        interval: str,
        strategies: List[str],
        data_provider,
        confluence_mode: str = "MAJORITY"
    ):
        self.symbol = symbol
        self.interval = interval
        
        self.strategy_name_map = {
            "smc_bos": "bos",
            "smc_choch": "choch",
            "smc_order_blocks": "order_blocks",
            "smc_fvg": "fvg",
            "smc_liquidity_sweep": "liquidity_sweep"
        }
        
        self.strategies = [self.strategy_name_map.get(s, s) for s in strategies]
        self.data_provider = data_provider
        self.confluence_mode = confluence_mode
        
        self.ws_provider = None
        self.candles_deque = deque(maxlen=1000)
        self.signals_history = deque(maxlen=100)
        self.running = False
        
        self.candles_df = None
        self.processing_window = 200
        
        self.context_analyzer = MarketContextAnalyzer(lookback_days=60)
        
        self.state = {
            'price': 0.0,
            'delta_since': 0.0,
            'latency_ms': 0,
            'label': 'HOLD',
            'label_emoji': '• HOLD',
            'confidence': 0.0,
            'signals': {},
            'last_state_price': 0.0,
            'msgs_received': 0,
            'msgs_processed': 0,
            'reconnections': 0,
            'last_update': datetime.now(),
            'strategy_results': [],
            'market_context': None,
            'total_latency': 0,
            'latency_count': 0,
            'total_signals': 0,
            'buy_signals': 0,
            'sell_signals': 0
        }
        
        self.strategy_functions = {
            'rsi_mean_reversion': self._apply_rsi_strategy,
            'ema_crossover': self._apply_ema_strategy,
            'bollinger_breakout': self._apply_bollinger_strategy,
            'macd': self._apply_macd_strategy,
            'stochastic': self._apply_stochastic_strategy,
            'williams_r': self._apply_williams_r_strategy,
            'adx': self._apply_adx_strategy,
            'fibonacci': self._apply_fibonacci_strategy,
            'bos': detect_bos,
            'choch': detect_choch,
            'order_blocks': detect_order_blocks,
            'fvg': detect_fvg,
            'liquidity_sweep': detect_liquidity_sweep
        }
    
    def _apply_rsi_strategy(self, df: pd.DataFrame) -> Signal:
        """Apply RSI strategy"""
        rsi = calculate_rsi(df['close'], 14)
        last_rsi = rsi.iloc[-1]
        
        if pd.isna(last_rsi):
            return Signal(action="HOLD", confidence=0.0, reasons=["Dados insuficientes"], tags=["RSI"])
        
        if last_rsi < 30:
            confidence = (30 - last_rsi) / 30
            return Signal(
                action="BUY",
                confidence=min(confidence, 1.0),
                reasons=[f"RSI sobrevenda: {last_rsi:.2f}"],
                tags=["RSI", "OVERSOLD"]
            )
        elif last_rsi > 70:
            confidence = (last_rsi - 70) / 30
            return Signal(
                action="SELL",
                confidence=min(confidence, 1.0),
                reasons=[f"RSI sobrecompra: {last_rsi:.2f}"],
                tags=["RSI", "OVERBOUGHT"]
            )
        
        return Signal(action="HOLD", confidence=0.0, reasons=["RSI neutro"], tags=["RSI"])
    
    def _apply_ema_strategy(self, df: pd.DataFrame) -> Signal:
        """Apply EMA crossover strategy"""
        ema_fast = calculate_ema(df['close'], 12)
        ema_slow = calculate_ema(df['close'], 26)
        
        last_fast = ema_fast.iloc[-1]
        last_slow = ema_slow.iloc[-1]
        
        if pd.isna(last_fast) or pd.isna(last_slow):
            return Signal(action="HOLD", confidence=0.0, reasons=["Dados insuficientes"], tags=["EMA"])
        
        diff = abs(last_fast - last_slow) / last_slow
        
        if last_fast > last_slow:
            return Signal(
                action="BUY",
                confidence=min(diff * 10, 1.0),
                reasons=[f"EMA rápida acima da lenta"],
                tags=["EMA", "CROSSOVER"]
            )
        elif last_fast < last_slow:
            return Signal(
                action="SELL",
                confidence=min(diff * 10, 1.0),
                reasons=[f"EMA rápida abaixo da lenta"],
                tags=["EMA", "CROSSOVER"]
            )
        
        return Signal(action="HOLD", confidence=0.0, reasons=["EMAs neutras"], tags=["EMA"])
    
    def _apply_bollinger_strategy(self, df: pd.DataFrame) -> Signal:
        """Apply Bollinger Bands strategy"""
        upper, middle, lower = calculate_bollinger_bands(df['close'], 20, 2)
        
        last_close = df['close'].iloc[-1]
        last_upper = upper.iloc[-1]
        last_lower = lower.iloc[-1]
        
        if pd.isna(last_upper) or pd.isna(last_lower):
            return Signal(action="HOLD", confidence=0.0, reasons=["Dados insuficientes"], tags=["BB"])
        
        if last_close > last_upper:
            confidence = (last_close - last_upper) / last_upper
            return Signal(
                action="SELL",
                confidence=min(confidence * 10, 1.0),
                reasons=[f"Preço acima da banda superior"],
                tags=["BB", "BREAKOUT"]
            )
        elif last_close < last_lower:
            confidence = (last_lower - last_close) / last_lower
            return Signal(
                action="BUY",
                confidence=min(confidence * 10, 1.0),
                reasons=[f"Preço abaixo da banda inferior"],
                tags=["BB", "BREAKOUT"]
            )
        
        return Signal(action="HOLD", confidence=0.0, reasons=["Preço dentro das bandas"], tags=["BB"])
    
    def _apply_macd_strategy(self, df: pd.DataFrame) -> Signal:
        """Apply MACD strategy"""
        macd_line, signal_line, histogram = calculate_macd(df['close'], 12, 26, 9)
        
        last_macd = macd_line.iloc[-1]
        last_signal = signal_line.iloc[-1]
        
        if pd.isna(last_macd) or pd.isna(last_signal):
            return Signal(action="HOLD", confidence=0.0, reasons=["Dados insuficientes"], tags=["MACD"])
        
        diff = abs(last_macd - last_signal) / abs(last_signal) if last_signal != 0 else 0
        
        if last_macd > last_signal:
            return Signal(
                action="BUY",
                confidence=min(diff, 1.0),
                reasons=[f"MACD acima do sinal"],
                tags=["MACD", "CROSSOVER"]
            )
        elif last_macd < last_signal:
            return Signal(
                action="SELL",
                confidence=min(diff, 1.0),
                reasons=[f"MACD abaixo do sinal"],
                tags=["MACD", "CROSSOVER"]
            )
        
        return Signal(action="HOLD", confidence=0.0, reasons=["MACD neutro"], tags=["MACD"])
    
    def _apply_stochastic_strategy(self, df: pd.DataFrame) -> Signal:
        """Apply Stochastic strategy"""
        k_period = 14
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        
        stoch_k = 100 * ((df['close'] - low_min) / (high_max - low_min))
        last_k = stoch_k.iloc[-1]
        
        if pd.isna(last_k):
            return Signal(action="HOLD", confidence=0.0, reasons=["Dados insuficientes"], tags=["STOCH"])
        
        if last_k < 20:
            confidence = (20 - last_k) / 20
            return Signal(
                action="BUY",
                confidence=min(confidence, 1.0),
                reasons=[f"Stochastic sobrevenda: {last_k:.2f}"],
                tags=["STOCH", "OVERSOLD"]
            )
        elif last_k > 80:
            confidence = (last_k - 80) / 20
            return Signal(
                action="SELL",
                confidence=min(confidence, 1.0),
                reasons=[f"Stochastic sobrecompra: {last_k:.2f}"],
                tags=["STOCH", "OVERBOUGHT"]
            )
        
        return Signal(action="HOLD", confidence=0.0, reasons=["Stochastic neutro"], tags=["STOCH"])
    
    def _apply_adx_strategy(self, df: pd.DataFrame) -> Signal:
        """Apply ADX strategy"""
        adx, plus_di, minus_di = calculate_adx(df, 14)
        
        last_adx = adx.iloc[-1]
        last_plus = plus_di.iloc[-1]
        last_minus = minus_di.iloc[-1]
        
        if pd.isna(last_adx) or pd.isna(last_plus) or pd.isna(last_minus):
            return Signal(action="HOLD", confidence=0.0, reasons=["Dados insuficientes"], tags=["ADX"])
        
        if last_adx > 25:
            confidence = min(last_adx / 50, 1.0)
            if last_plus > last_minus:
                return Signal(
                    action="BUY",
                    confidence=confidence,
                    reasons=[f"ADX forte tendência de alta"],
                    tags=["ADX", "TREND"]
                )
            elif last_minus > last_plus:
                return Signal(
                    action="SELL",
                    confidence=confidence,
                    reasons=[f"ADX forte tendência de baixa"],
                    tags=["ADX", "TREND"]
                )
        
        return Signal(action="HOLD", confidence=0.0, reasons=["ADX sem tendência forte"], tags=["ADX"])
    
    def _apply_williams_r_strategy(self, df: pd.DataFrame) -> Signal:
        """Apply Williams %R strategy"""
        period = 14
        if len(df) < period:
            return Signal(action="HOLD", confidence=0.0, reasons=["Dados insuficientes"], tags=["WILLIAMS_R"])
        
        highest_high = df['high'].rolling(window=period).max().iloc[-1]
        lowest_low = df['low'].rolling(window=period).min().iloc[-1]
        last_close = df['close'].iloc[-1]
        
        if pd.isna(highest_high) or pd.isna(lowest_low):
            return Signal(action="HOLD", confidence=0.0, reasons=["Dados insuficientes"], tags=["WILLIAMS_R"])
        
        if highest_high == lowest_low:
            wr = -50
        else:
            wr = ((highest_high - last_close) / (highest_high - lowest_low)) * -100
        
        if wr < -80:
            confidence = (80 - abs(wr)) / 20
            return Signal(
                action="BUY",
                confidence=min(confidence, 1.0),
                reasons=[f"Williams %R sobrevenda: {wr:.2f}"],
                tags=["WILLIAMS_R", "OVERSOLD"]
            )
        elif wr > -20:
            confidence = (20 - abs(wr)) / 20
            return Signal(
                action="SELL",
                confidence=min(confidence, 1.0),
                reasons=[f"Williams %R sobrecompra: {wr:.2f}"],
                tags=["WILLIAMS_R", "OVERBOUGHT"]
            )
        
        return Signal(action="HOLD", confidence=0.0, reasons=["Williams %R neutro"], tags=["WILLIAMS_R"])
    
    def _apply_fibonacci_strategy(self, df: pd.DataFrame) -> Signal:
        """Apply Fibonacci Retracement strategy"""
        return fibonacci_signal(df, params={'lookback': 50})
    
    async def _analyze_context(self):
        """Analisa contexto de mercado antes de iniciar streaming"""
        try:
            print("\n🔍 Analisando contexto de mercado dos últimos 60 dias...")
            
            context = await asyncio.get_event_loop().run_in_executor(
                None,
                self.context_analyzer.analyze,
                self.data_provider,
                self.symbol,
                self.interval
            )
            
            if context:
                self.context_analyzer.display_context(context)
                self.state['market_context'] = context
            else:
                print("⚠️  Análise de contexto indisponível - continuando sem ajustes")
            
            return context
            
        except Exception as e:
            print(f"⚠️  Erro na análise de contexto: {e} - continuando sem ajustes")
            return None
    
    async def bootstrap_historical_data(self) -> bool:
        """Load historical data to initialize indicators"""
        try:
            interval_map = {
                '1m': '1', '5m': '5', '15m': '15',
                '1h': '60', '4h': '240'
            }
            api_interval = interval_map.get(self.interval, '5')
            
            print(f"📥 Carregando dados históricos para {self.symbol}...")
            klines = self.data_provider.get_kline(
                category="spot",
                symbol=self.symbol,
                interval=api_interval,
                limit=500
            )
            
            if not klines:
                print("⚠️  Aviso: Não foi possível carregar dados históricos")
                return False
            
            for kline in klines:
                candle = {
                    'timestamp': int(kline[0]),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                }
                self.candles_deque.append(candle)
            
            print(f"✅ {len(self.candles_deque)} candles carregados")
            return True
            
        except Exception as e:
            print(f"⚠️  Erro no bootstrap: {e}")
            return False
    
    async def apply_strategies_parallel(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Apply all strategies in parallel using asyncio"""
        async def apply_single_strategy(strategy_name: str):
            try:
                if strategy_name not in self.strategy_functions:
                    return strategy_name, Signal(
                        action="HOLD",
                        confidence=0.0,
                        reasons=["Estratégia não encontrada"],
                        tags=["ERROR"]
                    )
                
                strategy_func = self.strategy_functions[strategy_name]
                signal = await asyncio.to_thread(strategy_func, df)
                
                if signal and self.state.get('market_context'):
                    context = self.state['market_context']
                    weight_adjustment = context.recommendations.get(strategy_name, 1.0)
                    signal.confidence *= weight_adjustment
                    signal.confidence = max(0.0, min(signal.confidence, 1.0))
                
                return strategy_name, signal or Signal(
                    action="HOLD",
                    confidence=0.0,
                    reasons=["Sem sinal"],
                    tags=["NO_SIGNAL"]
                )
                
            except Exception as e:
                print(f"⚠️  Erro na estratégia {strategy_name}: {e}")
                return strategy_name, Signal(
                    action="HOLD",
                    confidence=0.0,
                    reasons=[f"Erro: {str(e)[:30]}"],
                    tags=["ERROR"]
                )
        
        tasks = [apply_single_strategy(strategy) for strategy in self.strategies]
        results = await asyncio.gather(*tasks)
        
        return {name: signal for name, signal in results}
    
    def calculate_confluence(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate confluence from multiple signals"""
        if not signals:
            return {
                'action': 'HOLD',
                'confidence': 0.0,
                'reasons': ['Sem sinais disponíveis']
            }
        
        buy_signals = []
        sell_signals = []
        hold_signals = []
        
        for strategy_name, signal in signals.items():
            if hasattr(signal, 'action'):
                action = signal.action
                confidence = signal.confidence
                
                if action == 'BUY':
                    buy_signals.append((strategy_name, confidence))
                elif action == 'SELL':
                    sell_signals.append((strategy_name, confidence))
                else:
                    hold_signals.append((strategy_name, confidence))
        
        total_strategies = len(signals)
        
        if self.confluence_mode == "ALL":
            if len(buy_signals) == total_strategies:
                avg_confidence = np.mean([conf for _, conf in buy_signals])
                return {
                    'action': 'BUY',
                    'confidence': avg_confidence,
                    'reasons': [f'{name} ({conf:.2f})' for name, conf in buy_signals[:3]]
                }
            elif len(sell_signals) == total_strategies:
                avg_confidence = np.mean([conf for _, conf in sell_signals])
                return {
                    'action': 'SELL',
                    'confidence': avg_confidence,
                    'reasons': [f'{name} ({conf:.2f})' for name, conf in sell_signals[:3]]
                }
        
        elif self.confluence_mode == "ANY":
            if buy_signals:
                max_conf = max([conf for _, conf in buy_signals])
                return {
                    'action': 'BUY',
                    'confidence': max_conf,
                    'reasons': [f'{name} ({conf:.2f})' for name, conf in buy_signals[:3]]
                }
            elif sell_signals:
                max_conf = max([conf for _, conf in sell_signals])
                return {
                    'action': 'SELL',
                    'confidence': max_conf,
                    'reasons': [f'{name} ({conf:.2f})' for name, conf in sell_signals[:3]]
                }
        
        elif self.confluence_mode == "MAJORITY":
            if len(buy_signals) > total_strategies / 2:
                avg_confidence = np.mean([conf for _, conf in buy_signals])
                return {
                    'action': 'BUY',
                    'confidence': avg_confidence,
                    'reasons': [f'{name} ({conf:.2f})' for name, conf in buy_signals[:3]]
                }
            elif len(sell_signals) > total_strategies / 2:
                avg_confidence = np.mean([conf for _, conf in sell_signals])
                return {
                    'action': 'SELL',
                    'confidence': avg_confidence,
                    'reasons': [f'{name} ({conf:.2f})' for name, conf in sell_signals[:3]]
                }
        
        return {
            'action': 'HOLD',
            'confidence': 0.0,
            'reasons': ['Confluência insuficiente']
        }
    
    async def process_candle(self, candle_data: Dict[str, Any]):
        """Process incoming candle data - OPTIMIZED"""
        try:
            start_time = datetime.now()
            
            candle = {
                'timestamp': candle_data['timestamp'],
                'open': candle_data['open'],
                'high': candle_data['high'],
                'low': candle_data['low'],
                'close': candle_data['close'],
                'volume': candle_data['volume']
            }
            
            is_closed = candle_data.get('is_closed', False)
            
            if is_closed:
                self.candles_deque.append(candle)
            else:
                if len(self.candles_deque) > 0:
                    self.candles_deque[-1] = candle
            
            self.state['price'] = candle['close']
            self.state['msgs_processed'] += 1
            
            if not is_closed or len(self.candles_deque) < 50:
                self.state['latency_ms'] = int((datetime.now() - start_time).total_seconds() * 1000)
                return
            
            candles_list = list(self.candles_deque)
            window_size = min(self.processing_window, len(candles_list))
            df = pd.DataFrame(candles_list[-window_size:])
            
            signals = await self.apply_strategies_parallel(df)
            
            confluence = self.calculate_confluence(signals)
            
            self.state['signals'] = signals
            self.state['label'] = confluence['action']
            self.state['confidence'] = confluence['confidence']
            self.state['strategy_results'] = confluence['reasons']
            
            if confluence['action'] == 'BUY':
                self.state['label_emoji'] = '↑ BUY'
                self.state['buy_signals'] += 1
                self.state['total_signals'] += 1
            elif confluence['action'] == 'SELL':
                self.state['label_emoji'] = '↓ SELL'
                self.state['sell_signals'] += 1
                self.state['total_signals'] += 1
            else:
                self.state['label_emoji'] = '• HOLD'
            
            if self.state['last_state_price'] > 0:
                self.state['delta_since'] = self.state['price'] - self.state['last_state_price']
            
            if confluence['action'] != 'HOLD':
                self.state['last_state_price'] = self.state['price']
                
                self.signals_history.append({
                    'timestamp': datetime.now(),
                    'price': self.state['price'],
                    'action': confluence['action'],
                    'confidence': confluence['confidence'],
                    'strategies': confluence['reasons'][:3]
                })
            
            end_time = datetime.now()
            latency = int((end_time - start_time).total_seconds() * 1000)
            self.state['latency_ms'] = latency
            self.state['total_latency'] += latency
            self.state['latency_count'] += 1
            self.state['last_update'] = datetime.now()
            
        except Exception as e:
            print(f"⚠️  Erro ao processar candle: {e}")
    
    async def collect_ws_messages(self):
        """Collect messages from WebSocket"""
        try:
            async for msg in self.ws_provider:
                self.state['msgs_received'] += 1
                await self.process_candle(msg)
        except Exception as e:
            print(f"⚠️  Erro na coleta WS: {e}")
            self.state['reconnections'] += 1
    
    def render_ui(self) -> Layout:
        """Render live UI"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="metrics", size=2),
            Layout(name="body"),
            Layout(name="footer", size=6)
        )
        
        header_table = Table.grid(expand=True)
        header_table.add_column(justify="left")
        header_table.add_column(justify="center")
        header_table.add_column(justify="center")
        header_table.add_column(justify="right")
        
        header_table.add_row(
            f"[bold cyan]Exchange:[/bold cyan] Binance.US",
            f"[bold yellow]Symbol:[/bold yellow] {self.symbol}",
            f"[bold magenta]TF:[/bold magenta] {self.interval}",
            f"[bold green]Latency:[/bold green] {self.state['latency_ms']}ms"
        )
        header_table.add_row(
            f"[dim]Recebidas: {self.state['msgs_received']}[/dim]",
            f"[dim]Processadas: {self.state['msgs_processed']}[/dim]",
            f"[dim]Reconexões: {self.state['reconnections']}[/dim]",
            f"[dim]{datetime.now().strftime('%H:%M:%S')}[/dim]"
        )
        
        layout["header"].update(Panel(header_table, title="🔴 LIVE STREAMING", border_style="red"))
        
        avg_latency = int(self.state['total_latency'] / self.state['latency_count']) if self.state['latency_count'] > 0 else 0
        
        metrics_table = Table.grid(expand=True)
        metrics_table.add_column(justify="center")
        metrics_table.add_column(justify="center")
        metrics_table.add_column(justify="center")
        metrics_table.add_column(justify="center")
        
        metrics_table.add_row(
            f"[bold yellow]Latência Média:[/bold yellow] {avg_latency}ms",
            f"[bold cyan]Total Sinais:[/bold cyan] {self.state['total_signals']}",
            f"[bold green]BUY:[/bold green] {self.state['buy_signals']}",
            f"[bold red]SELL:[/bold red] {self.state['sell_signals']}"
        )
        
        layout["metrics"].update(Panel(metrics_table, title="📈 Métricas de Performance", border_style="yellow"))
        
        layout["body"].split_row(
            Layout(name="price", ratio=1),
            Layout(name="signal", ratio=2)
        )
        
        price_change_color = "green" if self.state['delta_since'] >= 0 else "red"
        price_change_symbol = "+" if self.state['delta_since'] >= 0 else ""
        
        price_text = Text()
        price_text.append(f"${self.state['price']:,.2f}\n", style="bold white")
        price_text.append(
            f"{price_change_symbol}${self.state['delta_since']:,.2f} desde mudança",
            style=price_change_color
        )
        
        layout["price"].update(
            Panel(price_text, title="💰 Preço Atual", border_style="cyan")
        )
        
        signal_table = Table(show_header=True, expand=True)
        signal_table.add_column("Sinal", style="bold", width=12)
        signal_table.add_column("Conf.", justify="center", width=8)
        signal_table.add_column("Estratégias", overflow="fold")
        
        label_style = "green" if "BUY" in self.state['label'] else ("red" if "SELL" in self.state['label'] else "yellow")
        
        signal_table.add_row(
            f"[{label_style}]{self.state['label_emoji']}[/{label_style}]",
            f"{self.state['confidence']:.2f}",
            ", ".join(self.state['strategy_results'][:3]) if self.state['strategy_results'] else "Aguardando..."
        )
        
        layout["signal"].update(
            Panel(signal_table, title=f"🎯 Confluência ({self.confluence_mode})", border_style="magenta")
        )
        
        strategy_table = Table(show_header=True, expand=True, show_lines=False)
        strategy_table.add_column("Estratégia", style="cyan")
        strategy_table.add_column("Sinal", justify="center", width=8)
        strategy_table.add_column("Conf.", justify="center", width=8)
        
        signals_dict = self.state.get('signals', {})
        if signals_dict:
            for strategy_name, signal in signals_dict.items():
                if hasattr(signal, 'action'):
                    action_emoji = "🟢" if signal.action == "BUY" else ("🔴" if signal.action == "SELL" else "⚪")
                    strategy_table.add_row(
                        strategy_name.replace('_', ' ').title(),
                        f"{action_emoji} {signal.action}",
                        f"{signal.confidence:.2f}"
                    )
        
        layout["footer"].split_row(
            Layout(name="strategies", ratio=2),
            Layout(name="history", ratio=1)
        )
        
        layout["strategies"].update(
            Panel(strategy_table, title="📊 Estratégias Individuais", border_style="blue")
        )
        
        history_table = Table(show_header=True, expand=True, show_lines=False)
        history_table.add_column("Hora", style="dim", width=8)
        history_table.add_column("Ação", justify="center", width=6)
        history_table.add_column("Conf.", justify="center", width=6)
        history_table.add_column("Preço", justify="right", width=10)
        
        for signal in list(self.signals_history)[-10:]:
            time_str = signal['timestamp'].strftime("%H:%M:%S")
            action_color = "green" if signal['action'] == "BUY" else "red"
            action_emoji = "↑" if signal['action'] == "BUY" else "↓"
            
            history_table.add_row(
                time_str,
                f"[{action_color}]{action_emoji} {signal['action']}[/{action_color}]",
                f"{signal['confidence']:.2f}",
                f"${signal['price']:,.2f}"
            )
        
        layout["history"].update(
            Panel(history_table, title="📜 Histórico de Sinais (últimos 10)", border_style="yellow")
        )
        
        return layout
    
    async def start(self):
        """Start real-time execution"""
        self.running = True
        
        await self._analyze_context()
        
        success = await self.bootstrap_historical_data()
        if not success:
            print("❌ Falha ao carregar dados históricos")
            return
        
        self.ws_provider = BinanceUSWebSocket(self.symbol, self.interval)
        
        print(f"\n🚀 Iniciando execução em tempo real...")
        print(f"📊 Símbolo: {self.symbol}")
        print(f"⏰ Intervalo: {self.interval}")
        print(f"🎯 Estratégias: {', '.join(self.strategies)}")
        print(f"🤝 Modo Confluência: {self.confluence_mode}")
        print(f"\n⏹️  Pressione Ctrl+C para parar\n")
        
        try:
            with Live(self.render_ui(), refresh_per_second=2) as live:
                async def update_ui():
                    while self.running:
                        live.update(self.render_ui())
                        await asyncio.sleep(0.5)
                
                collector_task = asyncio.create_task(self.collect_ws_messages())
                ui_task = asyncio.create_task(update_ui())
                
                await asyncio.gather(collector_task, ui_task)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Execução interrompida pelo usuário")
            self.running = False
        except Exception as e:
            print(f"\n\n❌ Erro: {e}")
            self.running = False
    
    def stop(self):
        """Stop execution"""
        self.running = False
