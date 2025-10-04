"""
Strategy Explanations System
Gera e exibe documentação para todas as 13 estratégias
"""

import os
from pathlib import Path
from typing import Dict


class StrategyExplanations:
    """Gerencia explicações de estratégias"""
    
    def __init__(self):
        self.explanations_dir = Path(__file__).parent
        self.strategies = self._define_strategies()
    
    def _define_strategies(self) -> Dict[str, Dict]:
        """Define metadados e explicações das 13 estratégias"""
        return {
            "rsi_mean_reversion": {
                "name": "RSI Mean Reversion",
                "emoji": "📊",
                "type": "Oscillator",
                "description": "Estratégia de reversão à média baseada no RSI (Relative Strength Index)",
                "logic": """
Identifica momentos de sobrecompra e sobrevenda através do RSI:
- RSI < 30: Mercado sobrevendido → sinal BUY (reversão esperada para cima)
- RSI > 70: Mercado sobrecomprado → sinal SELL (reversão esperada para baixo)
- RSI entre 30-70: Neutro → HOLD
                """,
                "triggers": {
                    "BUY": "RSI cai abaixo de 30 (sobrevenda)",
                    "SELL": "RSI sobe acima de 70 (sobrecompra)",
                    "Confidence": "Quanto mais distante do threshold, maior a confiança"
                },
                "parameters": {
                    "rsi_period": "14 candles (período de cálculo do RSI)",
                    "oversold": "30 (nível de sobrevenda)",
                    "overbought": "70 (nível de sobrecompra)"
                },
                "best_for": "Mercados laterais, ativos com alta volatilidade, timeframes curtos (1m-15m)",
                "avoid": "Tendências fortes (breakouts), baixa liquidez"
            },
            
            "ema_crossover": {
                "name": "EMA Crossover",
                "emoji": "📈",
                "type": "Trend Following",
                "description": "Cruzamento de médias móveis exponenciais para identificar tendências",
                "logic": """
Utiliza duas EMAs (rápida e lenta) para detectar mudanças de tendência:
- EMA rápida cruza acima da EMA lenta → sinal BUY (início de tendência de alta)
- EMA rápida cruza abaixo da EMA lenta → sinal SELL (início de tendência de baixa)
                """,
                "triggers": {
                    "BUY": "EMA12 cruza acima de EMA26 (Golden Cross)",
                    "SELL": "EMA12 cruza abaixo de EMA26 (Death Cross)",
                    "Confidence": "Baseada na distância entre as EMAs"
                },
                "parameters": {
                    "fast_ema": "12 períodos (EMA rápida)",
                    "slow_ema": "26 períodos (EMA lenta)"
                },
                "best_for": "Tendências claras, timeframes médios (15m-1h), alta liquidez",
                "avoid": "Mercados laterais (gera muitos falsos sinais)"
            },
            
            "bollinger_breakout": {
                "name": "Bollinger Bands Breakout",
                "emoji": "🎯",
                "type": "Volatility",
                "description": "Rompimento das Bandas de Bollinger para capturar expansões de volatilidade",
                "logic": """
Detecta breakouts quando preço rompe as bandas:
- Preço fecha ACIMA da banda superior → sinal BUY (momentum forte)
- Preço fecha ABAIXO da banda inferior → sinal SELL (pressão vendedora)
                """,
                "triggers": {
                    "BUY": "Close > Banda Superior (breakout bullish)",
                    "SELL": "Close < Banda Inferior (breakout bearish)",
                    "Confidence": "Distância do preço em relação à banda"
                },
                "parameters": {
                    "period": "20 candles (período da MA central)",
                    "std_dev": "2.0 (desvios padrão das bandas)"
                },
                "best_for": "Breakouts de consolidação, alta volatilidade, notícias importantes",
                "avoid": "Mercados de range estreito, baixa volatilidade"
            },
            
            "macd": {
                "name": "MACD",
                "emoji": "📊",
                "type": "Momentum",
                "description": "Moving Average Convergence Divergence - identificador de momentum e reversões",
                "logic": """
Compara EMAs e sinaliza mudanças de momentum:
- MACD cruza acima da linha de sinal → BUY (momentum bullish)
- MACD cruza abaixo da linha de sinal → SELL (momentum bearish)
- Histograma positivo/negativo confirma direção
                """,
                "triggers": {
                    "BUY": "MACD line cruza acima da Signal line",
                    "SELL": "MACD line cruza abaixo da Signal line",
                    "Confidence": "Magnitude do histograma"
                },
                "parameters": {
                    "fast_period": "12 (EMA rápida)",
                    "slow_period": "26 (EMA lenta)",
                    "signal_period": "9 (linha de sinal)"
                },
                "best_for": "Identificar reversões, confirmar tendências, timeframes médios",
                "avoid": "Choppy markets (oscilações rápidas)"
            },
            
            "stochastic": {
                "name": "Stochastic Oscillator",
                "emoji": "📈",
                "type": "Oscillator",
                "description": "Oscilador que compara preço atual com range recente",
                "logic": """
Mede posição do preço em relação ao range:
- %K cruza acima de %D em zona oversold → BUY
- %K cruza abaixo de %D em zona overbought → SELL
                """,
                "triggers": {
                    "BUY": "%K > %D e ambos < 20 (oversold)",
                    "SELL": "%K < %D e ambos > 80 (overbought)",
                    "Confidence": "Posição em relação aos thresholds"
                },
                "parameters": {
                    "k_period": "14 (período %K)",
                    "d_period": "3 (suavização %D)",
                    "oversold": "20",
                    "overbought": "80"
                },
                "best_for": "Scalping, reversões de curto prazo, timeframes baixos",
                "avoid": "Tendências fortes prolongadas"
            },
            
            "williams_r": {
                "name": "Williams %R",
                "emoji": "📉",
                "type": "Oscillator",
                "description": "Oscilador de momentum medindo distância do preço em relação ao high/low",
                "logic": """
Identifica condições extremas de mercado:
- %R < -80: Oversold → BUY esperado
- %R > -20: Overbought → SELL esperado
                """,
                "triggers": {
                    "BUY": "%R cruza acima de -80 (saindo de oversold)",
                    "SELL": "%R cruza abaixo de -20 (saindo de overbought)",
                    "Confidence": "Velocidade da mudança"
                },
                "parameters": {
                    "period": "14 (lookback)",
                    "oversold": "-80",
                    "overbought": "-20"
                },
                "best_for": "Identificar reversões, complementar outras estratégias",
                "avoid": "Usar isoladamente em tendências"
            },
            
            "adx": {
                "name": "ADX (Average Directional Index)",
                "emoji": "🎯",
                "type": "Trend Strength",
                "description": "Mede força da tendência independente de direção",
                "logic": """
Determina se vale a pena seguir a tendência:
- ADX > 25 + DI+ > DI- → BUY (tendência bullish forte)
- ADX > 25 + DI- > DI+ → SELL (tendência bearish forte)
- ADX < 25 → Sem tendência clara
                """,
                "triggers": {
                    "BUY": "ADX > 25 e +DI cruza acima de -DI",
                    "SELL": "ADX > 25 e -DI cruza acima de +DI",
                    "Confidence": "Valor do ADX (quanto maior, mais forte)"
                },
                "parameters": {
                    "period": "14 (cálculo de ADX)",
                    "adx_threshold": "25 (mínimo para tendência forte)"
                },
                "best_for": "Confirmar tendências, evitar false breakouts",
                "avoid": "Mercados laterais (ADX baixo)"
            },
            
            "fibonacci": {
                "name": "Fibonacci Retracement",
                "emoji": "🔢",
                "type": "Support/Resistance",
                "description": "Níveis de retração de Fibonacci para identificar suportes/resistências",
                "logic": """
Calcula níveis de Fibonacci no swing mais recente:
- Preço toca 0.618 ou 0.786 e reverte → BUY (em downtrend)
- Preço toca 0.382 ou 0.236 e reverte → SELL (em uptrend)
                """,
                "triggers": {
                    "BUY": "Preço próximo de nível Fib (0.618/0.786) em pullback",
                    "SELL": "Preço próximo de nível Fib (0.382/0.236) em rally",
                    "Confidence": "Proximidade exata do nível"
                },
                "parameters": {
                    "lookback_period": "50 (para detectar swing)",
                    "tolerance_pct": "0.5% (margem de erro)"
                },
                "best_for": "Tendências com pullbacks, níveis de entrada precisos",
                "avoid": "Mercados sem tendência definida"
            },
            
            "smc_bos": {
                "name": "SMC: Break of Structure",
                "emoji": "🔥",
                "type": "Smart Money Concepts",
                "description": "Continuação de tendência após rompimento de swing high/low",
                "logic": """
Identifica quando 'smart money' está empurrando o mercado:
- Preço rompe swing high anterior → BOS bullish → BUY
- Preço rompe swing low anterior → BOS bearish → SELL
                """,
                "triggers": {
                    "BUY": "High atual > último swing high significativo",
                    "SELL": "Low atual < último swing low significativo",
                    "Confidence": "Magnitude do displacement"
                },
                "parameters": {
                    "min_displacement": "0.1% (movimento mínimo para validar)"
                },
                "best_for": "Tendências fortes, continuação de momentum, timeframes altos",
                "avoid": "Consolidações, baixa liquidez"
            },
            
            "smc_choch": {
                "name": "SMC: Change of Character",
                "emoji": "🔄",
                "type": "Smart Money Concepts",
                "description": "Reversão quando sequência de topos/fundos muda",
                "logic": """
Detecta mudança de estrutura de mercado:
- Uptrend: Low rompe low anterior → CHoCH → SELL
- Downtrend: High rompe high anterior → CHoCH → BUY
                """,
                "triggers": {
                    "BUY": "Em downtrend, high rompe high anterior (reversão)",
                    "SELL": "Em uptrend, low rompe low anterior (reversão)",
                    "Confidence": "Força da quebra estrutural"
                },
                "parameters": {},
                "best_for": "Identificar reversões early, tops/bottoms de tendência",
                "avoid": "Mercados laterais com muitos whipsaws"
            },
            
            "smc_order_blocks": {
                "name": "SMC: Order Blocks",
                "emoji": "📦",
                "type": "Smart Money Concepts",
                "description": "Última vela de acumulação antes do rompimento",
                "logic": """
Identifica zonas onde instituições acumularam posições:
- Vela antes de BOS bullish = Bullish OB → suporte futuro
- Vela antes de BOS bearish = Bearish OB → resistência futura
                """,
                "triggers": {
                    "BUY": "Preço retorna para Bullish Order Block",
                    "SELL": "Preço retorna para Bearish Order Block",
                    "Confidence": "Força do BOS subsequente"
                },
                "parameters": {
                    "min_range": "0 (tamanho mínimo do bloco)"
                },
                "best_for": "Re-entries em tendência, zonas de interesse institucional",
                "avoid": "Mercados sem estrutura clara"
            },
            
            "smc_fvg": {
                "name": "SMC: Fair Value Gap",
                "emoji": "⚡",
                "type": "Smart Money Concepts",
                "description": "Gap entre corpos/sombras indicando imbalance",
                "logic": """
Detecta desequilíbrio de oferta/demanda (gaps):
- Gap bullish (low[1] > high[-1]) → preço deve preencher → BUY
- Gap bearish (high[1] < low[-1]) → preço deve preencher → SELL
                """,
                "triggers": {
                    "BUY": "FVG bullish detectado (gap para cima)",
                    "SELL": "FVG bearish detectado (gap para baixo)",
                    "Confidence": "Tamanho do gap"
                },
                "parameters": {},
                "best_for": "Movimentos rápidos, imbalances institucionais",
                "avoid": "Mercados de baixa volatilidade"
            },
            
            "smc_liquidity_sweep": {
                "name": "SMC: Liquidity Sweep",
                "emoji": "🎣",
                "type": "Smart Money Concepts",
                "description": "Rompimento falso para capturar liquidez (stop hunt)",
                "logic": """
Identifica quando smart money caça stops:
- Spike acima de high anterior + reversão rápida → Liquidity Grab → SELL
- Spike abaixo de low anterior + reversão rápida → Liquidity Grab → BUY
                """,
                "triggers": {
                    "BUY": "Wick longo abaixo + reversão (sweep de lows)",
                    "SELL": "Wick longo acima + reversão (sweep de highs)",
                    "Confidence": "Tamanho do wick vs corpo"
                },
                "parameters": {},
                "best_for": "Identificar armadilhas, reversões após stop hunt",
                "avoid": "Sem confirmação de reversão"
            }
        }
    
    def generate_markdown_files(self):
        """Gera arquivos markdown para todas as estratégias"""
        for key, data in self.strategies.items():
            filename = self.explanations_dir / f"{key}.md"
            content = self._create_markdown_content(key, data)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Gerado: {filename.name}")
    
    def _create_markdown_content(self, key: str, data: Dict) -> str:
        """Cria conteúdo markdown formatado"""
        content = f"""# {data['emoji']} {data['name']}

**Tipo:** {data['type']}

## Descrição
{data['description']}

## Lógica da Estratégia
{data['logic']}

## Triggers de Sinal

"""
        
        for trigger_type, trigger_desc in data['triggers'].items():
            content += f"- **{trigger_type}**: {trigger_desc}\n"
        
        content += "\n## Parâmetros\n\n"
        
        for param, desc in data['parameters'].items():
            content += f"- **{param}**: {desc}\n"
        
        content += f"""
## Melhor Para
{data['best_for']}

## Evitar
{data['avoid']}

## Exemplo de Uso

### Cenário Bullish
Quando a estratégia gera sinal BUY, indica que as condições favoráveis para entrada long foram detectadas.

### Cenário Bearish
Quando a estratégia gera sinal SELL, indica que as condições favoráveis para entrada short foram detectadas.

---
*Documento gerado automaticamente pelo Market Manus Strategy Lab*
"""
        
        return content
    
    def display_strategy(self, strategy_key: str):
        """Exibe explicação de uma estratégia"""
        if strategy_key not in self.strategies:
            print(f"❌ Estratégia '{strategy_key}' não encontrada")
            return
        
        data = self.strategies[strategy_key]
        
        print("\n" + "=" * 70)
        print(f"{data['emoji']} {data['name']}")
        print("=" * 70)
        print(f"\nTipo: {data['type']}")
        print(f"\n{data['description']}")
        print(f"\n{data['logic']}")
        print("\nTriggers:")
        for trigger, desc in data['triggers'].items():
            print(f"  • {trigger}: {desc}")
        print("\nParâmetros:")
        for param, desc in data['parameters'].items():
            print(f"  • {param}: {desc}")
        print(f"\n✅ Melhor para: {data['best_for']}")
        print(f"❌ Evitar: {data['avoid']}")
        print("=" * 70)
    
    def list_all_strategies(self):
        """Lista todas as estratégias disponíveis"""
        print("\n" + "=" * 70)
        print("📚 ESTRATÉGIAS DISPONÍVEIS (13 total)")
        print("=" * 70)
        
        # Agrupar por tipo
        classic = []
        smc = []
        
        for key, data in self.strategies.items():
            if key.startswith("smc_"):
                smc.append((key, data))
            else:
                classic.append((key, data))
        
        print("\n📊 CLÁSSICAS (8):")
        for key, data in classic:
            print(f"   {data['emoji']} {key.ljust(25)} - {data['name']}")
        
        print("\n🔥 SMART MONEY CONCEPTS (5):")
        for key, data in smc:
            print(f"   {data['emoji']} {key.ljust(25)} - {data['name']}")
        
        print("=" * 70)


