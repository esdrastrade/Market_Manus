#!/usr/bin/env python3
"""
BybitRealDataProvider - Módulo para obter dados reais da Bybit API V5.
Integração completa com autenticação e endpoints principais.
"""

import requests
import time
import hmac
import hashlib
from typing import Dict, List, Optional, Any

class BybitRealDataProvider:
    """Provedor de dados reais da Bybit API V5"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """
        Inicializa o provedor de dados da Bybit
        
        Args:
            api_key: Chave da API Bybit
            api_secret: Segredo da API Bybit
            testnet: Se True, usa testnet; se False, usa mainnet
        """
        self.testnet = testnet
        self.base_url = "https://api-demo.bybit.com" if testnet else "https://api.bybit.com"
        self.api_key = api_key
        self.api_secret = api_secret

    def _generate_signature(self, params: str) -> str:
        """Gera assinatura HMAC-SHA256 para autenticação"""
        return hmac.new(
            self.api_secret.encode("utf-8"), 
            params.encode("utf-8"), 
            hashlib.sha256
        ).hexdigest()

    def _get_public(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Faz requisição GET pública (sem autenticação) para a API Bybit
        
        Args:
            endpoint: Endpoint da API (ex: "/v5/market/tickers")
            params: Parâmetros da requisição
            
        Returns:
            Dados da resposta ou None em caso de erro
        """
        url = self.base_url + endpoint
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("retCode") == 0:
                return data.get("result")
            else:
                print(f"❌ Erro na API Bybit: {data.get('retMsg')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de conexão: {e}")
            return None

    def _get(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Faz requisição GET autenticada para a API Bybit
        
        Args:
            endpoint: Endpoint da API (ex: "/v5/market/tickers")
            params: Parâmetros da requisição
            
        Returns:
            Dados da resposta ou None em caso de erro
        """
        url = self.base_url + endpoint
        timestamp = str(int(time.time() * 1000))
        recv_window = "10000"
        
        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window,
        }

        if params:
            query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            signature_payload = timestamp + self.api_key + recv_window + query_string
        else:
            query_string = ""
            signature_payload = timestamp + self.api_key + recv_window

        headers["X-BAPI-SIGN"] = self._generate_signature(signature_payload)

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("retCode") == 0:
                return data.get("result")
            else:
                print(f"❌ Erro na API Bybit: {data.get('retMsg')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de conexão: {e}")
            return None

    def get_tickers(self, category: str = "spot") -> Optional[Dict[str, Any]]:
        """
        Obtém informações de tickers (preços, volumes, etc.)
        
        Args:
            category: Categoria do instrumento ("spot", "linear", "inverse", "option")
            
        Returns:
            Dados dos tickers ou None em caso de erro
        """
        return self._get_public("/v5/market/tickers", {"category": category})

    def get_kline(
        self, 
        category: str, 
        symbol: str, 
        interval: str, 
        limit: int = 200
    ) -> Optional[List[List[Any]]]:
        """
        Obtém dados de k-line (velas/candlesticks)
        
        Args:
            category: Categoria do instrumento
            symbol: Símbolo do par (ex: "BTCUSDT")
            interval: Intervalo das velas ("1", "5", "15", "30", "60", "240", "D")
            limit: Número máximo de velas (máx: 1000)
            
        Returns:
            Lista de velas ou None em caso de erro
        """
        params = {
            "category": category,
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        result = self._get_public("/v5/market/kline", params)
        return result.get("list") if result else None

    def get_latest_price(self, category: str, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Obtém o preço mais recente para um símbolo específico
        
        Args:
            category: Categoria do instrumento
            symbol: Símbolo do par
            
        Returns:
            Dados do ticker ou None em caso de erro
        """
        params = {"category": category, "symbol": symbol}
        result = self._get_public("/v5/market/tickers", params)
        
        if result and result.get("list"):
            return result["list"][0]
        return None

    def get_orderbook(self, category: str, symbol: str, limit: int = 25) -> Optional[Dict[str, Any]]:
        """
        Obtém o livro de ofertas (orderbook)
        
        Args:
            category: Categoria do instrumento
            symbol: Símbolo do par
            limit: Profundidade do livro (1, 25, 50, 100, 200)
            
        Returns:
            Dados do orderbook ou None em caso de erro
        """
        params = {
            "category": category,
            "symbol": symbol,
            "limit": limit
        }
        return self._get_public("/v5/market/orderbook", params)

    def get_recent_trades(self, category: str, symbol: str, limit: int = 60) -> Optional[List[Dict[str, Any]]]:
        """
        Obtém negociações recentes
        
        Args:
            category: Categoria do instrumento
            symbol: Símbolo do par
            limit: Número de negociações (máx: 1000)
            
        Returns:
            Lista de negociações ou None em caso de erro
        """
        params = {
            "category": category,
            "symbol": symbol,
            "limit": limit
        }
        result = self._get_public("/v5/market/recent-trade", params)
        return result.get("list") if result else None

    def test_connection(self) -> bool:
        """
        Testa a conectividade com a API
        
        Returns:
            True se a conexão estiver funcionando, False caso contrário
        """
        try:
            result = self.get_tickers(category="spot")
            return result is not None
        except Exception:
            return False

    def get_server_time(self) -> Optional[int]:
        """
        Obtém o timestamp do servidor Bybit
        
        Returns:
            Timestamp em milissegundos ou None em caso de erro
        """
        try:
            response = requests.get(f"{self.base_url}/v5/market/time", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("retCode") == 0:
                    return int(data.get("result", {}).get("timeSecond", 0)) * 1000
        except Exception:
            pass
        return None
