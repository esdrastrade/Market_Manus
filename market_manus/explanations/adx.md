# 🎯 ADX (Average Directional Index)

**Tipo:** Trend Strength

## Descrição
Mede força da tendência independente de direção

## Lógica da Estratégia

Determina se vale a pena seguir a tendência:
- ADX > 25 + DI+ > DI- → BUY (tendência bullish forte)
- ADX > 25 + DI- > DI+ → SELL (tendência bearish forte)
- ADX < 25 → Sem tendência clara
                

## Triggers de Sinal

- **BUY**: ADX > 25 e +DI cruza acima de -DI
- **SELL**: ADX > 25 e -DI cruza acima de +DI
- **Confidence**: Valor do ADX (quanto maior, mais forte)

## Parâmetros

- **period**: 14 (cálculo de ADX)
- **adx_threshold**: 25 (mínimo para tendência forte)

## Melhor Para
Confirmar tendências, evitar false breakouts

## Evitar
Mercados laterais (ADX baixo)

## Exemplo de Uso

### Cenário Bullish
Quando a estratégia gera sinal BUY, indica que as condições favoráveis para entrada long foram detectadas.

### Cenário Bearish
Quando a estratégia gera sinal SELL, indica que as condições favoráveis para entrada short foram detectadas.

---
*Documento gerado automaticamente pelo Market Manus Strategy Lab*
