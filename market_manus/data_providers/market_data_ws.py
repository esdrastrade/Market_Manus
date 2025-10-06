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
