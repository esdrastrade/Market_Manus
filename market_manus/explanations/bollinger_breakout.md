# 🎯 Bollinger Bands Breakout

**Tipo:** Volatility

## Descrição
Rompimento das Bandas de Bollinger para capturar expansões de volatilidade

## Lógica da Estratégia

Detecta breakouts quando preço rompe as bandas:
- Preço fecha ACIMA da banda superior → sinal BUY (momentum forte)
- Preço fecha ABAIXO da banda inferior → sinal SELL (pressão vendedora)
                

## Triggers de Sinal

- **BUY**: Close > Banda Superior (breakout bullish)
- **SELL**: Close < Banda Inferior (breakout bearish)
- **Confidence**: Distância do preço em relação à banda

## Parâmetros

- **period**: 20 candles (período da MA central)
- **std_dev**: 2.0 (desvios padrão das bandas)

## Melhor Para
Breakouts de consolidação, alta volatilidade, notícias importantes

## Evitar
Mercados de range estreito, baixa volatilidade

## Exemplo de Uso

### Cenário Bullish
Quando a estratégia gera sinal BUY, indica que as condições favoráveis para entrada long foram detectadas.

### Cenário Bearish
Quando a estratégia gera sinal SELL, indica que as condições favoráveis para entrada short foram detectadas.

---
*Documento gerado automaticamente pelo Market Manus Strategy Lab*
