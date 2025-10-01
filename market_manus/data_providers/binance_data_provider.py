#!/usr/bin/env python3
"""
BinanceDataProvider - Módulo para obter dados reais da Binance API.
Integração completa com endpoints públicos para dados de mercado.
"""

import requests
import time
import hmac
import hashlib
from typing import Dict, List, Optional, Any

class BinanceDataProvider:
    """Provedor de dados reais da Binance API"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """
        Inicializa o provedor de dados da Binance
        
        Args:
            api_key: Chave da API Binance
            api_secret: Segredo da API Binance
            testnet: Se True, usa testnet; se False, usa mainnet
        """
        self.testnet = testnet
        if testnet:
            self.base_url = "https://testnet.binance.vision/api"
        else:
            # Usar Binance.US pois funciona no Replit (binance.com é bloqueado)
            self.base_url = "https://api.binance.us/api"
        
        self.api_key = api_key
        self.api_secret = api_secret

    def _generate_signature(self, query_string: str) -> str:
        """Gera assinatura HMAC-SHA256 para autenticação"""
        return hmac.new(
            self.api_secret.encode("utf-8"), 
            query_string.encode("utf-8"), 
            hashlib.sha256
        ).hexdigest()

    def _get_public(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Any]:
        """
        Faz requisição GET pública (sem autenticação) para a API Binance
        
        Args:
            endpoint: Endpoint da API (ex: "/v3/ticker/24hr")
            params: Parâmetros da requisição
            
        Returns:
            Dados da resposta ou None em caso de erro
        """
        url = self.base_url + endpoint
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de conexão: {e}")
            return None

    def _get_authenticated(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Any]:
        """
        Faz requisição GET autenticada para a API Binance
        
        Args:
            endpoint: Endpoint da API
            params: Parâmetros da requisição
            
        Returns:
            Dados da resposta ou None em caso de erro
        """
        url = self.base_url + endpoint
        
        if params is None:
            params = {}
        
        params['timestamp'] = int(time.time() * 1000)
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        signature = self._generate_signature(query_string)
        params['signature'] = signature
        
        headers = {
            "X-MBX-APIKEY": self.api_key
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de conexão autenticada: {e}")
            return None

    def get_tickers(self, category: str = "spot") -> Optional[Dict[str, Any]]:
        """
        Obtém informações de todos os tickers (compatível com interface Bybit)
        
        Args:
            category: Categoria (ignorado na Binance, sempre spot)
            
        Returns:
            Dados dos tickers em formato compatível
        """
        data = self._get_public("/v3/ticker/24hr")
        
        if data:
            # Converter formato Binance para formato compatível
            result = {
                "list": []
            }
            
            for ticker in data:
                result["list"].append({
                    "symbol": ticker.get("symbol"),
                    "lastPrice": ticker.get("lastPrice"),
                    "highPrice24h": ticker.get("highPrice"),
                    "lowPrice24h": ticker.get("lowPrice"),
                    "volume24h": ticker.get("volume"),
                    "turnover24h": ticker.get("quoteVolume"),
                    "price24hPcnt": ticker.get("priceChangePercent")
                })
            
            return result
        return None

    def get_kline(
        self, 
        category: str, 
        symbol: str, 
        interval: str, 
        limit: int = 200,
        start: int = None,
        end: int = None
    ) -> Optional[List[List[Any]]]:
        """
        Obtém dados de k-line (velas/candlesticks)
        
        Args:
            category: Categoria (ignorado na Binance)
            symbol: Símbolo do par (ex: "BTCUSDT")
            interval: Intervalo das velas (Bybit format: "1", "5", "15", "60", "240", "D")
            limit: Número máximo de velas (máx: 1000)
            start: Timestamp inicial em milissegundos (opcional)
            end: Timestamp final em milissegundos (opcional)
            
        Returns:
            Lista de velas em formato compatível com Bybit
        """
        # Converter intervalo Bybit para Binance
        interval_map = {
            "1": "1m",
            "5": "5m",
            "15": "15m",
            "30": "30m",
            "60": "1h",
            "240": "4h",
            "D": "1d"
        }
        
        binance_interval = interval_map.get(interval, "1m")
        
        params = {
            "symbol": symbol,
            "interval": binance_interval,
            "limit": min(limit, 1000)  # Binance máx é 1000
        }
        
        # Adicionar timestamps se fornecidos
        if start is not None:
            params["startTime"] = start
        if end is not None:
            params["endTime"] = end
        
        data = self._get_public("/v3/klines", params)
        
        if data:
            # Converter formato Binance [timestamp, open, high, low, close, volume, ...]
            # para formato Bybit [[timestamp, open, high, low, close, volume], ...]
            result = []
            for kline in data:
                result.append([
                    str(kline[0]),  # timestamp
                    str(kline[1]),  # open
                    str(kline[2]),  # high
                    str(kline[3]),  # low
                    str(kline[4]),  # close
                    str(kline[5]),  # volume
                ])
            return result
        
        return None

    def get_latest_price(self, category: str, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Obtém o preço mais recente para um símbolo específico
        
        Args:
            category: Categoria (ignorado na Binance)
            symbol: Símbolo do par
            
        Returns:
            Dados do ticker em formato compatível
        """
        params = {"symbol": symbol}
        data = self._get_public("/v3/ticker/24hr", params)
        
        if data:
            # Converter para formato compatível
            return {
                "symbol": data.get("symbol"),
                "lastPrice": data.get("lastPrice"),
                "highPrice24h": data.get("highPrice"),
                "lowPrice24h": data.get("lowPrice"),
                "volume24h": data.get("volume"),
                "turnover24h": data.get("quoteVolume"),
                "price24hPcnt": data.get("priceChangePercent")
            }
        
        return None

    def get_orderbook(self, category: str, symbol: str, limit: int = 25) -> Optional[Dict[str, Any]]:
        """
        Obtém o livro de ofertas (orderbook)
        
        Args:
            category: Categoria (ignorado na Binance)
            symbol: Símbolo do par
            limit: Profundidade do livro (5, 10, 20, 50, 100, 500, 1000, 5000)
            
        Returns:
            Dados do orderbook em formato compatível
        """
        params = {
            "symbol": symbol,
            "limit": limit
        }
        
        data = self._get_public("/v3/depth", params)
        
        if data:
            # Converter para formato compatível
            return {
                "a": data.get("asks", []),  # asks
                "b": data.get("bids", [])   # bids
            }
        
        return None

    def get_recent_trades(self, category: str, symbol: str, limit: int = 60) -> Optional[List[Dict[str, Any]]]:
        """
        Obtém negociações recentes
        
        Args:
            category: Categoria (ignorado na Binance)
            symbol: Símbolo do par
            limit: Número de negociações (máx: 1000)
            
        Returns:
            Lista de negociações em formato compatível
        """
        params = {
            "symbol": symbol,
            "limit": limit
        }
        
        data = self._get_public("/v3/trades", params)
        
        if data:
            # Converter para formato compatível
            result = []
            for trade in data:
                result.append({
                    "price": trade.get("price"),
                    "qty": trade.get("qty"),
                    "time": trade.get("time"),
                    "isBuyerMaker": trade.get("isBuyerMaker")
                })
            return result
        
        return None

    def test_connection(self) -> bool:
        """
        Testa a conectividade com a API
        
        Returns:
            True se a conexão estiver funcionando, False caso contrário
        """
        try:
            result = self._get_public("/v3/ping")
            return result is not None
        except Exception:
            return False

    def get_server_time(self) -> Optional[int]:
        """
        Obtém o timestamp do servidor Binance
        
        Returns:
            Timestamp em milissegundos ou None em caso de erro
        """
        try:
            data = self._get_public("/v3/time")
            if data:
                return data.get("serverTime")
        except Exception:
            pass
        return None

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Obtém informações da conta (requer autenticação)
        
        Returns:
            Informações da conta ou None em caso de erro
        """
        return self._get_authenticated("/v3/account")
