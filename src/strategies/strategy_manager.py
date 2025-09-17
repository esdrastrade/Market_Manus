#!/usr/bin/env python3
"""
STRATEGY MANAGER - Gerenciador Dinâmico de Estratégias
Sistema para carregar, combinar e gerenciar estratégias de trading
"""

import importlib
import inspect
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.base_strategy import BaseStrategy, StrategyRegistry


class StrategyManager:
    """Gerenciador dinâmico de estratégias"""

    def __init__(self, strategies_dir: str = "src/strategies"):
        """
        Inicializa o gerenciador de estratégias

        Args:
            strategies_dir: Diretório onde estão as estratégias
        """
        self.strategies_dir = Path(strategies_dir)
        self.loaded_strategies: Dict[str, BaseStrategy] = {}

        # Carregar estratégias automaticamente
        self._load_all_strategies()

    def _load_all_strategies(self):
        """Carrega todas as estratégias do diretório"""
        if not self.strategies_dir.exists():
            print(f"⚠️ Diretório de estratégias não encontrado: {self.strategies_dir}")
            return

        # Procurar por arquivos Python no diretório de estratégias
        strategy_files = list(self.strategies_dir.glob("*_strategy.py"))

        for strategy_file in strategy_files:
            try:
                self._load_strategy_from_file(strategy_file)
            except Exception as e:
                print(f"❌ Erro ao carregar estratégia {strategy_file.name}: {e}")

    def _load_strategy_from_file(self, strategy_file: Path):
        """
        Carrega uma estratégia de um arquivo

        Args:
            strategy_file: Caminho para o arquivo da estratégia
        """
        # Importar módulo dinamicamente
        module_name = strategy_file.stem
        spec = importlib.util.spec_from_file_location(module_name, strategy_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Procurar por configuração STRATEGY_CONFIG
        if hasattr(module, "STRATEGY_CONFIG"):
            config = module.STRATEGY_CONFIG

            # Registrar estratégia
            StrategyRegistry.register(config)

            # Criar instância padrão
            strategy_instance = StrategyRegistry.get_strategy(config["key"])
            if strategy_instance:
                self.loaded_strategies[config["key"]] = strategy_instance
                print(f"✅ Estratégia carregada: {config['key']}")
        else:
            print(f"⚠️ Arquivo {strategy_file.name} não possui STRATEGY_CONFIG")

    def get_strategy(self, strategy_key: str, **params) -> Optional[BaseStrategy]:
        """
        Obtém uma estratégia por chave

        Args:
            strategy_key: Chave da estratégia
            **params: Parâmetros personalizados

        Returns:
            Instância da estratégia ou None se não encontrada
        """
        if params:
            # Criar nova instância com parâmetros personalizados
            return StrategyRegistry.get_strategy(strategy_key, **params)
        else:
            # Retornar instância padrão carregada
            return self.loaded_strategies.get(strategy_key)

    def list_strategies(self) -> List[str]:
        """Lista todas as estratégias disponíveis"""
        return list(self.loaded_strategies.keys())

    def get_strategy_info(self, strategy_key: str) -> Optional[Dict]:
        """
        Obtém informações de uma estratégia

        Args:
            strategy_key: Chave da estratégia

        Returns:
            Informações da estratégia ou None se não encontrada
        """
        strategy = self.loaded_strategies.get(strategy_key)
        if strategy:
            return strategy.get_strategy_info()
        return None

    def get_all_strategies_info(self) -> Dict[str, Dict]:
        """Obtém informações de todas as estratégias"""
        return {
            key: strategy.get_strategy_info()
            for key, strategy in self.loaded_strategies.items()
        }

    def combine_strategies(
        self, strategy_keys: List[str], data: List[Dict]
    ) -> List[Dict]:
        """
        Combina sinais de múltiplas estratégias

        Args:
            strategy_keys: Lista de chaves das estratégias
            data: Dados históricos OHLCV

        Returns:
            Dados com sinais combinados
        """
        if not strategy_keys:
            return data

        if len(strategy_keys) == 1:
            # Estratégia única
            strategy = self.get_strategy(strategy_keys[0])
            if strategy:
                return strategy.calculate_signals(data)
            else:
                return data

        # Múltiplas estratégias - combinar sinais
        all_signals = []

        for strategy_key in strategy_keys:
            strategy = self.get_strategy(strategy_key)
            if strategy:
                signals = strategy.calculate_signals(data)
                all_signals.append(signals)

        if not all_signals:
            return data

        # Combinar sinais usando votação majoritária
        combined_data = []

        for i in range(len(data)):
            # Coletar sinais de todas as estratégias para este ponto
            signals_at_point = []
            strengths_at_point = []

            for strategy_signals in all_signals:
                if i < len(strategy_signals):
                    signal = strategy_signals[i].get("signal", 0)
                    strength = strategy_signals[i].get("signal_strength", 0.0)
                    signals_at_point.append(signal)
                    strengths_at_point.append(strength)

            # Calcular sinal combinado
            combined_signal = self._combine_signals(
                signals_at_point, strengths_at_point
            )
            combined_strength = self._combine_strengths(
                signals_at_point, strengths_at_point
            )

            # Adicionar dados combinados
            combined_data.append(
                {
                    **data[i],
                    "signal": combined_signal,
                    "signal_strength": combined_strength,
                    "strategy": f"combo_{'+'.join(strategy_keys)}",
                    "individual_signals": signals_at_point,
                    "individual_strengths": strengths_at_point,
                }
            )

        return combined_data

    def _combine_signals(self, signals: List[int], strengths: List[float]) -> int:
        """
        Combina sinais usando votação ponderada por força

        Args:
            signals: Lista de sinais (-1, 0, 1)
            strengths: Lista de forças dos sinais (0.0 - 1.0)

        Returns:
            Sinal combinado
        """
        if not signals:
            return 0

        # Calcular votos ponderados
        long_weight = 0.0
        short_weight = 0.0

        for signal, strength in zip(signals, strengths):
            if signal == 1:  # Long
                long_weight += strength
            elif signal == -1:  # Short
                short_weight += strength

        # Determinar sinal final
        if long_weight > short_weight and long_weight > 0.5:
            return 1
        elif short_weight > long_weight and short_weight > 0.5:
            return -1
        else:
            return 0

    def _combine_strengths(self, signals: List[int], strengths: List[float]) -> float:
        """
        Combina forças dos sinais

        Args:
            signals: Lista de sinais
            strengths: Lista de forças

        Returns:
            Força combinada
        """
        if not signals or not strengths:
            return 0.0

        # Calcular força média dos sinais não-zero
        active_strengths = [
            strength for signal, strength in zip(signals, strengths) if signal != 0
        ]

        if active_strengths:
            return sum(active_strengths) / len(active_strengths)
        else:
            return 0.0

    def validate_strategy_combination(self, strategy_keys: List[str]) -> Dict[str, Any]:
        """
        Valida se uma combinação de estratégias é viável

        Args:
            strategy_keys: Lista de chaves das estratégias

        Returns:
            Resultado da validação
        """
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": [],
        }

        # Verificar se todas as estratégias existem
        missing_strategies = []
        existing_strategies = []

        for key in strategy_keys:
            if key in self.loaded_strategies:
                existing_strategies.append(key)
            else:
                missing_strategies.append(key)

        if missing_strategies:
            validation_result["valid"] = False
            validation_result["errors"].append(
                f"Estratégias não encontradas: {missing_strategies}"
            )

        if not existing_strategies:
            validation_result["valid"] = False
            validation_result["errors"].append(
                "Nenhuma estratégia válida na combinação"
            )
            return validation_result

        # Analisar compatibilidade das estratégias
        risk_levels = []
        timeframes = []
        market_conditions = []

        for key in existing_strategies:
            strategy = self.loaded_strategies[key]
            info = strategy.get_strategy_info()

            risk_levels.append(info["risk_level"])
            timeframes.extend(info["best_timeframes"])
            market_conditions.append(info["market_conditions"])

        # Verificar compatibilidade de risco
        unique_risks = set(risk_levels)
        if len(unique_risks) > 2:
            validation_result["warnings"].append(
                "Combinação com níveis de risco muito diversos"
            )

        if "high" in unique_risks and "low" in unique_risks:
            validation_result["warnings"].append(
                "Combinação de estratégias de alto e baixo risco"
            )

        # Verificar compatibilidade de timeframes
        common_timeframes = set(timeframes)
        if len(common_timeframes) < 2:
            validation_result["warnings"].append("Poucas opções de timeframe em comum")

        # Verificar compatibilidade de condições de mercado
        unique_conditions = set(market_conditions)
        if len(unique_conditions) > 1:
            validation_result["recommendations"].append(
                "Estratégias otimizadas para condições de mercado diferentes"
            )

        # Recomendações baseadas no número de estratégias
        if len(existing_strategies) > 3:
            validation_result["warnings"].append(
                "Muitas estratégias podem gerar sinais conflitantes"
            )

        if len(existing_strategies) == 1:
            validation_result["recommendations"].append(
                "Considere adicionar estratégia complementar"
            )

        return validation_result

    def get_strategy_combinations(self) -> Dict[str, List[List[str]]]:
        """
        Gera todas as combinações possíveis de estratégias

        Returns:
            Dicionário com combinações organizadas por tipo
        """
        strategies = self.list_strategies()

        combinations = {
            "single": [[s] for s in strategies],
            "dual": [],
            "triple": [],
            "full": [strategies] if len(strategies) > 1 else [],
        }

        # Combinações duplas
        for i in range(len(strategies)):
            for j in range(i + 1, len(strategies)):
                combinations["dual"].append([strategies[i], strategies[j]])

        # Combinações triplas
        if len(strategies) >= 3:
            for i in range(len(strategies)):
                for j in range(i + 1, len(strategies)):
                    for k in range(j + 1, len(strategies)):
                        combinations["triple"].append(
                            [strategies[i], strategies[j], strategies[k]]
                        )

        return combinations

    def reload_strategies(self):
        """Recarrega todas as estratégias"""
        self.loaded_strategies.clear()
        self._load_all_strategies()
        print(f"✅ {len(self.loaded_strategies)} estratégias recarregadas")

    def add_strategy_from_code(self, strategy_code: str, strategy_key: str):
        """
        Adiciona uma estratégia a partir de código Python

        Args:
            strategy_code: Código Python da estratégia
            strategy_key: Chave única para a estratégia
        """
        # Esta funcionalidade permite adicionar estratégias dinamicamente
        # Útil para desenvolvimento e testes de novas estratégias
        try:
            # Executar código em namespace isolado
            namespace = {}
            exec(strategy_code, namespace)

            # Procurar por classe que herda de BaseStrategy
            strategy_class = None
            for name, obj in namespace.items():
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BaseStrategy)
                    and obj != BaseStrategy
                ):
                    strategy_class = obj
                    break

            if strategy_class:
                # Criar instância e registrar
                strategy_instance = strategy_class()
                self.loaded_strategies[strategy_key] = strategy_instance
                print(f"✅ Estratégia {strategy_key} adicionada dinamicamente")
            else:
                print(f"❌ Nenhuma classe de estratégia válida encontrada no código")

        except Exception as e:
            print(f"❌ Erro ao adicionar estratégia {strategy_key}: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do gerenciador de estratégias"""
        strategies = self.list_strategies()

        risk_distribution = {}
        timeframe_usage = {}
        market_condition_distribution = {}

        for key in strategies:
            info = self.get_strategy_info(key)

            # Distribuição de risco
            risk = info["risk_level"]
            risk_distribution[risk] = risk_distribution.get(risk, 0) + 1

            # Uso de timeframes
            for tf in info["best_timeframes"]:
                timeframe_usage[tf] = timeframe_usage.get(tf, 0) + 1

            # Condições de mercado
            condition = info["market_conditions"]
            market_condition_distribution[condition] = (
                market_condition_distribution.get(condition, 0) + 1
            )

        combinations = self.get_strategy_combinations()

        return {
            "total_strategies": len(strategies),
            "risk_distribution": risk_distribution,
            "timeframe_usage": timeframe_usage,
            "market_condition_distribution": market_condition_distribution,
            "possible_combinations": {
                "single": len(combinations["single"]),
                "dual": len(combinations["dual"]),
                "triple": len(combinations["triple"]),
                "total": len(combinations["single"])
                + len(combinations["dual"])
                + len(combinations["triple"]),
            },
        }
