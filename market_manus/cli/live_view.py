from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.console import Group
from datetime import datetime


def render_live_ui(state) -> Layout:
    layout = Layout()
    
    # Expandido para incluir painéis ICT e Costs
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="ict_costs", size=6),
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
    
    # FASE 2: Painéis de Transparência (ICT + Trading Costs)
    layout["ict_costs"].split_row(
        Layout(name="ict_context", ratio=1),
        Layout(name="trading_costs", ratio=1)
    )
    
    # Painel ICT Market Context
    ict_table = Table(show_header=True, expand=True, box=None)
    ict_table.add_column("Métrica ICT", style="cyan", width=20)
    ict_table.add_column("Valor", justify="left")
    
    # Premium/Discount Classification
    pd_class = state.ict_premium_discount or "N/A"
    pd_color = "red" if "Premium" in pd_class else ("green" if "Discount" in pd_class else "yellow")
    ict_table.add_row(
        "Premium/Discount",
        f"[{pd_color}]{pd_class}[/{pd_color}]"
    )
    
    # Price Zone
    price_zone = state.ict_price_in_zone or "N/A"
    ict_table.add_row(
        "Zona de Preço",
        f"[bold]{price_zone}[/bold]"
    )
    
    # OTE (Optimal Trade Entry)
    if state.ict_ote_active:
        ote_style = "green bold" if state.ict_ote_type == "BULLISH" else "red bold"
        ict_table.add_row(
            "🎯 OTE Ativo",
            f"[{ote_style}]{state.ict_ote_type}[/{ote_style}]"
        )
    else:
        ict_table.add_row("🎯 OTE Ativo", "[dim]Não[/dim]")
    
    # CE (Consequent Encroachment)
    if state.ict_ce_level:
        ict_table.add_row(
            "CE Level (50%)",
            f"[yellow]${state.ict_ce_level:,.2f}[/yellow]"
        )
    else:
        ict_table.add_row("CE Level (50%)", "[dim]N/A[/dim]")
    
    layout["ict_context"].update(
        Panel(ict_table, title="🎯 ICT Market Context", border_style="cyan")
    )
    
    # Painel Trading Costs
    costs_table = Table(show_header=True, expand=True, box=None)
    costs_table.add_column("Métrica", style="yellow", width=20)
    costs_table.add_column("Valor", justify="right")
    
    # Paper Trading Stats
    costs_table.add_row(
        "💰 Equity",
        f"[bold green]${state.paper_equity:,.2f}[/bold green]"
    )
    
    # Position Status
    pos_status = "🟢 ABERTA" if state.paper_position_open else "⚪ Fechada"
    pos_color = "green" if state.paper_position_open else "dim"
    costs_table.add_row(
        "Posição",
        f"[{pos_color}]{pos_status}[/{pos_color}]"
    )
    
    # Unrealized P&L
    if state.paper_position_open:
        upnl_color = "green" if state.paper_unrealized_pnl >= 0 else "red"
        upnl_sign = "+" if state.paper_unrealized_pnl >= 0 else ""
        costs_table.add_row(
            "P&L Não Realizado",
            f"[{upnl_color}]{upnl_sign}${state.paper_unrealized_pnl:,.2f}[/{upnl_color}]"
        )
    
    # Last Trade Breakdown (se disponível)
    if state.paper_last_trade_net is not None:
        costs_table.add_row("[dim]─[/dim]" * 20, "[dim]─[/dim]" * 10)
        costs_table.add_row(
            "Último Trade (Bruto)",
            f"${state.paper_last_trade_gross:,.2f}" if state.paper_last_trade_gross else "N/A"
        )
        costs_table.add_row(
            "Custos (Fees+Slip)",
            f"[red]-${state.paper_last_trade_costs:,.2f}[/red]" if state.paper_last_trade_costs else "N/A"
        )
        net_color = "green" if state.paper_last_trade_net >= 0 else "red"
        net_sign = "+" if state.paper_last_trade_net >= 0 else ""
        costs_table.add_row(
            "Líquido (Net)",
            f"[{net_color} bold]{net_sign}${state.paper_last_trade_net:,.2f}[/{net_color} bold]"
        )
    
    # Win Rate
    if state.paper_total_trades > 0:
        wr_color = "green" if state.paper_win_rate >= 50 else "red"
        costs_table.add_row(
            f"Win Rate ({state.paper_total_trades} trades)",
            f"[{wr_color}]{state.paper_win_rate:.1f}%[/{wr_color}]"
        )
    
    layout["trading_costs"].update(
        Panel(costs_table, title="💰 Trading Costs & P&L", border_style="yellow")
    )
    
    return layout


async def run_live_view(stream_runtime):
    import asyncio
    
    print("📥 Carregando dados históricos...")
    success = await stream_runtime.bootstrap_historical_data()
    if not success:
        print("⚠️  Aviso: Bootstrap falhou. Continuando apenas com WebSocket...")
    else:
        print(f"✅ {len(stream_runtime.candles_deque)} candles carregados")
    
    with Live(render_live_ui(stream_runtime.state), refresh_per_second=2) as live:
        stream_runtime.running = True
        
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
