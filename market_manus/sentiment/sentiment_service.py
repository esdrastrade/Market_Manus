import asyncio
import time
from .collectors import alt_fng, bybit_derivs, coingecko, coinglass, cryptopanic, glassnode, santiment, google_trends
from .services.normalizers import fng_to_score, pct_to_score, volume_to_score, clamp01
from .services.weights import DEFAULT_WEIGHTS
from .cache import memo

SOURCES = [
    ("alt_fng", alt_fng.fetch),
    ("coingecko", coingecko.fetch),
    ("bybit", bybit_derivs.fetch),
    ("coinglass", coinglass.fetch),
    ("cryptopanic", cryptopanic.fetch),
    ("santiment", santiment.fetch),
    ("glassnode", glassnode.fetch),
    ("google_trends", google_trends.fetch),
]

async def gather_sentiment(symbol: str, window: str = "1d") -> dict:
    tasks = []
    for name, fn in SOURCES:
        key = (name, symbol, window)
        cached = memo.get(key)
        if cached is None:
            tasks.append(_wrap_fetch(name, fn, symbol, window, key))
        else:
            tasks.append(asyncio.create_task(_return_cached(name, cached)))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    data = [r for r in results if isinstance(r, dict)]
    score = _composite_score(data)
    return {"symbol": symbol, "window": window, "score": score, "sources": data, "ts": time.time()}

async def _return_cached(name, cached):
    return cached

async def _wrap_fetch(name, fn, symbol, window, key):
    try:
        out = await fn(symbol, window)
        out["__name__"] = name
        memo.put(key, out)
        return out
    except Exception as e:
        return {"__name__":name, "error":str(e)}

def _composite_score(items):
    w = DEFAULT_WEIGHTS
    total_w = 0.0
    acc = 0.0
    for it in items:
        if it.get("error"):
            continue
        
        kind = it.get("kind")
        if kind == "macro_sentiment" and "score" in it:
            s = fng_to_score(float(it["score"]))
            acc += w["macro_sentiment"]*s
            total_w += w["macro_sentiment"]
        elif kind == "spot_market" and "chg_24h" in it:
            s = 0.6*pct_to_score(it.get("chg_24h",0.0)) + 0.4*volume_to_score(it.get("vol_24h",0.0))
            acc += w["spot_market"]*s
            total_w += w["spot_market"]
        elif kind == "derivatives" and it.get("funding"):
            f = 0.5
            acc += w["derivatives"]*clamp01(f)
            total_w += w["derivatives"]
        elif kind == "news" and "count" in it and it.get("count") > 0:
            acc += w["news"]*0.5
            total_w += w["news"]
        elif kind == "social" and "note" not in it:
            acc += w["social"]*0.5
            total_w += w["social"]
        elif kind == "onchain" and "note" not in it:
            acc += w["onchain"]*0.5
            total_w += w["onchain"]
    return round(acc/total_w, 3) if total_w>0 else None
