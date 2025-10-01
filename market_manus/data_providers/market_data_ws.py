import asyncio
import json
import random
from typing import AsyncIterator, Dict, Any
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
        self.ping_timeout = 20
        
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
                async with websockets.connect(
                    self.url,
                    ping_interval=self.ping_interval,
                    ping_timeout=self.ping_timeout
                ) as ws:
                    self._reset_backoff()
                    
                    async for raw_message in ws:
                        try:
                            msg = json.loads(raw_message)
                            
                            if "k" not in msg:
                                continue
                            
                            k = msg["k"]
                            
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
                            print(f"⚠️  Erro ao processar mensagem: {e}")
                            continue
                            
            except WebSocketException as e:
                delay = self._backoff_with_jitter()
                print(f"⚠️  WebSocket desconectado: {e}. Reconectando em {delay:.1f}s...")
                await asyncio.sleep(delay)
                
            except Exception as e:
                delay = self._backoff_with_jitter()
                print(f"⚠️  Erro inesperado: {e}. Reconectando em {delay:.1f}s...")
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
