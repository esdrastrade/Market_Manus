import httpx
import os
from tenacity import retry, stop_after_attempt, wait_exponential

BASE = "https://api.bybit.com" if os.getenv("BYBIT_MODE","real")=="real" else "https://api-demo.bybit.com"

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def fetch(symbol: str, window: str) -> dict:
    async with httpx.AsyncClient(timeout=10, base_url=BASE) as client:
        funding = None
        try:
            r = await client.get("/v5/market/funding/history", params={"category":"linear","symbol":symbol})
            if r.status_code == 200:
                funding = r.json()
        except Exception:
            pass
    return {
        "source": "bybit",
        "funding": funding,
        "kind": "derivatives"
    }
