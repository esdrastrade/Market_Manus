import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from ..sentiment_service import gather_sentiment

console = Console()

def _interpret_score(score: float) -> tuple[str, str, str]:
    if score >= 0.75:
        return ("🚀 EXTREMAMENTE OTIMISTA", "green", "O mercado está em forte alta com confiança elevada dos investidores.")
    elif score >= 0.65:
        return ("📈 OTIMISTA", "bright_green", "Sentimento positivo predomina, indicando boa disposição de compra.")
    elif score >= 0.55:
        return ("🟢 LEVEMENTE OTIMISTA", "yellow", "Leve tendência positiva, mas com cautela moderada no ar.")
    elif score >= 0.45:
        return ("⚖️ NEUTRO", "white", "Mercado indeciso, sem uma direção clara no momento.")
    elif score >= 0.35:
        return ("🟠 LEVEMENTE PESSIMISTA", "orange1", "Alguma apreensão presente, pressão vendedora começando a aparecer.")
    elif score >= 0.25:
        return ("📉 PESSIMISTA", "red", "Sentimento negativo domina, indicando preocupação dos investidores.")
    else:
        return ("⚠️ EXTREMAMENTE PESSIMISTA", "dark_red", "Medo intenso no mercado, forte pressão de venda.")

def _build_narrative(res: dict) -> str:
    score = res.get("score")
    if score is None:
        return "❌ Não foi possível analisar o sentimento do mercado. Nenhuma fonte de dados está disponível no momento."
    
    symbol = res.get("symbol", "ATIVO")
    sentiment_label, _, sentiment_desc = _interpret_score(score)
    
    sources = res.get("sources", [])
    active_sources = [s for s in sources if not s.get("error") and "note" not in s]
    
    narrative_parts = []
    
    narrative_parts.append(f"📊 **Análise para {symbol}**\n")
    narrative_parts.append(f"Com base em {len(active_sources)} fonte(s) de dados confiável(is), ")
    narrative_parts.append(f"o sentimento do mercado está {sentiment_label.lower()}. {sentiment_desc}\n")
    
    for src in active_sources:
        name = src.get("__name__")
        kind = src.get("kind", "")
        
        if name == "alt_fng":
            fng_score = src.get("score", 0)
            fng_label = src.get("label", "Neutral")
            if fng_score >= 75:
                narrative_parts.append(f"\n🎭 **Sentimento Geral**: O índice Fear & Greed marca {fng_score}/100 ({fng_label}), indicando que a ganância está dominando o mercado cripto.")
            elif fng_score >= 55:
                narrative_parts.append(f"\n🎭 **Sentimento Geral**: O índice Fear & Greed está em {fng_score}/100 ({fng_label}), mostrando leve otimismo entre investidores.")
            elif fng_score >= 45:
                narrative_parts.append(f"\n🎭 **Sentimento Geral**: O índice Fear & Greed está em {fng_score}/100 ({fng_label}), mostrando equilíbrio entre medo e ganância.")
            elif fng_score >= 25:
                narrative_parts.append(f"\n🎭 **Sentimento Geral**: O índice Fear & Greed marca {fng_score}/100 ({fng_label}), revelando que o medo predomina entre investidores.")
            else:
                narrative_parts.append(f"\n🎭 **Sentimento Geral**: O índice Fear & Greed despenca para {fng_score}/100 ({fng_label}), sinalizando pânico extremo no mercado.")
        
        elif name == "coingecko":
            price = src.get("price", 0)
            chg = src.get("chg_24h", 0)
            vol = src.get("vol_24h", 0)
            
            price_str = f"${price:,.2f}" if price >= 10 else f"${price:,.4f}"
            vol_billions = vol / 1_000_000_000
            
            if chg > 3:
                narrative_parts.append(f"\n💰 **Ação de Preço**: O {symbol} está negociando a {price_str}, com forte alta de {chg:+.2f}% nas últimas 24h. O volume de ${vol_billions:.2f}B confirma movimentação significativa.")
            elif chg > 0:
                narrative_parts.append(f"\n💰 **Ação de Preço**: Cotado a {price_str}, o {symbol} registra leve ganho de {chg:+.2f}% no dia, com volume de ${vol_billions:.2f}B indicando interesse moderado.")
            elif chg > -3:
                narrative_parts.append(f"\n💰 **Ação de Preço**: Negociando a {price_str}, o {symbol} recua {chg:.2f}% hoje. Volume de ${vol_billions:.2f}B mostra certa pressão vendedora.")
            else:
                narrative_parts.append(f"\n💰 **Ação de Preço**: ATENÇÃO! O {symbol} despenca {chg:.2f}% para {price_str}. Volume elevado de ${vol_billions:.2f}B indica possível pânico ou capitulação.")
        
        elif name == "bybit" and src.get("funding"):
            narrative_parts.append(f"\n⚡ **Derivativos**: Dados de funding e open interest indicam atividade em futuros e perpétuos, sinalizando posicionamento especulativo.")
        
        elif name == "coinglass" and src.get("oi"):
            narrative_parts.append(f"\n📊 **Open Interest**: Rastreamento de posições abertas mostra {kind} em movimento.")
        
        elif name == "cryptopanic" and src.get("count", 0) > 0:
            count = src.get("count")
            positive = src.get("positive", 0)
            negative = src.get("negative", 0)
            titles = src.get("titles", [])
            
            total_votes = positive + negative
            if total_votes > 0:
                pos_pct = (positive / total_votes) * 100
                sentiment_emoji = "📈" if pos_pct > 60 else "📉" if pos_pct < 40 else "⚖️"
                sentiment_text = "predominantemente positivo" if pos_pct > 60 else "predominantemente negativo" if pos_pct < 40 else "misto"
            else:
                pos_pct = 50
                sentiment_emoji = "📰"
                sentiment_text = "neutro"
            
            narrative_parts.append(f"\n{sentiment_emoji} **Contexto Macroeconômico**: Detectadas {count} notícia(s) recente(s) sobre {symbol.replace('USDT', '')}. Sentimento da mídia: {sentiment_text}.")
            
            if titles and len(titles) > 0:
                narrative_parts.append(f"\n   💬 Destaque: \"{titles[0]}\"")
                if pos_pct > 60:
                    narrative_parts.append(" — Notícias otimistas podem impulsionar novos investidores.")
                elif pos_pct < 40:
                    narrative_parts.append(" — Cobertura negativa pode pressionar preços no curto prazo.")
    
    if score >= 0.65:
        narrative_parts.append(f"\n\n✅ **Recomendação**: O sentimento favorável pode indicar boas oportunidades de entrada em posições long. Monitore níveis de resistência.")
    elif score >= 0.45:
        narrative_parts.append(f"\n\n⏸️ **Recomendação**: Momento de cautela. Aguarde sinais mais claros antes de abrir novas posições. Consolidação provável.")
    else:
        narrative_parts.append(f"\n\n⚠️ **Recomendação**: Sentimento negativo sugere aguardar melhores pontos de entrada. Considere proteção de posições existentes.")
    
    inactive_count = len(sources) - len(active_sources)
    if inactive_count > 0:
        narrative_parts.append(f"\n\n💡 *Nota: {inactive_count} fonte(s) adicional(is) está(ão) disponível(is) mediante configuração de API keys.*")
    
    return "".join(narrative_parts)

