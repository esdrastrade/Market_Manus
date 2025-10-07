"""
Volume Filter - Filtra e amplifica sinais baseado em volume
Normaliza volume via z-score e ajusta confidence de sinais
"""

import pandas as pd
import numpy as np
from typing import List, Optional
from market_manus.core.signal import Signal


class VolumeFilter:
    """
    Filtro de volume para sinais de trading
    
    - Rejeita sinais com baixo volume (z-score < threshold_reject)
    - Amplifica confiança com alto volume (z-score > threshold_boost)
    - Mantém sinais normais inalterados
    """
    
    def __init__(
        self,
        threshold_reject: float = 0.5,
        threshold_boost: float = 1.5,
        boost_factor: float = 1.3,
        lookback_period: int = 50
    ):
        """
        Args:
            threshold_reject: Z-score abaixo do qual sinais são rejeitados (padrão 0.5)
            threshold_boost: Z-score acima do qual sinais são amplificados (padrão 1.5)
            boost_factor: Fator de amplificação para alto volume (padrão 1.3x)
            lookback_period: Período para cálculo de z-score (padrão 50)
        """
        self.threshold_reject = threshold_reject
        self.threshold_boost = threshold_boost
        self.boost_factor = boost_factor
        self.lookback_period = lookback_period
    
    def calculate_volume_zscore(self, volumes: pd.Series) -> pd.Series:
        """
        Calcula z-score do volume
        
        Args:
            volumes: Série de volumes
            
        Returns:
            Série de z-scores
        """
        # Calcular média e desvio padrão móvel
        mean = volumes.rolling(window=self.lookback_period).mean()
        std = volumes.rolling(window=self.lookback_period).std()
        
        # Z-score = (valor - média) / desvio padrão
        zscore = (volumes - mean) / std
        
        # Preencher NaN com 0
        zscore = zscore.fillna(0)
        
        return zscore
    
    def filter_signal(
        self,
        signal: Signal,
        volume_zscore: float
    ) -> Optional[Signal]:
        """
        Filtra ou amplifica um sinal baseado no z-score de volume
        
        Args:
            signal: Sinal original
            volume_zscore: Z-score do volume no momento do sinal
            
        Returns:
            Sinal modificado ou None se rejeitado
        """
        if signal.action == "HOLD":
            return signal
        
        # REJEITAR sinais com baixo volume
        if volume_zscore < self.threshold_reject:
            # Adicionar razão de rejeição
            rejection_reason = f"Volume insuficiente (z-score: {volume_zscore:.2f})"
            
            # Retornar sinal HOLD com razão
            return Signal(
                action="HOLD",
                confidence=0.0,
                reasons=[rejection_reason] + signal.reasons,
                tags=signal.tags + ["VOLUME_REJECTED"],
                metadata={
                    **signal.metadata,
                    "original_action": signal.action,
                    "original_confidence": signal.confidence,
                    "volume_zscore": volume_zscore,
                    "rejection_reason": rejection_reason
                }
            )
        
        # AMPLIFICAR sinais com alto volume
        elif volume_zscore > self.threshold_boost:
            boosted_confidence = min(signal.confidence * self.boost_factor, 1.0)
            
            # Criar novo sinal amplificado
            return Signal(
                action=signal.action,
                confidence=boosted_confidence,
                reasons=signal.reasons + [f"Alto volume (z-score: {volume_zscore:.2f})"],
                tags=signal.tags + ["VOLUME_BOOSTED"],
                metadata={
                    **signal.metadata,
                    "original_confidence": signal.confidence,
                    "volume_zscore": volume_zscore,
                    "boost_factor": self.boost_factor
                }
            )
        
        # MANTER sinal normal
        else:
            # Adicionar metadata de volume sem modificar
            return Signal(
                action=signal.action,
                confidence=signal.confidence,
                reasons=signal.reasons,
                tags=signal.tags + ["VOLUME_NORMAL"],
                metadata={
                    **signal.metadata,
                    "volume_zscore": volume_zscore
                }
            )
    
    def filter_signals_batch(
        self,
        signal_indices: List[int],
        volumes: pd.Series,
        signal_generator_func
    ) -> List[int]:
        """
        Filtra batch de sinais baseado em volume
        
        Args:
            signal_indices: Lista de índices onde sinais ocorreram
            volumes: Série completa de volumes
            signal_generator_func: Função que gera Signal para um índice
            
        Returns:
            Lista de índices de sinais que passaram no filtro
        """
        # Calcular z-scores para todo o período
        volume_zscores = self.calculate_volume_zscore(volumes)
        
        filtered_indices = []
        
        for idx in signal_indices:
            if idx >= len(volume_zscores):
                continue
            
            # Obter z-score do volume neste índice
            zscore = volume_zscores.iloc[idx]
            
            # Gerar sinal original
            signal = signal_generator_func(idx)
            
            # Filtrar baseado em volume
            filtered_signal = self.filter_signal(signal, zscore)
            
            # Manter índice se sinal não foi rejeitado
            if filtered_signal and filtered_signal.action != "HOLD":
                filtered_indices.append(idx)
        
        return filtered_indices
    
    def analyze_volume_distribution(self, volumes: pd.Series) -> dict:
        """
        Analisa distribuição de volume para ajuste de thresholds
        
        Args:
            volumes: Série de volumes
            
        Returns:
            Dict com estatísticas de distribuição
        """
        zscores = self.calculate_volume_zscore(volumes)
        
        # Remover NaN
        zscores_clean = zscores.dropna()
        
        if len(zscores_clean) == 0:
            return {}
        
        return {
            "mean_volume": volumes.mean(),
            "std_volume": volumes.std(),
            "mean_zscore": zscores_clean.mean(),
            "std_zscore": zscores_clean.std(),
            "percentile_25": zscores_clean.quantile(0.25),
            "percentile_50": zscores_clean.quantile(0.50),
            "percentile_75": zscores_clean.quantile(0.75),
            "below_reject_threshold": (zscores_clean < self.threshold_reject).sum(),
            "above_boost_threshold": (zscores_clean > self.threshold_boost).sum(),
            "total_candles": len(zscores_clean)
        }
    
    def display_filter_stats(self, volumes: pd.Series):
        """Exibe estatísticas do filtro de volume"""
        stats = self.analyze_volume_distribution(volumes)
        
        if not stats:
            print("⚠️ Dados insuficientes para análise de volume")
            return
        
        print("\n" + "=" * 60)
        print("📊 ANÁLISE DE VOLUME - FILTRO CONFIGURADO")
        print("=" * 60)
        
        # Formatar volume com detecção automática de escala
        mean_vol = stats['mean_volume']
        std_vol = stats['std_volume']
        
        # Escolher formato baseado na magnitude (corrigido para volumes fracionários)
        if mean_vol >= 1000:
            vol_format = f"{mean_vol:,.2f}"
        elif mean_vol >= 1:
            vol_format = f"{mean_vol:.2f}"
        elif mean_vol >= 0.000001:  # Mostrar até 6 decimais para volumes pequenos
            vol_format = f"{mean_vol:.6f}"
        else:  # Apenas valores extremamente pequenos usam notação científica
            vol_format = f"{mean_vol:.2e}"
        
        # Formato do desvio padrão baseado em sua própria magnitude
        if std_vol >= 1000:
            std_format = f"{std_vol:,.2f}"
        elif std_vol >= 1:
            std_format = f"{std_vol:.2f}"
        elif std_vol >= 0.000001:
            std_format = f"{std_vol:.6f}"
        else:
            std_format = f"{std_vol:.2e}"
        
        print(f"\n📈 Distribuição de Volume:")
        print(f"   Média: {vol_format}")
        print(f"   Desvio Padrão: {std_format}")
        
        print(f"\n📉 Distribuição de Z-Score:")
        print(f"   Média: {stats['mean_zscore']:.2f}")
        print(f"   25º Percentil: {stats['percentile_25']:.2f}")
        print(f"   50º Percentil: {stats['percentile_50']:.2f}")
        print(f"   75º Percentil: {stats['percentile_75']:.2f}")
        
        reject_pct = (stats['below_reject_threshold'] / stats['total_candles']) * 100
        boost_pct = (stats['above_boost_threshold'] / stats['total_candles']) * 100
        
        print(f"\n⚙️ Configuração do Filtro:")
        print(f"   Threshold Rejeição: {self.threshold_reject}")
        print(f"   Threshold Amplificação: {self.threshold_boost}")
        print(f"   Fator de Amplificação: {self.boost_factor}x")
        
        print(f"\n🎯 Impacto Estimado:")
        print(f"   Candles com volume BAIXO: {stats['below_reject_threshold']} ({reject_pct:.1f}%)")
        print(f"   Candles com volume ALTO: {stats['above_boost_threshold']} ({boost_pct:.1f}%)")
        print(f"   Candles com volume NORMAL: {stats['total_candles'] - stats['below_reject_threshold'] - stats['above_boost_threshold']}")
        
        print("=" * 60)


