import os
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def fetch(symbol: str, window: str) -> dict:
    if not os.getenv("SANTIMENT_API_KEY"):
        return {"source":"santiment","error":"no-key","kind":"social"}
    return {"source":"santiment","note":"implement SAN queries", "kind":"social"}
