import httpx
import os
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_URL = "https://api.bybit.com"

@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4))
async def fetch(symbol: str, window: str) -> dict:
    """
    Fetch derivatives data from Bybit (funding rate, open interest).
    Note: Bybit API may be geo-restricted (403 Forbidden) depending on region.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MarketManus/1.0)",
        "Accept": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10, headers=headers) as client:
            funding_rate = None
            
            try:
                funding_resp = await client.get(
                    f"{BASE_URL}/v5/market/funding/history",
                    params={"category": "linear", "symbol": symbol, "limit": 1}
                )
                
                if funding_resp.status_code == 200:
                    data = funding_resp.json()
                    if data.get("result", {}).get("list"):
                        latest = data["result"]["list"][0]
                        funding_rate = float(latest.get("fundingRate", 0))
                elif funding_resp.status_code == 403:
                    return {
                        "source": "bybit",
                        "error": "geo-blocked",
                        "kind": "derivatives"
                    }
            except Exception:
                pass
            
            if funding_rate is None:
                return {
                    "source": "bybit",
                    "error": "no-data",
                    "kind": "derivatives"
                }
            
            sentiment_score = None
            if funding_rate > 0.01:
                sentiment_score = 0.7
            elif funding_rate > 0:
                sentiment_score = 0.6  
            elif funding_rate > -0.01:
                sentiment_score = 0.4
            else:
                sentiment_score = 0.3
            
            return {
                "source": "bybit",
                "funding_rate": funding_rate,
                "sentiment_score": sentiment_score,
                "kind": "derivatives"
            }
            
    except Exception:
        return {
            "source": "bybit",
            "error": "fetch-failed",
            "kind": "derivatives"
        }
