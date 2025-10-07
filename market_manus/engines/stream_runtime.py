import asyncio
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd


@dataclass
class StateChange:
    timestamp: datetime
    action: str
    price: float
    confidence: float
    score: float
    reasons: List[str]
    tags: List[str]


@dataclass
class StreamState:
    provider: str = "Binance.US"
    symbol: str = "BTCUSDT"
    interval: str = "1m"
    price: float = 0.0
    delta_since: float = 0.0
    latency_ms: int = 0
    label: str = "HOLD"
    label_emoji: str = "• HOLD"
    confidence: float = 0.0
    score: float = 0.0
    top_reasons: List[str] = field(default_factory=list)
    last_events: deque = field(default_factory=lambda: deque(maxlen=5))
    msgs_received: int = 0
    msgs_processed: int = 0
    reconnections: int = 0
    last_state_price: float = 0.0
    
    # FASE 2: ICT Market Context (OTE/CE/Premium-Discount)
    ict_premium_discount: Optional[str] = None
    ict_ote_active: bool = False
    ict_ote_type: Optional[str] = None
    ict_ce_level: Optional[float] = None
    ict_price_in_zone: Optional[str] = None
    
    # FASE 2: Paper Trading Costs
    paper_equity: float = 0.0
    paper_position_open: bool = False
    paper_unrealized_pnl: float = 0.0
    paper_last_trade_gross: Optional[float] = None
    paper_last_trade_costs: Optional[float] = None
    paper_last_trade_net: Optional[float] = None
    paper_win_rate: float = 0.0
    paper_total_trades: int = 0


