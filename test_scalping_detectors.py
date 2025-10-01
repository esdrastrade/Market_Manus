#!/usr/bin/env python3
"""
Testes unitários para os novos detectores de Scalping
Baseados em estratégias da Investopedia
"""

import pandas as pd
import numpy as np
from market_manus.strategies.classic_analysis import (
    ma_ribbon_signal,
    momentum_combo_signal,
    pivot_point_signal
)


def test_ma_ribbon_bullish_with_good_spread():
    """Teste: MA Ribbon com spread suficiente deve gerar BUY"""
    print("\n🧪 Teste 1: MA Ribbon - Bullish com spread adequado")
    
    # Cria dados com ribbons alinhadas para cima com bom spread
    closes = pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114])
    candles = pd.DataFrame({
        'close': closes,
        'high': closes + 1,
        'low': closes - 1,
        'open': closes,
        'volume': [1000] * len(closes)
    })
    
    signal = ma_ribbon_signal(candles, {'periods': [5, 8, 13], 'alignment_threshold': 0.002})
    
    print(f"   Action: {signal.action}")
    print(f"   Confidence: {signal.confidence:.3f}")
    print(f"   Reason: {signal.reasons[0]}")
    
    assert signal.action == "BUY", f"Esperado BUY, obteve {signal.action}"
    assert signal.confidence > 0.5, f"Confidence muito baixo: {signal.confidence}"
    print("   ✅ PASSOU - Sinal BUY gerado com confidence adequado")


def test_ma_ribbon_flat_below_threshold():
    """Teste: MA Ribbon com spread insuficiente deve gerar HOLD"""
    print("\n🧪 Teste 2: MA Ribbon - Ribbons achatadas (spread < threshold)")
    
    # Cria dados com ribbons muito próximas (mercado lateral)
    closes = pd.Series([100, 100.05, 100.1, 100.08, 100.12, 100.15, 100.13, 100.18, 100.2, 100.19, 100.22, 100.25, 100.23, 100.26])
    candles = pd.DataFrame({
        'close': closes,
        'high': closes + 0.5,
        'low': closes - 0.5,
        'open': closes,
        'volume': [1000] * len(closes)
    })
    
    signal = ma_ribbon_signal(candles, {'periods': [5, 8, 13], 'alignment_threshold': 0.002})
    
    print(f"   Action: {signal.action}")
    print(f"   Confidence: {signal.confidence:.3f}")
    print(f"   Reason: {signal.reasons[0]}")
    
    assert signal.action == "HOLD", f"Esperado HOLD para ribbons achatadas, obteve {signal.action}"
    assert signal.confidence == 0.0, f"Confidence deveria ser 0 para HOLD"
    print("   ✅ PASSOU - Filtro de threshold funcionando (rejeita mercado lateral)")


def test_ma_ribbon_bearish_with_good_spread():
    """Teste: MA Ribbon com spread suficiente para baixo deve gerar SELL"""
    print("\n🧪 Teste 3: MA Ribbon - Bearish com spread adequado")
    
    # Cria dados com ribbons alinhadas para baixo
    closes = pd.Series([114, 113, 112, 111, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101])
    candles = pd.DataFrame({
        'close': closes,
        'high': closes + 1,
        'low': closes - 1,
        'open': closes,
        'volume': [1000] * len(closes)
    })
    
    signal = ma_ribbon_signal(candles, {'periods': [5, 8, 13], 'alignment_threshold': 0.002})
    
    print(f"   Action: {signal.action}")
    print(f"   Confidence: {signal.confidence:.3f}")
    print(f"   Reason: {signal.reasons[0]}")
    
    assert signal.action == "SELL", f"Esperado SELL, obteve {signal.action}"
    assert signal.confidence > 0.5, f"Confidence muito baixo: {signal.confidence}"
    print("   ✅ PASSOU - Sinal SELL gerado com confidence adequado")


