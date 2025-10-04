# 📊 RSI Mean Reversion

**Tipo:** Oscillator

## Descrição
Estratégia de reversão à média baseada no RSI (Relative Strength Index)

## Lógica da Estratégia

Identifica momentos de sobrecompra e sobrevenda através do RSI:
- RSI < 30: Mercado sobrevendido → sinal BUY (reversão esperada para cima)
- RSI > 70: Mercado sobrecomprado → sinal SELL (reversão esperada para baixo)
- RSI entre 30-70: Neutro → HOLD
                

## Triggers de Sinal

- **BUY**: RSI cai abaixo de 30 (sobrevenda)
- **SELL**: RSI sobe acima de 70 (sobrecompra)
- **Confidence**: Quanto mais distante do threshold, maior a confiança

## Parâmetros

- **rsi_period**: 14 candles (período de cálculo do RSI)
- **oversold**: 30 (nível de sobrevenda)
- **overbought**: 70 (nível de sobrecompra)

## Melhor Para
Mercados laterais, ativos com alta volatilidade, timeframes curtos (1m-15m)

## Evitar
Tendências fortes (breakouts), baixa liquidez

## Exemplo de Uso

### Cenário Bullish
Quando a estratégia gera sinal BUY, indica que as condições favoráveis para entrada long foram detectadas.

### Cenário Bearish
Quando a estratégia gera sinal SELL, indica que as condições favoráveis para entrada short foram detectadas.

---
*Documento gerado automaticamente pelo Market Manus Strategy Lab*
