#!/usr/bin/env python3
"""
BASE STRATEGY - Classe base para todas as estratégias do Market Manus
Sistema modular e extensível para estratégias de trading
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional


@dataclass
class StrategyConfig:
    """Configuração de uma estratégia"""
    name: str
    description: str
    risk_level: str  # "low", "medium", "high"
    best_timeframes: List[str]
    market_conditions: str
    params: Dict[str, Any]


class BaseStrategy(ABC):
    """Classe base abstrata para todas as estratégias"""
    
    def __init__(self, config: StrategyConfig):
        """
        Inicializa estratégia base
        
        Args:
            config: Configuração da estratégia
        """
        self.config = config
        self._validate_config()
    
    def _validate_config(self):
        """Valida configuração da estratégia"""
        required_fields = ['name', 'description', 'risk_level', 'best_timeframes', 'market_conditions', 'params']
        for field in required_fields:
            if not hasattr(self.config, field):
                raise ValueError(f"Configuração inválida: campo '{field}' é obrigatório")
        
        # Validar risk_level
        if self.config.risk_level not in ['low', 'medium', 'high']:
            raise ValueError("risk_level deve ser 'low', 'medium' ou 'high'")
        
        # Validar timeframes
        valid_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d']
        for tf in self.config.best_timeframes:
            if tf not in valid_timeframes:
                raise ValueError(f"Timeframe inválido: {tf}")
    
    @abstractmethod
    def calculate_signals(self, data: List[Dict]) -> List[Dict]:
        """
        Calcula sinais da estratégia
        
        Args:
            data: Lista de dados OHLCV
            
        Returns:
            Lista de dados com sinais adicionados
        """
        pass
    
    def _add_empty_signals(self, data: List[Dict]) -> List[Dict]:
        """Adiciona sinais vazios quando não há dados suficientes"""
        return [
            {
                **d,
                'signal': 0,
                'signal_strength': 0.0,
                'strategy': self.get_key()
            }
            for d in data
        ]
    
    def get_key(self) -> str:
        """Retorna chave única da estratégia"""
        return self.config.name.lower().replace(' ', '_')
    
    def get_name(self) -> str:
        """Retorna nome da estratégia"""
        return self.config.name
    
    def get_description(self) -> str:
        """Retorna descrição da estratégia"""
        return self.config.description
    
    def get_risk_level(self) -> str:
        """Retorna nível de risco"""
        return self.config.risk_level
    
    def get_best_timeframes(self) -> List[str]:
        """Retorna melhores timeframes"""
        return self.config.best_timeframes
    
    def get_market_conditions(self) -> str:
        """Retorna condições de mercado ideais"""
        return self.config.market_conditions
    
    def get_params(self) -> Dict[str, Any]:
        """Retorna parâmetros da estratégia"""
        return self.config.params.copy()
    
    def update_params(self, new_params: Dict[str, Any]):
        """Atualiza parâmetros da estratégia"""
        self.config.params.update(new_params)
    
    def get_strategy_info(self) -> Dict:
        """Retorna informações completas da estratégia"""
        return {
            'key': self.get_key(),
            'name': self.get_name(),
            'description': self.get_description(),
            'risk_level': self.get_risk_level(),
            'best_timeframes': self.get_best_timeframes(),
            'market_conditions': self.get_market_conditions(),
            'params': self.get_params()
        }
    
    def validate_data(self, data: List[Dict]) -> bool:
        """
        Valida se os dados são adequados para a estratégia
        
        Args:
            data: Lista de dados OHLCV
            
        Returns:
            True se dados são válidos, False caso contrário
        """
        if not data:
            return False
        
        # Verificar campos obrigatórios
        required_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for field in required_fields:
            if field not in data[0]:
                return False
        
        # Verificar se há dados suficientes
        min_data_points = max(self.config.params.values()) if self.config.params else 20
        if isinstance(min_data_points, (int, float)) and len(data) < min_data_points:
            return False
        
        return True
    
    def __str__(self) -> str:
        """Representação string da estratégia"""
        return f"{self.config.name} ({self.config.risk_level} risk)"
    
    def __repr__(self) -> str:
        """Representação detalhada da estratégia"""
        return f"BaseStrategy(name='{self.config.name}', risk='{self.config.risk_level}')"


class StrategyRegistry:
    """Registro global de estratégias disponíveis"""
    
    _strategies: Dict[str, Dict] = {}
    
    @classmethod
    def register(cls, strategy_config: Dict):
        """
        Registra uma estratégia no sistema
        
        Args:
            strategy_config: Configuração da estratégia com 'key', 'class', 'factory', 'default_params'
        """
        required_keys = ['key', 'class', 'factory', 'default_params']
        for key in required_keys:
            if key not in strategy_config:
                raise ValueError(f"Configuração de estratégia inválida: '{key}' é obrigatório")
        
        cls._strategies[strategy_config['key']] = strategy_config
    
    @classmethod
    def get_strategy(cls, key: str, **params) -> Optional[BaseStrategy]:
        """
        Cria instância de uma estratégia
        
        Args:
            key: Chave da estratégia
            **params: Parâmetros personalizados
            
        Returns:
            Instância da estratégia ou None se não encontrada
        """
        if key not in cls._strategies:
            return None
        
        strategy_config = cls._strategies[key]
        factory = strategy_config['factory']
        
        # Mesclar parâmetros padrão com personalizados
        final_params = strategy_config['default_params'].copy()
        final_params.update(params)
        
        return factory(**final_params)
    
    @classmethod
    def list_strategies(cls) -> List[str]:
        """Lista todas as estratégias registradas"""
        return list(cls._strategies.keys())
    
    @classmethod
    def get_strategy_info(cls, key: str) -> Optional[Dict]:
        """Retorna informações de uma estratégia"""
        if key not in cls._strategies:
            return None
        
        strategy_config = cls._strategies[key]
        strategy_instance = cls.get_strategy(key)
        
        if strategy_instance:
            return strategy_instance.get_strategy_info()
        
        return None
    
    @classmethod
    def get_all_strategies_info(cls) -> Dict[str, Dict]:
        """Retorna informações de todas as estratégias"""
        return {
            key: cls.get_strategy_info(key)
            for key in cls._strategies.keys()
        }


# Decorador para registro automático de estratégias
def register_strategy(strategy_config: Dict):
    """
    Decorador para registro automático de estratégias
    
    Args:
        strategy_config: Configuração da estratégia
    """
    def decorator(strategy_class):
        StrategyRegistry.register(strategy_config)
        return strategy_class
    return decorator

