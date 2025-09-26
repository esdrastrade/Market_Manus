"""
Capital Manager - Módulo de Gerenciamento de Capital
Localização: market_manus/core/capital_manager.py
Data: 24/09/2025

FUNCIONALIDADES:
✅ Gerenciamento de capital com tracking completo
✅ Position sizing automático
✅ Cálculo de P&L em tempo real
✅ Controle de drawdown
✅ Histórico de trades
✅ Métricas de performance
✅ Integração com compliance
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class CapitalManager:
    """Gerenciador de capital com tracking completo"""
    
    def __init__(self, initial_capital: float = 10000.0, position_size_pct: float = 0.02):
        """
        Inicializa o gerenciador de capital
        
        Args:
            initial_capital: Capital inicial em USD
            position_size_pct: Percentual do capital por trade (0.02 = 2%)
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.position_size_pct = position_size_pct
        
        # Histórico de trades
        self.trades_history = []
        
        # Métricas de performance
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_capital = initial_capital
        
        # Configurações de risco
        self.max_position_size_pct = 0.10  # Máximo 10% por trade
        self.max_drawdown_limit = 0.20     # Máximo 20% de drawdown
        self.max_daily_trades = 50         # Máximo 50 trades por dia
        
        # Controle diário
        self.daily_trades_count = 0
        self.last_trade_date = None
        
        # Arquivo de persistência
        self.data_file = Path("capital_data.json")
        self._load_data()
    
    def get_position_size(self) -> float:
        """Calcula o position size baseado no capital atual"""
        return self.current_capital * self.position_size_pct
    
    def can_trade(self) -> Tuple[bool, str]:
        """
        Verifica se pode executar um trade baseado nas regras de compliance
        
        Returns:
            Tuple[bool, str]: (pode_tradear, motivo_se_nao_pode)
        """
        # Verificar drawdown máximo
        current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
        if current_drawdown > self.max_drawdown_limit:
            return False, f"Drawdown máximo excedido ({current_drawdown:.1%} > {self.max_drawdown_limit:.1%})"
        
        # Verificar capital mínimo
        if self.current_capital < self.initial_capital * 0.1:  # Mínimo 10% do capital inicial
            return False, "Capital insuficiente (< 10% do inicial)"
        
        # Verificar limite diário de trades
        today = datetime.now().date()
        if self.last_trade_date != today:
            self.daily_trades_count = 0
            self.last_trade_date = today
        
        if self.daily_trades_count >= self.max_daily_trades:
            return False, f"Limite diário de trades excedido ({self.daily_trades_count}/{self.max_daily_trades})"
        
        # Verificar position size
        position_size = self.get_position_size()
        max_position = self.current_capital * self.max_position_size_pct
        if position_size > max_position:
            return False, f"Position size muito grande ({position_size:.2f} > {max_position:.2f})"
        
        return True, "OK"
    
    def execute_trade(self, 
                     action: str, 
                     symbol: str, 
                     entry_price: float, 
                     exit_price: float = None,
                     strategy: str = "Unknown",
                     notes: str = "") -> Dict:
        """
        Executa um trade e atualiza o capital
        
        Args:
            action: "BUY" ou "SELL"
            symbol: Símbolo do ativo (ex: "BTCUSDT")
            entry_price: Preço de entrada
            exit_price: Preço de saída (se None, será definido posteriormente)
            strategy: Nome da estratégia utilizada
            notes: Notas adicionais
            
        Returns:
            Dict: Informações do trade executado
        """
        # Verificar se pode tradear
        can_trade, reason = self.can_trade()
        if not can_trade:
            return {
                "success": False,
                "reason": reason,
                "trade_id": None
            }
        
        # Calcular position size
        position_size = self.get_position_size()
        
        # Simular execução do trade
        if exit_price is not None:
            # Trade completo - calcular P&L
            if action == "BUY":
                pnl_pct = (exit_price - entry_price) / entry_price
            else:  # SELL
                pnl_pct = (entry_price - exit_price) / entry_price
            
            pnl_amount = position_size * pnl_pct
            
            # Atualizar capital
            self.current_capital += pnl_amount
            self.total_pnl += pnl_amount
            
            # Atualizar estatísticas
            self.total_trades += 1
            self.daily_trades_count += 1
            
            if pnl_amount > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1
            
            # Atualizar peak capital e drawdown
            if self.current_capital > self.peak_capital:
                self.peak_capital = self.current_capital
            
            current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
            if current_drawdown > self.max_drawdown:
                self.max_drawdown = current_drawdown
        else:
            # Trade aberto - apenas registrar
            pnl_amount = 0.0
            pnl_pct = 0.0
        
        # Criar registro do trade
        trade_record = {
            "trade_id": f"T{int(time.time())}{self.total_trades:03d}",
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "symbol": symbol,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "position_size": position_size,
            "pnl_amount": pnl_amount,
            "pnl_pct": pnl_pct * 100,  # Converter para percentual
            "strategy": strategy,
            "notes": notes,
            "capital_before": self.current_capital - pnl_amount,
            "capital_after": self.current_capital
        }
        
        # Adicionar ao histórico
        self.trades_history.append(trade_record)
        
        # Salvar dados
        self._save_data()
        
        return {
            "success": True,
            "trade_id": trade_record["trade_id"],
            "pnl_amount": pnl_amount,
            "pnl_pct": pnl_pct * 100,
            "new_capital": self.current_capital
        }
    
    def close_trade(self, trade_id: str, exit_price: float) -> Dict:
        """
        Fecha um trade aberto
        
        Args:
            trade_id: ID do trade a ser fechado
            exit_price: Preço de saída
            
        Returns:
            Dict: Resultado do fechamento
        """
        # Encontrar o trade
        trade = None
        for t in self.trades_history:
            if t["trade_id"] == trade_id and t["exit_price"] is None:
                trade = t
                break
        
        if not trade:
            return {
                "success": False,
                "reason": "Trade não encontrado ou já fechado"
            }
        
        # Calcular P&L
        entry_price = trade["entry_price"]
        position_size = trade["position_size"]
        action = trade["action"]
        
        if action == "BUY":
            pnl_pct = (exit_price - entry_price) / entry_price
        else:  # SELL
            pnl_pct = (entry_price - exit_price) / entry_price
        
        pnl_amount = position_size * pnl_pct
        
        # Atualizar capital
        self.current_capital += pnl_amount
        self.total_pnl += pnl_amount
        
        # Atualizar trade
        trade["exit_price"] = exit_price
        trade["pnl_amount"] = pnl_amount
        trade["pnl_pct"] = pnl_pct * 100
        trade["capital_after"] = self.current_capital
        trade["closed_at"] = datetime.now().isoformat()
        
        # Atualizar estatísticas
        if pnl_amount > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        # Atualizar peak capital e drawdown
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital
        
        current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown
        
        # Salvar dados
        self._save_data()
        
        return {
            "success": True,
            "trade_id": trade_id,
            "pnl_amount": pnl_amount,
            "pnl_pct": pnl_pct * 100,
            "new_capital": self.current_capital
        }
    
    def get_stats(self) -> Dict:
        """
        Obtém estatísticas completas do capital
        
        Returns:
            Dict: Estatísticas detalhadas
        """
        total_return = ((self.current_capital - self.initial_capital) / self.initial_capital) * 100
        win_rate = (self.winning_trades / max(self.total_trades, 1)) * 100
        
        # Calcular métricas adicionais
        avg_win = 0.0
        avg_loss = 0.0
        
        if self.trades_history:
            winning_trades_pnl = [t["pnl_amount"] for t in self.trades_history if t["pnl_amount"] > 0]
            losing_trades_pnl = [t["pnl_amount"] for t in self.trades_history if t["pnl_amount"] < 0]
            
            if winning_trades_pnl:
                avg_win = sum(winning_trades_pnl) / len(winning_trades_pnl)
            
            if losing_trades_pnl:
                avg_loss = sum(losing_trades_pnl) / len(losing_trades_pnl)
        
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        return {
            "initial_capital": self.initial_capital,
            "current_capital": self.current_capital,
            "total_pnl": self.total_pnl,
            "total_return": total_return,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": win_rate,
            "max_drawdown": self.max_drawdown * 100,  # Converter para percentual
            "peak_capital": self.peak_capital,
            "position_size": self.get_position_size(),
            "position_size_pct": self.position_size_pct * 100,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "daily_trades_count": self.daily_trades_count,
            "max_daily_trades": self.max_daily_trades
        }
    
    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """
        Obtém os trades mais recentes
        
        Args:
            limit: Número máximo de trades a retornar
            
        Returns:
            List[Dict]: Lista dos trades mais recentes
        """
        return self.trades_history[-limit:] if self.trades_history else []
    
    def get_trades_by_strategy(self, strategy: str) -> List[Dict]:
        """
        Obtém trades filtrados por estratégia
        
        Args:
            strategy: Nome da estratégia
            
        Returns:
            List[Dict]: Lista de trades da estratégia
        """
        return [t for t in self.trades_history if t["strategy"] == strategy]
    
    def get_daily_pnl(self, date: str = None) -> float:
        """
        Obtém P&L de um dia específico
        
        Args:
            date: Data no formato YYYY-MM-DD (se None, usa hoje)
            
        Returns:
            float: P&L do dia
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        daily_pnl = 0.0
        for trade in self.trades_history:
            trade_date = trade["timestamp"][:10]  # Extrair YYYY-MM-DD
            if trade_date == date and trade["pnl_amount"] is not None:
                daily_pnl += trade["pnl_amount"]
        
        return daily_pnl
    
    def reset_capital(self):
        """Reseta o capital para o valor inicial"""
        self.current_capital = self.initial_capital
        self.total_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.max_drawdown = 0.0
        self.peak_capital = self.initial_capital
        self.trades_history = []
        self.daily_trades_count = 0
        self._save_data()
    
    def update_position_size(self, new_pct: float):
        """
        Atualiza o percentual de position size
        
        Args:
            new_pct: Novo percentual (0.01 = 1%)
        """
        if 0.001 <= new_pct <= self.max_position_size_pct:
            self.position_size_pct = new_pct
            self._save_data()
            return True
        return False
    
    def _save_data(self):
        """Salva dados no arquivo JSON"""
        try:
            data = {
                "initial_capital": self.initial_capital,
                "current_capital": self.current_capital,
                "position_size_pct": self.position_size_pct,
                "total_trades": self.total_trades,
                "winning_trades": self.winning_trades,
                "losing_trades": self.losing_trades,
                "total_pnl": self.total_pnl,
                "max_drawdown": self.max_drawdown,
                "peak_capital": self.peak_capital,
                "daily_trades_count": self.daily_trades_count,
                "last_trade_date": self.last_trade_date.isoformat() if self.last_trade_date else None,
                "trades_history": self.trades_history[-1000:]  # Manter apenas os últimos 1000 trades
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ Erro ao salvar dados do capital: {e}")
    
    def _load_data(self):
        """Carrega dados do arquivo JSON"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                
                self.initial_capital = data.get("initial_capital", self.initial_capital)
                self.current_capital = data.get("current_capital", self.current_capital)
                self.position_size_pct = data.get("position_size_pct", self.position_size_pct)
                self.total_trades = data.get("total_trades", 0)
                self.winning_trades = data.get("winning_trades", 0)
                self.losing_trades = data.get("losing_trades", 0)
                self.total_pnl = data.get("total_pnl", 0.0)
                self.max_drawdown = data.get("max_drawdown", 0.0)
                self.peak_capital = data.get("peak_capital", self.initial_capital)
                self.daily_trades_count = data.get("daily_trades_count", 0)
                self.trades_history = data.get("trades_history", [])
                
                # Converter data se existir
                last_trade_date_str = data.get("last_trade_date")
                if last_trade_date_str:
                    self.last_trade_date = datetime.fromisoformat(last_trade_date_str).date()
        except Exception as e:
            print(f"⚠️ Erro ao carregar dados do capital: {e}")
            print("💡 Iniciando com configuração padrão")
    
    def export_trades_csv(self, filename: str = None) -> str:
        """
        Exporta histórico de trades para CSV
        
        Args:
            filename: Nome do arquivo (se None, gera automaticamente)
            
        Returns:
            str: Caminho do arquivo gerado
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trades_history_{timestamp}.csv"
        
        try:
            with open(filename, 'w') as f:
                # Cabeçalho
                f.write("trade_id,timestamp,action,symbol,entry_price,exit_price,position_size,pnl_amount,pnl_pct,strategy,capital_before,capital_after\n")
                
                # Dados
                for trade in self.trades_history:
                    f.write(f"{trade['trade_id']},{trade['timestamp']},{trade['action']},{trade['symbol']},{trade['entry_price']},{trade.get('exit_price', '')},{trade['position_size']},{trade.get('pnl_amount', 0)},{trade.get('pnl_pct', 0)},{trade['strategy']},{trade['capital_before']},{trade['capital_after']}\n")
            
            return filename
        except Exception as e:
            print(f"❌ Erro ao exportar CSV: {e}")
            return None

# Exemplo de uso
if __name__ == "__main__":
    # Teste do Capital Manager
    cm = CapitalManager(initial_capital=10000.0, position_size_pct=0.02)
    
    print("💰 Capital Manager - Teste")
    print(f"Capital inicial: ${cm.current_capital:.2f}")
    print(f"Position size: ${cm.get_position_size():.2f}")
    
    # Simular alguns trades
    result1 = cm.execute_trade("BUY", "BTCUSDT", 50000, 51000, "RSI", "Trade de teste")
    print(f"Trade 1: {result1}")
    
    result2 = cm.execute_trade("SELL", "ETHUSDT", 3000, 2950, "EMA", "Trade de teste 2")
    print(f"Trade 2: {result2}")
    
    # Mostrar estatísticas
    stats = cm.get_stats()
    print(f"\nEstatísticas:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