def run_explanations_menu():
    """Menu interativo de explanations"""
    explainer = StrategyExplanations()
    
    while True:
        print("\n" + "=" * 70)
        print("📚 MENU DE EXPLICAÇÕES DAS ESTRATÉGIAS")
        print("=" * 70)
        print("\n1️⃣  Listar todas as estratégias")
        print("2️⃣  Ver explicação detalhada de uma estratégia")
        print("3️⃣  Gerar/Atualizar arquivos markdown")
        print("0️⃣  Voltar")
        
        choice = input("\n🔢 Escolha uma opção (0-3): ").strip()
        
        if choice == "1":
            explainer.list_all_strategies()
            input("\n📖 Pressione ENTER para continuar...")
        
        elif choice == "2":
            explainer.list_all_strategies()
            strategy_key = input("\n💡 Digite o nome da estratégia (ex: rsi_mean_reversion): ").strip()
            explainer.display_strategy(strategy_key)
            input("\n📖 Pressione ENTER para continuar...")
        
        elif choice == "3":
            print("\n📝 Gerando arquivos markdown...")
            explainer.generate_markdown_files()
            print(f"\n✅ Arquivos salvos em: {explainer.explanations_dir}")
            input("\n📖 Pressione ENTER para continuar...")
        
        elif choice == "0":
            break
        
        else:
            print("❌ Opção inválida")


if __name__ == "__main__":
    run_explanations_menu()
