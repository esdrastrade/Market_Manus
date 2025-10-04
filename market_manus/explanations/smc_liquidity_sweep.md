# 🎣 SMC: Liquidity Sweep

**Tipo:** Smart Money Concepts

## Descrição
Rompimento falso para capturar liquidez (stop hunt)

## Lógica da Estratégia

Identifica quando smart money caça stops:
- Spike acima de high anterior + reversão rápida → Liquidity Grab → SELL
- Spike abaixo de low anterior + reversão rápida → Liquidity Grab → BUY
                

## Triggers de Sinal

- **BUY**: Wick longo abaixo + reversão (sweep de lows)
- **SELL**: Wick longo acima + reversão (sweep de highs)
- **Confidence**: Tamanho do wick vs corpo

## Parâmetros


## Melhor Para
Identificar armadilhas, reversões após stop hunt

## Evitar
Sem confirmação de reversão

## Exemplo de Uso

### Cenário Bullish
Quando a estratégia gera sinal BUY, indica que as condições favoráveis para entrada long foram detectadas.

### Cenário Bearish
Quando a estratégia gera sinal SELL, indica que as condições favoráveis para entrada short foram detectadas.

---
*Documento gerado automaticamente pelo Market Manus Strategy Lab*
