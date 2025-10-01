import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

API = "https://api.alternative.me/fng/"

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def fetch(symbol: str, window: str) -> dict:
    params = {"limit": 2, "format": "json"}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(API, params=params)
        r.raise_for_status()
        data = r.json()
    latest = data["data"][0]
    return {
        "source": "alt_fng",
        "score": float(latest["value"]),
        "label": latest["value_classification"],
        "ts": latest["timestamp"],
        "kind": "macro_sentiment"
    }
