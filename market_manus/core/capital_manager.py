#!/usr/bin/env python3
"""
Capital Manager - Fixed Version
Includes the missing get_capital_summary method and all required functionality
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import numpy as np

class CapitalManager:
    """
    Capital Manager com lógica financeira correta e método get_capital_summary
    """
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.position_size_percent = 2.0  # 2% do capital por trade
        
        # Histórico de trades
        self.trades = []
        self.total_profit = 0.0
        self.total_loss = 0.0
        self.winning_trades = 0
        self.losing_trades = 0
        
        # Métricas de risco
        self.max_drawdown = 0.0
        self.peak_capital = initial_capital
        self.daily_returns = []
        
        # Configurações
        self.config_file = "config/capital_config.json"
        self.data_file = "capital_data.json"
        
        # Carregar dados salvos
        self.load_capital_data()
    
    def get_capital_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo completo do capital - MÉTODO QUE ESTAVA FALTANDO
        """
        total_trades = self.winning_trades + self.losing_trades
        win_rate = (self.winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = self.current_capital - self.initial_capital
        roi = (total_pnl / self.initial_capital * 100) if self.initial_capital > 0 else 0
        
        # Calcular Sharpe Ratio
        sharpe_ratio = self.calculate_sharpe_ratio()
        
        # Calcular Profit Factor
        profit_factor = (self.total_profit / abs(self.total_loss)) if self.total_loss != 0 else float('inf')
        
        return {
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'total_pnl': total_pnl,
            'roi': roi,
            'position_size_percent': self.position_size_percent,
            'position_size_usd': self.current_capital * (self.position_size_percent / 100),
            'total_trades': total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'total_profit': self.total_profit,
            'total_loss': self.total_loss,
            'profit_factor': profit_factor,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'peak_capital': self.peak_capital
        }
    
    def update_capital(self, trade_pnl: float, trade_details: Optional[Dict] = None):
        """
        Atualiza o capital após um trade - MÉTODO CORRIGIDO
        """
        # Atualizar capital
        self.current_capital += trade_pnl
        
        # Atualizar estatísticas
        if trade_pnl > 0:
            self.winning_trades += 1
            self.total_profit += trade_pnl
        else:
            self.losing_trades += 1
            self.total_loss += trade_pnl
        
        # Atualizar peak capital e drawdown
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital
        
        # Calcular drawdown atual
        current_drawdown = ((self.peak_capital - self.current_capital) / self.peak_capital) * 100
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown
        
        # Registrar trade
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'pnl': trade_pnl,
            'capital_before': self.current_capital - trade_pnl,
            'capital_after': self.current_capital,
            'drawdown': current_drawdown,
            'details': trade_details or {}
        }
        
        self.trades.append(trade_record)
        
        # Salvar dados
        self.save_capital_data()
        
        return trade_record
    
    def execute_trade(self, signal_action: str, entry_price: float, exit_price: float, 
                     confidence: float = 1.0, strategy_name: str = "Unknown") -> Dict[str, Any]:
        """
        Executa um trade completo com lógica financeira correta
        """
        # Calcular position size baseado no capital ATUAL
        position_size_usd = self.current_capital * (self.position_size_percent / 100)
        
        # Calcular quantidade baseada no preço de entrada
        quantity = position_size_usd / entry_price
        
        # Calcular P&L baseado na direção do sinal
        if signal_action.upper() == 'BUY':
            # Long position: lucro quando preço sobe
            pnl_percent = (exit_price - entry_price) / entry_price
        elif signal_action.upper() == 'SELL':
            # Short position: lucro quando preço desce
            pnl_percent = (entry_price - exit_price) / entry_price
        else:
            # Sinal inválido
            return {'error': f'Ação inválida: {signal_action}'}
        
        # Calcular P&L em USD
        trade_pnl = position_size_usd * pnl_percent
        
        # Detalhes do trade
        trade_details = {
            'strategy': strategy_name,
            'action': signal_action.upper(),
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantity,
            'position_size_usd': position_size_usd,
            'pnl_percent': pnl_percent * 100,
            'confidence': confidence
        }
        
        # Atualizar capital
        trade_record = self.update_capital(trade_pnl, trade_details)
        
        # Retornar resultado completo
        return {
            'success': True,
            'trade_pnl': trade_pnl,
            'pnl_percent': pnl_percent * 100,
            'new_capital': self.current_capital,
            'position_size': position_size_usd,
            'details': trade_details,
            'record': trade_record
        }
    
    def calculate_sharpe_ratio(self) -> float:
        """
        Calcula Sharpe Ratio baseado nos retornos dos trades
        """
        if len(self.trades) < 2:
            return 0.0
        
        # Calcular retornos percentuais
        returns = []
        for trade in self.trades:
            if trade['capital_before'] > 0:
                trade_return = (trade['pnl'] / trade['capital_before']) * 100
                returns.append(trade_return)
        
        if len(returns) < 2:
            return 0.0
        
        # Calcular Sharpe Ratio
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        # Assumindo risk-free rate de 0% para simplificar
        sharpe_ratio = mean_return / std_return
        return sharpe_ratio
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """
        Calcula todas as métricas de performance
        """
        summary = self.get_capital_summary()
        
        # Métricas adicionais
        if len(self.trades) > 0:
            # Maior ganho e perda
            profits = [t['pnl'] for t in self.trades if t['pnl'] > 0]
            losses = [t['pnl'] for t in self.trades if t['pnl'] < 0]
            
            summary['largest_win'] = max(profits) if profits else 0.0
            summary['largest_loss'] = min(losses) if losses else 0.0
            
            # Média de ganhos e perdas
            summary['avg_win'] = np.mean(profits) if profits else 0.0
            summary['avg_loss'] = np.mean(losses) if losses else 0.0
            
            # Sequências
            summary['max_consecutive_wins'] = self.calculate_max_consecutive_wins()
            summary['max_consecutive_losses'] = self.calculate_max_consecutive_losses()
        
        return summary
    
    def calculate_max_consecutive_wins(self) -> int:
        """Calcula máximo de vitórias consecutivas"""
        max_wins = 0
        current_wins = 0
        
        for trade in self.trades:
            if trade['pnl'] > 0:
                current_wins += 1
                max_wins = max(max_wins, current_wins)
            else:
                current_wins = 0
        
        return max_wins
    
    def calculate_max_consecutive_losses(self) -> int:
        """Calcula máximo de perdas consecutivas"""
        max_losses = 0
        current_losses = 0
        
        for trade in self.trades:
            if trade['pnl'] < 0:
                current_losses += 1
                max_losses = max(max_losses, current_losses)
            else:
                current_losses = 0
        
        return max_losses
    
    def set_initial_capital(self, capital: float):
        """
        Define capital inicial
        """
        if capital <= 0:
            raise ValueError("Capital inicial deve ser maior que zero")
        
        self.initial_capital = capital
        self.current_capital = capital
        self.peak_capital = capital
        
        # Reset das estatísticas
        self.trades = []
        self.total_profit = 0.0
        self.total_loss = 0.0
        self.winning_trades = 0
        self.losing_trades = 0
        self.max_drawdown = 0.0
        
        self.save_capital_data()
    
    def set_position_size_percent(self, percent: float):
        """
        Define percentual do capital por trade
        """
        if not 0.1 <= percent <= 10.0:
            raise ValueError("Position size deve estar entre 0.1% e 10%")
        
        self.position_size_percent = percent
        self.save_capital_data()
    
    def reset_capital(self):
        """
        Reset completo do capital
        """
        self.current_capital = self.initial_capital
        self.peak_capital = self.initial_capital
        self.trades = []
        self.total_profit = 0.0
        self.total_loss = 0.0
        self.winning_trades = 0
        self.losing_trades = 0
        self.max_drawdown = 0.0
        
        self.save_capital_data()
    
    def save_capital_data(self):
        """
        Salva dados do capital em arquivo JSON
        """
        try:
            data = {
                'initial_capital': self.initial_capital,
                'current_capital': self.current_capital,
                'position_size_percent': self.position_size_percent,
                'peak_capital': self.peak_capital,
                'max_drawdown': self.max_drawdown,
                'total_profit': self.total_profit,
                'total_loss': self.total_loss,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'trades': self.trades[-100:],  # Manter apenas últimos 100 trades
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Erro ao salvar dados do capital: {e}")
    
    def load_capital_data(self):
        """
        Carrega dados do capital do arquivo JSON
        """
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                
                self.initial_capital = data.get('initial_capital', 10000.0)
                self.current_capital = data.get('current_capital', self.initial_capital)
                self.position_size_percent = data.get('position_size_percent', 2.0)
                self.peak_capital = data.get('peak_capital', self.initial_capital)
                self.max_drawdown = data.get('max_drawdown', 0.0)
                self.total_profit = data.get('total_profit', 0.0)
                self.total_loss = data.get('total_loss', 0.0)
                self.winning_trades = data.get('winning_trades', 0)
                self.losing_trades = data.get('losing_trades', 0)
                self.trades = data.get('trades', [])
                
        except Exception as e:
            print(f"⚠️ Erro ao carregar dados do capital: {e}")
            # Usar valores padrão se houver erro
            pass
    
    def export_report(self, filename: Optional[str] = None) -> str:
        """
        Exporta relatório completo do capital
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capital_report_{timestamp}.json"
        
        try:
            # Criar diretório de relatórios se não existir
            os.makedirs("reports", exist_ok=True)
            filepath = os.path.join("reports", filename)
            
            # Preparar dados do relatório
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'summary': self.get_capital_summary(),
                'metrics': self.calculate_metrics(),
                'recent_trades': self.trades[-20:],  # Últimos 20 trades
                'configuration': {
                    'initial_capital': self.initial_capital,
                    'position_size_percent': self.position_size_percent
                }
            }
            
            # Salvar relatório
            with open(filepath, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            return filepath
            
        except Exception as e:
            raise Exception(f"Erro ao exportar relatório: {e}")
    
    def __str__(self) -> str:
        """
        Representação string do Capital Manager
        """
        summary = self.get_capital_summary()
        return f"CapitalManager(Capital: ${summary['current_capital']:,.2f}, ROI: {summary['roi']:+.2f}%, Trades: {summary['total_trades']})"
    
    def __repr__(self) -> str:
        return self.__str__()

# Função de teste
def test_capital_manager():
    """
    Teste básico do Capital Manager
    """
    print("🧪 Testando Capital Manager...")
    
    # Criar instância
    cm = CapitalManager(10000.0)
    
    # Testar get_capital_summary
    summary = cm.get_capital_summary()
    print(f"✅ Capital inicial: ${summary['current_capital']:,.2f}")
    
    # Testar trade vencedor
    trade1 = cm.execute_trade('BUY', 100.0, 103.0, strategy_name='Test Strategy')
    print(f"✅ Trade 1 (BUY): P&L = ${trade1['trade_pnl']:+.2f}")
    
    # Testar trade perdedor
    trade2 = cm.execute_trade('SELL', 100.0, 102.0, strategy_name='Test Strategy')
    print(f"✅ Trade 2 (SELL): P&L = ${trade2['trade_pnl']:+.2f}")
    
    # Verificar métricas
    final_summary = cm.get_capital_summary()
    print(f"✅ Capital final: ${final_summary['current_capital']:,.2f}")
    print(f"✅ ROI: {final_summary['roi']:+.2f}%")
    print(f"✅ Win Rate: {final_summary['win_rate']:.1f}%")
    
    print("🎉 Teste concluído com sucesso!")

if __name__ == "__main__":
    test_capital_manager()
