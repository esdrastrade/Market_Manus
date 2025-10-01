import json
import websockets

BASE_WS = "wss://data-stream.binance.vision/ws"

async def stream_prices(symbol: str, interval="1m"):
    stream = f"{symbol.lower()}@kline_{interval}"
    url = f"{BASE_WS}/{stream}"
    async with websockets.connect(url, ping_interval=15, close_timeout=5) as ws:
        async for msg in ws:
            yield json.loads(msg)
