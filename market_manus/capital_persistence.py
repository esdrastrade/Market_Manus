#!/usr/bin/env python3
"""
CAPITAL PERSISTENCE - Market Manus
Sistema de persistência de capital e configurações com proteção contra drawdown
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum


class PositionSizeMode(Enum):
    """Modos de cálculo de position size"""
    FIXED_NOTIONAL = "fixed_notional"  # Valor fixo em dinheiro
    FIXED_RISK = "fixed_risk"          # Risco fixo por trade
    PERCENTAGE = "percentage"          # Percentual do capital
    KELLY = "kelly"                    # Critério de Kelly


@dataclass
class CapitalConfig:
    """Configuração de capital"""
    initial_capital: float = 10000.0
    current_capital: float = 10000.0
    risk_per_trade: float = 0.01        # 1% por trade
    max_drawdown: float = 0.20          # 20% máximo drawdown
    position_size_mode: str = "fixed_notional"
    max_per_trade: float = 1000.0       # Máximo por trade em $
    leverage: float = 1.0               # Alavancagem
    stop_loss_pct: float = 0.02         # 2% stop loss padrão
    take_profit_pct: float = 0.04       # 4% take profit padrão
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CapitalConfig':
        """Cria instância a partir de dicionário"""
        return cls(**data)


@dataclass
class Trade:
    """Registro de uma operação"""
    id: Optional[int] = None
    timestamp: Optional[datetime] = None
    symbol: str = ""
    strategy: str = ""
    side: str = ""                      # "buy" ou "sell"
    entry_price: float = 0.0
    exit_price: float = 0.0
    quantity: float = 0.0
    pnl: float = 0.0
    fees: float = 0.0
    net_pnl: float = 0.0
    capital_before: float = 0.0
    capital_after: float = 0.0
    drawdown: float = 0.0
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        data = asdict(self)
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trade':
        """Cria instância a partir de dicionário"""
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class CapitalManager:
    """
    Gerenciador de capital com persistência e proteção contra drawdown
    
    Features:
    - Persistência em JSON e SQLite
    - Cálculo correto de position size
    - Proteção contra drawdown excessivo
    - Histórico completo de operações
    - Métricas de performance
    """
    
    def __init__(self, config_dir: str = "config", db_path: str = "logs/portfolio.db"):
        """
        Inicializa gerenciador de capital
        
        Args:
            config_dir: Diretório de configurações
            db_path: Caminho do banco de dados
        """
        self.config_dir = Path(config_dir)
        self.db_path = Path(db_path)
        
        # Criar diretórios
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Arquivos de configuração
        self.capital_config_file = self.config_dir / "capital_config.json"
        self.settings_file = self.config_dir / "settings.json"
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
        
        # Carregar configurações
        self.config = self._load_capital_config()
        self.settings = self._load_settings()
        
        # Inicializar banco de dados
        self._init_database()
        
        # Estado atual
        self.peak_capital = self.config.current_capital
        self.current_drawdown = 0.0
        self.is_drawdown_protection_active = False
        
        self.logger.info(f"Capital Manager inicializado - Capital: ${self.config.current_capital:,.2f}")
    
    def _load_capital_config(self) -> CapitalConfig:
        """Carrega configuração de capital"""
        if self.capital_config_file.exists():
            try:
                with open(self.capital_config_file, 'r') as f:
                    data = json.load(f)
                return CapitalConfig.from_dict(data)
            except Exception as e:
                self.logger.warning(f"Erro ao carregar config de capital: {e}")
        
        # Retornar configuração padrão
        return CapitalConfig()
    
    def _save_capital_config(self):
        """Salva configuração de capital"""
        try:
            with open(self.capital_config_file, 'w') as f:
                json.dump(self.config.to_dict(), f, indent=2)
        except Exception as e:
            self.logger.error(f"Erro ao salvar config de capital: {e}")
    
    def _load_settings(self) -> Dict[str, Any]:
        """Carrega configurações gerais"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Erro ao carregar settings: {e}")
        
        # Configurações padrão
        return {
            "last_symbol": "BTCUSDT",
            "last_timeframe": "1h",
            "last_strategies": ["rsi_mean_reversion"],
            "theme": "dark",
            "auto_save": True
        }
    
    def _save_settings(self):
        """Salva configurações gerais"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            self.logger.error(f"Erro ao salvar settings: {e}")
    
    def _init_database(self):
        """Inicializa banco de dados SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        strategy TEXT NOT NULL,
                        side TEXT NOT NULL,
                        entry_price REAL NOT NULL,
                        exit_price REAL NOT NULL,
                        quantity REAL NOT NULL,
                        pnl REAL NOT NULL,
                        fees REAL NOT NULL,
                        net_pnl REAL NOT NULL,
                        capital_before REAL NOT NULL,
                        capital_after REAL NOT NULL,
                        drawdown REAL NOT NULL,
                        notes TEXT
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS capital_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        capital REAL NOT NULL,
                        peak_capital REAL NOT NULL,
                        drawdown REAL NOT NULL,
                        total_trades INTEGER NOT NULL,
                        win_rate REAL NOT NULL,
                        notes TEXT
                    )
                ''')
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Erro ao inicializar banco: {e}")
    
    def calculate_position_size(self, 
                              price: float, 
                              stop_loss_price: Optional[float] = None,
                              strategy_risk: float = 1.0) -> Dict[str, float]:
        """
        Calcula position size corrigido
        
        Args:
            price: Preço de entrada
            stop_loss_price: Preço de stop loss (opcional)
            strategy_risk: Multiplicador de risco da estratégia (0.5 - 2.0)
            
        Returns:
            Dicionário com informações de position size
        """
        if self.is_drawdown_protection_active:
            return {
                'quantity': 0.0,
                'notional': 0.0,
                'risk_amount': 0.0,
                'max_loss': 0.0,
                'reason': 'Proteção de drawdown ativa'
            }
        
        # Ajustar risco baseado na estratégia
        adjusted_risk = self.config.risk_per_trade * strategy_risk
        adjusted_risk = max(0.001, min(adjusted_risk, 0.05))  # Entre 0.1% e 5%
        
        mode = PositionSizeMode(self.config.position_size_mode)
        
        if mode == PositionSizeMode.FIXED_NOTIONAL:
            # Valor fixo em dinheiro
            notional = min(
                self.config.max_per_trade,
                self.config.current_capital * self.config.leverage * 0.1  # Máx 10% do capital
            )
            quantity = notional / price
            
        elif mode == PositionSizeMode.FIXED_RISK:
            # Risco fixo por trade
            if stop_loss_price is None:
                stop_loss_price = price * (1 - self.config.stop_loss_pct)
            
            risk_amount = self.config.current_capital * adjusted_risk
            stop_size = abs(price - stop_loss_price)
            
            if stop_size > 0:
                quantity = risk_amount / stop_size
                notional = quantity * price
            else:
                quantity = 0.0
                notional = 0.0
                
        elif mode == PositionSizeMode.PERCENTAGE:
            # Percentual do capital
            percentage = min(adjusted_risk * 10, 0.2)  # Máx 20%
            notional = self.config.current_capital * percentage
            quantity = notional / price
            
        else:  # KELLY ou outros
            # Usar fixed_risk como fallback
            risk_amount = self.config.current_capital * adjusted_risk
            notional = min(risk_amount * 10, self.config.max_per_trade)
            quantity = notional / price
        
        # Limitar por capital disponível
        max_notional = self.config.current_capital * 0.95  # Máx 95% do capital
        if notional > max_notional:
            notional = max_notional
            quantity = notional / price
        
        # Calcular risco máximo
        if stop_loss_price:
            max_loss = quantity * abs(price - stop_loss_price)
        else:
            max_loss = notional * self.config.stop_loss_pct
        
        return {
            'quantity': round(quantity, 8),
            'notional': round(notional, 2),
            'risk_amount': round(max_loss, 2),
            'max_loss': round(max_loss, 2),
            'risk_percentage': round((max_loss / self.config.current_capital) * 100, 2),
            'mode': mode.value
        }
    
    def apply_trade(self, 
                   symbol: str,
                   strategy: str,
                   side: str,
                   entry_price: float,
                   exit_price: float,
                   quantity: float,
                   fees_bps: float = 2.0) -> Trade:
        """
        Aplica resultado de uma operação
        
        Args:
            symbol: Símbolo do ativo
            strategy: Nome da estratégia
            side: "buy" ou "sell"
            entry_price: Preço de entrada
            exit_price: Preço de saída
            quantity: Quantidade
            fees_bps: Taxa em basis points
            
        Returns:
            Objeto Trade com resultado
        """
        # Calcular P&L
        if side.lower() == "buy":
            pnl = (exit_price - entry_price) * quantity
        else:  # sell
            pnl = (entry_price - exit_price) * quantity
        
        # Calcular fees
        entry_notional = entry_price * quantity
        exit_notional = exit_price * quantity
        fees = (entry_notional + exit_notional) * (fees_bps / 10000)
        
        net_pnl = pnl - fees
        
        # Atualizar capital
        capital_before = self.config.current_capital
        capital_after = capital_before + net_pnl
        
        # Atualizar peak e drawdown
        if capital_after > self.peak_capital:
            self.peak_capital = capital_after
            self.current_drawdown = 0.0
        else:
            self.current_drawdown = (self.peak_capital - capital_after) / self.peak_capital
        
        # Verificar proteção de drawdown
        if self.current_drawdown >= self.config.max_drawdown:
            self.is_drawdown_protection_active = True
            self.logger.warning(f"Proteção de drawdown ativada! Drawdown: {self.current_drawdown:.2%}")
        
        # Criar registro de trade
        trade = Trade(
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            strategy=strategy,
            side=side,
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            pnl=pnl,
            fees=fees,
            net_pnl=net_pnl,
            capital_before=capital_before,
            capital_after=capital_after,
            drawdown=self.current_drawdown
        )
        
        # Salvar no banco
        self._save_trade(trade)
        
        # Atualizar capital atual
        self.config.current_capital = capital_after
        self._save_capital_config()
        
        self.logger.info(f"Trade aplicado: {symbol} {side} P&L: ${net_pnl:+.2f} Capital: ${capital_after:,.2f}")
        
        return trade
    
    def _save_trade(self, trade: Trade):
        """Salva trade no banco de dados"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO trades (
                        timestamp, symbol, strategy, side, entry_price, exit_price,
                        quantity, pnl, fees, net_pnl, capital_before, capital_after,
                        drawdown, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade.timestamp.isoformat(),
                    trade.symbol,
                    trade.strategy,
                    trade.side,
                    trade.entry_price,
                    trade.exit_price,
                    trade.quantity,
                    trade.pnl,
                    trade.fees,
                    trade.net_pnl,
                    trade.capital_before,
                    trade.capital_after,
                    trade.drawdown,
                    trade.notes
                ))
                
                trade.id = cursor.lastrowid
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Erro ao salvar trade: {e}")
    
    def get_capital_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo do capital
        
        Returns:
            Dicionário com métricas de capital
        """
        roi = ((self.config.current_capital - self.config.initial_capital) / self.config.initial_capital) * 100
        
        # Buscar estatísticas de trades
        trades_stats = self._get_trades_statistics()
        
        return {
            'initial_capital': self.config.initial_capital,
            'current_capital': self.config.current_capital,
            'peak_capital': self.peak_capital,
            'total_pnl': self.config.current_capital - self.config.initial_capital,
            'roi': roi,
            'current_drawdown': self.current_drawdown,
            'max_drawdown': self.config.max_drawdown,
            'drawdown_protection_active': self.is_drawdown_protection_active,
            'position_size_mode': self.config.position_size_mode,
            'risk_per_trade': self.config.risk_per_trade,
            **trades_stats
        }
    
    def _get_trades_statistics(self) -> Dict[str, Any]:
        """Calcula estatísticas de trades"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total de trades
                cursor.execute("SELECT COUNT(*) FROM trades")
                total_trades = cursor.fetchone()[0]
                
                if total_trades == 0:
                    return {
                        'total_trades': 0,
                        'winning_trades': 0,
                        'losing_trades': 0,
                        'win_rate': 0.0,
                        'avg_win': 0.0,
                        'avg_loss': 0.0,
                        'profit_factor': 0.0
                    }
                
                # Trades vencedores e perdedores
                cursor.execute("SELECT COUNT(*) FROM trades WHERE net_pnl > 0")
                winning_trades = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM trades WHERE net_pnl < 0")
                losing_trades = cursor.fetchone()[0]
                
                # Médias
                cursor.execute("SELECT AVG(net_pnl) FROM trades WHERE net_pnl > 0")
                avg_win = cursor.fetchone()[0] or 0.0
                
                cursor.execute("SELECT AVG(net_pnl) FROM trades WHERE net_pnl < 0")
                avg_loss = cursor.fetchone()[0] or 0.0
                
                # Profit factor
                cursor.execute("SELECT SUM(net_pnl) FROM trades WHERE net_pnl > 0")
                total_wins = cursor.fetchone()[0] or 0.0
                
                cursor.execute("SELECT SUM(ABS(net_pnl)) FROM trades WHERE net_pnl < 0")
                total_losses = cursor.fetchone()[0] or 0.0
                
                profit_factor = total_wins / total_losses if total_losses > 0 else 0.0
                win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0.0
                
                return {
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': losing_trades,
                    'win_rate': round(win_rate, 2),
                    'avg_win': round(avg_win, 2),
                    'avg_loss': round(avg_loss, 2),
                    'profit_factor': round(profit_factor, 2)
                }
                
        except Exception as e:
            self.logger.error(f"Erro ao calcular estatísticas: {e}")
            return {}
    
    def reset_capital(self, new_initial_capital: float):
        """
        Reseta capital para novo valor inicial
        
        Args:
            new_initial_capital: Novo capital inicial
        """
        self.config.initial_capital = new_initial_capital
        self.config.current_capital = new_initial_capital
        self.peak_capital = new_initial_capital
        self.current_drawdown = 0.0
        self.is_drawdown_protection_active = False
        
        self._save_capital_config()
        
        # Salvar snapshot
        self._save_capital_snapshot("Capital resetado")
        
        self.logger.info(f"Capital resetado para ${new_initial_capital:,.2f}")
    
    def _save_capital_snapshot(self, notes: str = ""):
        """Salva snapshot do capital atual"""
        try:
            trades_stats = self._get_trades_statistics()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO capital_snapshots (
                        timestamp, capital, peak_capital, drawdown, 
                        total_trades, win_rate, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now(timezone.utc).isoformat(),
                    self.config.current_capital,
                    self.peak_capital,
                    self.current_drawdown,
                    trades_stats.get('total_trades', 0),
                    trades_stats.get('win_rate', 0.0),
                    notes
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Erro ao salvar snapshot: {e}")
    
    def update_settings(self, **kwargs):
        """Atualiza configurações gerais"""
        self.settings.update(kwargs)
        self._save_settings()
    
    def get_recent_trades(self, limit: int = 10) -> List[Trade]:
        """
        Retorna trades recentes
        
        Args:
            limit: Número máximo de trades
            
        Returns:
            Lista de trades
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM trades 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
                
                trades = []
                for row in cursor.fetchall():
                    trade_data = {
                        'id': row[0],
                        'timestamp': datetime.fromisoformat(row[1]),
                        'symbol': row[2],
                        'strategy': row[3],
                        'side': row[4],
                        'entry_price': row[5],
                        'exit_price': row[6],
                        'quantity': row[7],
                        'pnl': row[8],
                        'fees': row[9],
                        'net_pnl': row[10],
                        'capital_before': row[11],
                        'capital_after': row[12],
                        'drawdown': row[13],
                        'notes': row[14] or ""
                    }
                    trades.append(Trade.from_dict(trade_data))
                
                return trades
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar trades recentes: {e}")
            return []
    
    def disable_drawdown_protection(self):
        """Desabilita proteção de drawdown (usar com cuidado)"""
        self.is_drawdown_protection_active = False
        self.logger.warning("Proteção de drawdown desabilitada manualmente")


if __name__ == "__main__":
    # Teste do sistema de capital
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    # Criar gerenciador
    capital_manager = CapitalManager()
    
    print("💰 Testando Capital Manager...")
    
    # Mostrar resumo inicial
    summary = capital_manager.get_capital_summary()
    print(f"Capital inicial: ${summary['current_capital']:,.2f}")
    
    # Testar cálculo de position size
    position_info = capital_manager.calculate_position_size(50000, 49000)
    print(f"Position size para BTC a $50k: {position_info}")
    
    # Simular alguns trades
    print("\\n📊 Simulando trades...")
    
    # Trade vencedor
    trade1 = capital_manager.apply_trade(
        symbol="BTCUSDT",
        strategy="rsi_mean_reversion",
        side="buy",
        entry_price=50000,
        exit_price=51000,
        quantity=0.1
    )
    print(f"Trade 1: ${trade1.net_pnl:+.2f}")
    
    # Trade perdedor
    trade2 = capital_manager.apply_trade(
        symbol="ETHUSDT",
        strategy="ema_crossover",
        side="buy",
        entry_price=3000,
        exit_price=2950,
        quantity=1.0
    )
    print(f"Trade 2: ${trade2.net_pnl:+.2f}")
    
    # Resumo final
    final_summary = capital_manager.get_capital_summary()
    print(f"\\n📈 Resumo final:")
    print(f"Capital: ${final_summary['current_capital']:,.2f}")
    print(f"ROI: {final_summary['roi']:+.2f}%")
    print(f"Drawdown: {final_summary['current_drawdown']:.2%}")
    print(f"Win Rate: {final_summary['win_rate']:.1f}%")
    
    print("\\n✅ Teste do Capital Manager concluído!")
