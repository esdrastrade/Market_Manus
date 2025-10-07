import os
from typing import Dict, List, Optional
from openai import OpenAI

class SemanticKernelAdvisor:
    """Advisor de IA usando Semantic Kernel/OpenAI para recomendações"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.enabled = bool(self.api_key)
    
    def is_available(self) -> bool:
        """Verifica se o advisor está disponível"""
        return self.enabled and self.client is not None
    
    def generate_recommendations(
        self,
        backtest_summary: Dict,
        strategy_contributions: List[Dict],
        weight_recommendations: List[Dict]
    ) -> str:
        """Gera recomendações textuais baseadas nos resultados do backtest"""
        
        if not self.is_available():
            return "❌ Semantic Kernel não disponível (OPENAI_API_KEY não configurada)"
        
        # Construir contexto para o modelo
        context = self._build_context(backtest_summary, strategy_contributions, weight_recommendations)
        
        # Prompt para o modelo
        prompt = f"""Você é um especialista em trading quantitativo e análise de estratégias de confluência.

Analise os resultados do backtest abaixo e forneça recomendações PRÁTICAS e ACIONÁVEIS para melhorar o win rate:

{context}

Forneça recomendações em português brasileiro, estruturadas em:

1. DIAGNÓSTICO (2-3 frases sobre o que os dados revelam)
2. RECOMENDAÇÕES DE PESOS (quais ajustar e por quê)
3. OTIMIZAÇÕES ADICIONAIS (outras melhorias sugeridas: timeframe, modo confluência, etc)
4. PRÓXIMOS PASSOS (ações concretas)

Seja direto, prático e baseie-se nos dados fornecidos. Limite a 400 palavras."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um especialista em trading quantitativo, análise técnica e otimização de estratégias."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            return f"❌ Erro ao gerar recomendações: {str(e)}"
    
    def _build_context(
        self,
        backtest_summary: Dict,
        strategy_contributions: List[Dict],
        weight_recommendations: List[Dict]
    ) -> str:
        """Constrói contexto formatado para o modelo"""
        
        context = f"""
RESUMO DO BACKTEST:
- Ativo: {backtest_summary.get('asset', 'N/A')}
- Timeframe: {backtest_summary.get('timeframe', 'N/A')}
- Período: {backtest_summary.get('start_date', 'N/A')} até {backtest_summary.get('end_date', 'N/A')}
- Modo: {backtest_summary.get('confluence_mode', 'N/A')}
- Win Rate: {backtest_summary.get('win_rate', 0):.1f}%
- Total Trades: {backtest_summary.get('total_trades', 0)}
- ROI: {backtest_summary.get('roi', 0):.2f}%
- Capital: ${backtest_summary.get('initial_capital', 0):.2f} → ${backtest_summary.get('final_capital', 0):.2f}

CONTRIBUIÇÃO DAS ESTRATÉGIAS:
"""
        
        for contrib in strategy_contributions:
            context += f"\n- {contrib.get('strategy_name', 'Unknown')}:"
            context += f"\n  • Sinais (após filtro): {contrib.get('signals_after_volume_filter', 0)}"
            context += f"\n  • Win Rate: {contrib.get('win_rate', 0):.1f}%"
            context += f"\n  • Peso atual: {contrib.get('weight', 1.0):.2f}"
            context += f"\n  • Trades vencedores: {contrib.get('winning_signals', 0)} | Perdedores: {contrib.get('losing_signals', 0)}"
        
        if weight_recommendations:
            context += "\n\nRECOMENDAÇÕES DE PESO (AUTOMÁTICAS):\n"
            for rec in weight_recommendations[:5]:  # Top 5
                context += f"\n- {rec.get('strategy_name', 'Unknown')}: {rec.get('current_weight', 1.0):.2f} → {rec.get('recommended_weight', 1.0):.2f}"
                context += f"\n  Razão: {rec.get('reason', 'N/A')}"
                context += f"\n  Confiança: {rec.get('confidence', 0)*100:.0f}%"
        
        return context
    
    def get_status_display(self) -> str:
        """Retorna status formatado para exibição"""
        if self.is_available():
            return "✅ Disponível (OPENAI_API_KEY configurada)"
        else:
            return "❌ Indisponível (OPENAI_API_KEY não configurada)"
