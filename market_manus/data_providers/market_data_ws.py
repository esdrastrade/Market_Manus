import asyncio
import json
import random
from typing import AsyncIterator, Dict, Any
from datetime import datetime
import websockets
from websockets.exceptions import WebSocketException


class BinanceUSWebSocket:
    def __init__(self, symbol: str, interval: str):
        self.symbol = symbol.lower()
        self.interval = interval
        self.url = f"wss://stream.binance.us:9443/ws/{self.symbol}@kline_{self.interval}"
        self.reconnect_delay = 1
        self.max_reconnect_delay = 30
        self.ping_interval = 20
        self.ping_timeout = 30
        self.close_timeout = 10
        self.max_msg_size = 10 * 1024 * 1024
        
        self.connection_count = 0
        self.total_messages = 0
        self.last_message_time = None
        self.connection_start_time = None
        
    def _backoff_with_jitter(self) -> float:
        jitter = random.uniform(0, 0.3 * self.reconnect_delay)
        delay = min(self.reconnect_delay + jitter, self.max_reconnect_delay)
        self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
        return delay
    
    def _reset_backoff(self):
        self.reconnect_delay = 1
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """Retorna métricas de saúde da conexão"""
        uptime = None
        if self.connection_start_time:
            uptime = (datetime.now() - self.connection_start_time).total_seconds()
        
        time_since_last_msg = None
        if self.last_message_time:
            time_since_last_msg = (datetime.now() - self.last_message_time).total_seconds()
        
        return {
            "connection_count": self.connection_count,
            "total_messages": self.total_messages,
            "uptime_seconds": uptime,
            "time_since_last_message": time_since_last_msg,
            "is_healthy": time_since_last_msg < 60 if time_since_last_msg else False
        }
    
    async def __aiter__(self) -> AsyncIterator[Dict[str, Any]]:
        while True:
            try:
                async with websockets.connect(
                    self.url,
                    ping_interval=self.ping_interval,
                    ping_timeout=self.ping_timeout,
                    close_timeout=self.close_timeout,
                    max_size=self.max_msg_size
                ) as ws:
                    self._reset_backoff()
                    self.connection_count += 1
                    self.connection_start_time = datetime.now()
                    
                    async for raw_message in ws:
                        try:
                            msg = json.loads(raw_message)
                            
                            if "k" not in msg:
                                continue
                            
                            k = msg["k"]
                            
                            self.total_messages += 1
                            self.last_message_time = datetime.now()
                            
                            yield {
                                "event_time": msg["E"],
                                "symbol": msg["s"],
                                "interval": k["i"],
                                "open": float(k["o"]),
                                "high": float(k["h"]),
                                "low": float(k["l"]),
                                "close": float(k["c"]),
                                "volume": float(k["v"]),
                                "is_closed": bool(k["x"]),
                                "timestamp": int(k["t"])
                            }
                            
                        except (json.JSONDecodeError, KeyError) as e:
                            print(f"⚠️  [{datetime.now().strftime('%H:%M:%S')}] Erro ao processar mensagem: {e}")
                            continue
                            
            except WebSocketException as e:
                delay = self._backoff_with_jitter()
                uptime = (datetime.now() - self.connection_start_time).total_seconds() if self.connection_start_time else 0
                print(f"⚠️  [{datetime.now().strftime('%H:%M:%S')}] WebSocket desconectado após {uptime:.1f}s: {e}. Reconectando em {delay:.1f}s...")
                await asyncio.sleep(delay)
                
            except Exception as e:
                delay = self._backoff_with_jitter()
                print(f"⚠️  [{datetime.now().strftime('%H:%M:%S')}] Erro inesperado: {e}. Reconectando em {delay:.1f}s...")
                await asyncio.sleep(delay)