class VolumeFilterPipeline:
    """
    Pipeline de aplicação de filtro de volume para múltiplas estratégias
    Integra-se facilmente com sistemas existentes
    """
    
    def __init__(self, volume_filter: VolumeFilter = None):
        """
        Args:
            volume_filter: Instância de VolumeFilter (cria padrão se None)
        """
        self.volume_filter = volume_filter or VolumeFilter()
        self.stats = {
            "signals_received": 0,
            "signals_rejected": 0,
            "signals_boosted": 0,
            "signals_passed": 0
        }
    
    def apply_to_strategy_signals(
        self,
        strategy_signals: dict,
        volumes: pd.Series
    ) -> dict:
        """
        Aplica filtro de volume a sinais de múltiplas estratégias
        
        ATUALIZADO (Out 2025 - Fase 2): Suporta tuplas (índice, direção)
        
        Args:
            strategy_signals: Dict {strategy_key: {"signal_indices": [(idx, dir), ...] ou [idx, ...], ...}}
            volumes: Série de volumes
            
        Returns:
            Dict com sinais filtrados (mesmo formato, preserva tuplas se presente)
        """
        # Calcular z-scores uma vez
        volume_zscores = self.volume_filter.calculate_volume_zscore(volumes)
        
        filtered_signals = {}
        
        for strategy_key, data in strategy_signals.items():
            signal_indices = data.get("signal_indices", [])
            
            self.stats["signals_received"] += len(signal_indices)
            
            # Filtrar índices baseado em volume
            filtered_indices = []
            
            for signal_item in signal_indices:
                # FASE 2: Desempacotar tupla (índice, direção) se presente
                if isinstance(signal_item, tuple):
                    idx, direction = signal_item
                else:
                    idx = signal_item
                    direction = None
                
                if idx >= len(volume_zscores):
                    continue
                
                zscore = volume_zscores.iloc[idx]
                
                # Aplicar critérios de filtro
                if zscore < self.volume_filter.threshold_reject:
                    self.stats["signals_rejected"] += 1
                    continue  # Rejeitar
                
                elif zscore > self.volume_filter.threshold_boost:
                    self.stats["signals_boosted"] += 1
                    # Preservar formato original (tupla ou int)
                    if direction is not None:
                        filtered_indices.append((idx, direction))
                    else:
                        filtered_indices.append(idx)
                
                else:
                    self.stats["signals_passed"] += 1
                    # Preservar formato original (tupla ou int)
                    if direction is not None:
                        filtered_indices.append((idx, direction))
                    else:
                        filtered_indices.append(idx)
            
            # Criar entrada filtrada
            filtered_signals[strategy_key] = {
                **data,
                "signal_indices": filtered_indices,
                "volume_filtered": True,
                "original_count": len(signal_indices),
                "filtered_count": len(filtered_indices)
            }
        
        return filtered_signals
    
    def get_stats_summary(self) -> str:
        """Retorna resumo das estatísticas do pipeline"""
        total = self.stats["signals_received"]
        if total == 0:
            return "Nenhum sinal processado"
        
        rejected_pct = (self.stats["signals_rejected"] / total) * 100
        boosted_pct = (self.stats["signals_boosted"] / total) * 100
        passed_pct = (self.stats["signals_passed"] / total) * 100
        
        return (
            f"📊 Filtro de Volume:\n"
            f"   Total: {total} sinais\n"
            f"   ❌ Rejeitados: {self.stats['signals_rejected']} ({rejected_pct:.1f}%)\n"
            f"   📈 Amplificados: {self.stats['signals_boosted']} ({boosted_pct:.1f}%)\n"
            f"   ✅ Normais: {self.stats['signals_passed']} ({passed_pct:.1f}%)"
        )
    
    def reset_stats(self):
        """Reseta estatísticas do pipeline"""
        self.stats = {
            "signals_received": 0,
            "signals_rejected": 0,
            "signals_boosted": 0,
            "signals_passed": 0
        }
