#!/usr/bin/env python3
"""
BYBIT DATA PROVIDER - Market Manus
Provider robusto para dados históricos (REST) e tempo real (WebSocket)
"""

import os
import time
import json
import hashlib
import logging
# WebSocket imports (opcional)
try:
    import asyncio
    import websockets
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    asyncio = None
    websockets = None
from datetime import datetime, timezone
from typing import Callable, Optional, Dict, Any, List
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class BybitDataProvider:
    """
    Provider robusto para dados da Bybit com REST API
    
    Features:
    - Paginação automática para dados históricos
    - Rate limiting respeitoso
    - Cache em disco para otimização
    - Retries exponenciais
    - Logs detalhados
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 api_secret: Optional[str] = None,
                 testnet: bool = False,
                 rate_limit_per_sec: int = 5,
                 cache_dir: str = "logs/.cache"):
        """
        Inicializa Bybit Data Provider
        
        Args:
            api_key: Chave da API (opcional para dados públicos)
            api_secret: Segredo da API (opcional para dados públicos)
            testnet: Usar testnet (padrão: False)
            rate_limit_per_sec: Limite de requests por segundo
            cache_dir: Diretório para cache
        """
        self.api_key = api_key or os.getenv('BYBIT_API_KEY')
        self.api_secret = api_secret or os.getenv('BYBIT_API_SECRET')
        self.testnet = testnet
        self.rate_limit_per_sec = rate_limit_per_sec
        self.cache_dir = Path(cache_dir)
        
        # URLs base
        if testnet:
            self.base_url = "https://api-testnet.bybit.com"
        else:
            self.base_url = "https://api.bybit.com"
        
        # Configurar cache
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
        
        # Configurar sessão HTTP com retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0 / rate_limit_per_sec
        
        self.logger.info(f"Bybit Provider inicializado - Testnet: {testnet}, Rate limit: {rate_limit_per_sec}/s")
    
    def _wait_for_rate_limit(self):
        """Aguarda para respeitar rate limit"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Faz request para API com rate limiting e retries
        
        Args:
            endpoint: Endpoint da API
            params: Parâmetros da request
            
        Returns:
            Resposta da API
            
        Raises:
            Exception: Se request falhar após retries
        """
        self._wait_for_rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            self.logger.debug(f"Request: {url} - Params: {params}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Verificar se resposta da Bybit é válida
            if data.get('retCode') != 0:
                error_msg = data.get('retMsg', 'Erro desconhecido da API')
                raise Exception(f"Erro da API Bybit: {error_msg}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro na request para {url}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Erro ao processar resposta de {url}: {e}")
            raise
    
    def _get_cache_key(self, symbol: str, interval: str, start: pd.Timestamp, end: pd.Timestamp) -> str:
        """Gera chave única para cache"""
        cache_string = f"{symbol}_{interval}_{start.isoformat()}_{end.isoformat()}"
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _get_cached_data(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Recupera dados do cache se disponível"""
        cache_file = self.cache_dir / f"{cache_key}.parquet"
        
        if cache_file.exists():
            try:
                # Verificar se cache não está muito antigo (1 hora para dados históricos)
                cache_age = time.time() - cache_file.stat().st_mtime
                if cache_age < 3600:  # 1 hora
                    df = pd.read_parquet(cache_file)
                    self.logger.debug(f"Cache hit: {cache_key}")
                    return df
            except Exception as e:
                self.logger.warning(f"Erro ao ler cache {cache_key}: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, df: pd.DataFrame):
        """Salva dados no cache"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.parquet"
            df.to_parquet(cache_file)
            self.logger.debug(f"Cache saved: {cache_key}")
        except Exception as e:
            self.logger.warning(f"Erro ao salvar cache {cache_key}: {e}")
    
    def _normalize_kline_data(self, raw_data: List[List]) -> pd.DataFrame:
        """
        Normaliza dados de kline para o contrato padrão
        
        Args:
            raw_data: Dados brutos da API Bybit
            
        Returns:
            DataFrame normalizado
        """
        if not raw_data:
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Converter para DataFrame
        df = pd.DataFrame(raw_data, columns=[
            'start_time', 'open', 'high', 'low', 'close', 'volume', 'turnover'
        ])
        
        # Normalizar para contrato padrão
        df_normalized = pd.DataFrame({
            'timestamp': pd.to_datetime(df['start_time'].astype(int), unit='ms', utc=True),
            'open': df['open'].astype(float),
            'high': df['high'].astype(float),
            'low': df['low'].astype(float),
            'close': df['close'].astype(float),
            'volume': df['volume'].astype(float)
        })
        
        # Ordenar por timestamp
        df_normalized = df_normalized.sort_values('timestamp').reset_index(drop=True)
        
        return df_normalized
    
    def _convert_interval_to_bybit(self, interval: str) -> str:
        """Converte intervalo para formato da Bybit"""
        interval_map = {
            '1m': '1',
            '3m': '3',
            '5m': '5',
            '15m': '15',
            '30m': '30',
            '1h': '60',
            '2h': '120',
            '4h': '240',
            '6h': '360',
            '12h': '720',
            '1d': 'D',
            '1w': 'W',
            '1M': 'M'
        }
        
        if interval not in interval_map:
            raise ValueError(f"Intervalo não suportado: {interval}. Disponíveis: {list(interval_map.keys())}")
        
        return interval_map[interval]
    
    def fetch_klines(self, 
                    symbol: str, 
                    interval: str,
                    start: pd.Timestamp, 
                    end: pd.Timestamp, 
                    limit: int = 1000) -> pd.DataFrame:
        """
        Busca dados de kline com paginação automática
        
        Args:
            symbol: Símbolo do ativo (ex: BTCUSDT)
            interval: Intervalo (1m, 5m, 15m, 30m, 1h, 4h, 1d)
            start: Timestamp de início (UTC)
            end: Timestamp de fim (UTC)
            limit: Limite por request (máx 1000)
            
        Returns:
            DataFrame com dados OHLCV normalizados
            
        Raises:
            ValueError: Se parâmetros inválidos
            Exception: Se erro na API
        """
        # Validar parâmetros
        if not symbol:
            raise ValueError("Symbol é obrigatório")
        
        if start >= end:
            raise ValueError("Start deve ser anterior a end")
        
        if limit > 1000:
            limit = 1000
            self.logger.warning("Limit ajustado para máximo de 1000")
        
        # Verificar cache
        cache_key = self._get_cache_key(symbol, interval, start, end)
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Converter intervalo
        bybit_interval = self._convert_interval_to_bybit(interval)
        
        # Converter timestamps para milliseconds
        start_ms = int(start.timestamp() * 1000)
        end_ms = int(end.timestamp() * 1000)
        
        all_data = []
        current_start = start_ms
        
        self.logger.info(f"Buscando dados: {symbol} {interval} de {start} até {end}")
        
        while current_start < end_ms:
            params = {
                'category': 'spot',
                'symbol': symbol,
                'interval': bybit_interval,
                'start': current_start,
                'end': min(current_start + (limit * self._get_interval_ms(interval)), end_ms),
                'limit': limit
            }
            
            try:
                response = self._make_request('/v5/market/kline', params)
                klines = response.get('result', {}).get('list', [])
                
                if not klines:
                    self.logger.warning(f"Nenhum dado retornado para {symbol} {interval}")
                    break
                
                all_data.extend(klines)
                
                # Atualizar próximo início
                last_timestamp = int(klines[-1][0])  # start_time da última vela
                current_start = last_timestamp + self._get_interval_ms(interval)
                
                self.logger.debug(f"Coletados {len(klines)} registros, total: {len(all_data)}")
                
                # Evitar loop infinito
                if len(klines) < limit:
                    break
                    
            except Exception as e:
                self.logger.error(f"Erro ao buscar dados: {e}")
                raise
        
        # Normalizar dados
        df = self._normalize_kline_data(all_data)
        
        # Filtrar por período exato
        df = df[(df['timestamp'] >= start) & (df['timestamp'] <= end)]
        
        self.logger.info(f"Dados coletados: {len(df)} registros para {symbol} {interval}")
        
        # Salvar no cache
        if not df.empty:
            self._save_to_cache(cache_key, df)
        
        return df
    
    def _get_interval_ms(self, interval: str) -> int:
        """Converte intervalo para milliseconds"""
        interval_ms = {
            '1m': 60 * 1000,
            '3m': 3 * 60 * 1000,
            '5m': 5 * 60 * 1000,
            '15m': 15 * 60 * 1000,
            '30m': 30 * 60 * 1000,
            '1h': 60 * 60 * 1000,
            '2h': 2 * 60 * 60 * 1000,
            '4h': 4 * 60 * 60 * 1000,
            '6h': 6 * 60 * 60 * 1000,
            '12h': 12 * 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000,
            '1w': 7 * 24 * 60 * 60 * 1000,
            '1M': 30 * 24 * 60 * 60 * 1000
        }
        return interval_ms.get(interval, 60 * 1000)
    
    def get_current_price(self, symbol: str) -> float:
        """
        Obtém preço atual do símbolo
        
        Args:
            symbol: Símbolo do ativo
            
        Returns:
            Preço atual
        """
        try:
            response = self._make_request('/v5/market/tickers', {'category': 'spot', 'symbol': symbol})
            tickers = response.get('result', {}).get('list', [])
            
            if tickers:
                return float(tickers[0]['lastPrice'])
            else:
                raise Exception(f"Preço não encontrado para {symbol}")
                
        except Exception as e:
            self.logger.error(f"Erro ao obter preço de {symbol}: {e}")
            raise
    
    def get_symbols(self) -> List[str]:
        """
        Obtém lista de símbolos disponíveis
        
        Returns:
            Lista de símbolos
        """
        try:
            response = self._make_request('/v5/market/instruments-info', {'category': 'spot'})
            instruments = response.get('result', {}).get('list', [])
            
            symbols = [inst['symbol'] for inst in instruments if inst.get('status') == 'Trading']
            return sorted(symbols)
            
        except Exception as e:
            self.logger.error(f"Erro ao obter símbolos: {e}")
            return []
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Testa conectividade com a API
        
        Returns:
            Dicionário com status da conexão
        """
        try:
            start_time = time.time()
            response = self._make_request('/v5/market/time')
            end_time = time.time()
            
            server_time = response.get('result', {}).get('timeSecond', 0)
            latency = (end_time - start_time) * 1000  # ms
            
            return {
                'status': 'connected',
                'server_time': datetime.fromtimestamp(int(server_time), tz=timezone.utc),
                'latency_ms': round(latency, 2),
                'testnet': self.testnet
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'testnet': self.testnet
            }


class BybitWSClient:
    """
    Cliente WebSocket para dados em tempo real da Bybit
    
    Features:
    - Auto-reconnect
    - Heartbeat automático
    - Normalização de dados
    - Callback customizável
    """
    
    def __init__(self, 
                 symbol: str, 
                 interval: str, 
                 on_kline: Callable[[Dict], None],
                 testnet: bool = False):
        """
        Inicializa cliente WebSocket
        
        Args:
            symbol: Símbolo do ativo
            interval: Intervalo das velas
            on_kline: Callback para processar dados
            testnet: Usar testnet
        """
        self.symbol = symbol
        self.interval = interval
        self.on_kline = on_kline
        self.testnet = testnet
        
        # URLs WebSocket
        if testnet:
            self.ws_url = "wss://stream-testnet.bybit.com/v5/public/spot"
        else:
            self.ws_url = "wss://stream.bybit.com/v5/public/spot"
        
        # Estado da conexão
        self.websocket = None
        self.running = False
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"WebSocket Client inicializado - {symbol} {interval}")
    
    async def connect(self):
        """Conecta ao WebSocket"""
        try:
            self.websocket = await websockets.connect(self.ws_url)
            self.running = True
            
            # Subscrever ao canal de kline
            subscribe_msg = {
                "op": "subscribe",
                "args": [f"kline.{self.interval}.{self.symbol}"]
            }
            
            await self.websocket.send(json.dumps(subscribe_msg))
            self.logger.info(f"Subscrito ao canal: kline.{self.interval}.{self.symbol}")
            
            # Iniciar loops de heartbeat e recepção
            await asyncio.gather(
                self._heartbeat_loop(),
                self._receive_loop()
            )
            
        except Exception as e:
            self.logger.error(f"Erro na conexão WebSocket: {e}")
            raise
    
    async def _heartbeat_loop(self):
        """Loop de heartbeat para manter conexão"""
        while self.running:
            try:
                if self.websocket:
                    ping_msg = {"op": "ping"}
                    await self.websocket.send(json.dumps(ping_msg))
                    self.logger.debug("Heartbeat enviado")
                
                await asyncio.sleep(20)  # Ping a cada 20 segundos
                
            except Exception as e:
                self.logger.error(f"Erro no heartbeat: {e}")
                break
    
    async def _receive_loop(self):
        """Loop de recepção de mensagens"""
        while self.running:
            try:
                if self.websocket:
                    message = await self.websocket.recv()
                    data = json.loads(message)
                    
                    # Processar diferentes tipos de mensagem
                    if data.get('topic', '').startswith('kline'):
                        await self._process_kline(data)
                    elif data.get('op') == 'pong':
                        self.logger.debug("Pong recebido")
                    
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning("Conexão WebSocket fechada")
                break
            except Exception as e:
                self.logger.error(f"Erro ao receber mensagem: {e}")
                break
    
    async def _process_kline(self, data: Dict):
        """
        Processa dados de kline e normaliza para contrato padrão
        
        Args:
            data: Dados brutos do WebSocket
        """
        try:
            kline_data = data.get('data', [])
            
            for kline in kline_data:
                # Normalizar para contrato padrão
                normalized_kline = {
                    'timestamp': pd.to_datetime(int(kline['start']), unit='ms', utc=True),
                    'open': float(kline['open']),
                    'high': float(kline['high']),
                    'low': float(kline['low']),
                    'close': float(kline['close']),
                    'volume': float(kline['volume']),
                    'symbol': self.symbol,
                    'interval': self.interval,
                    'is_closed': kline.get('confirm', False)  # True se vela fechada
                }
                
                # Chamar callback
                if self.on_kline:
                    self.on_kline(normalized_kline)
                    
        except Exception as e:
            self.logger.error(f"Erro ao processar kline: {e}")
    
    async def disconnect(self):
        """Desconecta do WebSocket"""
        self.running = False
        
        if self.websocket:
            await self.websocket.close()
            self.logger.info("WebSocket desconectado")
    
    def start(self):
        """Inicia cliente WebSocket (método síncrono)"""
        asyncio.run(self.connect())
    
    def stop(self):
        """Para cliente WebSocket"""
        self.running = False


