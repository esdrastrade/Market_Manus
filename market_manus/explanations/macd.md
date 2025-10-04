# 📊 MACD

**Tipo:** Momentum

## Descrição
Moving Average Convergence Divergence - identificador de momentum e reversões

## Lógica da Estratégia

Compara EMAs e sinaliza mudanças de momentum:
- MACD cruza acima da linha de sinal → BUY (momentum bullish)
- MACD cruza abaixo da linha de sinal → SELL (momentum bearish)
- Histograma positivo/negativo confirma direção
                

## Triggers de Sinal

- **BUY**: MACD line cruza acima da Signal line
- **SELL**: MACD line cruza abaixo da Signal line
- **Confidence**: Magnitude do histograma

## Parâmetros

- **fast_period**: 12 (EMA rápida)
- **slow_period**: 26 (EMA lenta)
- **signal_period**: 9 (linha de sinal)

## Melhor Para
Identificar reversões, confirmar tendências, timeframes médios

## Evitar
Choppy markets (oscilações rápidas)

## Exemplo de Uso

### Cenário Bullish
Quando a estratégia gera sinal BUY, indica que as condições favoráveis para entrada long foram detectadas.

### Cenário Bearish
Quando a estratégia gera sinal SELL, indica que as condições favoráveis para entrada short foram detectadas.

---
*Documento gerado automaticamente pelo Market Manus Strategy Lab*
