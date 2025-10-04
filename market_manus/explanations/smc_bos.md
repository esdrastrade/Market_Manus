# 🔥 SMC: Break of Structure

**Tipo:** Smart Money Concepts

## Descrição
Continuação de tendência após rompimento de swing high/low

## Lógica da Estratégia

Identifica quando 'smart money' está empurrando o mercado:
- Preço rompe swing high anterior → BOS bullish → BUY
- Preço rompe swing low anterior → BOS bearish → SELL
                

## Triggers de Sinal

- **BUY**: High atual > último swing high significativo
- **SELL**: Low atual < último swing low significativo
- **Confidence**: Magnitude do displacement

## Parâmetros

- **min_displacement**: 0.1% (movimento mínimo para validar)

## Melhor Para
Tendências fortes, continuação de momentum, timeframes altos

## Evitar
Consolidações, baixa liquidez

## Exemplo de Uso

### Cenário Bullish
Quando a estratégia gera sinal BUY, indica que as condições favoráveis para entrada long foram detectadas.

### Cenário Bearish
Quando a estratégia gera sinal SELL, indica que as condições favoráveis para entrada short foram detectadas.

---
*Documento gerado automaticamente pelo Market Manus Strategy Lab*
