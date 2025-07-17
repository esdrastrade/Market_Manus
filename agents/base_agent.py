#!/usr/bin/env python3
"""
Base Agent para Sistema de Scalping Automatizado
Classe base que define a interface comum para todos os agentes
Autor: Manus AI
Data: 17 de Julho de 2025
"""

import json
import os
import sys
import time
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from abc import ABC, abstractmethod
from pathlib import Path

# Configurar logging
def setup_logging(agent_name: str, log_level: str = "INFO") -> logging.Logger:
    """Configura sistema de logging para o agente"""
    logger = logging.getLogger(agent_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Evitar duplicação de handlers
    if logger.handlers:
        return logger
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    log_file = Path("data/logs/agents.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class BaseAgent(ABC):
    """
    Classe base para todos os agentes do sistema de scalping
    
    Responsabilidades:
    - Gerenciamento de configuração
    - Sistema de logging padronizado
    - Salvamento de métricas e sugestões
    - Interface comum para todos os agentes
    """
    
    def __init__(self, name: str, config_path: str = "config/trading_config.json"):
        self.name = name
        self.config_path = config_path
        self.config = self.load_config()
        self.logger = setup_logging(name, self.config.get("monitoring", {}).get("log_level", "INFO"))
        
        # Arquivos de output
        self.suggestions_file = "data/suggestions/suggestions.json"
        self.metrics_file = "data/metrics/current.json"
        self.system_status_file = "data/system_status.json"
        
        # Criar diretórios necessários
        self._create_directories()
        
        # Estado do agente
        self.last_run = None
        self.run_count = 0
        self.errors = []
        
        self.logger.info(f"Agente {self.name} inicializado com sucesso")
    
    def _create_directories(self):
        """Cria diretórios necessários para operação"""
        directories = [
            "data/logs",
            "data/metrics", 
            "data/signals",
            "data/suggestions",
            "data/alerts",
            "data/reports",
            "data/historical",
            "data/backups"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> Dict:
        """Carrega configuração do arquivo JSON"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {self.config_path}")
            return self.get_default_config()
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing config file: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Configuração padrão se arquivo não existir"""
        return {
            "trading": {
                "symbols": ["BTC/USDT", "ETH/USDT"],
                "timeframe": "5m",
                "risk_per_trade": 0.02,
                "max_drawdown": 0.10,
                "max_positions": 3
            },
            "strategies": {
                "ema_triple": {"periods": [8, 13, 21], "weight": 0.4, "enabled": True},
                "bollinger_rsi": {"bb_period": 20, "rsi_period": 14, "weight": 0.4, "enabled": True},
                "breakout": {"volume_threshold": 1.5, "weight": 0.2, "enabled": True}
            },
            "risk_management": {
                "stop_loss_percentage": 0.005,
                "take_profit_percentage": 0.010,
                "trailing_stop_enabled": True
            },
            "monitoring": {
                "log_level": "INFO",
                "save_signals": True,
                "save_metrics": True,
                "alert_on_errors": True
            }
        }
    
    def save_suggestion(self, suggestion: Dict):
        """
        Salva sugestão de melhoria para implementação manual
        
        Args:
            suggestion: Dicionário com detalhes da sugestão
        """
        suggestion["timestamp"] = datetime.now().isoformat()
        suggestion["agent"] = self.name
        suggestion["applied"] = False
        suggestion["priority"] = suggestion.get("priority", "medium")
        
        # Carregar sugestões existentes
        suggestions = []
        if os.path.exists(self.suggestions_file):
            try:
                with open(self.suggestions_file, 'r', encoding='utf-8') as f:
                    suggestions = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                suggestions = []
        
        suggestions.append(suggestion)
        
        # Manter apenas últimas 100 sugestões
        suggestions = suggestions[-100:]
        
        # Salvar sugestões atualizadas
        Path(self.suggestions_file).parent.mkdir(parents=True, exist_ok=True)
        with open(self.suggestions_file, 'w', encoding='utf-8') as f:
            json.dump(suggestions, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Sugestão salva: {suggestion['suggested_changes']['reason']}")
    
    def save_metrics(self, metrics: Dict):
        """
        Salva métricas atuais do agente
        
        Args:
            metrics: Dicionário com métricas do agente
        """
        metrics["timestamp"] = datetime.now().isoformat()
        metrics["agent"] = self.name
        metrics["run_count"] = self.run_count
        metrics["last_run"] = self.last_run.isoformat() if self.last_run else None
        
        # Salvar métricas
        Path(self.metrics_file).parent.mkdir(parents=True, exist_ok=True)
        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
    
    def save_alert(self, alert: Dict):
        """
        Salva alerta para processamento pelo NotificationAgent
        
        Args:
            alert: Dicionário com detalhes do alerta
        """
        alert["timestamp"] = datetime.now().isoformat()
        alert["agent"] = self.name
        alert["id"] = f"{self.name}_{int(time.time())}"
        
        # Salvar alerta individual
        alert_file = f"data/alerts/alert_{alert['id']}.json"
        Path(alert_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(alert_file, 'w', encoding='utf-8') as f:
            json.dump(alert, f, indent=2, ensure_ascii=False)
        
        self.logger.warning(f"Alerta gerado: {alert.get('message', 'Sem mensagem')}")
    
    def load_system_status(self) -> Dict:
        """Carrega status atual do sistema"""
        try:
            if os.path.exists(self.system_status_file):
                with open(self.system_status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
        
        return {
            "overall_status": "unknown",
            "agents": {},
            "last_update": datetime.now().isoformat()
        }
    
    def update_system_status(self, status_update: Dict):
        """Atualiza status do sistema"""
        system_status = self.load_system_status()
        
        # Atualizar status do agente atual
        system_status["agents"][self.name] = {
            "status": status_update.get("status", "running"),
            "last_run": datetime.now().isoformat(),
            "run_count": self.run_count,
            "errors": len(self.errors),
            "last_error": self.errors[-1] if self.errors else None
        }
        
        system_status["last_update"] = datetime.now().isoformat()
        
        # Salvar status atualizado
        with open(self.system_status_file, 'w', encoding='utf-8') as f:
            json.dump(system_status, f, indent=2, ensure_ascii=False)
    
    def handle_error(self, error: Exception, context: str = ""):
        """
        Trata erros de forma padronizada
        
        Args:
            error: Exceção capturada
            context: Contexto onde o erro ocorreu
        """
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        }
        
        self.errors.append(error_info)
        
        # Manter apenas últimos 50 erros
        self.errors = self.errors[-50:]
        
        self.logger.error(f"Erro em {context}: {error}")
        
        # Gerar alerta para erros críticos
        if isinstance(error, (ConnectionError, TimeoutError)):
            self.save_alert({
                "type": "system_error",
                "severity": "high",
                "message": f"Erro crítico em {self.name}: {error}",
                "context": context,
                "error_details": error_info
            })
    
    def validate_config(self) -> bool:
        """
        Valida configuração do agente
        
        Returns:
            bool: True se configuração válida
        """
        required_sections = ["trading", "strategies", "risk_management", "monitoring"]
        
        for section in required_sections:
            if section not in self.config:
                self.logger.error(f"Seção obrigatória '{section}' não encontrada na configuração")
                return False
        
        # Validações específicas
        trading_config = self.config["trading"]
        
        if not trading_config.get("symbols"):
            self.logger.error("Lista de símbolos não pode estar vazia")
            return False
        
        if trading_config.get("risk_per_trade", 0) <= 0 or trading_config.get("risk_per_trade", 0) > 0.1:
            self.logger.error("risk_per_trade deve estar entre 0 e 0.1 (10%)")
            return False
        
        if trading_config.get("max_drawdown", 0) <= 0 or trading_config.get("max_drawdown", 0) > 0.5:
            self.logger.error("max_drawdown deve estar entre 0 e 0.5 (50%)")
            return False
        
        return True
    
    def get_performance_window_data(self, data_type: str, window_size: int = 100) -> List[Dict]:
        """
        Obtém dados de uma janela de performance
        
        Args:
            data_type: Tipo de dados (signals, trades, metrics)
            window_size: Tamanho da janela
            
        Returns:
            List[Dict]: Lista com dados da janela
        """
        data_dir = f"data/{data_type}"
        
        if not os.path.exists(data_dir):
            return []
        
        # Listar arquivos ordenados por data de modificação
        files = []
        for file_path in Path(data_dir).glob("*.json"):
            try:
                files.append((file_path.stat().st_mtime, file_path))
            except OSError:
                continue
        
        files.sort(reverse=True)  # Mais recentes primeiro
        
        # Carregar dados dos arquivos mais recentes
        data = []
        for _, file_path in files[:window_size]:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    if isinstance(file_data, list):
                        data.extend(file_data)
                    else:
                        data.append(file_data)
            except (json.JSONDecodeError, FileNotFoundError):
                continue
        
        return data[-window_size:] if data else []
    
    def calculate_basic_stats(self, values: List[float]) -> Dict:
        """
        Calcula estatísticas básicas de uma lista de valores
        
        Args:
            values: Lista de valores numéricos
            
        Returns:
            Dict: Estatísticas calculadas
        """
        if not values:
            return {
                "count": 0,
                "mean": 0,
                "std": 0,
                "min": 0,
                "max": 0,
                "median": 0
            }
        
        values_array = np.array(values)
        
        return {
            "count": len(values),
            "mean": float(np.mean(values_array)),
            "std": float(np.std(values_array)),
            "min": float(np.min(values_array)),
            "max": float(np.max(values_array)),
            "median": float(np.median(values_array))
        }
    
    def run_with_error_handling(self):
        """
        Executa o agente com tratamento de erros padronizado
        """
        try:
            self.logger.info(f"Iniciando execução do {self.name}")
            
            # Validar configuração
            if not self.validate_config():
                raise ValueError("Configuração inválida")
            
            # Executar lógica principal do agente
            self.run()
            
            # Atualizar contadores
            self.last_run = datetime.now()
            self.run_count += 1
            
            # Atualizar status do sistema
            self.update_system_status({"status": "completed"})
            
            self.logger.info(f"Execução do {self.name} concluída com sucesso")
            
        except Exception as e:
            self.handle_error(e, "run_with_error_handling")
            self.update_system_status({"status": "error"})
            raise
    
    @abstractmethod
    def run(self):
        """
        Método principal do agente - deve ser implementado por cada agente
        """
        pass
    
    @abstractmethod
    def analyze_performance(self) -> Dict:
        """
        Analisa performance e retorna métricas
        
        Returns:
            Dict: Métricas de performance do agente
        """
        pass
    
    @abstractmethod
    def suggest_improvements(self) -> List[Dict]:
        """
        Analisa métricas e sugere melhorias
        
        Returns:
            List[Dict]: Lista de sugestões de melhoria
        """
        pass

class AgentStatus:
    """Enum para status dos agentes"""
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    STOPPED = "stopped"

class SuggestionType:
    """Enum para tipos de sugestões"""
    PARAMETER_ADJUSTMENT = "parameter_adjustment"
    STRATEGY_OPTIMIZATION = "strategy_optimization"
    RISK_REDUCTION = "risk_reduction"
    PERFORMANCE_IMPROVEMENT = "performance_improvement"
    SYSTEM_MAINTENANCE = "system_maintenance"
    CONFIGURATION_UPDATE = "configuration_update"

class AlertSeverity:
    """Enum para severidade de alertas"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Utilitários para agentes
def format_currency(value: float, currency: str = "USD") -> str:
    """Formata valor monetário"""
    return f"{currency} {value:,.2f}"

def format_percentage(value: float) -> str:
    """Formata percentual"""
    return f"{value:.2%}"

def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
    """Calcula Sharpe ratio"""
    if not returns or len(returns) < 2:
        return 0.0
    
    returns_array = np.array(returns)
    excess_returns = returns_array - (risk_free_rate / 252)  # Daily risk-free rate
    
    if np.std(excess_returns) == 0:
        return 0.0
    
    return float(np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252))

def calculate_max_drawdown(equity_curve: List[float]) -> float:
    """Calcula drawdown máximo"""
    if not equity_curve or len(equity_curve) < 2:
        return 0.0
    
    equity_array = np.array(equity_curve)
    peak = np.maximum.accumulate(equity_array)
    drawdown = (peak - equity_array) / peak
    
    return float(np.max(drawdown))

def is_market_hours() -> bool:
    """Verifica se está em horário de mercado (crypto 24/7)"""
    return True  # Crypto markets are 24/7

def get_next_run_time(frequency_minutes: int) -> datetime:
    """Calcula próximo horário de execução"""
    now = datetime.now()
    next_run = now + timedelta(minutes=frequency_minutes)
    return next_run

if __name__ == "__main__":
    # Teste básico da classe base
    class TestAgent(BaseAgent):
        def run(self):
            self.logger.info("Teste executado com sucesso")
        
        def analyze_performance(self):
            return {"test_metric": 1.0}
        
        def suggest_improvements(self):
            return []
    
    agent = TestAgent("TestAgent")
    agent.run_with_error_handling()

