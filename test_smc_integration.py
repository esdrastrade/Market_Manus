"""
Test SMC strategies with real Binance data
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from market_manus.data_providers.binance_data_provider import BinanceDataProvider
from market_manus.strategies.smc.patterns import (
    detect_bos,
    detect_choch,
    detect_order_blocks,
    detect_fvg,
    detect_liquidity_sweep
)

def test_smc_strategies():
    """Test all 5 SMC strategies with real data"""
    
    # Initialize data provider
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ API keys not found")
        return
    
    provider = BinanceDataProvider(api_key=api_key, api_secret=api_secret, testnet=False)
    
    # Fetch real data
    print("📊 Fetching real market data from Binance...")
    data = provider.get_kline(category="spot", symbol="BTCUSDT", interval="60", limit=100)
    
    if data is None or len(data) == 0:
        print("❌ Failed to fetch data")
        return
    
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    print(f"✅ Loaded {len(df)} candles from Binance")
    print(f"📅 Period: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
    
    # Test each SMC strategy
    strategies = {
        "BOS (Break of Structure)": detect_bos,
        "CHoCH (Change of Character)": detect_choch,
        "Order Blocks": detect_order_blocks,
        "FVG (Fair Value Gap)": detect_fvg,
        "Liquidity Sweep": detect_liquidity_sweep
    }
    
    print("\n" + "=" * 80)
    print("🧪 TESTING SMC STRATEGIES")
    print("=" * 80)
    
    for name, strategy_func in strategies.items():
        print(f"\n🔍 Testing: {name}")
        try:
            signal = strategy_func(df)
            print(f"   Action: {signal.action}")
            print(f"   Confidence: {signal.confidence:.2f}")
            print(f"   Reasons: {', '.join(signal.reasons)}")
            print(f"   Tags: {', '.join(signal.tags)}")
            if signal.meta:
                print(f"   Meta: {signal.meta}")
            print("   ✅ PASSED")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
    
    print("\n" + "=" * 80)
    print("✅ SMC INTEGRATION TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_smc_strategies()
