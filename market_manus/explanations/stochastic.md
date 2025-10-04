# 📈 Stochastic Oscillator

**Tipo:** Oscillator

## Descrição
Oscilador que compara preço atual com range recente

## Lógica da Estratégia

Mede posição do preço em relação ao range:
- %K cruza acima de %D em zona oversold → BUY
- %K cruza abaixo de %D em zona overbought → SELL
                

## Triggers de Sinal

- **BUY**: %K > %D e ambos < 20 (oversold)
- **SELL**: %K < %D e ambos > 80 (overbought)
- **Confidence**: Posição em relação aos thresholds

## Parâmetros

- **k_period**: 14 (período %K)
- **d_period**: 3 (suavização %D)
- **oversold**: 20
- **overbought**: 80

## Melhor Para
Scalping, reversões de curto prazo, timeframes baixos

## Evitar
Tendências fortes prolongadas

## Exemplo de Uso

### Cenário Bullish
Quando a estratégia gera sinal BUY, indica que as condições favoráveis para entrada long foram detectadas.

### Cenário Bearish
Quando a estratégia gera sinal SELL, indica que as condições favoráveis para entrada short foram detectadas.

---
*Documento gerado automaticamente pelo Market Manus Strategy Lab*
