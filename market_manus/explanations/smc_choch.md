# 🔄 SMC: Change of Character

**Tipo:** Smart Money Concepts

## Descrição
Reversão quando sequência de topos/fundos muda

## Lógica da Estratégia

Detecta mudança de estrutura de mercado:
- Uptrend: Low rompe low anterior → CHoCH → SELL
- Downtrend: High rompe high anterior → CHoCH → BUY
                

## Triggers de Sinal

- **BUY**: Em downtrend, high rompe high anterior (reversão)
- **SELL**: Em uptrend, low rompe low anterior (reversão)
- **Confidence**: Força da quebra estrutural

## Parâmetros


## Melhor Para
Identificar reversões early, tops/bottoms de tendência

## Evitar
Mercados laterais com muitos whipsaws

## Exemplo de Uso

### Cenário Bullish
Quando a estratégia gera sinal BUY, indica que as condições favoráveis para entrada long foram detectadas.

### Cenário Bearish
Quando a estratégia gera sinal SELL, indica que as condições favoráveis para entrada short foram detectadas.

---
*Documento gerado automaticamente pelo Market Manus Strategy Lab*
