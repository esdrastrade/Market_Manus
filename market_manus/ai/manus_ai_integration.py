"""
Manus AI Integration Module
Provides premium AI-powered market analysis and strategy enhancement
"""
import os
import json
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd


class ManusAIAnalyzer:
    """
    Premium AI layer for market data analysis using Manus AI
    Enhances strategy signals and provides intelligent market insights
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('MANUS_AI_API_KEY')
        self.api_url = "https://api.manus.im/apiproxy.v1.ApiProxyService/CallApi"
        self.enabled = bool(self.api_key)
        
    def is_enabled(self) -> bool:
        """Check if Manus AI is enabled and configured"""
        return self.enabled and self.api_key is not None
    
    async def analyze_market_context(
        self, 
        df: pd.DataFrame, 
        symbol: str,
        strategies_votes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze market context using AI to enhance strategy decisions
        
        Args:
            df: OHLCV dataframe
            symbol: Trading symbol
            strategies_votes: Current strategy votes/signals
            
        Returns:
            AI-enhanced analysis with recommendations
        """
        if not self.is_enabled():
            return self._get_fallback_response()
        
        try:
            market_summary = self._prepare_market_summary(df, symbol)
            strategies_summary = self._prepare_strategies_summary(strategies_votes)
            
            prompt = self._build_analysis_prompt(market_summary, strategies_summary, symbol)
            
            ai_response = await self._call_manus_api(prompt)
            
            return self._parse_ai_response(ai_response)
            
        except Exception as e:
            print(f"⚠️ Manus AI Error: {e}")
            return self._get_fallback_response()
    
    def _prepare_market_summary(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Prepare concise market data summary for AI analysis"""
        latest = df.iloc[-1]
        prev_20 = df.iloc[-20:]
        
        return {
            "symbol": symbol,
            "current_price": float(latest['close']),
            "price_change_20": float((latest['close'] - prev_20.iloc[0]['close']) / prev_20.iloc[0]['close'] * 100),
            "volume_avg_20": float(prev_20['volume'].mean()),
            "volume_current": float(latest['volume']),
            "high_20": float(prev_20['high'].max()),
            "low_20": float(prev_20['low'].min()),
            "volatility": float(prev_20['close'].pct_change().std() * 100),
            "timestamp": datetime.now().isoformat()
        }
    
    def _prepare_strategies_summary(self, strategies_votes: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare strategies votes summary for AI analysis"""
        buy_count = sum(1 for v in strategies_votes.values() if v.get('action') == 'BUY')
        sell_count = sum(1 for v in strategies_votes.values() if v.get('action') == 'SELL')
        neutral_count = len(strategies_votes) - buy_count - sell_count
        
        return {
            "total_strategies": len(strategies_votes),
            "buy_signals": buy_count,
            "sell_signals": sell_count,
            "neutral_signals": neutral_count,
            "strategies_detail": {
                name: {
                    "action": vote.get('action', 'NEUTRAL'),
                    "confidence": vote.get('confidence', 0.5)
                }
                for name, vote in strategies_votes.items()
            }
        }
    
    def _build_analysis_prompt(
        self, 
        market_summary: Dict[str, Any], 
        strategies_summary: Dict[str, Any],
        symbol: str
    ) -> str:
        """Build comprehensive analysis prompt for Manus AI"""
        return f"""Analyze this cryptocurrency market data and trading signals for {symbol}:

MARKET DATA:
- Current Price: ${market_summary['current_price']:.2f}
- 20-Period Change: {market_summary['price_change_20']:.2f}%
- Volatility: {market_summary['volatility']:.2f}%
- Volume (Current): {market_summary['volume_current']:,.0f}
- Volume (Avg 20): {market_summary['volume_avg_20']:,.0f}
- High (20): ${market_summary['high_20']:.2f}
- Low (20): ${market_summary['low_20']:.2f}

STRATEGY SIGNALS:
- Total Strategies: {strategies_summary['total_strategies']}
- BUY Signals: {strategies_summary['buy_signals']}
- SELL Signals: {strategies_summary['sell_signals']}
- NEUTRAL Signals: {strategies_summary['neutral_signals']}

DETAILED SIGNALS:
{json.dumps(strategies_summary['strategies_detail'], indent=2)}

Please provide:
1. Market regime analysis (trending/ranging/volatile)
2. Signal quality assessment (confluence strength)
3. Risk level evaluation (low/medium/high)
4. Recommended action (BUY/SELL/WAIT)
5. Confidence score (0-100%)
6. Key insights (2-3 bullet points)

Respond in JSON format with keys: regime, signal_quality, risk_level, action, confidence, insights"""
    
    async def _call_manus_api(self, prompt: str) -> Dict[str, Any]:
        """Call Manus AI API with analysis prompt"""
        headers = {
            "x-sandbox-token": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": prompt,
            "task_type": "analysis",
            "response_format": "json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    def _parse_ai_response(self, ai_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate AI response"""
        try:
            if isinstance(ai_response, str):
                ai_response = json.loads(ai_response)
            
            result = ai_response.get('result', ai_response)
            if isinstance(result, str):
                result = json.loads(result)
            
            return {
                "regime": result.get("regime", "UNKNOWN"),
                "signal_quality": result.get("signal_quality", "MODERATE"),
                "risk_level": result.get("risk_level", "MEDIUM"),
                "action": result.get("action", "WAIT"),
                "confidence": float(result.get("confidence", 50.0)),
                "insights": result.get("insights", ["AI analysis completed"]),
                "ai_enabled": True
            }
        except Exception as e:
            print(f"⚠️ AI Response Parse Error: {e}")
            return self._get_fallback_response()
    
    def _get_fallback_response(self) -> Dict[str, Any]:
        """Fallback response when AI is disabled or fails"""
        return {
            "regime": "UNKNOWN",
            "signal_quality": "STANDARD",
            "risk_level": "MEDIUM",
            "action": "CONTINUE",
            "confidence": 0.0,
            "insights": ["AI analysis not available"],
            "ai_enabled": False
        }
    
    def enhance_signal_with_ai(
        self,
        base_signal: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance base trading signal with AI insights
        
        Args:
            base_signal: Original signal from confluence system
            ai_analysis: AI analysis results
            
        Returns:
            Enhanced signal with AI layer
        """
        if not ai_analysis.get('ai_enabled', False):
            return base_signal
        
        enhanced = base_signal.copy()
        
        enhanced['ai_regime'] = ai_analysis['regime']
        enhanced['ai_quality'] = ai_analysis['signal_quality']
        enhanced['ai_risk'] = ai_analysis['risk_level']
        enhanced['ai_confidence'] = ai_analysis['confidence']
        enhanced['ai_insights'] = ai_analysis['insights']
        
        if ai_analysis['action'] != 'CONTINUE':
            if ai_analysis['action'] == enhanced.get('action'):
                enhanced['confidence'] = min(100, enhanced.get('confidence', 50) + 15)
                enhanced['ai_boost'] = True
            elif ai_analysis['action'] == 'WAIT':
                enhanced['confidence'] = max(0, enhanced.get('confidence', 50) - 10)
                enhanced['ai_warning'] = True
            else:
                enhanced['confidence'] = max(0, enhanced.get('confidence', 50) - 20)
                enhanced['ai_conflict'] = True
        
        return enhanced
    
    def get_ai_status_display(self) -> str:
        """Get AI status for UI display"""
        if self.is_enabled():
            return "🤖 Manus AI: ✅ ATIVO"
        return "🤖 Manus AI: ⏸️ DESATIVADO"
