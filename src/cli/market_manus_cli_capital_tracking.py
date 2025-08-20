#!/usr/bin/env python3
"""
Market Manus CLI - Capital Tracking Enhanced
Data: 16/01/2025 20:30

FOCO PRINCIPAL: Mostrar como as operações afetam o capital inicial

Melhorias implementadas:
- ✅ Tracking detalhado de P&L em tempo real
- ✅ Dashboard de capital com evolução visual
- ✅ Histórico de operações com impacto no capital
- ✅ Métricas de performance em dólares
- ✅ Simulação realista de trades com capital real
- ✅ Compound interest visual
- ✅ Alertas de drawdown e ganhos
"""

import os
import sys
import json
import logging
import time
import requests
import hashlib
import hmac
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('market_manus_capital_tracking.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Auto-detecção do diretório do projeto
def find_project_root():
    """Encontra o diretório raiz do projeto"""
    current_dir = Path(__file__).parent.absolute()
    
    # Procurar por indicadores do projeto
    indicators = ['.git', 'README.md', 'requirements.txt', 'src']
    
    for parent in [current_dir] + list(current_dir.parents):
        if any((parent / indicator).exists() for indicator in indicators):
            return parent
    
    return current_dir

PROJECT_ROOT = find_project_root()
SRC_DIR = PROJECT_ROOT / 'src'

# Adicionar diretórios ao path
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_DIR))

print(f"📁 Diretório do projeto: {PROJECT_ROOT}")


class Trade:
    """Representa uma operação de trading"""
    def __init__(self, strategy: str, entry_price: float, exit_price: float, 
                 position_size: float, timestamp: datetime, duration_hours: float):
        self.strategy = strategy
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.position_size = position_size  # Em USD
        self.timestamp = timestamp
        self.duration_hours = duration_hours
        
        # Calcular P&L
        self.pnl_pct = (exit_price - entry_price) / entry_price
        self.pnl_usd = position_size * self.pnl_pct
        self.is_profitable = self.pnl_usd > 0
        
        # Fees (simulado)
        self.fees_usd = position_size * 0.001  # 0.1% fee
        self.net_pnl_usd = self.pnl_usd - self.fees_usd
    
    def to_dict(self) -> Dict:
        """Converte trade para dict"""
        return {
            'strategy': self.strategy,
            'timestamp': self.timestamp.isoformat(),
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'position_size_usd': self.position_size,
            'duration_hours': self.duration_hours,
            'pnl_pct': self.pnl_pct,
            'pnl_usd': self.pnl_usd,
            'fees_usd': self.fees_usd,
            'net_pnl_usd': self.net_pnl_usd,
            'is_profitable': self.is_profitable
        }


