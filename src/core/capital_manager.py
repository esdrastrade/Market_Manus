#!/usr/bin/env python3
"""
CAPITAL MANAGER - Gestão de Capital para Backtesting
Sistema de Trading Automatizado - Gestão de capital inicial e compound interest
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple


@dataclass
class CapitalConfig:
    """Configuração de capital para backtesting"""

    initial_capital_usd: float
    position_size_percent: float = 2.0  # % do capital por trade
    compound_interest: bool = True  # Reinvestir lucros
    min_position_size_usd: float = 10.0  # Tamanho mínimo da posição em USD
    max_position_size_usd: float = 10000.0  # Tamanho máximo da posição em USD
    risk_per_trade_percent: float = 1.0  # % máximo de risco por trade

    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            "initial_capital_usd": self.initial_capital_usd,
            "position_size_percent": self.position_size_percent,
            "compound_interest": self.compound_interest,
            "min_position_size_usd": self.min_position_size_usd,
            "max_position_size_usd": self.max_position_size_usd,
            "risk_per_trade_percent": self.risk_per_trade_percent,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "CapitalConfig":
        """Cria instância a partir de dicionário"""
        return cls(**data)


@dataclass
class TradeResult:
    """Resultado de um trade com informações de capital"""

    entry_price: float
    exit_price: float
    direction: int  # 1 para long, -1 para short
    position_size_usd: float
    pnl_usd: float
    pnl_percent: float
    capital_before: float
    capital_after: float
    timestamp: str
    exit_reason: str


class CapitalManager:
    """Gerenciador de capital para backtesting"""

    def __init__(self, config: CapitalConfig):
        self.config = config
        self.current_capital = config.initial_capital_usd
        self.trade_history: List[TradeResult] = []
        self.capital_evolution: List[Tuple[str, float]] = []

        # Adicionar capital inicial ao histórico
        self.capital_evolution.append(
            (datetime.now().isoformat(), self.current_capital)
        )

    def calculate_position_size(
        self, price: float, stop_loss_percent: float = 0.015
    ) -> float:
        """
        Calcula o tamanho da posição baseado no capital atual

        Args:
            price: Preço atual do ativo
            stop_loss_percent: Percentual de stop loss (padrão 1.5%)

        Returns:
            Tamanho da posição em USD
        """
        # Calcular baseado no percentual do capital
        position_size_by_percent = self.current_capital * (
            self.config.position_size_percent / 100
        )

        # Calcular baseado no risco máximo por trade
        max_risk_usd = self.current_capital * (self.config.risk_per_trade_percent / 100)
        position_size_by_risk = max_risk_usd / stop_loss_percent

        # Usar o menor dos dois
        position_size = min(position_size_by_percent, position_size_by_risk)

        # Aplicar limites mínimo e máximo
        position_size = max(position_size, self.config.min_position_size_usd)
        position_size = min(position_size, self.config.max_position_size_usd)

        # Não pode exceder o capital disponível
        position_size = min(
            position_size, self.current_capital * 0.95
        )  # Máximo 95% do capital

        return position_size

    def execute_trade(
        self,
        entry_price: float,
        exit_price: float,
        direction: int,
        timestamp: str,
        exit_reason: str,
        stop_loss_percent: float = 0.015,
    ) -> TradeResult:
        """
        Executa um trade e atualiza o capital

        Args:
            entry_price: Preço de entrada
            exit_price: Preço de saída
            direction: 1 para long, -1 para short
            timestamp: Timestamp do trade
            exit_reason: Razão da saída
            stop_loss_percent: Percentual de stop loss usado

        Returns:
            Resultado do trade
        """
        # Calcular tamanho da posição
        position_size_usd = self.calculate_position_size(entry_price, stop_loss_percent)

        # Calcular P&L percentual
        if direction == 1:  # Long
            pnl_percent = (exit_price - entry_price) / entry_price
        else:  # Short
            pnl_percent = (entry_price - exit_price) / entry_price

        # Calcular P&L em USD
        pnl_usd = position_size_usd * pnl_percent

        # Capital antes do trade
        capital_before = self.current_capital

        # Atualizar capital
        if self.config.compound_interest:
            # Compound interest: reinvestir lucros - capital cresce/diminui
            self.current_capital += pnl_usd
        else:
            # Capital fixo: não reinvestir - manter capital inicial para position sizing
            # mas ainda rastrear P&L total
            pass  # current_capital permanece inalterado para position sizing

        # Garantir que o capital não fique negativo
        self.current_capital = max(self.current_capital, 0)

        # Criar resultado do trade
        trade_result = TradeResult(
            entry_price=entry_price,
            exit_price=exit_price,
            direction=direction,
            position_size_usd=position_size_usd,
            pnl_usd=pnl_usd,
            pnl_percent=pnl_percent,
            capital_before=capital_before,
            capital_after=self.current_capital,
            timestamp=timestamp,
            exit_reason=exit_reason,
        )

        # Adicionar ao histórico
        self.trade_history.append(trade_result)
        self.capital_evolution.append((timestamp, self.current_capital))

        return trade_result

    def get_metrics(self) -> Dict:
        """Calcula métricas detalhadas baseadas no capital"""
        if not self.trade_history:
            return self._empty_capital_metrics()

        # Métricas básicas
        total_trades = len(self.trade_history)
        winning_trades = [t for t in self.trade_history if t.pnl_usd > 0]
        losing_trades = [t for t in self.trade_history if t.pnl_usd < 0]

        # Retornos
        if self.config.compound_interest:
            # Com compound interest: capital final é o atual
            final_capital = self.current_capital
        else:
            # Sem compound interest: capital final = inicial + soma dos P&Ls
            final_capital = self.config.initial_capital_usd + sum(
                t.pnl_usd for t in self.trade_history
            )

        total_return_usd = final_capital - self.config.initial_capital_usd
        total_return_percent = (
            total_return_usd / self.config.initial_capital_usd
        ) * 100

        # Win rate
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0

        # Profit factor
        gross_profit = sum(t.pnl_usd for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t.pnl_usd for t in losing_trades)) if losing_trades else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        # Drawdown máximo
        peak_capital = self.config.initial_capital_usd
        max_drawdown_usd = 0
        max_drawdown_percent = 0

        for _, capital in self.capital_evolution:
            if capital > peak_capital:
                peak_capital = capital

            drawdown_usd = peak_capital - capital
            drawdown_percent = (
                (drawdown_usd / peak_capital) * 100 if peak_capital > 0 else 0
            )

            max_drawdown_usd = max(max_drawdown_usd, drawdown_usd)
            max_drawdown_percent = max(max_drawdown_percent, drawdown_percent)

        # Trades por direção
        long_trades = [t for t in self.trade_history if t.direction == 1]
        short_trades = [t for t in self.trade_history if t.direction == -1]

        # Métricas de trades
        avg_win_usd = (
            sum(t.pnl_usd for t in winning_trades) / len(winning_trades)
            if winning_trades
            else 0
        )
        avg_loss_usd = (
            sum(t.pnl_usd for t in losing_trades) / len(losing_trades)
            if losing_trades
            else 0
        )

        best_trade_usd = (
            max(t.pnl_usd for t in self.trade_history) if self.trade_history else 0
        )
        worst_trade_usd = (
            min(t.pnl_usd for t in self.trade_history) if self.trade_history else 0
        )

        # Tamanho médio das posições
        avg_position_size = (
            sum(t.position_size_usd for t in self.trade_history) / total_trades
            if total_trades > 0
            else 0
        )

        return {
            # Capital
            "initial_capital_usd": self.config.initial_capital_usd,
            "final_capital_usd": final_capital,
            "total_return_usd": total_return_usd,
            "total_return_percent": total_return_percent,
            "roi_percent": total_return_percent,
            # Trades
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            # P&L
            "gross_profit_usd": gross_profit,
            "gross_loss_usd": gross_loss,
            "avg_win_usd": avg_win_usd,
            "avg_loss_usd": avg_loss_usd,
            "best_trade_usd": best_trade_usd,
            "worst_trade_usd": worst_trade_usd,
            # Drawdown
            "max_drawdown_usd": max_drawdown_usd,
            "max_drawdown_percent": max_drawdown_percent,
            # Position sizing
            "avg_position_size_usd": avg_position_size,
            "position_size_percent": self.config.position_size_percent,
            # Direções
            "long_trades": len(long_trades),
            "short_trades": len(short_trades),
            "long_win_rate": (
                len([t for t in long_trades if t.pnl_usd > 0]) / len(long_trades)
                if long_trades
                else 0
            ),
            "short_win_rate": (
                len([t for t in short_trades if t.pnl_usd > 0]) / len(short_trades)
                if short_trades
                else 0
            ),
            # Configuração
            "compound_interest": self.config.compound_interest,
            "risk_per_trade_percent": self.config.risk_per_trade_percent,
            # Evolução do capital
            "capital_evolution": self.capital_evolution.copy(),
        }

    def _empty_capital_metrics(self) -> Dict:
        """Retorna métricas vazias"""
        return {
            "initial_capital_usd": self.config.initial_capital_usd,
            "final_capital_usd": self.config.initial_capital_usd,
            "total_return_usd": 0.0,
            "total_return_percent": 0.0,
            "roi_percent": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "gross_profit_usd": 0.0,
            "gross_loss_usd": 0.0,
            "avg_win_usd": 0.0,
            "avg_loss_usd": 0.0,
            "best_trade_usd": 0.0,
            "worst_trade_usd": 0.0,
            "max_drawdown_usd": 0.0,
            "max_drawdown_percent": 0.0,
            "avg_position_size_usd": 0.0,
            "position_size_percent": self.config.position_size_percent,
            "long_trades": 0,
            "short_trades": 0,
            "long_win_rate": 0.0,
            "short_win_rate": 0.0,
            "compound_interest": self.config.compound_interest,
            "risk_per_trade_percent": self.config.risk_per_trade_percent,
            "capital_evolution": [
                (datetime.now().isoformat(), self.config.initial_capital_usd)
            ],
        }

    def save_config(self, filepath: str = "config/capital_config.json"):
        """Salva configuração de capital"""
        try:
            # Garantir que o diretório existe
            dir_path = os.path.dirname(filepath)
            if dir_path:  # Se há um diretório especificado
                os.makedirs(dir_path, exist_ok=True)

            with open(filepath, "w") as f:
                json.dump(self.config.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar configuração: {e}")
            return False

    @classmethod
    def load_config(
        cls, filepath: str = "config/capital_config.json"
    ) -> Optional["CapitalManager"]:
        """Carrega configuração de capital"""
        try:
            if not os.path.exists(filepath):
                return None

            with open(filepath, "r") as f:
                data = json.load(f)

            config = CapitalConfig.from_dict(data)
            return cls(config)
        except Exception as e:
            print(f"❌ Erro ao carregar configuração: {e}")
            return None

    def reset_capital(self):
        """Reseta o capital para o valor inicial"""
        self.current_capital = self.config.initial_capital_usd
        self.trade_history.clear()
        self.capital_evolution.clear()
        self.capital_evolution.append(
            (datetime.now().isoformat(), self.current_capital)
        )


def create_default_capital_config(initial_capital: float = 10000.0) -> CapitalConfig:
    """Cria configuração padrão de capital"""
    return CapitalConfig(
        initial_capital_usd=initial_capital,
        position_size_percent=2.0,
        compound_interest=True,
        min_position_size_usd=max(
            1.0, initial_capital * 0.001
        ),  # Mínimo $1 ou 0.1% do capital
        max_position_size_usd=min(
            initial_capital * 0.1, 10000.0
        ),  # Máximo 10% do capital ou $10k
        risk_per_trade_percent=1.0,
    )


if __name__ == "__main__":
    # Teste da classe CapitalManager
    print("🧪 Testando CapitalManager...")

    # Criar configuração
    config = create_default_capital_config(10000.0)
    manager = CapitalManager(config)

    print(f"💰 Capital inicial: ${config.initial_capital_usd:,.2f}")
    print(f"📊 Position size: {config.position_size_percent}%")
    print(f"🔄 Compound interest: {config.compound_interest}")

    # Simular alguns trades
    trades = [
        (100.0, 102.0, 1, "2024-01-01T10:00:00", "take_profit"),  # +2% long
        (102.0, 101.0, -1, "2024-01-01T11:00:00", "stop_loss"),  # +0.98% short
        (101.0, 99.0, 1, "2024-01-01T12:00:00", "stop_loss"),  # -1.98% long
        (99.0, 101.0, 1, "2024-01-01T13:00:00", "take_profit"),  # +2.02% long
    ]

    print(f"\n🔄 Executando {len(trades)} trades de teste...")

    for i, (entry, exit, direction, timestamp, reason) in enumerate(trades, 1):
        result = manager.execute_trade(entry, exit, direction, timestamp, reason)

        print(
            f"   Trade {i}: {'+' if result.pnl_usd >= 0 else ''}{result.pnl_usd:.2f} USD "
            f"({result.pnl_percent:.2%}) - Capital: ${result.capital_after:,.2f}"
        )

    # Exibir métricas
    metrics = manager.get_metrics()
    print(f"\n📊 RESULTADOS:")
    print(f"   💰 Capital final: ${metrics['final_capital_usd']:,.2f}")
    print(
        f"   📈 Retorno total: ${metrics['total_return_usd']:,.2f} ({metrics['total_return_percent']:.2f}%)"
    )
    print(f"   🎯 Win rate: {metrics['win_rate']:.1%}")
    print(f"   📊 Total trades: {metrics['total_trades']}")
    print(
        f"   📉 Max drawdown: ${metrics['max_drawdown_usd']:.2f} ({metrics['max_drawdown_percent']:.1f}%)"
    )

    print(f"\n✅ Teste concluído!")
