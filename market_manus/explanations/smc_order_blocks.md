# 📦 SMC: Order Blocks

**Tipo:** Smart Money Concepts

## Descrição
Última vela de acumulação antes do rompimento

## Lógica da Estratégia

Identifica zonas onde instituições acumularam posições:
- Vela antes de BOS bullish = Bullish OB → suporte futuro
- Vela antes de BOS bearish = Bearish OB → resistência futura
                

## Triggers de Sinal

- **BUY**: Preço retorna para Bullish Order Block
- **SELL**: Preço retorna para Bearish Order Block
- **Confidence**: Força do BOS subsequente

## Parâmetros

- **min_range**: 0 (tamanho mínimo do bloco)

## Melhor Para
Re-entries em tendência, zonas de interesse institucional

## Evitar
Mercados sem estrutura clara

## Exemplo de Uso

### Cenário Bullish
Quando a estratégia gera sinal BUY, indica que as condições favoráveis para entrada long foram detectadas.

### Cenário Bearish
Quando a estratégia gera sinal SELL, indica que as condições favoráveis para entrada short foram detectadas.

---
*Documento gerado automaticamente pelo Market Manus Strategy Lab*