async def render_sentiment(symbol: str):
    res = await gather_sentiment(symbol)
    
    score = res.get("score")
    sentiment_label, color, _ = _interpret_score(score) if score is not None else ("INDISPONÍVEL", "red", "")
    
    header = Text()
    header.append("🧭 ANÁLISE DE SENTIMENTO DE MERCADO\n\n", style="bold cyan")
    header.append(f"Ativo: ", style="white")
    header.append(f"{symbol}", style="bold yellow")
    header.append(f"  |  Score: ", style="white")
    header.append(f"{score if score is not None else 'N/A'}", style=f"bold {color}")
    header.append(f"  |  Status: ", style="white")
    header.append(sentiment_label, style=f"bold {color}")
    
    console.print(Panel(header, border_style="cyan"))
    
    narrative = _build_narrative(res)
    console.print(Panel(narrative, title="📖 Interpretação", border_style="green", padding=(1, 2)))
    
    sources = res.get("sources", [])
    if sources:
        console.print("\n[dim]━━━ Detalhamento Técnico das Fontes ━━━[/dim]\n")
        
        t = Table(show_header=True, header_style="bold magenta", show_lines=False)
        t.add_column("Fonte", style="cyan")
        t.add_column("Categoria", style="blue")
        t.add_column("Status", style="white")
        
        for src in sources:
            name = src.get("__name__", "?")
            kind = src.get("kind", "-")
            
            if src.get("error"):
                status = f"❌ {src.get('error')}"
                style = "red"
            elif "note" in src:
                status = f"ℹ️ {src.get('note')}"
                style = "yellow"
            elif name == "alt_fng":
                status = f"✅ F&G: {src.get('score')} ({src.get('label')})"
                style = "green"
            elif name == "coingecko":
                status = f"✅ ${src.get('price'):,.0f} ({src.get('chg_24h'):+.2f}%)"
                style = "green"
            elif name == "bybit":
                status = "✅ Conectado" if src.get("funding") else "⚠️ Sem dados"
                style = "green" if src.get("funding") else "yellow"
            elif name == "cryptopanic":
                count = src.get("count", 0)
                status = f"✅ {count} notícias" if count > 0 else "⚠️ 0 notícias"
                style = "green" if count > 0 else "yellow"
            else:
                status = "✅ Ativo" if not src.get("error") else "❌ Inativo"
                style = "green" if not src.get("error") else "red"
            
            t.add_row(name, kind, status)
        
        console.print(t)
    
    console.print()

def run_blocking(symbol: str):
    asyncio.run(render_sentiment(symbol))