class StreamRuntime:
    def __init__(
        self,
        ws_provider,
        data_provider,
        symbol: str,
        interval: str,
        engine: Any,
        debounce_sec: float = 1.0,
        max_queue_size: int = 100
    ):
        self.ws_provider = ws_provider
        self.data_provider = data_provider
        self.symbol = symbol
        self.interval = interval
        self.engine = engine
        self.debounce_sec = debounce_sec
        self.max_queue_size = max_queue_size
        
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.state = StreamState(symbol=symbol, interval=interval)
        self.candles_deque = deque(maxlen=1000)
        self.last_candle = None
        self.running = False
        
    async def bootstrap_historical_data(self):
        try:
            interval_map = {
                '1m': '1', '5m': '5', '15m': '15',
                '1h': '60', '4h': '240'
            }
            api_interval = interval_map.get(self.interval, '5')
            
            klines = self.data_provider.get_kline(
                category="spot",
                symbol=self.symbol,
                interval=api_interval,
                limit=500
            )
            
            if not klines:
                return False
                
            df = pd.DataFrame(
                klines,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            for col in ['timestamp', 'open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
                
            for _, row in df.iterrows():
                self.candles_deque.append(row.to_dict())
                
            return True
        except Exception as e:
            print(f"⚠️  Erro no bootstrap: {e}. Tentando continuar com dados do WebSocket...")
            return True
    
    async def collect_ws_messages(self):
        try:
            async for msg in self.ws_provider:
                self.state.msgs_received += 1
                
                if self.queue.full():
                    try:
                        self.queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                
                await self.queue.put(msg)
                
        except Exception as e:
            print(f"⚠️  Erro na coleta WS: {e}")
            self.state.reconnections += 1
    
    async def process_micro_batches(self):
        while self.running:
            try:
                await asyncio.sleep(self.debounce_sec)
                
                latest_msg = None
                while not self.queue.empty():
                    try:
                        latest_msg = self.queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                
                if latest_msg:
                    await self.process_message(latest_msg)
                    
            except Exception as e:
                print(f"⚠️  Erro no processamento: {e}")
    
    async def process_message(self, msg: Dict[str, Any]):
        now = datetime.now()
        event_time = datetime.fromtimestamp(msg["event_time"] / 1000)
        self.state.latency_ms = int((now - event_time).total_seconds() * 1000)
        
        candle_dict = {
            "timestamp": msg["timestamp"],
            "open": msg["open"],
            "high": msg["high"],
            "low": msg["low"],
            "close": msg["close"],
            "volume": msg["volume"]
        }
        
        if self.last_candle and self.last_candle["timestamp"] == candle_dict["timestamp"]:
            self.candles_deque[-1] = candle_dict
        elif msg["is_closed"]:
            self.candles_deque.append(candle_dict)
            self.last_candle = candle_dict
        else:
            if len(self.candles_deque) > 0:
                self.candles_deque[-1] = candle_dict
        
        self.state.price = msg["close"]
        self.state.msgs_processed += 1
        
        df = pd.DataFrame(list(self.candles_deque))
        
        # Usar process_candle do RealTimeConfluenceEngine
        signal = self.engine.process_candle(
            candles=df,
            symbol=self.symbol,
            timeframe=self.interval,
            callback=None
        )
        
        if signal is not None:
            self.state.label = signal.action
            self.state.confidence = signal.confidence
            self.state.score = signal.meta.get('score', 0.0)
            self.state.top_reasons = signal.reasons[:3]
            
            if signal.action == "BUY":
                self.state.label_emoji = "↑ BUY"
            elif signal.action == "SELL":
                self.state.label_emoji = "↓ SELL"
            else:
                self.state.label_emoji = "• HOLD"
            
            # FASE 2: Extrair dados ICT (OTE/CE/Premium-Discount) do signal.meta
            narrative = signal.meta.get('narrative')
            if narrative and hasattr(narrative, 'meta'):
                nar_meta = narrative.meta
                self.state.ict_premium_discount = nar_meta.get('premium_discount_classification')
                self.state.ict_price_in_zone = nar_meta.get('price_in_zone')
                self.state.ict_ce_level = nar_meta.get('ce_level')
                
                ote_data = nar_meta.get('ote_zones')
                if ote_data:
                    self.state.ict_ote_active = ote_data.get('active', False)
                    self.state.ict_ote_type = ote_data.get('type')
            
            # FASE 2: Extrair dados de Paper Trading do engine
            if hasattr(self.engine, 'state'):
                eng_state = self.engine.state
                self.state.paper_equity = eng_state.get('paper_equity', 0.0)
                self.state.paper_unrealized_pnl = eng_state.get('paper_unrealized_pnl', 0.0)
                total_trades = eng_state.get('paper_total_trades', 0)
                self.state.paper_total_trades = total_trades
                
                if total_trades > 0:
                    wins = eng_state.get('paper_winning_trades', 0)
                    self.state.paper_win_rate = (wins / total_trades) * 100
                
                if hasattr(self.engine, 'current_position'):
                    self.state.paper_position_open = self.engine.current_position is not None
                
                # Último trade (se disponível)
                if hasattr(self.engine, 'paper_trades') and len(self.engine.paper_trades) > 0:
                    last_trade = self.engine.paper_trades[-1]
                    self.state.paper_last_trade_gross = last_trade.get('gross_pnl')
                    self.state.paper_last_trade_costs = last_trade.get('trading_costs')
                    self.state.paper_last_trade_net = last_trade.get('net_pnl')
            
            self.state.last_state_price = self.state.price
            self.state.delta_since = 0.0
            
            event = StateChange(
                timestamp=now,
                action=signal.action,
                price=self.state.price,
                confidence=signal.confidence,
                score=self.state.score,
                reasons=signal.reasons[:2],
                tags=signal.tags[:3]
            )
            self.state.last_events.append(event)
        else:
            if self.state.last_state_price > 0:
                self.state.delta_since = self.state.price - self.state.last_state_price
    
    async def start(self):
        self.running = True
        
        print("📥 Carregando dados históricos...")
        success = await self.bootstrap_historical_data()
        if not success:
            print("❌ Falha ao carregar dados históricos")
            return False
        
        print(f"✅ {len(self.candles_deque)} candles carregados")
        
        collector_task = asyncio.create_task(self.collect_ws_messages())
        processor_task = asyncio.create_task(self.process_micro_batches())
        
        await asyncio.gather(collector_task, processor_task)
    
    def stop(self):
        self.running = False
