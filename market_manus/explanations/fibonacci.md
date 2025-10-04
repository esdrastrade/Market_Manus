# 🔢 Fibonacci Retracement

**Tipo:** Support/Resistance

## Descrição
Níveis de retração de Fibonacci para identificar suportes/resistências

## Lógica da Estratégia

Calcula níveis de Fibonacci no swing mais recente:
- Preço toca 0.618 ou 0.786 e reverte → BUY (em downtrend)
- Preço toca 0.382 ou 0.236 e reverte → SELL (em uptrend)
                

## Triggers de Sinal

- **BUY**: Preço próximo de nível Fib (0.618/0.786) em pullback
- **SELL**: Preço próximo de nível Fib (0.382/0.236) em rally
- **Confidence**: Proximidade exata do nível

## Parâmetros

- **lookback_period**: 50 (para detectar swing)
- **tolerance_pct**: 0.5% (margem de erro)

## Melhor Para
Tendências com pullbacks, níveis de entrada precisos

## Evitar
Mercados sem tendência definida

## Exemplo de Uso

### Cenário Bullish
Quando a estratégia gera sinal BUY, indica que as condições favoráveis para entrada long foram detectadas.

### Cenário Bearish
Quando a estratégia gera sinal SELL, indica que as condições favoráveis para entrada short foram detectadas.

---
*Documento gerado automaticamente pelo Market Manus Strategy Lab*
