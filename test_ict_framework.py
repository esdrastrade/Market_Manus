"""
Script de teste para ICT Framework v2.0
Valida a integração dos 4 pilares ICT
"""

import pandas as pd
import numpy as np
from datetime import datetime
from market_manus.strategies.smc import (
    detect_ict_signal,
    validate_ict_setup_components,
    ICTFramework
)

def create_sample_data(rows: int = 200) -> pd.DataFrame:
    """Cria dados de teste simulando price action realista"""
    np.random.seed(42)
    
    base_price = 50000.0
    prices = []
    
    for i in range(rows):
        volatility = 0.01
        change = np.random.randn() * volatility
        base_price *= (1 + change)
        prices.append(base_price)
    
    highs = [p * (1 + abs(np.random.randn() * 0.005)) for p in prices]
    lows = [p * (1 - abs(np.random.randn() * 0.005)) for p in prices]
    closes = prices
    opens = [p * (1 + np.random.randn() * 0.003) for p in prices]
    volumes = [1000000 + abs(np.random.randn() * 200000) for _ in range(rows)]
    
    df = pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    })
    
    df.index = pd.date_range(start='2024-01-01', periods=rows, freq='1h')
    
    return df

def test_ict_framework():
    """Testa ICT Framework completo"""
    print("=" * 60)
    print("TESTE ICT FRAMEWORK v2.0")
    print("=" * 60)
    
    df = create_sample_data(200)
    
    print(f"\n✅ Dados carregados: {len(df)} candles")
    print(f"   Período: {df.index[0]} → {df.index[-1]}")
    print(f"   Preço atual: ${df['close'].iloc[-1]:,.2f}")
    
    print("\n" + "-" * 60)
    print("1. VALIDAÇÃO DE COMPONENTES ICT")
    print("-" * 60)
    
    components = validate_ict_setup_components(df)
    
    for component, status in components.items():
        icon = "✓" if status else "✗"
        print(f"   {icon} {component}: {status}")
    
    print("\n" + "-" * 60)
    print("2. ANÁLISE ICT FRAMEWORK")
    print("-" * 60)
    
    framework = ICTFramework(min_rr=2.0, use_killzones=False)
    signal = framework.analyze(df, timestamp=datetime.now())
    
    print(f"\n📊 RESULTADO:")
    print(f"   Action: {signal.action}")
    print(f"   Confidence: {signal.confidence:.2%}")
    print(f"   Tags: {', '.join(signal.tags)}")
    
    print(f"\n📝 RAZÕES:")
    for reason in signal.reasons:
        print(f"   • {reason}")
    
    if signal.meta:
        print(f"\n🔍 METADATA:")
        for key, value in signal.meta.items():
            if key in ['entry', 'stop_loss', 'target', 'risk_reward']:
                if isinstance(value, float):
                    print(f"   • {key}: ${value:,.2f}" if 'entry' in key or 'stop' in key or 'target' in key else f"   • {key}: {value:.2f}")
    
    print("\n" + "-" * 60)
    print("3. RELATÓRIO DE ANÁLISE")
    print("-" * 60)
    
    report = framework.get_analysis_report()
    
    print(f"\n📈 Market Structure:")
    print(f"   Trend: {report['market_structure']['trend']}")
    print(f"   Last BOS: {'SIM' if report['market_structure']['last_bos'] else 'NÃO'}")
    print(f"   Last CHoCH: {'SIM' if report['market_structure']['last_choch'] else 'NÃO'}")
    print(f"   Fresh OBs: {len(report['market_structure']['fresh_obs'])}")
    
    print(f"\n⚙️ Framework:")
    print(f"   Version: {report['framework_version']}")
    print(f"   Min R:R: {report['min_risk_reward']}")
    
    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO COM SUCESSO! ✅")
    print("=" * 60)

if __name__ == "__main__":
    test_ict_framework()