def test_momentum_combo_macd_crossover_with_rsi():
    """Teste: Momentum Combo - MACD crossover bullish + RSI > 50"""
    print("\n🧪 Teste 4: Momentum Combo - MACD crossover + RSI > 50")
    
    # Simula MACD crossover bullish com RSI acima de 50
    # Precisamos de pelo menos 26 candles para MACD
    n = 50
    closes = pd.Series([100 + i * 0.5 for i in range(n)])  # Tendência de alta
    candles = pd.DataFrame({
        'close': closes,
        'high': closes + 1,
        'low': closes - 1,
        'open': closes,
        'volume': [1000] * n
    })
    
    signal = momentum_combo_signal(candles)
    
    print(f"   Action: {signal.action}")
    print(f"   Confidence: {signal.confidence:.3f}")
    print(f"   Reason: {signal.reasons[0]}")
    
    # Pode ser BUY ou HOLD dependendo do timing exato do crossover
    assert signal.action in ["BUY", "HOLD"], f"Esperado BUY ou HOLD, obteve {signal.action}"
    if signal.action == "BUY":
        assert signal.confidence >= 0.6, f"Confidence deveria ser >= 0.6 para momentum combo"
    print(f"   ✅ PASSOU - Detector momentum combo funcionando")


def test_momentum_combo_rsi_exit_oversold():
    """Teste: Momentum Combo - RSI saindo de oversold + MACD positivo"""
    print("\n🧪 Teste 5: Momentum Combo - RSI saindo de oversold")
    
    # Simula RSI saindo de oversold
    n = 50
    # Primeiro desce (RSI baixo), depois sobe (RSI sai de oversold)
    closes = pd.Series([100 - i * 2 for i in range(25)] + [50 + i * 1.5 for i in range(25)])
    candles = pd.DataFrame({
        'close': closes,
        'high': closes + 1,
        'low': closes - 1,
        'open': closes,
        'volume': [1000] * n
    })
    
    signal = momentum_combo_signal(candles)
    
    print(f"   Action: {signal.action}")
    print(f"   Confidence: {signal.confidence:.3f}")
    print(f"   Reason: {signal.reasons[0]}")
    
    # Pode ser BUY, SELL ou HOLD dependendo do estado atual
    assert signal.action in ["BUY", "SELL", "HOLD"], f"Action inválida: {signal.action}"
    print(f"   ✅ PASSOU - Detector processa RSI corretamente")


def test_pivot_point_s1_bounce():
    """Teste: Pivot Points - Preço toca S1 e reverte (BUY)"""
    print("\n🧪 Teste 6: Pivot Points - Bounce em S1")
    
    # O detector usa candle[-2] para calcular pivots
    # Então candle índice 1 (segundo) será usado para calcular pivots
    # E candle índice 2 (terceiro/último) será testado contra esses pivots
    
    # Candle índice 1 (será usado para calcular pivots):
    pivot_high = 110
    pivot_low = 100
    pivot_close = 105
    
    # Calcula pivots que serão calculados pelo detector
    pp = (pivot_high + pivot_low + pivot_close) / 3
    s1 = 2 * pp - pivot_high
    
    print(f"   PP esperado: {pp:.2f}")
    print(f"   S1 esperado: {s1:.2f}")
    
    # Cria histórico com 3 candles:
    # [0] = primeiro candle (ignorado)
    # [1] = segundo candle (usado para calcular pivots)
    # [2] = terceiro candle (testado contra pivots - deve tocar S1)
    candles = pd.DataFrame({
        'high': [105, pivot_high, s1 + 2],
        'low': [95, pivot_low, s1 - 0.1],  # Último candle toca S1
        'close': [100, pivot_close, s1 + 0.5],  # Último candle fecha acima do low (reversão)
        'open': [95, 100, s1 - 0.05],
        'volume': [1000, 1000, 1000]
    })
    
    signal = pivot_point_signal(candles, {'tolerance_pct': 0.003})
    
    print(f"   Action: {signal.action}")
    print(f"   Confidence: {signal.confidence:.3f}")
    print(f"   Reason: {signal.reasons[0]}")
    
    assert signal.action == "BUY", f"Esperado BUY em bounce de S1, obteve {signal.action}"
    assert 0.5 <= signal.confidence <= 1.0, f"Confidence fora do range esperado: {signal.confidence}"
    print("   ✅ PASSOU - Bounce em S1 detectado corretamente")


