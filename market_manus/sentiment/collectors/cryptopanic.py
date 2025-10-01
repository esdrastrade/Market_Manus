import httpx
import os
from tenacity import retry, stop_after_attempt, wait_exponential

TOKEN = os.getenv("CRYPTOPANIC_TOKEN")
API_PLAN = os.getenv("CRYPTOPANIC_API_PLAN", "developer")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def fetch(symbol: str, window: str) -> dict:
    if not TOKEN:
        return {"source":"cryptopanic","error":"no-token","kind":"news"}
    
    currency = symbol.replace("USDT", "").replace("USDC", "").replace("USD", "")
    url = f"https://cryptopanic.com/api/{API_PLAN}/v2/posts/"
    
    params = {
        "auth_token": TOKEN,
        "currencies": currency,
        "public": "true",
        "kind": "news",
        "filter": "rising"
    }
    
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        d = r.json()
    
    results = d.get("results", [])
    
    positive = sum(1 for item in results if item.get("votes", {}).get("positive", 0) > item.get("votes", {}).get("negative", 0))
    negative = sum(1 for item in results if item.get("votes", {}).get("negative", 0) > item.get("votes", {}).get("positive", 0))
    
    titles = [item.get("title", "") for item in results[:5]]
    
    return {
        "source": "cryptopanic",
        "count": len(results),
        "positive": positive,
        "negative": negative,
        "titles": titles,
        "kind": "news"
    }
