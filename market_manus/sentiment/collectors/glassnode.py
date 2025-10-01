import httpx
import os
from tenacity import retry, stop_after_attempt, wait_exponential

KEY = os.getenv("GLASSNODE_API_KEY")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def fetch(symbol: str, window: str) -> dict:
    if not KEY:
        return {"source":"glassnode","error":"no-key","kind":"onchain"}
    return {"source":"glassnode","note":"implement specific metric endpoint for "+symbol, "kind":"onchain"}
