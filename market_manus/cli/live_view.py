from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.console import Group
from datetime import datetime


def render_live_ui(state) -> Layout:
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=8)
    )
    
    header_table = Table.grid(expand=True)
    header_table.add_column(justify="left")
    header_table.add_column(justify="center")
    header_table.add_column(justify="center")
    header_table.add_column(justify="right")
    
    header_table.add_row(
        f"[bold cyan]Provider:[/bold cyan] {state.provider}",
        f"[bold yellow]Symbol:[/bold yellow] {state.symbol}",
        f"[bold magenta]TF:[/bold magenta] {state.interval}",
        f"[bold green]Latency:[/bold green] {state.latency_ms}ms"
    )
    header_table.add_row(
        f"[dim]Msgs: {state.msgs_received}[/dim]",
        f"[dim]Processed: {state.msgs_processed}[/dim]",
        f"[dim]Reconnects: {state.reconnections}[/dim]",
        f"[dim]{datetime.now().strftime('%H:%M:%S')}[/dim]"
    )
    
    layout["header"].update(Panel(header_table, title="🔴 LIVE STREAMING", border_style="red"))
    
    layout["body"].split_row(
        Layout(name="price", ratio=1),
        Layout(name="confluence", ratio=2)
    )
    
    price_change_color = "green" if state.delta_since >= 0 else "red"
    price_change_symbol = "+" if state.delta_since >= 0 else ""
    
    price_text = Text()
    price_text.append(f"${state.price:,.2f}\n", style="bold white")
    price_text.append(
        f"{price_change_symbol}${state.delta_since:,.2f} desde mudança",
        style=price_change_color
    )
    
    layout["price"].update(
        Panel(price_text, title="💰 Preço Atual", border_style="cyan")
    )
    
    conf_table = Table(show_header=True, expand=True)
    conf_table.add_column("Estado", style="bold", width=10)
    conf_table.add_column("Conf.", justify="center", width=8)
    conf_table.add_column("Score", justify="center", width=8)
    conf_table.add_column("Razões Principais", overflow="fold")
    
    label_style = "green" if "BUY" in state.label else ("red" if "SELL" in state.label else "yellow")
    
    conf_table.add_row(
        f"[{label_style}]{state.label_emoji}[/{label_style}]",
        f"{state.confidence:.2f}",
        f"{state.score:.3f}",
        ", ".join(state.top_reasons) if state.top_reasons else "Aguardando..."
    )
    
    layout["confluence"].update(
        Panel(conf_table, title="🔍 Confluência (5 SMC + 7 Clássicos)", border_style="magenta")
    )
    
    events_table = Table(show_header=True, expand=True)
    events_table.add_column("Quando", width=10)
    events_table.add_column("Ação", width=8)
    events_table.add_column("Preço", justify="right", width=12)
    events_table.add_column("Score", justify="center", width=8)
    
    for event in reversed(list(state.last_events)):
        action_style = "green" if event.action == "BUY" else ("red" if event.action == "SELL" else "yellow")
        events_table.add_row(
            event.timestamp.strftime("%H:%M:%S"),
            f"[{action_style}]{event.action}[/{action_style}]",
            f"${event.price:,.2f}",
            f"{event.score:.3f}"
        )
    
    layout["footer"].update(
        Panel(events_table, title="📊 Últimas Mudanças de Estado", border_style="blue")
    )
    
    return layout


async def run_live_view(stream_runtime):
    with Live(render_live_ui(stream_runtime.state), refresh_per_second=2) as live:
        stream_runtime.running = True
        
        import asyncio
        collector_task = asyncio.create_task(stream_runtime.collect_ws_messages())
        processor_task = asyncio.create_task(stream_runtime.process_micro_batches())
        
        try:
            while stream_runtime.running:
                await asyncio.sleep(0.5)
                live.update(render_live_ui(stream_runtime.state))
                
        except KeyboardInterrupt:
            stream_runtime.stop()
            collector_task.cancel()
            processor_task.cancel()