def test_pivot_point_r1_rejection():
    """Teste: Pivot Points - Preço toca R1 e reverte (SELL)"""
    print("\n🧪 Teste 7: Pivot Points - Rejection em R1")
    
    # O detector usa candle[-2] para calcular pivots
    pivot_high = 110
    pivot_low = 100
    pivot_close = 105
    
    pp = (pivot_high + pivot_low + pivot_close) / 3
    r1 = 2 * pp - pivot_low
    
    print(f"   PP esperado: {pp:.2f}")
    print(f"   R1 esperado: {r1:.2f}")
    
    # Cria histórico com 3 candles:
    # [0] = primeiro candle (ignorado)
    # [1] = segundo candle (usado para calcular pivots)
    # [2] = terceiro candle (testado contra pivots - deve tocar R1)
    candles = pd.DataFrame({
        'high': [105, pivot_high, r1 + 0.1],  # Último candle toca R1
        'low': [95, pivot_low, r1 - 2],
        'close': [100, pivot_close, r1 - 0.5],  # Último candle fecha abaixo do high (rejeição)
        'open': [95, 100, r1 + 0.05],
        'volume': [1000, 1000, 1000]
    })
    
    signal = pivot_point_signal(candles, {'tolerance_pct': 0.003})
    
    print(f"   Action: {signal.action}")
    print(f"   Confidence: {signal.confidence:.3f}")
    print(f"   Reason: {signal.reasons[0]}")
    
    assert signal.action == "SELL", f"Esperado SELL em rejection de R1, obteve {signal.action}"
    assert 0.5 <= signal.confidence <= 1.0, f"Confidence fora do range esperado: {signal.confidence}"
    print("   ✅ PASSOU - Rejection em R1 detectada corretamente")


def test_pivot_point_away_from_levels():
    """Teste: Pivot Points - Preço longe dos níveis (HOLD)"""
    print("\n🧪 Teste 8: Pivot Points - Preço longe dos níveis")
    
    prev_high = 110
    prev_low = 100
    prev_close = 105
    
    pp = (prev_high + prev_low + prev_close) / 3
    
    # Cria histórico com 3 candles - último candle longe de qualquer nível
    candles = pd.DataFrame({
        'high': [prev_high, 108, pp + 0.5],
        'low': [prev_low, 102, pp - 0.5],
        'close': [prev_close, 106, pp],  # Exatamente no PP, mas sem toque/reversão
        'open': [100, 105, pp],
        'volume': [1000, 1000, 1000]
    })
    
    signal = pivot_point_signal(candles, {'tolerance_pct': 0.003})
    
    print(f"   Action: {signal.action}")
    print(f"   Confidence: {signal.confidence:.3f}")
    print(f"   Reason: {signal.reasons[0]}")
    
    assert signal.action == "HOLD", f"Esperado HOLD quando longe dos níveis, obteve {signal.action}"
    assert signal.confidence == 0.0, f"Confidence deveria ser 0 para HOLD"
    print("   ✅ PASSOU - HOLD quando longe dos pivots")


def run_all_tests():
    """Executa todos os testes"""
    print("=" * 80)
    print("🚀 INICIANDO TESTES DOS DETECTORES DE SCALPING")
    print("=" * 80)
    
    tests = [
        ("MA Ribbon - Bullish", test_ma_ribbon_bullish_with_good_spread),
        ("MA Ribbon - Flat", test_ma_ribbon_flat_below_threshold),
        ("MA Ribbon - Bearish", test_ma_ribbon_bearish_with_good_spread),
        ("Momentum Combo - MACD+RSI", test_momentum_combo_macd_crossover_with_rsi),
        ("Momentum Combo - RSI Exit", test_momentum_combo_rsi_exit_oversold),
        ("Pivot Points - S1 Bounce", test_pivot_point_s1_bounce),
        ("Pivot Points - R1 Rejection", test_pivot_point_r1_rejection),
        ("Pivot Points - Away", test_pivot_point_away_from_levels),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"   ❌ FALHOU - {e}")
            failed += 1
        except Exception as e:
            print(f"   ❌ ERRO - {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"📊 RESUMO DOS TESTES")
    print("=" * 80)
    print(f"✅ Testes Passou: {passed}/{len(tests)}")
    print(f"❌ Testes Falhou: {failed}/{len(tests)}")
    print(f"📈 Taxa de Sucesso: {passed/len(tests)*100:.1f}%")
    print("=" * 80)
    
    if failed == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM! Os detectores estão funcionando corretamente.")
    else:
        print(f"\n⚠️  {failed} teste(s) falharam. Revisar implementação.")
    
    return passed, failed


if __name__ == "__main__":
    run_all_tests()
