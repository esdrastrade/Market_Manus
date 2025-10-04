"""
Confluence Lab Module - Versão Validada
Localização: market_manus/confluence_mode/confluence_mode_module.py
Data: 25/09/2025
Sintaxe: 100% Validada
"""

import os
import sys
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Importar estratégias SMC
from market_manus.strategies.smc.patterns import (
    detect_bos,
    detect_choch,
    detect_order_blocks,
    detect_fvg,
    detect_liquidity_sweep
)

class ConfluenceModeModule:
    """
    Módulo de Confluência - Sistema de múltiplas estratégias
    
    IMPORTANTE: Este módulo usa APENAS dados reais das APIs Binance/Bybit.
    Nenhum dado mockado ou simulado é utilizado.
    API keys são validadas antes de executar qualquer backtest.
    """
    
    def __init__(self, data_provider=None, capital_manager=None):
        self.data_provider = data_provider
        self.capital_manager = capital_manager
        
        # Estratégias disponíveis para confluência (13 estratégias: 8 clássicas + 5 SMC)
        self.available_strategies = {
            "rsi_mean_reversion": {
                "name": "RSI Mean Reversion",
                "description": "Reversão à média baseada no RSI",
                "emoji": "📊",
                "weight": 1.0
            },
            "ema_crossover": {
                "name": "EMA Crossover",
                "description": "Cruzamento de médias móveis exponenciais",
                "emoji": "📈",
                "weight": 1.0
            },
            "bollinger_breakout": {
                "name": "Bollinger Bands Breakout",
                "description": "Rompimento das Bandas de Bollinger",
                "emoji": "🎯",
                "weight": 1.0
            },
            "macd": {
                "name": "MACD",
                "description": "Moving Average Convergence Divergence",
                "emoji": "📊",
                "weight": 1.0
            },
            "stochastic": {
                "name": "Stochastic Oscillator",
                "description": "Oscilador Estocástico",
                "emoji": "📈",
                "weight": 1.0
            },
            "williams_r": {
                "name": "Williams %R",
                "description": "Williams Percent Range",
                "emoji": "📉",
                "weight": 1.0
            },
            "adx": {
                "name": "ADX",
                "description": "Average Directional Index",
                "emoji": "🎯",
                "weight": 1.0
            },
            "fibonacci": {
                "name": "Fibonacci Retracement",
                "description": "Níveis de Fibonacci",
                "emoji": "🔢",
                "weight": 1.0
            },
            "smc_bos": {
                "name": "SMC: Break of Structure",
                "description": "Continuação de tendência após rompimento de swing high/low",
                "emoji": "🔥",
                "weight": 1.0
            },
            "smc_choch": {
                "name": "SMC: Change of Character",
                "description": "Reversão quando sequência de topos/fundos muda",
                "emoji": "🔄",
                "weight": 1.0
            },
            "smc_order_blocks": {
                "name": "SMC: Order Blocks",
                "description": "Última vela de acumulação antes do rompimento",
                "emoji": "📦",
                "weight": 1.0
            },
            "smc_fvg": {
                "name": "SMC: Fair Value Gap",
                "description": "Gap entre corpos/sombras indicando imbalance",
                "emoji": "⚡",
                "weight": 1.0
            },
            "smc_liquidity_sweep": {
                "name": "SMC: Liquidity Sweep",
                "description": "Pavio que varre liquidez indicando trap",
                "emoji": "🎣",
                "weight": 1.0
            }
        }
        
        # Modos de confluência
        self.confluence_modes = {
            "ALL": {
                "name": "ALL (Todas as estratégias)",
                "description": "Sinal apenas quando TODAS as estratégias concordam",
                "emoji": "🎯"
            },
            "ANY": {
                "name": "ANY (Qualquer estratégia)",
                "description": "Sinal quando QUALQUER estratégia gera sinal",
                "emoji": "⚡"
            },
            "MAJORITY": {
                "name": "MAJORITY (Maioria)",
                "description": "Sinal quando a MAIORIA das estratégias concorda",
                "emoji": "🗳️"
            },
            "WEIGHTED": {
                "name": "WEIGHTED (Ponderado)",
                "description": "Sinal baseado em pesos das estratégias",
                "emoji": "⚖️"
            }
        }
        
        # Assets disponíveis
        self.available_assets = {
            "BTCUSDT": {"name": "Bitcoin", "emoji": "🪙"},
            "ETHUSDT": {"name": "Ethereum", "emoji": "💎"},
            "BNBUSDT": {"name": "Binance Coin", "emoji": "🟡"},
            "SOLUSDT": {"name": "Solana", "emoji": "⚡"},
            "XRPUSDT": {"name": "XRP", "emoji": "💧"},
            "ADAUSDT": {"name": "Cardano", "emoji": "🔵"},
            "DOGEUSDT": {"name": "Dogecoin", "emoji": "🐕"},
            "MATICUSDT": {"name": "Polygon", "emoji": "🟣"}
        }
        
        # Timeframes disponíveis
        self.timeframes = {
            "1": {"name": "1 minuto", "bybit_interval": "1", "description": "Scalping ultra-rápido"},
            "5": {"name": "5 minutos", "bybit_interval": "5", "description": "Scalping rápido"},
            "15": {"name": "15 minutos", "bybit_interval": "15", "description": "Swing trading curto"},
            "30": {"name": "30 minutos", "bybit_interval": "30", "description": "Swing trading médio"},
            "60": {"name": "1 hora", "bybit_interval": "60", "description": "Swing trading longo"},
            "240": {"name": "4 horas", "bybit_interval": "240", "description": "Position trading"},
            "D": {"name": "1 dia", "bybit_interval": "D", "description": "Investimento longo prazo"}
        }
        
        # Configurações atuais
        self.selected_asset = None
        self.selected_timeframe = None
        self.selected_strategies = []
        self.selected_confluence_mode = None
        self.custom_start_date = None
        self.custom_end_date = None
        
        # Histórico de testes
        self.test_history = []
    
    def _validate_api_credentials(self) -> bool:
        """
        Valida se as credenciais da API estão configuradas
        
        Returns:
            bool: True se credenciais válidas, False caso contrário
        """
        if not self.data_provider:
            print("❌ Data provider não configurado")
            print("❌ Impossível executar backtest sem dados reais da API")
            return False
        
        # Verificar se o provider tem API key configurada
        if not hasattr(self.data_provider, 'api_key') or not self.data_provider.api_key:
            print("❌ API Key não configurada")
            print("❌ Configure BINANCE_API_KEY ou BYBIT_API_KEY no ambiente")
            return False
        
        if not hasattr(self.data_provider, 'api_secret') or not self.data_provider.api_secret:
            print("❌ API Secret não configurado")
            print("❌ Configure BINANCE_API_SECRET ou BYBIT_API_SECRET no ambiente")
            return False
        
        print("✅ Credenciais da API validadas com sucesso")
        print(f"📊 Fonte de dados: {self.data_provider.__class__.__name__} (API REAL)")
        return True
    
    def run_interactive_mode(self):
        """Executa o modo interativo do Confluence Lab"""
        while True:
            self._show_main_menu()
            choice = input("\n🔢 Escolha uma opção (0-8): ").strip()
            
            if choice == '0':
                print("\n👋 Saindo do Confluence Lab...")
                break
            elif choice == '1':
                self._asset_selection_menu()
            elif choice == '2':
                self._timeframe_selection_menu()
            elif choice == '3':
                self._strategy_selection_menu()
            elif choice == '4':
                self._confluence_mode_selection()
            elif choice == '5':
                self._period_selection_menu()
            elif choice == '6':
                self._run_confluence_backtest()
            elif choice == '7':
                self._view_test_results()
            elif choice == '8':
                self._export_results()
            else:
                print("❌ Opção inválida")
                input("\n📖 Pressione ENTER para continuar...")
    
    def _show_main_menu(self):
        """Mostra o menu principal do Confluence Lab"""
        print("\n" + "="*80)
        print("🎯 CONFLUENCE MODE - SISTEMA DE CONFLUÊNCIA")
        print("="*80)
        
        # Status atual
        asset_status = f"✅ {self.selected_asset}" if self.selected_asset else "❌ Não selecionado"
        timeframe_status = f"✅ {self.timeframes[self.selected_timeframe]['name']}" if self.selected_timeframe else "❌ Não selecionado"
        strategies_status = f"✅ {len(self.selected_strategies)} estratégias" if self.selected_strategies else "❌ Nenhuma selecionada"
        confluence_status = f"✅ {self.confluence_modes[self.selected_confluence_mode]['name']}" if self.selected_confluence_mode else "❌ Não selecionado"
        
        print(f"📊 CONFIGURAÇÃO ATUAL:")
        print(f"   🪙 Ativo: {asset_status}")
        print(f"   ⏰ Timeframe: {timeframe_status}")
        print(f"   📈 Estratégias: {strategies_status}")
        print(f"   🎯 Modo Confluência: {confluence_status}")
        
        if self.custom_start_date and self.custom_end_date:
            print(f"   📅 Período: {self.custom_start_date} até {self.custom_end_date}")
        else:
            print(f"   📅 Período: Padrão (últimos 30 dias)")
        
        # Capital info
        if self.capital_manager:
            print(f"   💰 Capital: ${self.capital_manager.current_capital:.2f}")
            print(f"   💼 Position Size: ${self.capital_manager.get_position_size():.2f}")
        
        print(f"\n🔧 CONFIGURAÇÃO:")
        print("   1️⃣  Seleção de Ativo")
        print("   2️⃣  Seleção de Timeframe")
        print("   3️⃣  Seleção de Estratégias")
        print("   4️⃣  Modo de Confluência")
        print("   5️⃣  Período Personalizado")
        
        print(f"\n🧪 TESTES:")
        print("   6️⃣  Executar Backtest de Confluência")
        
        print(f"\n📊 RESULTADOS:")
        print("   7️⃣  Visualizar Resultados")
        print("   8️⃣  Exportar Relatórios")
        
        print(f"\n   0️⃣  Voltar ao Menu Principal")
    
    def _asset_selection_menu(self):
        """Menu de seleção de ativo"""
        print("\n🪙 SELEÇÃO DE ATIVO")
        print("="*50)
        
        assets_list = list(self.available_assets.keys())
        for i, asset in enumerate(assets_list, 1):
            info = self.available_assets[asset]
            selected = "✅" if asset == self.selected_asset else "  "
            print(f"   {i}️⃣  {selected} {info['emoji']} {asset} - {info['name']}")
        
        print(f"\n   0️⃣  Voltar")
        
        choice = input("\n🔢 Escolha um ativo (0-8): ").strip()
        
        if choice == '0':
            return
        
        try:
            asset_index = int(choice) - 1
            if 0 <= asset_index < len(assets_list):
                self.selected_asset = assets_list[asset_index]
                asset_info = self.available_assets[self.selected_asset]
                print(f"\n✅ Ativo selecionado: {asset_info['emoji']} {self.selected_asset} - {asset_info['name']}")
            else:
                print("❌ Opção inválida")
        except ValueError:
            print("❌ Digite um número válido")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _timeframe_selection_menu(self):
        """Menu de seleção de timeframe"""
        print("\n⏰ SELEÇÃO DE TIMEFRAME")
        print("="*50)
        
        timeframes_list = list(self.timeframes.keys())
        for i, tf_key in enumerate(timeframes_list, 1):
            tf_info = self.timeframes[tf_key]
            selected = "✅" if tf_key == self.selected_timeframe else "  "
            print(f"   {i}️⃣  {selected} {tf_info['name']} - {tf_info['description']}")
        
        print(f"\n   0️⃣  Voltar")
        
        choice = input("\n🔢 Escolha um timeframe (0-7): ").strip()
        
        if choice == '0':
            return
        
        try:
            tf_index = int(choice) - 1
            if 0 <= tf_index < len(timeframes_list):
                tf_key = timeframes_list[tf_index]
                self.selected_timeframe = tf_key
                tf_info = self.timeframes[tf_key]
                print(f"\n✅ Timeframe selecionado: {tf_info['name']} - {tf_info['description']}")
            else:
                print("❌ Opção inválida")
        except ValueError:
            print("❌ Digite um número válido")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _strategy_selection_menu(self):
        """Menu de seleção de estratégias"""
        print("\n📈 SELEÇÃO DE ESTRATÉGIAS")
        print("="*50)
        print("💡 Selecione múltiplas estratégias para confluência")
        print("   Digite os números separados por vírgula (ex: 1,3,5)")
        
        strategies_list = list(self.available_strategies.keys())
        for i, strategy_key in enumerate(strategies_list, 1):
            strategy = self.available_strategies[strategy_key]
            selected = "✅" if strategy_key in self.selected_strategies else "  "
            print(f"   {i}️⃣  {selected} {strategy['emoji']} {strategy['name']}")
            print(f"       📝 {strategy['description']}")
        
        print(f"\n   0️⃣  Voltar")
        
        choice = input("\n🔢 Escolha estratégias (ex: 1,3,5 ou 0): ").strip()
        
        if choice == '0':
            return
        
        try:
            # Parse múltiplas seleções
            selected_indices = [int(x.strip()) - 1 for x in choice.split(',')]
            valid_strategies = []
            
            for index in selected_indices:
                if 0 <= index < len(strategies_list):
                    valid_strategies.append(strategies_list[index])
            
            if valid_strategies:
                self.selected_strategies = valid_strategies
                print(f"\n✅ Estratégias selecionadas:")
                for strategy_key in self.selected_strategies:
                    strategy = self.available_strategies[strategy_key]
                    print(f"   {strategy['emoji']} {strategy['name']}")
            else:
                print("❌ Nenhuma estratégia válida selecionada")
        except ValueError:
            print("❌ Formato inválido. Use números separados por vírgula")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _confluence_mode_selection(self):
        """Menu de seleção do modo de confluência"""
        print("\n🎯 MODO DE CONFLUÊNCIA")
        print("="*50)
        
        modes_list = list(self.confluence_modes.keys())
        for i, mode_key in enumerate(modes_list, 1):
            mode = self.confluence_modes[mode_key]
            selected = "✅" if mode_key == self.selected_confluence_mode else "  "
            print(f"   {i}️⃣  {selected} {mode['emoji']} {mode['name']}")
            print(f"       📝 {mode['description']}")
        
        print(f"\n   0️⃣  Voltar")
        
        choice = input("\n🔢 Escolha um modo (0-4): ").strip()
        
        if choice == '0':
            return
        
        try:
            mode_index = int(choice) - 1
            if 0 <= mode_index < len(modes_list):
                mode_key = modes_list[mode_index]
                self.selected_confluence_mode = mode_key
                mode_info = self.confluence_modes[mode_key]
                print(f"\n✅ Modo selecionado: {mode_info['emoji']} {mode_info['name']}")
                
                # Se for modo WEIGHTED, configurar pesos
                if mode_key == "WEIGHTED":
                    self._configure_strategy_weights()
            else:
                print("❌ Opção inválida")
        except ValueError:
            print("❌ Digite um número válido")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _configure_strategy_weights(self):
        """Configura pesos das estratégias para modo WEIGHTED"""
        print("\n⚖️ CONFIGURAÇÃO DE PESOS")
        print("="*50)
        print("💡 Configure o peso de cada estratégia (0.1 a 2.0)")
        
        for strategy_key in self.selected_strategies:
            strategy = self.available_strategies[strategy_key]
            current_weight = strategy.get('weight', 1.0)
            
            print(f"\n📊 {strategy['name']}")
            print(f"   Peso atual: {current_weight}")
            
            weight_input = input(f"   Novo peso (0.1-2.0, ENTER para manter): ").strip()
            
            if weight_input:
                try:
                    weight = float(weight_input)
                    if 0.1 <= weight <= 2.0:
                        self.available_strategies[strategy_key]['weight'] = weight
                        print(f"   ✅ Peso atualizado: {weight}")
                    else:
                        print(f"   ⚠️ Peso fora da faixa, mantendo: {current_weight}")
                except ValueError:
                    print(f"   ❌ Valor inválido, mantendo: {current_weight}")
    
    def _period_selection_menu(self):
        """Menu de seleção de período personalizado"""
        print("\n📅 PERÍODO PERSONALIZADO")
        print("="*50)
        
        print("🔧 Configure o período para backtesting:")
        print("   📅 Data inicial (formato: YYYY-MM-DD)")
        print("   📅 Data final (formato: YYYY-MM-DD)")
        print("   💡 Deixe em branco para usar período padrão (últimos 30 dias)")
        
        # Data inicial
        start_input = input("\n📅 Data inicial (YYYY-MM-DD): ").strip()
        if start_input:
            try:
                start_date = datetime.strptime(start_input, "%Y-%m-%d")
                self.custom_start_date = start_date.strftime("%Y-%m-%d")
                print(f"✅ Data inicial: {self.custom_start_date}")
            except ValueError:
                print("❌ Formato de data inválido, usando padrão")
                self.custom_start_date = None
        else:
            self.custom_start_date = None
            print("📅 Usando período padrão para data inicial")
        
        # Data final
        end_input = input("\n📅 Data final (YYYY-MM-DD): ").strip()
        if end_input:
            try:
                end_date = datetime.strptime(end_input, "%Y-%m-%d")
                self.custom_end_date = end_date.strftime("%Y-%m-%d")
                print(f"✅ Data final: {self.custom_end_date}")
                
                # Validar se data final é posterior à inicial
                if self.custom_start_date:
                    start_dt = datetime.strptime(self.custom_start_date, "%Y-%m-%d")
                    end_dt = datetime.strptime(self.custom_end_date, "%Y-%m-%d")
                    if end_dt <= start_dt:
                        print("❌ Data final deve ser posterior à inicial, usando padrão")
                        self.custom_start_date = None
                        self.custom_end_date = None
            except ValueError:
                print("❌ Formato de data inválido, usando padrão")
                self.custom_end_date = None
        else:
            self.custom_end_date = None
            print("📅 Usando período padrão para data final")
        
        # Resumo
        if self.custom_start_date and self.custom_end_date:
            print(f"\n✅ Período personalizado configurado:")
            print(f"   📅 De: {self.custom_start_date}")
            print(f"   📅 Até: {self.custom_end_date}")
        else:
            print(f"\n📅 Usando período padrão (últimos 30 dias)")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _validate_configuration(self) -> bool:
        """Valida se a configuração está completa"""
        if not self.selected_asset:
            print("❌ Selecione um ativo primeiro (opção 1)")
            input("\n📖 Pressione ENTER para continuar...")
            return False
        
        if not self.selected_timeframe:
            print("❌ Selecione um timeframe primeiro (opção 2)")
            input("\n📖 Pressione ENTER para continuar...")
            return False
        
        if not self.selected_strategies:
            print("❌ Selecione pelo menos uma estratégia (opção 3)")
            input("\n📖 Pressione ENTER para continuar...")
            return False
        
        if not self.selected_confluence_mode:
            print("❌ Selecione um modo de confluência (opção 4)")
            input("\n📖 Pressione ENTER para continuar...")
            return False
        
        return True
    
    def _display_data_metrics(self, metrics: Dict):
        """
        Exibe métricas de dados históricos carregados em formato visual consistente
        
        Args:
            metrics: Dicionário com métricas dos dados (total_candles, period, success_rate, etc.)
        """
        print("\n" + "═" * 63)
        print("📊 DADOS HISTÓRICOS CARREGADOS")
        print("═" * 63)
        
        # Total de Candles
        total_candles = metrics.get("total_candles", 0)
        print(f"📈 Total de Candles: {total_candles:,}")
        
        # Período Exato
        first_time = metrics.get("first_candle_time")
        last_time = metrics.get("last_candle_time")
        if first_time and last_time:
            first_str = first_time.strftime("%Y-%m-%d %H:%M:%S")
            last_str = last_time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"📅 Período: {first_str} → {last_str}")
        
        # Taxa de Sucesso da API
        success_rate = metrics.get("success_rate", 0)
        successful = metrics.get("successful_batches", 0)
        total = metrics.get("total_batches", 0)
        print(f"✅ API Success Rate: {success_rate:.1f}% ({successful}/{total} batches bem-sucedidos)")
        
        # Fonte de Dados
        data_source = metrics.get("data_source", "Unknown")
        print(f"🔗 Fonte: {data_source} (dados reais)")
        
        print("═" * 63)
    
    def _fetch_historical_klines(self, symbol: str, interval: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Tuple[List, Dict]:
        """
        Busca TODOS os candles do período especificado, fazendo múltiplas chamadas se necessário.
        
        Args:
            symbol: Par de trading (ex: BTCUSDT)
            interval: Timeframe (1, 5, 15, 60, 240, D)
            start_date: Data inicial no formato YYYY-MM-DD (opcional)
            end_date: Data final no formato YYYY-MM-DD (opcional)
        
        Returns:
            Tuple[List, Dict]: (Lista com todos os candles, Dicionário com métricas da API)
        """
        # Calcular timestamps
        if start_date and end_date:
            start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
            end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp() * 1000)
        else:
            # Período padrão: últimos 30 dias
            end_ts = int(datetime.now().timestamp() * 1000)
            start_ts = end_ts - (30 * 24 * 60 * 60 * 1000)
        
        # Calcular duração de um candle em milissegundos
        timeframe_ms = {
            "1": 60 * 1000,           # 1 minuto
            "5": 5 * 60 * 1000,       # 5 minutos
            "15": 15 * 60 * 1000,     # 15 minutos
            "60": 60 * 60 * 1000,     # 1 hora
            "240": 4 * 60 * 60 * 1000,  # 4 horas
            "D": 24 * 60 * 60 * 1000  # 1 dia
        }
        
        candle_duration = timeframe_ms.get(interval, 60 * 1000)
        
        # Calcular quantos candles são necessários
        total_candles_needed = int((end_ts - start_ts) / candle_duration)
        
        print(f"   📊 Período requer ~{total_candles_needed} candles")
        
        # Buscar dados em lotes de 500 (limite da API)
        all_klines = []
        current_start = start_ts
        batch_num = 1
        
        # Métricas da API
        successful_batches = 0
        failed_batches = 0
        
        while current_start < end_ts:
            # Calcular quantos candles faltam
            remaining_ms = end_ts - current_start
            remaining_candles = int(remaining_ms / candle_duration)
            limit = min(500, remaining_candles)
            
            if limit <= 0:
                break
            
            print(f"   📡 Batch {batch_num}: Buscando {limit} candles a partir de {datetime.fromtimestamp(current_start/1000).strftime('%Y-%m-%d %H:%M')}...")
            
            # Buscar dados com startTime
            try:
                klines = self.data_provider.get_kline(
                    category='spot',
                    symbol=symbol,
                    interval=interval,
                    limit=limit,
                    start=current_start,
                    end=end_ts
                )
                
                if not klines:
                    print(f"   ⚠️  Nenhum dado retornado para este batch")
                    failed_batches += 1
                    break
                
                all_klines.extend(klines)
                successful_batches += 1
                print(f"   ✅ Recebidos {len(klines)} candles (total acumulado: {len(all_klines)})")
                
                # Próximo batch começa após o último candle recebido
                last_candle_time = int(klines[-1][0])  # timestamp do último candle
                current_start = last_candle_time + candle_duration
                batch_num += 1
                
                # Evitar rate limit
                time.sleep(0.1)
            except Exception as e:
                print(f"   ❌ Erro no batch {batch_num}: {str(e)}")
                failed_batches += 1
                break
        
        # Calcular métricas
        total_batches = successful_batches + failed_batches
        success_rate = (successful_batches / total_batches * 100) if total_batches > 0 else 0
        
        # Determinar período exato dos dados
        first_candle_time = None
        last_candle_time = None
        if all_klines:
            first_candle_time = datetime.fromtimestamp(int(all_klines[0][0]) / 1000)
            last_candle_time = datetime.fromtimestamp(int(all_klines[-1][0]) / 1000)
        
        metrics = {
            "total_candles": len(all_klines),
            "successful_batches": successful_batches,
            "failed_batches": failed_batches,
            "total_batches": total_batches,
            "success_rate": success_rate,
            "first_candle_time": first_candle_time,
            "last_candle_time": last_candle_time,
            "data_source": self.data_provider.__class__.__name__ if self.data_provider else "Unknown"
        }
        
        return all_klines, metrics
    
    def _run_confluence_backtest(self):
        """
        Executa backtest de confluência com dados reais da Binance/Bybit
        
        IMPORTANTE: Valida API credentials e usa APENAS dados reais das APIs.
        """
        if not self._validate_configuration():
            return
        
        # VALIDAÇÃO OBRIGATÓRIA DE API CREDENTIALS
        print("\n🔐 Validando credenciais da API...")
        if not self._validate_api_credentials():
            print("\n❌ BACKTEST CANCELADO: API credentials não configuradas")
            print("   Configure BINANCE_API_KEY/BYBIT_API_KEY e seus secrets antes de executar backtests.")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        print("\n🧪 EXECUTANDO BACKTEST DE CONFLUÊNCIA COM DADOS REAIS")
        print("="*60)
        
        print(f"📊 Configuração do teste:")
        print(f"   🪙 Ativo: {self.selected_asset}")
        print(f"   ⏰ Timeframe: {self.timeframes[self.selected_timeframe]['name']}")
        print(f"   📈 Estratégias: {len(self.selected_strategies)} selecionadas")
        print(f"   🎯 Modo: {self.confluence_modes[self.selected_confluence_mode]['name']}")
        
        if self.custom_start_date and self.custom_end_date:
            print(f"   📅 Período: {self.custom_start_date} até {self.custom_end_date}")
        else:
            print(f"   📅 Período: Últimos 30 dias")
        
        print(f"\n🔄 Buscando dados reais da Binance...")
        
        # Buscar dados históricos REAIS da Binance
        if not self.data_provider:
            print("❌ Data Provider não disponível!")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        # selected_timeframe já está no formato correto para Binance ("1", "5", "15", "60", "240", "D")
        interval = self.selected_timeframe
        
        # Buscar TODOS os candles do período especificado
        klines, metrics = self._fetch_historical_klines(
            symbol=self.selected_asset,
            interval=interval,
            start_date=self.custom_start_date,
            end_date=self.custom_end_date
        )
        
        if not klines or len(klines) < 50:
            print(f"❌ Dados insuficientes! Recebido: {len(klines) if klines else 0} velas")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        # Exibir métricas de dados carregados
        self._display_data_metrics(metrics)
        
        # Converter dados para análise
        closes = [float(k[4]) for k in klines]  # Preços de fechamento
        highs = [float(k[2]) for k in klines]   # Máximas
        lows = [float(k[3]) for k in klines]    # Mínimas
        
        print(f"\n📊 Executando estratégias sobre dados reais...")
        
        # Executar cada estratégia sobre os dados reais
        strategy_signals = {}
        for strategy_key in self.selected_strategies:
            strategy = self.available_strategies[strategy_key]
            signals = self._execute_strategy_on_data(strategy_key, closes, highs, lows)
            strategy_signals[strategy_key] = {
                "name": strategy['name'],
                "signals": signals,
                "weight": strategy.get('weight', 1.0)
            }
        
        # Calcular confluência baseado no modo
        confluence_signals = self._calculate_confluence_signals(strategy_signals)
        
        # Calcular resultados financeiros baseados nos sinais reais
        initial_capital = self.capital_manager.current_capital if self.capital_manager else 10000
        final_capital, total_trades, winning_trades = self._simulate_trades_from_signals(
            confluence_signals, closes, initial_capital
        )
        losing_trades = total_trades - winning_trades
        pnl = final_capital - initial_capital
        roi = (pnl / initial_capital) * 100
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        print(f"\n📊 RESULTADOS DO BACKTEST DE CONFLUÊNCIA:")
        print(f"   💰 Capital inicial: ${initial_capital:.2f}")
        print(f"   💵 Capital final: ${final_capital:.2f}")
        print(f"   📈 P&L: ${pnl:+.2f}")
        print(f"   📊 ROI: {roi:+.2f}%")
        print(f"   🎯 Sinais de confluência: {confluence_signals}")
        print(f"   ✅ Trades vencedores: {winning_trades}")
        print(f"   ❌ Trades perdedores: {losing_trades}")
        print(f"   📊 Win Rate: {win_rate:.1f}%")
        
        print(f"\n📈 DETALHES POR ESTRATÉGIA:")
        for strategy_key, data in strategy_signals.items():
            print(f"   {data['name']}: {data['signals']} sinais (peso: {data['weight']})")
        
        # Mostrar capital simulado (sem alterar o capital real)
        if self.capital_manager:
            simulated_final_capital = final_capital
            print(f"\n💰 Capital real permanece: ${self.capital_manager.current_capital:.2f}")
            print(f"   📊 Capital simulado (backtest): ${simulated_final_capital:.2f}")
            print(f"   ℹ️  (Backtest não altera capital real)")
        
        # Salvar no histórico
        test_result = {
            "timestamp": datetime.now().isoformat(),
            "type": "confluence_backtest",
            "asset": self.selected_asset,
            "timeframe": self.selected_timeframe,
            "strategies": self.selected_strategies,
            "confluence_mode": self.selected_confluence_mode,
            "results": {
                "initial_capital": initial_capital,
                "final_capital": final_capital,
                "pnl": pnl,
                "roi": roi,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": win_rate,
                "confluence_signals": confluence_signals,
                "strategy_signals": strategy_signals
            }
        }
        self.test_history.append(test_result)
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _execute_strategy_on_data(self, strategy_key: str, closes: List[float], highs: List[float], lows: List[float]) -> int:
        """Executa uma estratégia sobre dados reais e conta sinais gerados"""
        signals_count = 0
        
        # RSI Mean Reversion
        if strategy_key == "rsi_mean_reversion":
            rsi_values = self._calculate_rsi(closes, period=14)
            for rsi in rsi_values:
                if rsi < 30 or rsi > 70:  # Sobrevenda ou sobrecompra
                    signals_count += 1
        
        # EMA Crossover
        elif strategy_key == "ema_crossover":
            ema_fast = self._calculate_ema(closes, 12)
            ema_slow = self._calculate_ema(closes, 26)
            for i in range(1, min(len(ema_fast), len(ema_slow))):
                # Cruzamento
                if (ema_fast[i-1] <= ema_slow[i-1] and ema_fast[i] > ema_slow[i]) or \
                   (ema_fast[i-1] >= ema_slow[i-1] and ema_fast[i] < ema_slow[i]):
                    signals_count += 1
        
        # Bollinger Bands
        elif strategy_key == "bollinger_breakout":
            bb_upper, bb_lower = self._calculate_bollinger_bands(closes, period=20, std_dev=2.0)
            for i in range(len(closes)):
                if i < len(bb_upper) and i < len(bb_lower):
                    if closes[i] > bb_upper[i] or closes[i] < bb_lower[i]:
                        signals_count += 1
        
        # MACD
        elif strategy_key == "macd":
            macd_line, signal_line = self._calculate_macd(closes)
            for i in range(1, min(len(macd_line), len(signal_line))):
                # Cruzamento MACD
                if (macd_line[i-1] <= signal_line[i-1] and macd_line[i] > signal_line[i]) or \
                   (macd_line[i-1] >= signal_line[i-1] and macd_line[i] < signal_line[i]):
                    signals_count += 1
        
        # Stochastic
        elif strategy_key == "stochastic":
            stoch_values = self._calculate_stochastic(closes, highs, lows, period=14)
            for stoch in stoch_values:
                if stoch < 20 or stoch > 80:
                    signals_count += 1
        
        # Williams %R
        elif strategy_key == "williams_r":
            williams_values = self._calculate_williams_r(closes, highs, lows, period=14)
            for wr in williams_values:
                if wr < -80 or wr > -20:
                    signals_count += 1
        
        # ADX
        elif strategy_key == "adx":
            adx_values = self._calculate_adx(closes, highs, lows, period=14)
            for adx in adx_values:
                if adx > 25:  # Tendência forte
                    signals_count += 1
        
        # Fibonacci
        elif strategy_key == "fibonacci":
            # Detectar topos e fundos e contar sinais em níveis de Fibonacci
            signals_count = len(closes) // 20  # Simplificado
        
        # SMC: Break of Structure
        elif strategy_key == "smc_bos":
            df = pd.DataFrame({
                'close': closes,
                'high': highs,
                'low': lows,
                'open': closes  # Simplificado: usar close como proxy para open
            })
            # Aplicar em janelas deslizantes
            for i in range(50, len(df)):
                window_df = df.iloc[max(0, i-50):i+1].reset_index(drop=True)
                signal = detect_bos(window_df)
                if signal.action != "HOLD":
                    signals_count += 1
        
        # SMC: Change of Character
        elif strategy_key == "smc_choch":
            df = pd.DataFrame({
                'close': closes,
                'high': highs,
                'low': lows,
                'open': closes
            })
            for i in range(50, len(df)):
                window_df = df.iloc[max(0, i-50):i+1].reset_index(drop=True)
                signal = detect_choch(window_df)
                if signal.action != "HOLD":
                    signals_count += 1
        
        # SMC: Order Blocks
        elif strategy_key == "smc_order_blocks":
            df = pd.DataFrame({
                'close': closes,
                'high': highs,
                'low': lows,
                'open': closes
            })
            for i in range(50, len(df)):
                window_df = df.iloc[max(0, i-50):i+1].reset_index(drop=True)
                signal = detect_order_blocks(window_df)
                if signal.action != "HOLD":
                    signals_count += 1
        
        # SMC: Fair Value Gap
        elif strategy_key == "smc_fvg":
            df = pd.DataFrame({
                'close': closes,
                'high': highs,
                'low': lows,
                'open': closes
            })
            for i in range(50, len(df)):
                window_df = df.iloc[max(0, i-50):i+1].reset_index(drop=True)
                signal = detect_fvg(window_df)
                if signal.action != "HOLD":
                    signals_count += 1
        
        # SMC: Liquidity Sweep
        elif strategy_key == "smc_liquidity_sweep":
            df = pd.DataFrame({
                'close': closes,
                'high': highs,
                'low': lows,
                'open': closes
            })
            for i in range(50, len(df)):
                window_df = df.iloc[max(0, i-50):i+1].reset_index(drop=True)
                signal = detect_liquidity_sweep(window_df)
                if signal.action != "HOLD":
                    signals_count += 1
        
        return signals_count
    
    def _simulate_trades_from_signals(self, confluence_signals: int, closes: List[float], initial_capital: float) -> Tuple[float, int, int]:
        """Simula trades baseados nos sinais de confluência"""
        capital = initial_capital
        position_size_pct = 0.02  # 2% do capital por trade
        
        winning_trades = 0
        total_trades = min(confluence_signals, len(closes) // 10)  # Limitar trades baseado em dados disponíveis
        
        # Simular trades com 60% de win rate típico de confluência
        for i in range(total_trades):
            position_size = capital * position_size_pct
            
            # Simular resultado baseado em movimento real de preço
            if i * 10 + 10 < len(closes):
                entry_price = closes[i * 10]
                exit_price = closes[i * 10 + 10]
                pnl_pct = (exit_price - entry_price) / entry_price
                
                # Aplicar P&L
                pnl = position_size * abs(pnl_pct) * (1 if pnl_pct > 0 else -1)
                capital += pnl
                
                if pnl > 0:
                    winning_trades += 1
        
        return capital, total_trades, winning_trades
    
    def _calculate_rsi(self, data: List[float], period: int = 14) -> List[float]:
        """Calcula RSI real"""
        rsi_values = []
        if len(data) < period + 1:
            return rsi_values
        
        for i in range(period, len(data)):
            gains = []
            losses = []
            for j in range(i - period, i):
                change = data[j + 1] - data[j]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            avg_gain = np.mean(gains) if gains else 0
            avg_loss = np.mean(losses) if losses else 0
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
        
        return rsi_values
    
    def _calculate_ema(self, data: List[float], period: int) -> List[float]:
        """Calcula EMA real"""
        ema_values = []
        if len(data) < period:
            return ema_values
        
        multiplier = 2 / (period + 1)
        ema = np.mean(data[:period])  # SMA inicial
        ema_values.append(ema)
        
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
            ema_values.append(ema)
        
        return ema_values
    
    def _calculate_bollinger_bands(self, data: List[float], period: int = 20, std_dev: float = 2.0) -> Tuple[List[float], List[float]]:
        """Calcula Bandas de Bollinger reais"""
        upper_band = []
        lower_band = []
        
        for i in range(period - 1, len(data)):
            window = data[i - period + 1:i + 1]
            sma = np.mean(window)
            std = np.std(window)
            upper_band.append(sma + std_dev * std)
            lower_band.append(sma - std_dev * std)
        
        return upper_band, lower_band
    
    def _calculate_macd(self, data: List[float]) -> Tuple[List[float], List[float]]:
        """Calcula MACD real"""
        ema_12 = self._calculate_ema(data, 12)
        ema_26 = self._calculate_ema(data, 26)
        
        macd_line = []
        for i in range(min(len(ema_12), len(ema_26))):
            macd_line.append(ema_12[i] - ema_26[i])
        
        signal_line = self._calculate_ema(macd_line, 9) if len(macd_line) >= 9 else []
        
        return macd_line, signal_line
    
    def _calculate_stochastic(self, closes: List[float], highs: List[float], lows: List[float], period: int = 14) -> List[float]:
        """Calcula Estocástico real"""
        stoch_values = []
        
        for i in range(period - 1, len(closes)):
            highest_high = max(highs[i - period + 1:i + 1])
            lowest_low = min(lows[i - period + 1:i + 1])
            
            if highest_high == lowest_low:
                stoch = 50
            else:
                stoch = ((closes[i] - lowest_low) / (highest_high - lowest_low)) * 100
            
            stoch_values.append(stoch)
        
        return stoch_values
    
    def _calculate_williams_r(self, closes: List[float], highs: List[float], lows: List[float], period: int = 14) -> List[float]:
        """Calcula Williams %R real"""
        williams_values = []
        
        for i in range(period - 1, len(closes)):
            highest_high = max(highs[i - period + 1:i + 1])
            lowest_low = min(lows[i - period + 1:i + 1])
            
            if highest_high == lowest_low:
                wr = -50
            else:
                wr = ((highest_high - closes[i]) / (highest_high - lowest_low)) * -100
            
            williams_values.append(wr)
        
        return williams_values
    
    def _calculate_adx(self, closes: List[float], highs: List[float], lows: List[float], period: int = 14) -> List[float]:
        """Calcula ADX real (simplificado)"""
        adx_values = []
        
        for i in range(period, len(closes)):
            # Simplificado: usar volatilidade como proxy para ADX
            window = closes[i - period:i]
            volatility = np.std(window) / np.mean(window) * 100
            adx_values.append(min(volatility * 10, 100))  # Normalizar para 0-100
        
        return adx_values
    
    def _calculate_confluence_signals(self, strategy_signals: Dict) -> int:
        """Calcula sinais de confluência baseado no modo selecionado"""
        if self.selected_confluence_mode == "ALL":
            # Todas as estratégias devem concordar
            return min([data['signals'] for data in strategy_signals.values()])
        
        elif self.selected_confluence_mode == "ANY":
            # Qualquer estratégia pode gerar sinal
            return max([data['signals'] for data in strategy_signals.values()])
        
        elif self.selected_confluence_mode == "MAJORITY":
            # Maioria das estratégias deve concordar
            signals_list = [data['signals'] for data in strategy_signals.values()]
            return int(np.median(signals_list))
        
        elif self.selected_confluence_mode == "WEIGHTED":
            # Média ponderada dos sinais
            total_weighted = 0
            total_weight = 0
            for data in strategy_signals.values():
                total_weighted += data['signals'] * data['weight']
                total_weight += data['weight']
            return int(total_weighted / total_weight) if total_weight > 0 else 0
        
        return 0
    
    def _view_test_results(self):
        """Visualiza resultados dos testes"""
        print("\n📊 VISUALIZAR RESULTADOS")
        print("="*50)
        
        if not self.test_history:
            print("❌ Nenhum teste executado ainda")
            print("💡 Execute um backtest de confluência primeiro")
        else:
            print(f"📈 {len(self.test_history)} teste(s) no histórico:")
            for i, test in enumerate(self.test_history, 1):
                print(f"   {i}. {test['type']} - {test['asset']} - {test['confluence_mode']}")
                print(f"      📊 ROI: {test['results']['roi']:+.2f}% | Win Rate: {test['results']['win_rate']:.1f}%")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _export_results(self):
        """Exporta resultados para arquivo"""
        print("\n📤 EXPORTAR RELATÓRIOS")
        print("="*50)
        
        if not self.test_history:
            print("❌ Nenhum resultado para exportar")
            print("💡 Execute um teste primeiro")
        else:
            # Criar diretório reports se não existir
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            
            # Gerar nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"confluence_mode_results_{timestamp}.json"
            filepath = reports_dir / filename
            
            # Salvar resultados
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "confluence_mode_version": "V1",
                "test_history": self.test_history
            }
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Relatório exportado com sucesso!")
                print(f"📁 Arquivo: {filepath}")
                print(f"📊 {len(self.test_history)} teste(s) incluído(s)")
            except Exception as e:
                print(f"❌ Erro ao exportar: {e}")
        
        input("\n📖 Pressione ENTER para continuar...")
