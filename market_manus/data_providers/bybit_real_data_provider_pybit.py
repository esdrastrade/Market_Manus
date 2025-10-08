#!/usr/bin/env python3
"""
Bybit Real Data Provider - Using Official pybit Library
Provides real market data from Bybit API using the official Python SDK
"""

import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd

try:
    from pybit.unified_trading import HTTP
    PYBIT_AVAILABLE = True
except ImportError:
    PYBIT_AVAILABLE = False
    print("⚠️ pybit not installed. Install with: pip install pybit")

class BybitRealDataProvider:
    """
    Real data provider using official Bybit pybit library
    Provides historical and real-time market data for trading strategies
    """
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = False):
        self.api_key = api_key or os.getenv('BYBIT_API_KEY')
        self.api_secret = api_secret or os.getenv('BYBIT_API_SECRET')
        self.testnet = testnet
        
        if not PYBIT_AVAILABLE:
            raise ImportError("pybit library is required. Install with: pip install pybit")
        
        # Initialize HTTP session
        self.session = HTTP(
            testnet=self.testnet,
            api_key=self.api_key,
            api_secret=self.api_secret,
        )
        
        # Interval mapping for Bybit API
        self.interval_mapping = {
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
        
        # Category mapping
        self.category_mapping = {
            'spot': 'spot',
            'linear': 'linear',
            'inverse': 'inverse'
        }
    
    def test_connection(self) -> bool:
        """Test connection to Bybit API"""
        try:
            # Test with a simple server time request
            response = self.session.get_server_time()
            return response.get('retCode') == 0
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def get_server_time(self) -> Dict[str, Any]:
        """Get Bybit server time"""
        try:
            return self.session.get_server_time()
        except Exception as e:
            print(f"❌ Error getting server time: {e}")
            return {}
    
    def get_instruments_info(self, category: str = 'spot', symbol: str = None) -> Dict[str, Any]:
        """Get instruments information"""
        try:
            params = {'category': category}
            if symbol:
                params['symbol'] = symbol
            return self.session.get_instruments_info(**params)
        except Exception as e:
            print(f"❌ Error getting instruments info: {e}")
            return {}
    
    def get_tickers(self, category: str = 'spot', symbol: str = None) -> Dict[str, Any]:
        """Get ticker information"""
        try:
            params = {'category': category}
            if symbol:
                params['symbol'] = symbol
            return self.session.get_tickers(**params)
        except Exception as e:
            print(f"❌ Error getting tickers: {e}")
            return {}
    
    def get_latest_price(self, symbol: str, category: str = 'spot') -> Optional[float]:
        """Get latest price for a symbol"""
        try:
            response = self.get_tickers(category=category, symbol=symbol)
            if response.get('retCode') == 0 and response.get('result', {}).get('list'):
                ticker = response['result']['list'][0]
                return float(ticker.get('lastPrice', 0))
            return None
        except Exception as e:
            print(f"❌ Error getting latest price for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, interval: str, start_time: datetime = None, 
                          end_time: datetime = None, limit: int = 200, 
                          category: str = 'spot') -> List[Dict[str, Any]]:
        """
        Get historical kline data from Bybit
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Time interval ('1m', '5m', '15m', '30m', '1h', '4h', '1d')
            start_time: Start datetime
            end_time: End datetime  
            limit: Number of candles to retrieve (max 1000)
            category: Product category ('spot', 'linear', 'inverse')
        
        Returns:
            List of OHLCV data dictionaries
        """
        try:
            # Map interval to Bybit format
            bybit_interval = self.interval_mapping.get(interval, '60')
            
            # Prepare parameters
            params = {
                'category': category,
                'symbol': symbol,
                'interval': bybit_interval,
                'limit': min(limit, 1000)  # Bybit max limit is 1000
            }
            
            # Add time parameters if provided
            if start_time:
                params['start'] = int(start_time.timestamp() * 1000)
            if end_time:
                params['end'] = int(end_time.timestamp() * 1000)
            
            print(f"🔄 Fetching {symbol} data: {interval} interval, limit: {limit}")
            
            # Make API request
            response = self.session.get_kline(**params)
            
            if response.get('retCode') != 0:
                print(f"❌ API Error: {response.get('retMsg', 'Unknown error')}")
                return []
            
            # Parse response
            klines = response.get('result', {}).get('list', [])
            
            # Convert to standardized format
            historical_data = []
            for kline in reversed(klines):  # Bybit returns in reverse order
                try:
                    candle = {
                        'timestamp': int(kline[0]),
                        'datetime': datetime.fromtimestamp(int(kline[0]) / 1000),
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5]),
                        'turnover': float(kline[6]) if len(kline) > 6 else 0.0
                    }
                    historical_data.append(candle)
                except (ValueError, IndexError) as e:
                    print(f"⚠️ Error parsing kline data: {e}")
                    continue
            
            print(f"✅ Retrieved {len(historical_data)} candles for {symbol}")
            return historical_data
            
        except Exception as e:
            print(f"❌ Error fetching historical data for {symbol}: {e}")
            return []
    
    def get_orderbook(self, symbol: str, category: str = 'spot', limit: int = 25) -> Dict[str, Any]:
        """Get orderbook data"""
        try:
            params = {
                'category': category,
                'symbol': symbol,
                'limit': limit
            }
            return self.session.get_orderbook(**params)
        except Exception as e:
            print(f"❌ Error getting orderbook for {symbol}: {e}")
            return {}
    
    def get_recent_trades(self, symbol: str, category: str = 'spot', limit: int = 60) -> Dict[str, Any]:
        """Get recent public trades"""
        try:
            params = {
                'category': category,
                'symbol': symbol,
                'limit': limit
            }
            return self.session.get_public_trade_history(**params)
        except Exception as e:
            print(f"❌ Error getting recent trades for {symbol}: {e}")
            return {}
    
    def calculate_period_data(self, symbol: str, interval: str, days: int, 
                            category: str = 'spot') -> List[Dict[str, Any]]:
        """
        Calculate how much data to fetch for a given period
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            days: Number of days to fetch
            category: Product category
        
        Returns:
            Historical data for the specified period
        """
        # Calculate intervals per day
        intervals_per_day = {
            '1m': 1440,
            '3m': 480,
            '5m': 288,
            '15m': 96,
            '30m': 48,
            '1h': 24,
            '2h': 12,
            '4h': 6,
            '6h': 4,
            '12h': 2,
            '1d': 1
        }
        
        intervals_needed = intervals_per_day.get(interval, 24) * days
        
        # Bybit API limit is 1000 per request
        if intervals_needed <= 1000:
            # Single request
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            return self.get_historical_data(symbol, interval, start_time, end_time, 
                                          intervals_needed, category)
        else:
            # Multiple requests needed
            print(f"📊 Large dataset requested: {intervals_needed} intervals, fetching in batches...")
            all_data = []
            
            # Calculate number of batches
            batch_size = 1000
            num_batches = (intervals_needed + batch_size - 1) // batch_size
            
            end_time = datetime.now()
            
            for i in range(num_batches):
                batch_end = end_time - timedelta(days=days * i / num_batches)
                batch_start = end_time - timedelta(days=days * (i + 1) / num_batches)
                
                batch_data = self.get_historical_data(symbol, interval, batch_start, 
                                                    batch_end, batch_size, category)
                all_data.extend(batch_data)
                
                # Rate limiting
                time.sleep(0.1)
            
            # Sort by timestamp
            all_data.sort(key=lambda x: x['timestamp'])
            return all_data
    
    def to_dataframe(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert historical data to pandas DataFrame"""
        try:
            import pandas as pd
            df = pd.DataFrame(data)
            if not df.empty:
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('datetime', inplace=True)
            return df
        except ImportError:
            print("⚠️ pandas not available. Install with: pip install pandas")
            return None
    
    def get_available_symbols(self, category: str = 'spot') -> List[str]:
        """Get list of available trading symbols"""
        try:
            response = self.get_instruments_info(category=category)
            if response.get('retCode') == 0:
                instruments = response.get('result', {}).get('list', [])
                return [instrument['symbol'] for instrument in instruments]
            return []
        except Exception as e:
            print(f"❌ Error getting available symbols: {e}")
            return []

if __name__ == "__main__":
    # Example usage
    print("🔄 Testing Bybit Real Data Provider...")
    
    # Initialize provider
    provider = BybitRealDataProvider(testnet=False)
    
    # Test connection
    if provider.test_connection():
        print("✅ Connection successful!")
        
        # Get latest Bitcoin price
        btc_price = provider.get_latest_price('BTCUSDT')
        if btc_price:
            print(f"💰 BTC Price: ${btc_price:,.2f}")
        
        # Get historical data
        print("\n📊 Fetching historical data...")
        historical_data = provider.get_historical_data(
            symbol='BTCUSDT',
            interval='1h',
            limit=24  # Last 24 hours
        )
        
        if historical_data:
            print(f"✅ Retrieved {len(historical_data)} candles")
            print(f"📅 From: {historical_data[0]['datetime']}")
            print(f"📅 To: {historical_data[-1]['datetime']}")
            print(f"💹 Price range: ${historical_data[0]['open']:.2f} - ${historical_data[-1]['close']:.2f}")
        
    else:
        print("❌ Connection failed!")
