# ⚡ SMC: Fair Value Gap

**Tipo:** Smart Money Concepts

## Descrição
Gap entre corpos/sombras indicando imbalance

## Lógica da Estratégia

Detecta desequilíbrio de oferta/demanda (gaps):
- Gap bullish (low[1] > high[-1]) → preço deve preencher → BUY
- Gap bearish (high[1] < low[-1]) → preço deve preencher → SELL
                

## Triggers de Sinal

- **BUY**: FVG bullish detectado (gap para cima)
- **SELL**: FVG bearish detectado (gap para baixo)
- **Confidence**: Tamanho do gap

## Parâmetros


## Melhor Para
Movimentos rápidos, imbalances institucionais

## Evitar
Mercados de baixa volatilidade

## Exemplo de Uso

### Cenário Bullish
Quando a estratégia gera sinal BUY, indica que as condições favoráveis para entrada long foram detectadas.

### Cenário Bearish
Quando a estratégia gera sinal SELL, indica que as condições favoráveis para entrada short foram detectadas.

---
*Documento gerado automaticamente pelo Market Manus Strategy Lab*
