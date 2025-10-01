import httpx
import os
from tenacity import retry, stop_after_attempt, wait_exponential

TOKEN = os.getenv("CRYPTOPANIC_TOKEN")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def fetch(symbol: str, window: str) -> dict:
    if not TOKEN:
        return {"source":"cryptopanic","error":"no-token","kind":"news"}
    url = "https://cryptopanic.com/api/v1/posts/"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, params={"auth_token":TOKEN,"currencies":symbol.replace("USDT",""),"public":"true"})
        r.raise_for_status()
        d = r.json()
    items = d.get("results",[])
    return {"source":"cryptopanic","count":len(items), "items":items[:10], "kind":"news"}
