import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def fetch(symbol: str, window: str) -> dict:
    mapping = {"BTCUSDT":"bitcoin","ETHUSDT":"ethereum","BNBUSDT":"binancecoin"}
    coin = mapping.get(symbol.upper(), "bitcoin")
    url = f"https://api.coingecko.com/api/v3/coins/{coin}"
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