class BybitWebSocket:
    def __init__(self, symbol: str, interval: str):
        self.symbol = symbol
        self.interval = interval
        self.url = "wss://stream.bybit.com/v5/public/spot"
        self.reconnect_delay = 1
        self.max_reconnect_delay = 30
        
    def _backoff_with_jitter(self) -> float:
        jitter = random.uniform(0, 0.3 * self.reconnect_delay)
        delay = min(self.reconnect_delay + jitter, self.max_reconnect_delay)
        self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
        return delay
    
    def _reset_backoff(self):
        self.reconnect_delay = 1
    
    async def __aiter__(self) -> AsyncIterator[Dict[str, Any]]:
        while True:
            try:
                async with websockets.connect(self.url) as ws:
                    self._reset_backoff()
                    
                    subscribe_msg = {
                        "op": "subscribe",
                        "args": [f"kline.{self.interval}.{self.symbol}"]
                    }
                    await ws.send(json.dumps(subscribe_msg))
                    
                    async for raw_message in ws:
                        try:
                            msg = json.loads(raw_message)
                            
                            if msg.get("topic", "").startswith("kline"):
                                data = msg["data"][0]
                                
                                yield {
                                    "event_time": msg["ts"],
                                    "symbol": data["symbol"],
                                    "interval": data["interval"],
                                    "open": float(data["open"]),
                                    "high": float(data["high"]),
                                    "low": float(data["low"]),
                                    "close": float(data["close"]),
                                    "volume": float(data["volume"]),
                                    "is_closed": bool(data["confirm"]),
                                    "timestamp": int(data["start"])
                                }
                                
                        except (json.JSONDecodeError, KeyError) as e:
                            print(f"⚠️  Erro ao processar mensagem Bybit: {e}")
                            continue
                            
            except WebSocketException as e:
                delay = self._backoff_with_jitter()
                print(f"⚠️  WebSocket Bybit desconectado: {e}. Reconectando em {delay:.1f}s...")
                await asyncio.sleep(delay)
                
            except Exception as e:
                delay = self._backoff_with_jitter()
                print(f"⚠️  Erro inesperado Bybit: {e}. Reconectando em {delay:.1f}s...")
                await asyncio.sleep(delay)


