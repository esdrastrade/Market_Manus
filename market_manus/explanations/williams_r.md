# 📉 Williams %R

**Tipo:** Oscillator

## Descrição
Oscilador de momentum medindo distância do preço em relação ao high/low

## Lógica da Estratégia

Identifica condições extremas de mercado:
- %R < -80: Oversold → BUY esperado
- %R > -20: Overbought → SELL esperado
                

## Triggers de Sinal

- **BUY**: %R cruza acima de -80 (saindo de oversold)
- **SELL**: %R cruza abaixo de -20 (saindo de overbought)
- **Confidence**: Velocidade da mudança

## Parâmetros

- **period**: 14 (lookback)
- **oversold**: -80
- **overbought**: -20

## Melhor Para
Identificar reversões, complementar outras estratégias

## Evitar
Usar isoladamente em tendências

## Exemplo de Uso

### Cenário Bullish
Quando a estratégia gera sinal BUY, indica que as condições favoráveis para entrada long foram detectadas.

### Cenário Bearish
Quando a estratégia gera sinal SELL, indica que as condições favoráveis para entrada short foram detectadas.

---
*Documento gerado automaticamente pelo Market Manus Strategy Lab*
