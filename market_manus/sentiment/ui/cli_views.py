import asyncio
from rich.console import Console
from rich.table import Table
from ..sentiment_service import gather_sentiment

console = Console()

async def render_sentiment(symbol: str):
    res = await gather_sentiment(symbol)
    console.print("\n[bold cyan]🧭 MARKET SENTIMENT ANALYSIS[/]")
    console.print(f"[white]Ativo:[/] [bold]{symbol}[/]   Janela: [bold]{res['window']}[/]")
    console.print(f"[white]Score composto:[/] [bold]{res['score']}[/] (0=Bearish, 1=Bullish)\n")

    t = Table(title="Fontes")
    t.add_column("Fonte")
    t.add_column("Tipo")
    t.add_column("Resumo")
    for src in res["sources"]:
        name = src.get("__name__")
        kind = src.get("kind","-")
        if name=="alt_fng":
            summary = f"F&G={src.get('score')} ({src.get('label')})"
        elif name=="coingecko":
            summary = f"Preço=${src.get('price')} Δ24h={src.get('chg_24h')}% Vol=${src.get('vol_24h')}"
        elif name=="bybit":
            summary = "Funding/OI recebidos" if src.get("funding") else "Sem dados/sem credenciais"
        elif name=="coinglass":
            summary = "OI disponível" if src.get("oi") else "Sem chave"
        elif name=="cryptopanic":
            summary = f"{src.get('count',0)} notícias"
        else:
            summary = ", ".join([f"{k}={v}" for k,v in src.items() if k not in {"__name__","kind"}])[:80]
        t.add_row(name, kind, summary)
    console.print(t)

def run_blocking(symbol: str):
    asyncio.run(render_sentiment(symbol))
