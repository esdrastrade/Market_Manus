"""
Market Manus - Semantic Kernel Integration CORRECTED
Versão corrigida baseada na documentação oficial do Semantic Kernel 1.37.0
Data: 24/09/2025
"""

import os
import sys
import json
import asyncio
import pandas as pd
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# Carregar variáveis de ambiente do arquivo .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Arquivo .env carregado com sucesso")
except ImportError:
    print("⚠️ python-dotenv não instalado. Usando variáveis de ambiente do sistema.")

# Importações corretas do Semantic Kernel (versão 1.37.0)
try:
    from semantic_kernel import Kernel
    from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
    from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
    from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.functions import kernel_function
    from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
        OpenAIChatPromptExecutionSettings,
    )
    print("✅ Semantic Kernel importado com sucesso")
except ImportError as e:
    print(f"⚠️ Erro na importação do Semantic Kernel: {e}")
    print("💡 Continuando sem funcionalidades de IA...")

# Adicionar o diretório do projeto ao sys.path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Importações do Market Manus
try:
    from market_manus.data_providers.bybit_real_data_provider import BybitRealDataProvider
    from market_manus.core.capital_manager import CapitalManager
    print("✅ Módulos do Market Manus importados com sucesso")
except ImportError as e:
    print(f"❌ Erro na importação dos módulos: {e}")
    sys.exit(1)

class MarketDataPlugin:
    """Plugin para dados de mercado"""
    
    def __init__(self, data_provider: BybitRealDataProvider):
        self.data_provider = data_provider
    
    @kernel_function(
        description="Obtém o preço atual de um símbolo de criptomoeda",
        name="obter_preco_atual"
    )
    async def obter_preco_atual(self, simbolo: str) -> str:
        """Obtém o preço atual de um símbolo."""
        try:
            ticker = self.data_provider.get_latest_price("spot", simbolo)
            if ticker:
                price = float(ticker['lastPrice'])
                change = float(ticker.get('price24hPcnt', 0)) * 100
                volume = float(ticker.get('volume24h', 0))
                return f"💰 {simbolo}: ${price:,.4f}\n" \
                       f"📈 Variação 24h: {change:+.2f}%\n" \
                       f"📊 Volume 24h: ${volume:,.0f}"
            else:
                return f"❌ Símbolo {simbolo} não encontrado"
        except Exception as e:
            return f"❌ Erro ao obter preço: {e}"
    
    @kernel_function(
        description="Obtém dados históricos (klines) de um símbolo",
        name="obter_klines"
    )
    async def obter_klines(self, simbolo: str, timeframe: str, limite: str = "100") -> str:
        """Obtém klines de um símbolo."""
        try:
            limit = int(limite)
            
            # Mapear timeframes para formato Bybit
            timeframe_map = {
                "1m": "1",
                "5m": "5", 
                "15m": "15",
                "30m": "30",
                "1h": "60",
                "4h": "240",
                "1d": "D"
            }
            
            bybit_timeframe = timeframe_map.get(timeframe, "60")  # Default 1h
            
            klines = self.data_provider.get_kline(
                category="spot",
                symbol=simbolo,
                interval=bybit_timeframe,
                limit=limit
            )
            
            if klines:
                return f"✅ Obtidos {len(klines)} candlesticks de {simbolo} ({timeframe})"
            else:
                return f"❌ Não foi possível obter dados de {simbolo}"
        except Exception as e:
            return f"❌ Erro ao obter klines: {e}"

