"""
Sistema de cache para dados históricos de mercado
Salva dados em formato Parquet para rápida recuperação
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd


class HistoricalDataCache:
    """Gerencia cache de dados históricos em disco"""
    
    def __init__(self, cache_dir: str = "data"):
        """
        Inicializa o sistema de cache
        
        Args:
            cache_dir: Diretório raiz para armazenar cache
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Carrega metadata do cache"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Salva metadata do cache"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _generate_cache_key(
        self,
        symbol: str,
        interval: str,
        start_date: str,
        end_date: str
    ) -> str:
        """
        Gera chave única para identificar cache
        
        Args:
            symbol: Símbolo do ativo (ex: BTCUSDT)
            interval: Intervalo (ex: 1h)
            start_date: Data inicial (YYYY-MM-DD)
            end_date: Data final (YYYY-MM-DD)
            
        Returns:
            Chave única do cache
        """
        start_fmt = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d%m%y")
        end_fmt = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d%m%y")
        return f"{symbol}_{interval}_{start_fmt}_until_{end_fmt}"
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Retorna caminho do arquivo de cache"""
        return self.cache_dir / f"{cache_key}.parquet"
    
    def get(
        self,
        symbol: str,
        interval: str,
        start_date: str,
        end_date: str
    ) -> Optional[List[List[Any]]]:
        """
        Recupera dados do cache se existirem
        
        Args:
            symbol: Símbolo do ativo
            interval: Intervalo
            start_date: Data inicial (YYYY-MM-DD)
            end_date: Data final (YYYY-MM-DD)
            
        Returns:
            Lista de klines no formato Binance ou None se não encontrado
        """
        cache_key = self._generate_cache_key(symbol, interval, start_date, end_date)
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            return None
        
        try:
            df = pd.read_parquet(cache_path)
            
            # Converter DataFrame de volta para formato kline
            klines = df.values.tolist()
            
            # Converter valores para strings no formato correto Binance
            # Timestamp (coluna 0) deve ser int sem decimais
            # OHLC e volume devem ser strings mantendo precisão decimal
            klines_str = []
            for row in klines:
                formatted_row = []
                for i, value in enumerate(row):
                    if i == 0:  # Timestamp - converter para int sem decimais
                        formatted_row.append(str(int(float(value))))
                    else:  # OHLC, volume, etc - remover .0 se for inteiro
                        str_val = str(value)
                        if str_val.endswith('.0'):
                            str_val = str_val[:-2]
                        formatted_row.append(str_val)
                klines_str.append(formatted_row)
            
            return klines_str
            
        except Exception as e:
            print(f"⚠️ Erro ao ler cache {cache_key}: {e}")
            return None
    
    def save(
        self,
        symbol: str,
        interval: str,
        start_date: str,
        end_date: str,
        klines: List[List[Any]]
    ):
        """
        Salva dados no cache
        
        Args:
            symbol: Símbolo do ativo
            interval: Intervalo
            start_date: Data inicial (YYYY-MM-DD)
            end_date: Data final (YYYY-MM-DD)
            klines: Lista de klines no formato Binance
        """
        cache_key = self._generate_cache_key(symbol, interval, start_date, end_date)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            # BUG FIX: Detectar número de colunas dinamicamente
            num_cols = len(klines[0]) if klines else 0
            
            if num_cols == 0:
                print(f"⚠️ Nenhum dado para salvar no cache {cache_key}")
                return
            
            # BUG FIX: Usar schema dinâmico baseado no número de colunas
            if num_cols == 6:
                col_names = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            else:
                col_names = ['timestamp', 'open', 'high', 'low', 'close', 'volume',
                           'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                           'taker_buy_quote', 'ignore'][:num_cols]
            
            # Converter klines para DataFrame com schema dinâmico
            df = pd.DataFrame(klines, columns=col_names)
            
            # BUG FIX: Converter tipos de forma segura para todas as colunas numéricas
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    pass
            
            # Salvar em Parquet
            df.to_parquet(cache_path, compression='snappy', index=False)
            
            # Atualizar metadata
            self.metadata[cache_key] = {
                "symbol": symbol,
                "interval": interval,
                "start_date": start_date,
                "end_date": end_date,
                "candles": len(klines),
                "columns": num_cols,
                "cached_at": datetime.now().isoformat(),
                "file_size_kb": round(cache_path.stat().st_size / 1024, 2)
            }
            self._save_metadata()
            
            print(f"✅ Cache salvo: {cache_key} ({len(klines):,} candles, {num_cols} colunas)")
            
        except Exception as e:
            print(f"❌ Erro ao salvar cache {cache_key}: {e}")
    
    def list_cached_datasets(self) -> List[Dict]:
        """
        Lista todos os datasets em cache
        
        Returns:
            Lista de dicionários com informações dos caches
        """
        return [
            {"key": key, **info}
            for key, info in self.metadata.items()
        ]
    
    def delete(self, cache_key: str) -> bool:
        """
        Remove um cache específico
        
        Args:
            cache_key: Chave do cache
            
        Returns:
            True se removido com sucesso
        """
        cache_path = self._get_cache_path(cache_key)
        
        if cache_path.exists():
            cache_path.unlink()
            if cache_key in self.metadata:
                del self.metadata[cache_key]
                self._save_metadata()
            return True
        return False
    
    def clear_all(self):
        """Remove todos os caches"""
        for cache_key in list(self.metadata.keys()):
            self.delete(cache_key)
        print("✅ Todos os caches foram removidos")
