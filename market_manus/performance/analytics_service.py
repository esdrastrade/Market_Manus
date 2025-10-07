from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from .history_repository import PerformanceHistoryRepository, WeightRecommendation

class PerformanceAnalyticsService:
    """Serviço de análise de performance histórica"""
    
    def __init__(self, repository: PerformanceHistoryRepository):
        self.repository = repository
    
    def get_combination_win_rate(self, combination_id: str, timeframe: str, days: Optional[int] = None) -> Dict:
        """Calcula win rate de uma combinação com janelas temporais"""
        history = self.repository.get_combination_history(combination_id, timeframe, days)
        
        if not history:
            return {
                'has_data': False,
                'win_rate': None,
                'total_trades': 0,
                'test_count': 0
            }
        
        total_trades = sum(h['total_trades'] for h in history)
        total_winning = sum(h['winning_trades'] for h in history)
        win_rate = (total_winning / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'has_data': True,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'test_count': len(history),
            'avg_roi': sum(h['roi'] for h in history) / len(history),
            'last_test_date': history[0]['timestamp'] if history else None
        }
    
    def get_rolling_win_rates(self, combination_id: str, timeframe: str) -> Dict:
        """Retorna win rates em diferentes janelas temporais"""
        return {
            'last_7_days': self.get_combination_win_rate(combination_id, timeframe, 7),
            'last_30_days': self.get_combination_win_rate(combination_id, timeframe, 30),
            'all_time': self.get_combination_win_rate(combination_id, timeframe, None)
        }
    
    def get_all_combinations_win_rates(self) -> Dict[str, Dict]:
        """Retorna win rates de todas as combinações"""
        return self.repository.get_all_combinations_summary()
    
    def calculate_weight_recommendations(
        self, 
        backtest_id: str, 
        current_weights: Dict[str, float]
    ) -> List[WeightRecommendation]:
        """Calcula recomendações de ajuste de pesos baseado em performance"""
        contributions = self.repository.get_strategy_contribution_history(backtest_id)
        
        if not contributions:
            return []
        
        recommendations = []
        
        # Calcular win rate médio geral
        total_winning = sum(c['winning_signals'] for c in contributions)
        total_losing = sum(c['losing_signals'] for c in contributions)
        overall_win_rate = (total_winning / (total_winning + total_losing) * 100) if (total_winning + total_losing) > 0 else 0
        
        for contrib in contributions:
            strategy_key = contrib['strategy_key']
            strategy_name = contrib['strategy_name']
            strategy_win_rate = contrib['win_rate']
            current_weight = contrib['weight']
            
            # Ignorar estratégias com poucos sinais
            if contrib['signals_after_volume_filter'] < 10:
                continue
            
            # Calcular delta de performance
            performance_delta = strategy_win_rate - overall_win_rate
            
            # Recomendação de ajuste
            if performance_delta > 15:  # 15%+ acima da média
                recommended_weight = min(current_weight * 1.3, 2.0)
                reason = f"Win rate {strategy_win_rate:.1f}% está {performance_delta:.1f}% acima da média geral"
                confidence = min(abs(performance_delta) / 20, 1.0)
            elif performance_delta > 5:  # 5-15% acima da média
                recommended_weight = min(current_weight * 1.15, 1.5)
                reason = f"Performance {performance_delta:.1f}% acima da média"
                confidence = min(abs(performance_delta) / 20, 1.0)
            elif performance_delta < -15:  # 15%+ abaixo da média
                recommended_weight = max(current_weight * 0.7, 0.5)
                reason = f"Win rate {strategy_win_rate:.1f}% está {abs(performance_delta):.1f}% abaixo da média geral"
                confidence = min(abs(performance_delta) / 20, 1.0)
            elif performance_delta < -5:  # 5-15% abaixo da média
                recommended_weight = max(current_weight * 0.85, 0.7)
                reason = f"Performance {abs(performance_delta):.1f}% abaixo da média"
                confidence = min(abs(performance_delta) / 20, 1.0)
            else:
                # Performance próxima à média, manter peso
                recommended_weight = current_weight
                reason = f"Performance equilibrada ({strategy_win_rate:.1f}%)"
                confidence = 0.5
            
            # Só adicionar se houver mudança significativa
            if abs(recommended_weight - current_weight) >= 0.1:
                recommendations.append(WeightRecommendation(
                    strategy_key=strategy_key,
                    strategy_name=strategy_name,
                    current_weight=current_weight,
                    recommended_weight=round(recommended_weight, 2),
                    reason=reason,
                    confidence=round(confidence, 2)
                ))
        
        # Ordenar por confidence (mais confiante primeiro)
        recommendations.sort(key=lambda x: x.confidence, reverse=True)
        
        return recommendations
    
    def format_win_rate_display(self, combination_id: str, timeframe: str, target_win_rate: str) -> str:
        """Formata display de win rate para menu (histórico + target)"""
        rolling = self.get_rolling_win_rates(combination_id, timeframe)
        
        # Priorizar dados dos últimos 30 dias
        recent = rolling['last_30_days']
        all_time = rolling['all_time']
        
        if recent['has_data'] and recent['total_trades'] >= 20:
            # Dados recentes suficientes
            return f"📊 Win Rate: {recent['win_rate']:.1f}% (últimos 30d: {recent['total_trades']} trades) | Target: {target_win_rate}"
        elif all_time['has_data'] and all_time['total_trades'] >= 10:
            # Usar histórico completo
            return f"📊 Win Rate: {all_time['win_rate']:.1f}% (histórico: {all_time['total_trades']} trades) | Target: {target_win_rate}"
        else:
            # Sem dados históricos, mostrar apenas target
            return f"📊 Win Rate: {target_win_rate} (target - sem histórico)"
