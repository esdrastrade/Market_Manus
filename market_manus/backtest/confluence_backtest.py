"""
Backtest de Confluência SMC + Clássicos
Loga score, componentes, decisão e P&L por candle
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
import yaml
from market_manus.strategies.smc.patterns import confluence_decision
from market_manus.core.signal import Signal


def backtest_confluence(data: pd.DataFrame, config_path: str = None, config: dict = None) -> dict:
    """
    Executa backtest de confluência com log detalhado por candle.
    
    Args:
        data: DataFrame OHLCV com histórico completo
        config_path: Caminho para arquivo YAML de config (opcional)
        config: Dict de config direto (opcional, prioritário sobre config_path)
    
    Returns:
        Dict com relatório completo:
        - trades: Lista de trades executados
        - candle_log: Log detalhado por candle
        - stats: Estatísticas finais (total_trades, win_rate, total_pnl, etc)
    """
    # Carrega config
    if config is None:
        if config_path is None:
            config_path = "config/confluence.yaml"
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    
    # Extrai parâmetros de risk management
    risk_cfg = config.get('risk_management', {})
    position_size_pct = risk_cfg.get('position_size_pct', 0.01)
    stop_multiplier = risk_cfg.get('stop_loss', {}).get('multiplier', 1.5)
    tp1_multiplier = risk_cfg.get('take_profit', {}).get('tp1', {}).get('multiplier', 2.5)
    
    # Inicializa estado
    capital = 10000.0  # Capital inicial
    position = None  # Posição atual
    trades = []
    candle_log = []
    
    # Itera sobre cada candle
    for i in range(50, len(data)):  # Começa em 50 para ter histórico suficiente
        candles = data.iloc[:i+1]  # Janela até candle atual
        current_candle = data.iloc[i]
        
        # Chama confluence_decision
        try:
            signal = confluence_decision(
                candles=candles,
                symbol="BACKTEST",
                timeframe="backtest",
                config=config
            )
        except Exception as e:
            signal = Signal(action="HOLD", confidence=0.0, reasons=[f"Erro: {e}"], tags=["ERROR"])
        
        # Log do candle (inclui componentes)
        log_entry = {
            'index': i,
            'timestamp': current_candle.get('timestamp', i),
            'close': current_candle['close'],
            'action': signal.action,
            'confidence': signal.confidence,
            'score': signal.meta.get('score', 0),
            'reasons': signal.reasons,
            'tags': signal.tags,
            'regime': signal.meta.get('regime', {}),
            'components': {  # Componentes de confluência
                'buy_count': signal.meta.get('buy_count', 0),
                'sell_count': signal.meta.get('sell_count', 0),
                'signal_count': signal.meta.get('signal_count', 0)
            }
        }
        
        # Calcula ATR para stop/tp
        if i >= 14:
            recent_candles = data.iloc[i-14:i+1]
            high_low = recent_candles['high'] - recent_candles['low']
            atr = high_low.mean()
        else:
            atr = current_candle['high'] - current_candle['low']
        
        # Executa lógica de trading
        if position is None:
            # Sem posição: verifica entrada
            if signal.action == "BUY":
                entry_price = current_candle['close']
                stop_loss = entry_price - (atr * stop_multiplier)
                take_profit = entry_price + (atr * tp1_multiplier)
                position_size = capital * position_size_pct
                
                position = {
                    'type': 'BUY',
                    'entry_price': entry_price,
                    'entry_index': i,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'position_size': position_size,
                    'signal': signal
                }
                
                log_entry['trade_action'] = 'ENTRY_BUY'
                log_entry['entry_price'] = entry_price
                
            elif signal.action == "SELL":
                entry_price = current_candle['close']
                stop_loss = entry_price + (atr * stop_multiplier)
                take_profit = entry_price - (atr * tp1_multiplier)
                position_size = capital * position_size_pct
                
                position = {
                    'type': 'SELL',
                    'entry_price': entry_price,
                    'entry_index': i,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'position_size': position_size,
                    'signal': signal
                }
                
                log_entry['trade_action'] = 'ENTRY_SELL'
                log_entry['entry_price'] = entry_price
        
        else:
            # Com posição: verifica saída
            exit_triggered = False
            exit_reason = None
            exit_price = None
            
            if position['type'] == 'BUY':
                # Verifica stop loss
                if current_candle['low'] <= position['stop_loss']:
                    exit_triggered = True
                    exit_reason = 'STOP_LOSS'
                    exit_price = position['stop_loss']
                
                # Verifica take profit
                elif current_candle['high'] >= position['take_profit']:
                    exit_triggered = True
                    exit_reason = 'TAKE_PROFIT'
                    exit_price = position['take_profit']
                
                # Verifica sinal contrário
                elif signal.action == "SELL":
                    exit_triggered = True
                    exit_reason = 'SIGNAL_REVERSAL'
                    exit_price = current_candle['close']
            
            elif position['type'] == 'SELL':
                # Verifica stop loss
                if current_candle['high'] >= position['stop_loss']:
                    exit_triggered = True
                    exit_reason = 'STOP_LOSS'
                    exit_price = position['stop_loss']
                
                # Verifica take profit
                elif current_candle['low'] <= position['take_profit']:
                    exit_triggered = True
                    exit_reason = 'TAKE_PROFIT'
                    exit_price = position['take_profit']
                
                # Verifica sinal contrário
                elif signal.action == "BUY":
                    exit_triggered = True
                    exit_reason = 'SIGNAL_REVERSAL'
                    exit_price = current_candle['close']
            
            if exit_triggered:
                # Calcula P&L
                if position['type'] == 'BUY':
                    pnl = (exit_price - position['entry_price']) * (position['position_size'] / position['entry_price'])
                else:  # SELL
                    pnl = (position['entry_price'] - exit_price) * (position['position_size'] / position['entry_price'])
                
                pnl_pct = (pnl / capital) * 100
                capital += pnl
                
                # Registra trade
                trade = {
                    'entry_index': position['entry_index'],
                    'exit_index': i,
                    'type': position['type'],
                    'entry_price': position['entry_price'],
                    'exit_price': exit_price,
                    'exit_reason': exit_reason,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'capital_after': capital,
                    'entry_signal': position['signal'].to_dict()
                }
                trades.append(trade)
                
                log_entry['trade_action'] = f'EXIT_{position["type"]}'
                log_entry['exit_price'] = exit_price
                log_entry['exit_reason'] = exit_reason
                log_entry['pnl'] = pnl
                log_entry['pnl_pct'] = pnl_pct
                
                # Reseta posição
                position = None
        
        candle_log.append(log_entry)
    
    # Fecha posição aberta no final (se houver)
    if position is not None:
        exit_price = data.iloc[-1]['close']
        
        if position['type'] == 'BUY':
            pnl = (exit_price - position['entry_price']) * (position['position_size'] / position['entry_price'])
        else:  # SELL
            pnl = (position['entry_price'] - exit_price) * (position['position_size'] / position['entry_price'])
        
        pnl_pct = (pnl / capital) * 100
        capital += pnl
        
        # Registra trade de fechamento
        trade = {
            'entry_index': position['entry_index'],
            'exit_index': len(data) - 1,
            'type': position['type'],
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'exit_reason': 'END_OF_TEST',
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'capital_after': capital,
            'entry_signal': position['signal'].to_dict()
        }
        trades.append(trade)
    
    # Calcula estatísticas finais
    if trades:
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['pnl'] > 0)
        losing_trades = sum(1 for t in trades if t['pnl'] < 0)
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        total_pnl = sum(t['pnl'] for t in trades)
        avg_win = np.mean([t['pnl'] for t in trades if t['pnl'] > 0]) if winning_trades > 0 else 0
        avg_loss = np.mean([t['pnl'] for t in trades if t['pnl'] < 0]) if losing_trades > 0 else 0
        
        profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 and avg_loss != 0 else 0
        
        roi = ((capital - 10000) / 10000) * 100
    else:
        total_trades = 0
        winning_trades = 0
        losing_trades = 0
        win_rate = 0
        total_pnl = 0
        avg_win = 0
        avg_loss = 0
        profit_factor = 0
        roi = 0
    
    stats = {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
        'initial_capital': 10000.0,
        'final_capital': capital,
        'roi': roi
    }
    
    return {
        'trades': trades,
        'candle_log': candle_log,
        'stats': stats,
        'config': config
    }


def print_backtest_report(report: dict):
    """Imprime relatório de backtest formatado"""
    stats = report['stats']
    
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO DE BACKTEST - CONFLUÊNCIA SMC + CLÁSSICOS")
    print("=" * 60)
    
    print(f"\n💰 PERFORMANCE FINANCEIRA:")
    print(f"   Capital inicial: ${stats['initial_capital']:,.2f}")
    print(f"   Capital final: ${stats['final_capital']:,.2f}")
    print(f"   P&L total: ${stats['total_pnl']:+,.2f}")
    print(f"   ROI: {stats['roi']:+.2f}%")
    
    print(f"\n📈 ESTATÍSTICAS DE TRADES:")
    print(f"   Total de trades: {stats['total_trades']}")
    print(f"   Trades vencedores: {stats['winning_trades']}")
    print(f"   Trades perdedores: {stats['losing_trades']}")
    print(f"   Win Rate: {stats['win_rate']:.1f}%")
    
    print(f"\n💵 MÉDIAS:")
    print(f"   Ganho médio: ${stats['avg_win']:,.2f}")
    print(f"   Perda média: ${stats['avg_loss']:,.2f}")
    print(f"   Profit Factor: {stats['profit_factor']:.2f}")
    
    print(f"\n📋 TRADES EXECUTADOS:")
    for i, trade in enumerate(report['trades'][:10], 1):  # Mostra primeiros 10
        print(f"   {i}. {trade['type']} | Entry: ${trade['entry_price']:.2f} | Exit: ${trade['exit_price']:.2f} | "
              f"P&L: ${trade['pnl']:+.2f} ({trade['pnl_pct']:+.2f}%) | Reason: {trade['exit_reason']}")
    
    if len(report['trades']) > 10:
        print(f"   ... e mais {len(report['trades']) - 10} trades")
    
    print("\n" + "=" * 60)