class StrategiesPlugin:
    """Plugin para estratégias de trading"""
    
    def __init__(self, data_provider: BybitRealDataProvider):
        self.data_provider = data_provider
    
    def _get_klines_dataframe(self, simbolo: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        """Obtém klines e converte para DataFrame"""
        # Mapear timeframes para formato Bybit
        timeframe_map = {
            "1m": "1",
            "5m": "5", 
            "15m": "15",
            "30m": "30",
            "1h": "60",
            "4h": "240",
            "1d": "D"
        }
        
        bybit_timeframe = timeframe_map.get(timeframe, "60")
        
        klines = self.data_provider.get_kline(
            category="spot",
            symbol=simbolo,
            interval=bybit_timeframe,
            limit=limit
        )
        
        if not klines:
            return None
        
        # Converter para DataFrame
        df = pd.DataFrame(klines, columns=[
            "timestamp", "open", "high", "low", "close", "volume", "turnover"
        ])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col])
        
        return df
    
    def _calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calcula EMA"""
        return prices.ewm(span=period, adjust=False).mean()
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calcula RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std: float = 2.0):
        """Calcula Bandas de Bollinger"""
        rolling_mean = prices.rolling(window=period).mean()
        rolling_std = prices.rolling(window=period).std()
        upper_band = rolling_mean + (rolling_std * std)
        lower_band = rolling_mean - (rolling_std * std)
        return upper_band, lower_band, rolling_mean
    
    @kernel_function(
        description="Executa a estratégia EMA Crossover para análise técnica",
        name="ema_crossover"
    )
    async def ema_crossover(self, simbolo: str, timeframe: str, short: str = "9", long: str = "21") -> str:
        """Executa a estratégia EMA Crossover."""
        try:
            # Obter dados
            df = self._get_klines_dataframe(simbolo, timeframe, 200)
            if df is None:
                return f"❌ Não foi possível obter dados de {simbolo}"
            
            # Calcular EMAs
            short_period = int(short)
            long_period = int(long)
            
            df['ema_short'] = self._calculate_ema(df['close'], short_period)
            df['ema_long'] = self._calculate_ema(df['close'], long_period)
            
            # Gerar sinais
            df['signal'] = 0
            df.loc[df['ema_short'] > df['ema_long'], 'signal'] = 1  # Buy
            df.loc[df['ema_short'] < df['ema_long'], 'signal'] = -1  # Sell
            
            # Detectar mudanças de sinal
            df['position'] = df['signal'].diff()
            
            # Contar sinais
            buy_signals = len(df[df['position'] == 2])  # Mudança de -1 para 1
            sell_signals = len(df[df['position'] == -2])  # Mudança de 1 para -1
            
            # Status atual
            current_price = df['close'].iloc[-1]
            current_ema_short = df['ema_short'].iloc[-1]
            current_ema_long = df['ema_long'].iloc[-1]
            current_signal = "COMPRA" if current_ema_short > current_ema_long else "VENDA"
            
            return f"✅ EMA Crossover - {simbolo} ({timeframe})\n" \
                   f"📊 Parâmetros: EMA rápida={short}, EMA lenta={long}\n" \
                   f"💰 Preço atual: ${current_price:.4f}\n" \
                   f"📈 EMA {short}: ${current_ema_short:.4f}\n" \
                   f"📉 EMA {long}: ${current_ema_long:.4f}\n" \
                   f"🎯 Sinal atual: {current_signal}\n" \
                   f"🟢 Sinais de compra: {buy_signals}\n" \
                   f"🔴 Sinais de venda: {sell_signals}"
        
        except Exception as e:
            return f"❌ Erro na estratégia EMA Crossover: {e}"
    
    @kernel_function(
        description="Executa a estratégia RSI Mean Reversion para análise técnica",
        name="rsi_mean_reversion"
    )
    async def rsi_mean_reversion(self, simbolo: str, timeframe: str, period: str = "14", buy_th: str = "30", sell_th: str = "70") -> str:
        """Executa a estratégia RSI Mean Reversion."""
        try:
            # Obter dados
            df = self._get_klines_dataframe(simbolo, timeframe, 200)
            if df is None:
                return f"❌ Não foi possível obter dados de {simbolo}"
            
            # Calcular RSI
            rsi_period = int(period)
            buy_threshold = float(buy_th)
            sell_threshold = float(sell_th)
            
            df['rsi'] = self._calculate_rsi(df['close'], rsi_period)
            
            # Gerar sinais
            df['signal'] = 0
            df.loc[df['rsi'] < buy_threshold, 'signal'] = 1  # Buy (oversold)
            df.loc[df['rsi'] > sell_threshold, 'signal'] = -1  # Sell (overbought)
            
            # Contar sinais
            buy_signals = len(df[df['signal'] == 1])
            sell_signals = len(df[df['signal'] == -1])
            
            # Status atual
            current_price = df['close'].iloc[-1]
            current_rsi = df['rsi'].iloc[-1]
            
            if current_rsi < buy_threshold:
                current_signal = "COMPRA (Oversold)"
            elif current_rsi > sell_threshold:
                current_signal = "VENDA (Overbought)"
            else:
                current_signal = "NEUTRO"
            
            return f"✅ RSI Mean Reversion - {simbolo} ({timeframe})\n" \
                   f"📊 Parâmetros: Período={period}, Compra<{buy_th}, Venda>{sell_th}\n" \
                   f"💰 Preço atual: ${current_price:.4f}\n" \
                   f"📈 RSI atual: {current_rsi:.2f}\n" \
                   f"🎯 Sinal atual: {current_signal}\n" \
                   f"🟢 Sinais de compra: {buy_signals}\n" \
                   f"🔴 Sinais de venda: {sell_signals}"
        
        except Exception as e:
            return f"❌ Erro na estratégia RSI: {e}"
    
    @kernel_function(
        description="Executa a estratégia Bollinger Bands Breakout para análise técnica",
        name="bollinger_breakout"
    )
    async def bollinger_breakout(self, simbolo: str, timeframe: str, period: str = "20", std: str = "2.0") -> str:
        """Executa a estratégia Bollinger Bands Breakout."""
        try:
            # Obter dados
            df = self._get_klines_dataframe(simbolo, timeframe, 200)
            if df is None:
                return f"❌ Não foi possível obter dados de {simbolo}"
            
            # Calcular Bollinger Bands
            bb_period = int(period)
            bb_std = float(std)
            
            df['upper_band'], df['lower_band'], df['middle_band'] = self._calculate_bollinger_bands(
                df['close'], bb_period, bb_std
            )
            
            # Gerar sinais
            df['signal'] = 0
            df.loc[df['close'] > df['upper_band'], 'signal'] = 1  # Buy breakout
            df.loc[df['close'] < df['lower_band'], 'signal'] = -1  # Sell breakout
            
            # Contar sinais
            buy_signals = len(df[df['signal'] == 1])
            sell_signals = len(df[df['signal'] == -1])
            
            # Status atual
            current_price = df['close'].iloc[-1]
            current_upper = df['upper_band'].iloc[-1]
            current_lower = df['lower_band'].iloc[-1]
            current_middle = df['middle_band'].iloc[-1]
            
            if current_price > current_upper:
                current_signal = "COMPRA (Breakout Superior)"
            elif current_price < current_lower:
                current_signal = "VENDA (Breakout Inferior)"
            else:
                current_signal = "NEUTRO (Dentro das Bandas)"
            
            return f"✅ Bollinger Breakout - {simbolo} ({timeframe})\n" \
                   f"📊 Parâmetros: Período={period}, Desvio={std}\n" \
                   f"💰 Preço atual: ${current_price:.4f}\n" \
                   f"📈 Banda superior: ${current_upper:.4f}\n" \
                   f"📊 Banda média: ${current_middle:.4f}\n" \
                   f"📉 Banda inferior: ${current_lower:.4f}\n" \
                   f"🎯 Sinal atual: {current_signal}\n" \
                   f"🟢 Sinais de compra: {buy_signals}\n" \
                   f"🔴 Sinais de venda: {sell_signals}"
        
        except Exception as e:
            return f"❌ Erro na estratégia Bollinger: {e}"

class BacktestPlugin:
    """Plugin para backtesting"""
    
    def __init__(self, data_provider: BybitRealDataProvider, capital_manager: CapitalManager):
        self.data_provider = data_provider
        self.capital_manager = capital_manager
        self.strategies_plugin = StrategiesPlugin(data_provider)
    
    @kernel_function(
        description="Executa backtest completo de uma estratégia de trading",
        name="backtest_estrategia"
    )
    async def backtest_estrategia(self, simbolo: str, timeframe: str, estrategia: str, dias: str = "30") -> str:
        """Executa backtest de uma estratégia."""
        try:
            # Calcular limite de dados baseado no timeframe
            days = int(dias)
            if timeframe in ["1m", "5m"]:
                limit = min(1000, days * 24 * 12)  # 12 candles por hora para 5m
            elif timeframe in ["15m", "30m"]:
                limit = min(1000, days * 24 * 2)   # 2-4 candles por hora
            elif timeframe == "1h":
                limit = min(1000, days * 24)       # 24 candles por dia
            elif timeframe == "4h":
                limit = min(1000, days * 6)        # 6 candles por dia
            else:  # 1d
                limit = min(1000, days)             # 1 candle por dia
            
            # Obter dados
            df = self.strategies_plugin._get_klines_dataframe(simbolo, timeframe, limit)
            if df is None:
                return f"❌ Não foi possível obter dados históricos de {simbolo}"
            
            # Executar estratégia
            if estrategia.lower() in ["ema", "ema_crossover"]:
                df['ema_short'] = self.strategies_plugin._calculate_ema(df['close'], 9)
                df['ema_long'] = self.strategies_plugin._calculate_ema(df['close'], 21)
                df['signal'] = 0
                df.loc[df['ema_short'] > df['ema_long'], 'signal'] = 1
                df.loc[df['ema_short'] < df['ema_long'], 'signal'] = -1
                strategy_name = "EMA Crossover"
                
            elif estrategia.lower() in ["rsi", "rsi_mean_reversion"]:
                df['rsi'] = self.strategies_plugin._calculate_rsi(df['close'], 14)
                df['signal'] = 0
                df.loc[df['rsi'] < 30, 'signal'] = 1
                df.loc[df['rsi'] > 70, 'signal'] = -1
                strategy_name = "RSI Mean Reversion"
                
            elif estrategia.lower() in ["bollinger", "bollinger_breakout"]:
                upper, lower, middle = self.strategies_plugin._calculate_bollinger_bands(df['close'], 20, 2.0)
                df['upper_band'] = upper
                df['lower_band'] = lower
                df['signal'] = 0
                df.loc[df['close'] > df['upper_band'], 'signal'] = 1
                df.loc[df['close'] < df['lower_band'], 'signal'] = -1
                strategy_name = "Bollinger Breakout"
                
            else:
                return f"❌ Estratégia '{estrategia}' não encontrada. Use: ema, rsi, bollinger"
            
            # Detectar mudanças de posição
            df['position'] = df['signal'].diff()
            
            # Simular trades
            trades = []
            position = 0
            entry_price = 0
            
            for i, row in df.iterrows():
                if row['position'] != 0 and position == 0:  # Abrir posição
                    position = row['signal']
                    entry_price = row['close']
                    
                elif row['position'] != 0 and position != 0:  # Fechar posição
                    exit_price = row['close']
                    
                    # Calcular P&L
                    if position == 1:  # Long
                        pnl_pct = (exit_price - entry_price) / entry_price
                    else:  # Short
                        pnl_pct = (entry_price - exit_price) / entry_price
                    
                    trades.append({
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'position': position,
                        'pnl_pct': pnl_pct,
                        'timestamp': i
                    })
                    
                    # Nova posição
                    position = row['signal']
                    entry_price = row['close']
            
            # Calcular métricas
            if not trades:
                return f"⚠️ Nenhum trade executado para {simbolo} com {strategy_name}"
            
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t['pnl_pct'] > 0])
            losing_trades = total_trades - winning_trades
            win_rate = (winning_trades / total_trades) * 100
            
            total_return = sum([t['pnl_pct'] for t in trades]) * 100
            avg_win = sum([t['pnl_pct'] for t in trades if t['pnl_pct'] > 0]) / max(winning_trades, 1) * 100
            avg_loss = sum([t['pnl_pct'] for t in trades if t['pnl_pct'] < 0]) / max(losing_trades, 1) * 100
            
            # Calcular capital final
            capital_inicial = self.capital_manager.current_capital
            position_size = self.capital_manager.get_position_size()
            total_pnl = sum([position_size * t['pnl_pct'] for t in trades])
            
            # Salvar relatório
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_data = {
                "timestamp": timestamp,
                "simbolo": simbolo,
                "timeframe": timeframe,
                "estrategia": strategy_name,
                "periodo_dias": days,
                "candlesticks_analisados": len(df),
                "total_trades": total_trades,
                "trades_vencedores": winning_trades,
                "trades_perdedores": losing_trades,
                "win_rate": win_rate,
                "retorno_total_pct": total_return,
                "retorno_medio_win": avg_win,
                "retorno_medio_loss": avg_loss,
                "capital_inicial": capital_inicial,
                "position_size": position_size,
                "pnl_total": total_pnl,
                "capital_final": capital_inicial + total_pnl,
                "roi_pct": (total_pnl / capital_inicial) * 100
            }
            
            # Salvar relatório
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            
            report_file = reports_dir / f"backtest_{estrategia}_{simbolo}_{timeframe}_{timestamp}.json"
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            return f"✅ BACKTEST CONCLUÍDO - {simbolo} ({timeframe})\n" \
                   f"🎯 Estratégia: {strategy_name}\n" \
                   f"📅 Período: {days} dias ({len(df)} candlesticks)\n" \
                   f"📊 Total de trades: {total_trades}\n" \
                   f"✅ Trades vencedores: {winning_trades}\n" \
                   f"❌ Trades perdedores: {losing_trades}\n" \
                   f"🎯 Win rate: {win_rate:.1f}%\n" \
                   f"📈 Retorno total: {total_return:+.2f}%\n" \
                   f"💰 P&L total: ${total_pnl:+.2f}\n" \
                   f"📊 ROI: {(total_pnl/capital_inicial)*100:+.2f}%\n" \
                   f"💵 Capital final: ${capital_inicial + total_pnl:.2f}\n" \
                   f"📁 Relatório: {report_file.name}"
        
        except Exception as e:
            return f"❌ Erro no backtest: {e}"

class MarketManusSemanticKernel:
    """Classe principal do Market Manus com Semantic Kernel"""
    
    def __init__(self):
        # Configurar APIs
        self.api_key = os.getenv("BYBIT_API_KEY", "")
        self.api_secret = os.getenv("BYBIT_API_SECRET", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        print(f"🔑 API Keys detectadas:")
        print(f"   Bybit API Key: {'✅ Configurada' if self.api_key else '❌ Não encontrada'}")
        print(f"   OpenAI API Key: {'✅ Configurada' if self.openai_api_key else '❌ Não encontrada'}")
        
        if not self.api_key or not self.api_secret:
            print("❌ Credenciais da API Bybit não configuradas!")
            sys.exit(1)
        
        # Inicializar componentes
        self.data_provider = BybitRealDataProvider(
            api_key=self.api_key,
            api_secret=self.api_secret,
            testnet=False
        )
        
        self.capital_manager = CapitalManager(
            initial_capital=10000.0,
            position_size_pct=0.02
        )
        
        # Inicializar plugins
        self.market_data_plugin = MarketDataPlugin(self.data_provider)
        self.strategies_plugin = StrategiesPlugin(self.data_provider)
        self.backtest_plugin = BacktestPlugin(self.data_provider, self.capital_manager)
        
        # Inicializar Semantic Kernel
        self.kernel = None
        self.chat_completion = None
        self.chat_history = None
        
        if self.openai_api_key:
            try:
                self.kernel = Kernel()
                
                # Adicionar serviço de chat OpenAI
                self.chat_completion = OpenAIChatCompletion(
                    ai_model_id="gpt-3.5-turbo",
                    api_key=self.openai_api_key
                )
                self.kernel.add_service(self.chat_completion)
                
                # Registrar plugins
                self._register_plugins()
                
                # Inicializar histórico de chat
                self.chat_history = ChatHistory()
                
                print("✅ Semantic Kernel com IA completa inicializado!")
            except Exception as e:
                print(f"⚠️ Erro ao inicializar Semantic Kernel: {e}")
                self.kernel = None
        else:
            print("⚠️ OpenAI API Key não configurada - Usando modo básico")
    
    def _register_plugins(self):
        """Registra plugins no kernel"""
        if not self.kernel:
            return
        
        try:
            self.kernel.add_plugin(self.market_data_plugin, plugin_name="market_data")
            self.kernel.add_plugin(self.strategies_plugin, plugin_name="strategies")
            self.kernel.add_plugin(self.backtest_plugin, plugin_name="backtest")
            
            print("✅ Plugins de IA registrados com sucesso")
        except Exception as e:
            print(f"⚠️ Erro ao registrar plugins: {e}")
    
    async def process_natural_language_command(self, command: str) -> str:
        """Processa comando em linguagem natural usando IA"""
        if not self.kernel or not self.chat_completion:
            return "❌ Semantic Kernel não disponível."
        
        try:
            # Configurar execution settings
            execution_settings = OpenAIChatPromptExecutionSettings()
            execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
            
            # Adicionar comando do usuário ao histórico
            self.chat_history.add_user_message(command)
            
            # Obter resposta da IA com plugins
            result = await self.chat_completion.get_chat_message_content(
                chat_history=self.chat_history,
                settings=execution_settings,
                kernel=self.kernel,
            )
            
            # Adicionar resposta ao histórico
            self.chat_history.add_message(result)
            
            return str(result)
            
        except Exception as e:
            return f"❌ Erro ao processar comando com IA: {e}"
    
    def _process_simple_command(self, command: str) -> str:
        """Processa comandos simples sem IA com melhor reconhecimento"""
        command_lower = command.lower()
        
        # Extrair símbolo se mencionado
        simbolo = "BTCUSDT"  # Default
        if any(word in command_lower for word in ["eth", "ethereum"]):
            simbolo = "ETHUSDT"
        elif any(word in command_lower for word in ["bnb", "binance"]):
            simbolo = "BNBUSDT"
        elif any(word in command_lower for word in ["sol", "solana"]):
            simbolo = "SOLUSDT"
        elif any(word in command_lower for word in ["xrp", "ripple"]):
            simbolo = "XRPUSDT"
        
        # Comandos de preço
        if any(word in command_lower for word in ["preço", "preco", "price", "valor", "cotação", "cotacao"]):
            # Usar método síncrono diretamente
            try:
                ticker = self.data_provider.get_latest_price("spot", simbolo)
                if ticker:
                    price = float(ticker['lastPrice'])
                    change = float(ticker.get('price24hPcnt', 0)) * 100
                    volume = float(ticker.get('volume24h', 0))
                    return f"💰 {simbolo}: ${price:,.4f}\n" \
                           f"📈 Variação 24h: {change:+.2f}%\n" \
                           f"📊 Volume 24h: ${volume:,.0f}"
                else:
                    return f"❌ Símbolo {simbolo} não encontrado"
            except Exception as e:
                return f"❌ Erro ao obter preço: {e}"
        
        # Comandos de estratégias (usar métodos síncronos)
        elif any(word in command_lower for word in ["ema", "média", "media", "crossover"]):
            return asyncio.run(self.strategies_plugin.ema_crossover(simbolo, "1h"))
        
        elif any(word in command_lower for word in ["rsi", "reversão", "reversao", "mean reversion"]):
            return asyncio.run(self.strategies_plugin.rsi_mean_reversion(simbolo, "1h"))
        
        elif any(word in command_lower for word in ["bollinger", "banda", "breakout", "rompimento"]):
            return asyncio.run(self.strategies_plugin.bollinger_breakout(simbolo, "1h"))
        
        # Comandos de backtest
        elif any(word in command_lower for word in ["backtest", "teste", "histórico", "historico"]):
            # Determinar estratégia
            if any(word in command_lower for word in ["ema", "média", "media"]):
                estrategia = "ema"
            elif any(word in command_lower for word in ["rsi"]):
                estrategia = "rsi"
            elif any(word in command_lower for word in ["bollinger", "banda"]):
                estrategia = "bollinger"
            else:
                estrategia = "ema"  # Default
            
            return asyncio.run(self.backtest_plugin.backtest_estrategia(simbolo, "1h", estrategia))
        
        # Comandos de dados
        elif any(word in command_lower for word in ["dados", "klines", "candlesticks", "histórico"]):
            return asyncio.run(self.market_data_plugin.obter_klines(simbolo, "1h"))
        
        else:
            return "❓ Comando não reconhecido. Tente:\n" \
                   "💰 'Preço do Bitcoin' ou 'Qual o preço do ETH?'\n" \
                   "📊 'EMA Crossover Bitcoin' ou 'RSI Ethereum'\n" \
                   "📈 'Backtest RSI Bitcoin' ou 'Teste Bollinger ETH'\n" \
                   "📋 'Dados históricos Bitcoin'"
    
    async def run_interactive_mode(self):
        """Executa modo interativo"""
        print("\n🤖 MARKET MANUS - SEMANTIC KERNEL ASSISTANT")
        print("=" * 60)
        
        if self.kernel:
            print("🧠 MODO IA COMPLETA ATIVADO")
            print("💬 Digite comandos em linguagem natural complexa")
        else:
            print("🔧 MODO BÁSICO ATIVADO")
            print("💬 Digite comandos simples")
        
        print("📊 Exemplos:")
        print('   "Qual o preço atual do Bitcoin?"')
        print('   "Execute EMA Crossover no ETHUSDT"')
        print('   "Faça backtest do RSI no Bitcoin por 30 dias"')
        print('   "Bollinger Breakout Ethereum timeframe 4h"')
        print("   'sair' para encerrar")
        print("=" * 60)
        
        while True:
            try:
                command = input("\n💬 Você: ").strip()
                
                if command.lower() in ['sair', 'exit', 'quit']:
                    print("👋 Até logo!")
                    break
                
                if not command:
                    continue
                
                print("🔄 Processando...")
                
                if self.kernel:
                    # Usar IA completa
                    response = await self.process_natural_language_command(command)
                else:
                    # Usar processamento básico
                    response = self._process_simple_command(command)
                
                print(f"\n🤖 Assistente: {response}")
                
            except KeyboardInterrupt:
                print("\n👋 Até logo!")
                break
            except Exception as e:
                print(f"\n❌ Erro: {e}")

async def main():
    """Função principal"""
    try:
        print("🚀 Iniciando Market Manus Semantic Kernel...")
        
        # Testar conectividade
        print("🔄 Testando conectividade...")
        
        sk_system = MarketManusSemanticKernel()
        
        # Testar API Bybit
        test_result = sk_system.data_provider.get_tickers(category="spot")
        if test_result:
            print("✅ Bybit API conectada")
        else:
            print("❌ Problema na Bybit API")
        
        # Executar modo interativo
        await sk_system.run_interactive_mode()
        
    except KeyboardInterrupt:
        print("\n👋 Sistema encerrado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