class CapitalTracker:
    """Rastreador de capital com histórico detalhado"""
    
    def __init__(self, initial_capital: float, position_size_pct: float = 2.0, 
                 compound_interest: bool = True):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.position_size_pct = position_size_pct
        self.compound_interest = compound_interest
        
        # Histórico
        self.trades: List[Trade] = []
        self.capital_history: List[Dict] = []
        self.daily_snapshots: List[Dict] = []
        
        # Métricas
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_fees_paid = 0.0
        self.max_capital_reached = initial_capital
        self.max_drawdown_usd = 0.0
        self.max_drawdown_pct = 0.0
        
        # Registrar estado inicial
        self._record_capital_snapshot("Initial Capital")
    
    def _record_capital_snapshot(self, event: str):
        """Registra snapshot do capital"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'event': event,
            'capital': self.current_capital,
            'total_return_usd': self.current_capital - self.initial_capital,
            'total_return_pct': (self.current_capital / self.initial_capital - 1) * 100,
            'total_trades': self.total_trades,
            'win_rate': self.get_win_rate()
        }
        self.capital_history.append(snapshot)
    
    def get_position_size_usd(self, price: float = 50000) -> float:
        """Calcula tamanho da posição em USD"""
        if self.compound_interest:
            return self.current_capital * (self.position_size_pct / 100)
        else:
            return self.initial_capital * (self.position_size_pct / 100)
    
    def execute_trade(self, trade: Trade):
        """Executa um trade e atualiza capital"""
        # Adicionar trade ao histórico
        self.trades.append(trade)
        self.total_trades += 1
        
        # Atualizar capital
        old_capital = self.current_capital
        self.current_capital += trade.net_pnl_usd
        
        # Atualizar estatísticas
        if trade.is_profitable:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        self.total_fees_paid += trade.fees_usd
        
        # Atualizar máximos e drawdowns
        if self.current_capital > self.max_capital_reached:
            self.max_capital_reached = self.current_capital
        
        # Calcular drawdown atual
        current_dd_usd = self.max_capital_reached - self.current_capital
        current_dd_pct = (current_dd_usd / self.max_capital_reached) * 100
        
        if current_dd_usd > self.max_drawdown_usd:
            self.max_drawdown_usd = current_dd_usd
            self.max_drawdown_pct = current_dd_pct
        
        # Registrar snapshot
        event = f"Trade {trade.strategy}: {'✅' if trade.is_profitable else '❌'} ${trade.net_pnl_usd:+.2f}"
        self._record_capital_snapshot(event)
        
        return {
            'old_capital': old_capital,
            'new_capital': self.current_capital,
            'change_usd': trade.net_pnl_usd,
            'change_pct': (trade.net_pnl_usd / old_capital) * 100
        }
    
    def get_win_rate(self) -> float:
        """Calcula win rate"""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100
    
    def get_profit_factor(self) -> float:
        """Calcula profit factor"""
        gross_profit = sum(t.net_pnl_usd for t in self.trades if t.is_profitable)
        gross_loss = abs(sum(t.net_pnl_usd for t in self.trades if not t.is_profitable))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0
        
        return gross_profit / gross_loss
    
    def get_avg_trade_usd(self) -> float:
        """Calcula trade médio em USD"""
        if self.total_trades == 0:
            return 0.0
        return sum(t.net_pnl_usd for t in self.trades) / self.total_trades
    
    def get_best_worst_trades(self) -> Tuple[Optional[Trade], Optional[Trade]]:
        """Retorna melhor e pior trade"""
        if not self.trades:
            return None, None
        
        best = max(self.trades, key=lambda t: t.net_pnl_usd)
        worst = min(self.trades, key=lambda t: t.net_pnl_usd)
        
        return best, worst
    
    def get_recent_trades(self, limit: int = 10) -> List[Trade]:
        """Retorna trades recentes"""
        return self.trades[-limit:] if self.trades else []
    
    def get_performance_summary(self) -> Dict:
        """Retorna resumo de performance"""
        total_return_usd = self.current_capital - self.initial_capital
        total_return_pct = (total_return_usd / self.initial_capital) * 100
        
        return {
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'total_return_usd': total_return_usd,
            'total_return_pct': total_return_pct,
            'max_capital_reached': self.max_capital_reached,
            'max_drawdown_usd': self.max_drawdown_usd,
            'max_drawdown_pct': self.max_drawdown_pct,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.get_win_rate(),
            'profit_factor': self.get_profit_factor(),
            'avg_trade_usd': self.get_avg_trade_usd(),
            'total_fees_paid': self.total_fees_paid,
            'position_size_pct': self.position_size_pct,
            'compound_interest': self.compound_interest
        }


class TradeSimulator:
    """Simulador de trades realistas"""
    
    def __init__(self):
        self.strategies = {
            'ema_crossover': {
                'win_rate': 0.58,
                'avg_win': 0.025,
                'avg_loss': -0.015,
                'avg_duration': 8.5
            },
            'rsi_mean_reversion': {
                'win_rate': 0.62,
                'avg_win': 0.018,
                'avg_loss': -0.012,
                'avg_duration': 4.2
            },
            'bollinger_breakout': {
                'win_rate': 0.52,
                'avg_win': 0.035,
                'avg_loss': -0.022,
                'avg_duration': 12.8
            },
            'ai_agent_bandit': {
                'win_rate': 0.65,
                'avg_win': 0.028,
                'avg_loss': -0.014,
                'avg_duration': 6.1
            }
        }
    
    def simulate_trade(self, strategy: str, position_size_usd: float, 
                      base_price: float = 50000) -> Trade:
        """Simula um trade realista"""
        import random
        
        if strategy not in self.strategies:
            strategy = 'ema_crossover'
        
        params = self.strategies[strategy]
        
        # Determinar se é win ou loss
        is_win = random.random() < params['win_rate']
        
        # Calcular retorno
        if is_win:
            return_pct = random.normalvariate(params['avg_win'], params['avg_win'] * 0.3)
        else:
            return_pct = random.normalvariate(params['avg_loss'], abs(params['avg_loss']) * 0.3)
        
        # Preços de entrada e saída
        entry_price = base_price * random.uniform(0.995, 1.005)  # Variação pequena
        exit_price = entry_price * (1 + return_pct)
        
        # Duração
        duration = random.normalvariate(params['avg_duration'], params['avg_duration'] * 0.4)
        duration = max(0.5, duration)  # Mínimo 30 minutos
        
        return Trade(
            strategy=strategy,
            entry_price=entry_price,
            exit_price=exit_price,
            position_size=position_size_usd,
            timestamp=datetime.now(),
            duration_hours=duration
        )


class MarketManusCapitalCLI:
    """Market Manus CLI com foco em tracking de capital"""
    
    def __init__(self):
        self.capital_tracker = None
        self.trade_simulator = TradeSimulator()
        self.setup()
    
    def setup(self):
        """Configuração inicial"""
        print("💰 Inicializando Capital Tracker...")
        
        # Configuração padrão
        initial_capital = 1000.0
        position_size_pct = 2.0
        compound_interest = True
        
        # Tentar carregar configuração salva
        config_file = PROJECT_ROOT / 'config' / 'capital_config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                initial_capital = config.get('initial_capital', 1000.0)
                position_size_pct = config.get('position_size_pct', 2.0)
                compound_interest = config.get('compound_interest', True)
            except Exception as e:
                logger.warning(f"Erro ao carregar config: {e}")
        
        self.capital_tracker = CapitalTracker(
            initial_capital=initial_capital,
            position_size_pct=position_size_pct,
            compound_interest=compound_interest
        )
        
        print(f"✅ Capital Tracker inicializado: ${initial_capital:,.2f}")
    
    def display_capital_dashboard(self):
        """Exibe dashboard detalhado do capital"""
        summary = self.capital_tracker.get_performance_summary()
        
        print("\n" + "="*80)
        print("💰 DASHBOARD DE CAPITAL - MARKET MANUS")
        print("="*80)
        
        # Capital atual vs inicial
        print(f"💵 Capital Inicial:     ${summary['initial_capital']:>12,.2f}")
        print(f"💰 Capital Atual:       ${summary['current_capital']:>12,.2f}")
        
        # Retorno total
        return_color = "🟢" if summary['total_return_usd'] >= 0 else "🔴"
        print(f"{return_color} Retorno Total:      ${summary['total_return_usd']:>+12,.2f} ({summary['total_return_pct']:>+6.2f}%)")
        
        # Máximo alcançado
        if summary['max_capital_reached'] > summary['initial_capital']:
            print(f"🏆 Máximo Alcançado:    ${summary['max_capital_reached']:>12,.2f}")
        
        # Drawdown
        if summary['max_drawdown_usd'] > 0:
            dd_color = "🟡" if summary['max_drawdown_pct'] < 10 else "🔴"
            print(f"{dd_color} Max Drawdown:       ${summary['max_drawdown_usd']:>12,.2f} ({summary['max_drawdown_pct']:>6.2f}%)")
        
        print("-" * 80)
        
        # Estatísticas de trading
        print(f"📊 Total de Trades:     {summary['total_trades']:>12}")
        if summary['total_trades'] > 0:
            print(f"✅ Trades Vencedores:   {summary['winning_trades']:>12} ({summary['win_rate']:>6.1f}%)")
            print(f"❌ Trades Perdedores:   {summary['losing_trades']:>12}")
            print(f"💎 Profit Factor:       {summary['profit_factor']:>12.2f}")
            print(f"📈 Trade Médio:         ${summary['avg_trade_usd']:>+12.2f}")
            print(f"💸 Fees Pagos:          ${summary['total_fees_paid']:>12.2f}")
        
        print("-" * 80)
        
        # Configurações
        print(f"⚙️ Position Size:       {summary['position_size_pct']:>12.1f}%")
        compound_status = "Ativo" if summary['compound_interest'] else "Inativo"
        print(f"🔄 Compound Interest:   {compound_status:>12}")
        
        # Position size atual
        current_position_usd = self.capital_tracker.get_position_size_usd()
        print(f"💼 Próxima Posição:     ${current_position_usd:>12,.2f}")
        
        print("="*80)
    
    def display_recent_trades(self, limit: int = 5):
        """Exibe trades recentes"""
        recent_trades = self.capital_tracker.get_recent_trades(limit)
        
        if not recent_trades:
            print("\n📊 Nenhum trade executado ainda.")
            return
        
        print(f"\n📊 ÚLTIMOS {len(recent_trades)} TRADES")
        print("="*80)
        print(f"{'#':<3} {'Estratégia':<20} {'P&L USD':<12} {'P&L %':<8} {'Duração':<10} {'Status':<6}")
        print("-"*80)
        
        for i, trade in enumerate(reversed(recent_trades), 1):
            status = "✅ WIN" if trade.is_profitable else "❌ LOSS"
            duration_str = f"{trade.duration_hours:.1f}h"
            
            print(f"{i:<3} {trade.strategy:<20} ${trade.net_pnl_usd:>+10.2f} "
                  f"{trade.pnl_pct*100:>+6.2f}% {duration_str:<10} {status}")
        
        # Resumo dos trades mostrados
        total_pnl = sum(t.net_pnl_usd for t in recent_trades)
        wins = sum(1 for t in recent_trades if t.is_profitable)
        
        print("-"*80)
        print(f"📊 Resumo: {wins}/{len(recent_trades)} wins | Total P&L: ${total_pnl:+.2f}")
        print("="*80)
    
    def display_best_worst_trades(self):
        """Exibe melhor e pior trade"""
        best, worst = self.capital_tracker.get_best_worst_trades()
        
        if not best or not worst:
            print("\n📊 Nenhum trade para análise ainda.")
            return
        
        print("\n🏆 MELHOR E PIOR TRADE")
        print("="*50)
        
        print(f"🏆 MELHOR TRADE:")
        print(f"   Estratégia: {best.strategy}")
        print(f"   P&L: ${best.net_pnl_usd:+.2f} ({best.pnl_pct*100:+.2f}%)")
        print(f"   Duração: {best.duration_hours:.1f}h")
        print(f"   Data: {best.timestamp.strftime('%d/%m/%Y %H:%M')}")
        
        print(f"\n💸 PIOR TRADE:")
        print(f"   Estratégia: {worst.strategy}")
        print(f"   P&L: ${worst.net_pnl_usd:+.2f} ({worst.pnl_pct*100:+.2f}%)")
        print(f"   Duração: {worst.duration_hours:.1f}h")
        print(f"   Data: {worst.timestamp.strftime('%d/%m/%Y %H:%M')}")
        
        print("="*50)
    
    def simulate_single_trade(self):
        """Simula um único trade"""
        print("\n🎯 SIMULAÇÃO DE TRADE ÚNICO")
        print("="*40)
        
        # Escolher estratégia
        strategies = list(self.trade_simulator.strategies.keys())
        print("Estratégias disponíveis:")
        for i, strategy in enumerate(strategies, 1):
            print(f"{i}. {strategy.replace('_', ' ').title()}")
        
        try:
            choice = int(input("\n🔢 Escolha a estratégia (1-4): ")) - 1
            if 0 <= choice < len(strategies):
                strategy = strategies[choice]
            else:
                strategy = strategies[0]
                print(f"⚠️ Opção inválida, usando {strategy}")
        except ValueError:
            strategy = strategies[0]
            print(f"⚠️ Entrada inválida, usando {strategy}")
        
        # Calcular position size
        position_size = self.capital_tracker.get_position_size_usd()
        
        print(f"\n🔄 Simulando trade com {strategy.replace('_', ' ').title()}...")
        print(f"💼 Position Size: ${position_size:,.2f}")
        
        # Simular trade
        trade = self.trade_simulator.simulate_trade(strategy, position_size)
        
        # Executar trade
        capital_change = self.capital_tracker.execute_trade(trade)
        
        # Exibir resultado
        print(f"\n📊 RESULTADO DO TRADE")
        print("-"*30)
        print(f"Estratégia: {trade.strategy.replace('_', ' ').title()}")
        print(f"Entrada: ${trade.entry_price:,.2f}")
        print(f"Saída: ${trade.exit_price:,.2f}")
        print(f"Duração: {trade.duration_hours:.1f} horas")
        print(f"P&L Bruto: ${trade.pnl_usd:+.2f} ({trade.pnl_pct*100:+.2f}%)")
        print(f"Fees: ${trade.fees_usd:.2f}")
        print(f"P&L Líquido: ${trade.net_pnl_usd:+.2f}")
        
        # Impacto no capital
        print(f"\n💰 IMPACTO NO CAPITAL")
        print("-"*25)
        print(f"Capital Anterior: ${capital_change['old_capital']:,.2f}")
        print(f"Capital Atual: ${capital_change['new_capital']:,.2f}")
        
        change_color = "🟢" if capital_change['change_usd'] >= 0 else "🔴"
        print(f"{change_color} Mudança: ${capital_change['change_usd']:+.2f} ({capital_change['change_pct']:+.2f}%)")
        
        # Status do trade
        if trade.is_profitable:
            print("\n✅ TRADE VENCEDOR! 🎉")
        else:
            print("\n❌ Trade perdedor 😞")
        
        # Alertas especiais
        summary = self.capital_tracker.get_performance_summary()
        
        if summary['current_capital'] > summary['max_capital_reached'] * 0.99:
            print("🏆 NOVO MÁXIMO DE CAPITAL ALCANÇADO!")
        
        if summary['max_drawdown_pct'] > 10:
            print("⚠️ ATENÇÃO: Drawdown acima de 10%!")
        
        if summary['total_return_pct'] > 20:
            print("🚀 EXCELENTE! Retorno acima de 20%!")
    
    def simulate_multiple_trades(self):
        """Simula múltiplos trades"""
        print("\n🔄 SIMULAÇÃO DE MÚLTIPLOS TRADES")
        print("="*45)
        
        try:
            num_trades = int(input("📊 Quantos trades simular (1-20): "))
            num_trades = max(1, min(20, num_trades))
        except ValueError:
            num_trades = 5
            print("⚠️ Entrada inválida, simulando 5 trades")
        
        print(f"\n🔄 Simulando {num_trades} trades...")
        
        # Capital inicial para comparação
        initial_capital = self.capital_tracker.current_capital
        
        # Simular trades
        strategies = list(self.trade_simulator.strategies.keys())
        
        for i in range(num_trades):
            # Escolher estratégia aleatoriamente
            import random
            strategy = random.choice(strategies)
            
            # Position size atual
            position_size = self.capital_tracker.get_position_size_usd()
            
            # Simular e executar trade
            trade = self.trade_simulator.simulate_trade(strategy, position_size)
            capital_change = self.capital_tracker.execute_trade(trade)
            
            # Mostrar progresso
            status = "✅" if trade.is_profitable else "❌"
            print(f"   Trade {i+1:2d}: {strategy:<20} {status} ${trade.net_pnl_usd:>+8.2f} | Capital: ${capital_change['new_capital']:>8,.0f}")
        
        # Resumo final
        final_capital = self.capital_tracker.current_capital
        total_change = final_capital - initial_capital
        total_change_pct = (total_change / initial_capital) * 100
        
        print(f"\n📊 RESUMO DA SIMULAÇÃO")
        print("-"*35)
        print(f"Capital Inicial: ${initial_capital:,.2f}")
        print(f"Capital Final: ${final_capital:,.2f}")
        
        change_color = "🟢" if total_change >= 0 else "🔴"
        print(f"{change_color} Mudança Total: ${total_change:+.2f} ({total_change_pct:+.2f}%)")
        
        # Estatísticas da simulação
        recent_trades = self.capital_tracker.get_recent_trades(num_trades)
        wins = sum(1 for t in recent_trades if t.is_profitable)
        win_rate = (wins / num_trades) * 100
        
        print(f"Win Rate: {wins}/{num_trades} ({win_rate:.1f}%)")
        
        if total_change > 0:
            print("🎉 SIMULAÇÃO LUCRATIVA!")
        else:
            print("😞 Simulação com prejuízo")
    
    def configure_capital(self):
        """Configura capital e parâmetros"""
        print("\n⚙️ CONFIGURAÇÃO DE CAPITAL")
        print("="*40)
        
        current_summary = self.capital_tracker.get_performance_summary()
        
        print(f"Capital atual: ${current_summary['current_capital']:,.2f}")
        print(f"Position size atual: {current_summary['position_size_pct']:.1f}%")
        print(f"Compound interest: {'Ativo' if current_summary['compound_interest'] else 'Inativo'}")
        
        print("\n1. Resetar capital para novo valor")
        print("2. Ajustar position size")
        print("3. Alternar compound interest")
        print("0. Voltar")
        
        choice = input("\n🔢 Escolha: ")
        
        if choice == '1':
            self._reset_capital()
        elif choice == '2':
            self._adjust_position_size()
        elif choice == '3':
            self._toggle_compound_interest()
        elif choice == '0':
            return
        else:
            print("❌ Opção inválida")
    
    def _reset_capital(self):
        """Reseta capital para novo valor"""
        try:
            new_capital = float(input("\n💵 Novo capital inicial ($1 - $100,000): $"))
            
            if not (1 <= new_capital <= 100000):
                print("❌ Capital deve estar entre $1 e $100,000")
                return
            
            confirm = input(f"⚠️ Isso resetará todo o histórico. Confirma? (s/N): ")
            if confirm.lower().startswith('s'):
                # Salvar configuração
                self._save_config(new_capital, self.capital_tracker.position_size_pct, 
                                self.capital_tracker.compound_interest)
                
                # Recriar tracker
                self.capital_tracker = CapitalTracker(
                    initial_capital=new_capital,
                    position_size_pct=self.capital_tracker.position_size_pct,
                    compound_interest=self.capital_tracker.compound_interest
                )
                
                print(f"✅ Capital resetado para ${new_capital:,.2f}")
            else:
                print("❌ Operação cancelada")
                
        except ValueError:
            print("❌ Valor inválido")
    
    def _adjust_position_size(self):
        """Ajusta position size"""
        try:
            new_size = float(input("\n📊 Novo position size (0.1% - 10%): "))
            
            if not (0.1 <= new_size <= 10):
                print("❌ Position size deve estar entre 0.1% e 10%")
                return
            
            self.capital_tracker.position_size_pct = new_size
            
            # Salvar configuração
            self._save_config(self.capital_tracker.initial_capital, new_size, 
                            self.capital_tracker.compound_interest)
            
            print(f"✅ Position size ajustado para {new_size:.1f}%")
            
            # Mostrar novo tamanho de posição
            new_position_usd = self.capital_tracker.get_position_size_usd()
            print(f"💼 Nova posição: ${new_position_usd:,.2f}")
            
        except ValueError:
            print("❌ Valor inválido")
    
    def _toggle_compound_interest(self):
        """Alterna compound interest"""
        current = self.capital_tracker.compound_interest
        new_value = not current
        
        self.capital_tracker.compound_interest = new_value
        
        # Salvar configuração
        self._save_config(self.capital_tracker.initial_capital, 
                        self.capital_tracker.position_size_pct, new_value)
        
        status = "Ativado" if new_value else "Desativado"
        print(f"✅ Compound interest {status}")
        
        if new_value:
            print("💡 Posições futuras usarão capital atual como base")
        else:
            print("💡 Posições futuras usarão capital inicial como base")
    
    def _save_config(self, capital: float, position_size: float, compound: bool):
        """Salva configuração"""
        try:
            config_dir = PROJECT_ROOT / 'config'
            config_dir.mkdir(exist_ok=True)
            
            config_data = {
                'initial_capital': capital,
                'position_size_pct': position_size,
                'compound_interest': compound,
                'updated_at': datetime.now().isoformat()
            }
            
            config_file = config_dir / 'capital_config.json'
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
        except Exception as e:
            logger.warning(f"Erro ao salvar configuração: {e}")
    
    def display_main_menu(self):
        """Exibe menu principal"""
        print("\n" + "="*80)
        print("💰 MARKET MANUS - CAPITAL TRACKING CLI")
        print("="*80)
        print("🎯 Foco: Como as operações afetam seu capital inicial")
        print("📊 Tracking completo de P&L em tempo real")
        print("🔄 Simulação realista com compound interest")
        print("="*80)
        
        print("\n🎯 MENU PRINCIPAL")
        print("="*30)
        print("   1️⃣  Dashboard de Capital")
        print("   2️⃣  Simular Trade Único")
        print("   3️⃣  Simular Múltiplos Trades")
        print("   4️⃣  Histórico de Trades")
        print("   5️⃣  Melhor/Pior Trade")
        print("   6️⃣  Configurar Capital")
        print("   7️⃣  Resetar Histórico")
        print("   0️⃣  Sair")
        print()
    
    def reset_history(self):
        """Reseta histórico mantendo configurações"""
        print("\n🔄 RESETAR HISTÓRICO")
        print("="*30)
        
        summary = self.capital_tracker.get_performance_summary()
        print(f"Trades atuais: {summary['total_trades']}")
        print(f"Capital atual: ${summary['current_capital']:,.2f}")
        
        confirm = input("\n⚠️ Resetar histórico de trades? (s/N): ")
        if confirm.lower().startswith('s'):
            # Manter configurações, resetar histórico
            self.capital_tracker = CapitalTracker(
                initial_capital=self.capital_tracker.initial_capital,
                position_size_pct=self.capital_tracker.position_size_pct,
                compound_interest=self.capital_tracker.compound_interest
            )
            
            print("✅ Histórico resetado!")
            print(f"💰 Capital voltou para ${self.capital_tracker.initial_capital:,.2f}")
        else:
            print("❌ Operação cancelada")
    
    def run(self):
        """Loop principal"""
        print("\n🚀 Bem-vindo ao Market Manus Capital Tracking CLI!")
        print("💡 Veja em tempo real como cada trade afeta seu capital")
        
        try:
            while True:
                self.display_main_menu()
                
                choice = input("🔢 Escolha uma opção: ").strip()
                
                if choice == '1':
                    self.display_capital_dashboard()
                elif choice == '2':
                    self.simulate_single_trade()
                elif choice == '3':
                    self.simulate_multiple_trades()
                elif choice == '4':
                    self.display_recent_trades(10)
                elif choice == '5':
                    self.display_best_worst_trades()
                elif choice == '6':
                    self.configure_capital()
                elif choice == '7':
                    self.reset_history()
                elif choice == '0':
                    print("\n👋 Obrigado por usar o Market Manus Capital Tracking!")
                    print("💰 Continue acompanhando a evolução do seu capital!")
                    break
                else:
                    print("❌ Opção inválida")
                
                if choice != '0':
                    input("\n📖 Pressione ENTER para continuar...")
                    
        except KeyboardInterrupt:
            print("\n\n👋 CLI encerrado pelo usuário. Até logo!")
        except Exception as e:
            logger.error(f"Erro no loop principal: {e}")
            print(f"\n❌ Erro inesperado: {e}")


if __name__ == "__main__":
    try:
        cli = MarketManusCapitalCLI()
        cli.run()
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        print(f"❌ Erro fatal: {e}")
        sys.exit(1)

