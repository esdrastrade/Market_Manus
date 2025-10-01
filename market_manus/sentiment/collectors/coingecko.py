import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from cachetools import TTLCache
import re

_coin_id_cache = TTLCache(maxsize=500, ttl=3600)

async def _resolve_coin_id(symbol: str) -> str | None:
    """
    Resolve Binance symbol (e.g., BTCUSDT) to CoinGecko coin ID (e.g., bitcoin).
    Uses search API with in-memory caching.
    """
    symbol_upper = symbol.upper()
    
    if symbol_upper in _coin_id_cache:
        return _coin_id_cache[symbol_upper]
    
    base_symbol = re.sub(r'(USDT|USDC|USD|BUSD|TUSD)$', '', symbol_upper)
    
    search_url = "https://api.coingecko.com/api/v3/search"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(search_url, params={"query": base_symbol})
        r.raise_for_status()
        data = r.json()
    
    coins = data.get("coins", [])
    if not coins:
        _coin_id_cache[symbol_upper] = None
        return None
    
    for coin in coins:
        coin_symbol = coin.get("symbol", "").upper()
        if coin_symbol == base_symbol:
            coin_id = coin.get("id")
            _coin_id_cache[symbol_upper] = coin_id
            return coin_id
    
    first_coin_id = coins[0].get("id")
    _coin_id_cache[symbol_upper] = first_coin_id
    return first_coin_id

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def fetch(symbol: str, window: str) -> dict:
    """
    Fetch spot market data from CoinGecko for any crypto asset.
    Automatically resolves Binance symbols to CoinGecko IDs via search API.
    """
    try:
        coin_id = await _resolve_coin_id(symbol)
        
        if not coin_id:
            return {
                "source": "coingecko",
                "error": "not-found",
                "kind": "spot_market"
            }
        
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, params={"localization":"false","tickers":"false","market_data":"true"})
            r.raise_for_status()
            d = r.json()
        
        md = d["market_data"]
        return {
            "source": "coingecko",
            "price": md["current_price"]["usd"],
            "chg_24h": md["price_change_percentage_24h"],
            "vol_24h": md["total_volume"]["usd"],
            "kind": "spot_market"
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            return {
                "source": "coingecko",
                "error": "rate-limit",
                "kind": "spot_market"
            }
        return {
            "source": "coingecko",
            "error": "api-error",
            "kind": "spot_market"
        }
    except Exception:
        return {
            "source": "coingecko",
            "error": "fetch-failed",
            "kind": "spot_market"
        }
