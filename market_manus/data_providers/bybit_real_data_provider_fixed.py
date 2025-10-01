# market_manus/data_providers/bybit_real_data_provider_fixed.py
from __future__ import annotations
import os
import time
import logging
from typing import Optional, List, Dict, Any
import requests
import pandas as pd

logger = logging.getLogger(__name__)

_BYBIT_BASE_REAL = "https://api.bybit.com"
_BYBIT_BASE_TEST = "https://api-demo.bybit.com"

_INTERVAL_MAP = {
    "1m": "1",
    "3m": "3",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "1h": "60",
    "2h": "120",
    "4h": "240",
    "6h": "360",
    "12h": "720",
    "1d": "D",
}

class RealBybitDataProvider:
    """
    Provider real Bybit (HTTP v5).
    - test_connection()
    - get_current_price(symbol)
    - get_klines(symbol, interval, start_ms=None, end_ms=None, limit=1000) -> DataFrame
    """

    def __init__(self, testnet: bool = True, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.testnet = testnet
        self.base_url = _BYBIT_BASE_TEST if testnet else _BYBIT_BASE_REAL
        self.api_key = api_key or os.getenv("BYBIT_API_KEY", "")
        self.api_secret = api_secret or os.getenv("BYBIT_API_SECRET", "")

        logger.debug("Inicializando Bybit Data Provider")
        logger.debug("Testnet: %s", self.testnet)
        logger.debug("Base URL: %s", self.base_url)
        logger.debug("API Key: %s...", (self.api_key[:10] if self.api_key else ""))

    # ------------------- util http -------------------
    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = self.base_url + path
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        if str(data.get("retCode")) != "0":
            raise RuntimeError(f"Bybit error: {data.get('retMsg')}")
        return data

    # ------------------- público -------------------
    def test_connection(self) -> bool:
        try:
            self.get_current_price("ETHUSDT")
            return True
        except Exception as e:
            logger.warning("Falha test_connection: %s", e)
            return False

    def get_current_price(self, symbol: str) -> float:
        data = self._get(
            "/v5/market/tickers",
            {"category": "linear", "symbol": symbol}
        )
        result = data["result"]["list"]
        if not result:
            raise RuntimeError("Sem preços")
        return float(result[0]["lastPrice"])

    def get_klines(
        self,
        symbol: str,
        interval: str,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """
        Baixa candles (máx servidor ~1000 por chamada).
        interval: '1m','5m','15m','30m','1h','4h','1d'
        """
        iv = _INTERVAL_MAP.get(interval, None)
        if iv is None:
            raise ValueError(f"Intervalo inválido: {interval}")

        remain = limit
        cursor = None
        frames: List[pd.DataFrame] = []

        while remain > 0:
            page_size = min(remain, 1000)  # limite seguro por chamada
            params = {
                "category": "linear",
                "symbol": symbol,
                "interval": iv,
                "limit": page_size,
            }
            if start_ms:
                params["start"] = start_ms
            if end_ms:
                params["end"] = end_ms
            if cursor:
                params["cursor"] = cursor

            data = self._get("/v5/market/kline", params)
            lst = data["result"].get("list", [])
            if not lst:
                break

            # Bybit retorna: [ startTime, open, high, low, close, volume, turnover ]
            df = pd.DataFrame(lst, columns=[
                "start", "open", "high", "low", "close", "volume", "turnover"
            ])
            # normaliza tipos
            for col in ["open", "high", "low", "close", "volume", "turnover"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            df["timestamp"] = pd.to_datetime(df["start"], unit="ms")
            df = df[["timestamp", "open", "high", "low", "close", "volume"]].sort_values("timestamp")
            frames.append(df)

            remain -= len(df)
            cursor = data["result"].get("nextPageCursor")
            if not cursor:
                break

            # evita rate limit
            time.sleep(0.15)

        if not frames:
            # sempre retorna DataFrame válido
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

        out = pd.concat(frames, ignore_index=True)
        return out
