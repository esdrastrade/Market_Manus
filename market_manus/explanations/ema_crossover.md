# 📈 EMA Crossover

**Tipo:** Trend Following

## Descrição
Cruzamento de médias móveis exponenciais para identificar tendências

## Lógica da Estratégia

Utiliza duas EMAs (rápida e lenta) para detectar mudanças de tendência:
- EMA rápida cruza acima da EMA lenta → sinal BUY (início de tendência de alta)
- EMA rápida cruza abaixo da EMA lenta → sinal SELL (início de tendência de baixa)
                

## Triggers de Sinal

- **BUY**: EMA12 cruza acima de EMA26 (Golden Cross)
- **SELL**: EMA12 cruza abaixo de EMA26 (Death Cross)
- **Confidence**: Baseada na distância entre as EMAs

## Parâmetros

- **fast_ema**: 12 períodos (EMA rápida)
- **slow_ema**: 26 períodos (EMA lenta)

## Melhor Para
Tendências claras, timeframes médios (15m-1h), alta liquidez

## Evitar
Mercados laterais (gera muitos falsos sinais)

## Exemplo de Uso

### Cenário Bullish
Quando a estratégia gera sinal BUY, indica que as condições favoráveis para entrada long foram detectadas.

### Cenário Bearish
Quando a estratégia gera sinal SELL, indica que as condições favoráveis para entrada short foram detectadas.

---
*Documento gerado automaticamente pelo Market Manus Strategy Lab*