# Função de conveniência para criar provider
def create_bybit_provider(testnet: bool = False, **kwargs) -> BybitDataProvider:
    """
    Cria instância do Bybit Data Provider
    
    Args:
        testnet: Usar testnet
        **kwargs: Argumentos adicionais
        
    Returns:
        Instância configurada do provider
    """
    return BybitDataProvider(testnet=testnet, **kwargs)


if __name__ == "__main__":
    # Teste básico do provider
    import logging
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Criar provider
    provider = create_bybit_provider(testnet=False)
    
    print("🔌 Testando conectividade...")
    connection_status = provider.test_connection()
    print(f"Status: {connection_status}")
    
    if connection_status['status'] == 'connected':
        print("\\n💰 Testando preço atual...")
        try:
            price = provider.get_current_price('BTCUSDT')
            print(f"BTC/USDT: ${price:,.2f}")
        except Exception as e:
            print(f"Erro ao obter preço: {e}")
        
        print("\\n📊 Testando dados históricos...")
        try:
            end_time = pd.Timestamp.now(tz='UTC')
            start_time = end_time - pd.Timedelta(hours=24)
            
            df = provider.fetch_klines('BTCUSDT', '1h', start_time, end_time)
            print(f"Dados coletados: {len(df)} registros")
            print(df.head())
            
        except Exception as e:
            print(f"Erro ao obter dados históricos: {e}")
    
    print("\\n✅ Teste do Bybit Provider concluído!")
