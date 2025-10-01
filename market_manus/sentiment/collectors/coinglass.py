import httpx
import os
from tenacity import retry, stop_after_attempt, wait_exponential

KEY = os.getenv("COINGLASS_API_KEY")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def fetch(symbol: str, window: str) -> dict:
    if not KEY:
        return {"source":"coinglass","error":"no-key","kind":"derivatives"}
    headers = {"coinglassSecret": KEY}
    async with httpx.AsyncClient(timeout=10, headers=headers) as client:
        r = await client.get("https://open-api-v4.coinglass.com/api/futures/openInterest", params={"symbol":symbol})
        data = r.json() if r.status_code==200 else {"status":r.status_code}
    return {"source":"coinglass","oi":data,"kind":"derivatives"}