class BinanceUSOrderFlowWebSocket:
    """
    WebSocket combinado para aggTrade e depth (L2) da Binance.US.
    Calcula métricas de microestrutura: CVD (cumulative volume delta),
    spread, e imbalance dos 10 primeiros níveis.
    """
    def __init__(self, symbol: str, depth_levels: int = 10):
        self.symbol = symbol.lower()
        self.depth_levels = depth_levels
        self.url = (
            f"wss://stream.binance.us:9443/stream?streams="
            f"{self.symbol}@aggTrade/{self.symbol}@depth{self.depth_levels}@100ms"
        )
        self.reconnect_delay = 1
        self.max_reconnect_delay = 30
        self.ping_interval = 20
        self.ping_timeout = 30
        self.close_timeout = 10
        self.max_msg_size = 10 * 1024 * 1024

        # Estado de métricas
        self.cvd = 0.0
        self.best_bid = None
        self.best_ask = None
        self.last_bids = []
        self.last_asks = []
        self.total_messages = 0
        self.connection_count = 0
        self.last_message_time = None
        self.connection_start_time = None

    def _backoff_with_jitter(self) -> float:
        jitter = random.uniform(0, 0.3 * self.reconnect_delay)
        delay = min(self.reconnect_delay + jitter, self.max_reconnect_delay)
        self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
        return delay

    def _reset_backoff(self):
        self.reconnect_delay = 1

    def get_health_metrics(self) -> Dict[str, Any]:
        uptime = None
        if self.connection_start_time:
            uptime = (datetime.now() - self.connection_start_time).total_seconds()
        time_since_last_msg = None
        if self.last_message_time:
            time_since_last_msg = (datetime.now() - self.last_message_time).total_seconds()
        return {
            "connection_count": self.connection_count,
            "total_messages": self.total_messages,
            "uptime_seconds": uptime,
            "time_since_last_message": time_since_last_msg,
            "is_healthy": time_since_last_msg < 60 if time_since_last_msg else False
        }

    async def __aiter__(self) -> AsyncIterator[Dict[str, Any]]:
        while True:
            try:
                async with websockets.connect(
                    self.url,
                    ping_interval=self.ping_interval,
                    ping_timeout=self.ping_timeout,
                    close_timeout=self.close_timeout,
                    max_size=self.max_msg_size
                ) as ws:
                    self._reset_backoff()
                    self.connection_count += 1
                    self.connection_start_time = datetime.now()

                    async for raw_message in ws:
                        try:
                            msg = json.loads(raw_message)
                            self.total_messages += 1
                            self.last_message_time = datetime.now()

                            stream = msg.get("stream")
                            data = msg.get("data", {})
                            if not stream or not data:
                                continue

                            now = datetime.now()
                            event_time = data.get("E") or data.get("T")
                            latency_ms = None
                            if event_time:
                                try:
                                    # Binance envia ms desde epoch
                                    latency_ms = int((now.timestamp() * 1000) - int(event_time))
                                except Exception:
                                    latency_ms = None

                            if stream.endswith("aggTrade"):
                                price = float(data.get("p", 0.0))
                                qty = float(data.get("q", 0.0))
                                is_buyer_maker = bool(data.get("m", False))
                                # Se buyer é maker, agressor foi vendedor -> delta negativo
                                sign = -1.0 if is_buyer_maker else 1.0
                                self.cvd += sign * qty

                                yield {
                                    "type": "aggTrade",
                                    "symbol": data.get("s"),
                                    "price": price,
                                    "qty": qty,
                                    "event_time": event_time,
                                    "latency_ms": latency_ms,
                                    "cvd": self.cvd,
                                    "best_bid": self.best_bid,
                                    "best_ask": self.best_ask,
                                    "spread": (self.best_ask - self.best_bid) if (self.best_ask and self.best_bid) else None
                                }

                            elif "depth" in stream:
                                # Combined stream pode usar campos 'b'/'a' ou 'bids'/'asks'
                                bids = data.get("b") or data.get("bids") or []
                                asks = data.get("a") or data.get("asks") or []

                                # Normalizar para float
                                def _norm(levels):
                                    out = []
                                    for lv in levels[:self.depth_levels]:
                                        try:
                                            price = float(lv[0])
                                            qty = float(lv[1])
                                            out.append((price, qty))
                                        except Exception:
                                            continue
                                    return out

                                self.last_bids = _norm(bids)
                                self.last_asks = _norm(asks)

                                if self.last_bids:
                                    self.best_bid = self.last_bids[0][0]
                                if self.last_asks:
                                    self.best_ask = self.last_asks[0][0]

                                total_bid_qty = sum(q for _, q in self.last_bids)
                                total_ask_qty = sum(q for _, q in self.last_asks)
                                denom = (total_bid_qty + total_ask_qty) or 1e-9
                                imbalance = (total_bid_qty - total_ask_qty) / denom
                                spread = None
                                if self.best_bid is not None and self.best_ask is not None:
                                    spread = self.best_ask - self.best_bid

                                yield {
                                    "type": "depth",
                                    "symbol": data.get("s"),
                                    "event_time": event_time,
                                    "latency_ms": latency_ms,
                                    "best_bid": self.best_bid,
                                    "best_ask": self.best_ask,
                                    "spread": spread,
                                    "imbalance": imbalance,
                                    "bids": self.last_bids,
                                    "asks": self.last_asks
                                }

                        except (json.JSONDecodeError, KeyError) as e:
                            print(f"⚠️  [{datetime.now().strftime('%H:%M:%S')}] Erro ao processar mensagem: {e}")
                            continue

            except WebSocketException as e:
                delay = self._backoff_with_jitter()
                uptime = (datetime.now() - self.connection_start_time).total_seconds() if self.connection_start_time else 0
                print(f"⚠️  [{datetime.now().strftime('%H:%M:%S')}] OrderFlow WS desconectado após {uptime:.1f}s: {e}. Reconectando em {delay:.1f}s...")
                await asyncio.sleep(delay)

            except Exception as e:
                delay = self._backoff_with_jitter()
                print(f"⚠️  [{datetime.now().strftime('%H:%M:%S')}] Erro inesperado (OrderFlow): {e}. Reconectando em {delay:.1f}s...")
                await asyncio.sleep(delay)
