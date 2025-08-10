#!/usr/bin/env python3
"""
STRATEGY FACTORY CLI - Fábrica de Estratégias Validadas
Sistema de Trading Automatizado - Combinações múltiplas e validação automática
"""

import asyncio
import json
import logging
import os
import sys
import time
import itertools
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Importar componentes existentes
from capital_manager import CapitalManager, CapitalConfig, create_default_capital_config
from backtest_cli_enhanced import BybitAPIV5RealData, RealDataIndicators, RealDataStrategyEngine

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('strategy_factory.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StrategyValidator:
    """Validador de estratégias com critérios configuráveis"""
    
    def __init__(self):
        self.criteria = {
            'approved': {
                'min_roi': 5.0,           # ROI mínimo 5%
                'min_win_rate': 0.55,     # Win rate mínimo 55%
                'max_drawdown': 0.15,     # Drawdown máximo 15%
                'min_profit_factor': 1.2, # Profit factor mínimo 1.2
                'min_trades': 10          # Mínimo 10 trades
            },
            'conditional': {
                'min_roi': 2.0,           # ROI mínimo 2%
                'min_win_rate': 0.50,     # Win rate mínimo 50%
                'max_drawdown': 0.20,     # Drawdown máximo 20%
                'min_profit_factor': 1.0, # Profit factor mínimo 1.0
                'min_trades': 5           # Mínimo 5 trades
            }
        }
    
    def validate_strategy(self, metrics: Dict) -> str:
        """
        Valida uma estratégia baseada nas métricas
        
        Returns:
            'approved', 'conditional', ou 'rejected'
        """
        # Verificar critérios para aprovação
        if self._meets_criteria(metrics, 'approved'):
            return 'approved'
        
        # Verificar critérios condicionais
        elif self._meets_criteria(metrics, 'conditional'):
            return 'conditional'
        
        # Rejeitada
        else:
            return 'rejected'
    
    def _meets_criteria(self, metrics: Dict, level: str) -> bool:
        """Verifica se métricas atendem critérios do nível especificado"""
        criteria = self.criteria[level]
        
        # ROI
        if metrics.get('roi_percent', 0) < criteria['min_roi']:
            return False
        
        # Win rate
        if metrics.get('win_rate', 0) < criteria['min_win_rate']:
            return False
        
        # Drawdown
        if metrics.get('max_drawdown_percent', 100) > criteria['max_drawdown'] * 100:
            return False
        
        # Profit factor
        if metrics.get('profit_factor', 0) < criteria['min_profit_factor']:
            return False
        
        # Número mínimo de trades
        if metrics.get('total_trades', 0) < criteria['min_trades']:
            return False
        
        return True
    
    def calculate_composite_score(self, metrics: Dict) -> float:
        """Calcula score composto para ranking"""
        # Pesos para cada métrica
        weights = {
            'roi': 0.30,
            'win_rate': 0.25,
            'profit_factor': 0.25,
            'drawdown': 0.20
        }
        
        # Normalizar métricas (0-1)
        roi_norm = min(max(metrics.get('roi_percent', 0) / 50.0, 0), 1)  # Max 50% ROI
        win_rate_norm = metrics.get('win_rate', 0)  # Já está 0-1
        pf_norm = min(max((metrics.get('profit_factor', 0) - 1) / 2.0, 0), 1)  # PF 1-3 -> 0-1
        dd_norm = 1 - min(metrics.get('max_drawdown_percent', 100) / 100.0, 1)  # Inverso do drawdown
        
        # Calcular score composto
        score = (
            weights['roi'] * roi_norm +
            weights['win_rate'] * win_rate_norm +
            weights['profit_factor'] * pf_norm +
            weights['drawdown'] * dd_norm
        )
        
        return score * 100  # Converter para 0-100

class StrategyCombinator:
    """Gerador de combinações de estratégias"""
    
    def __init__(self):
        self.base_strategies = ['ema_crossover', 'rsi_mean_reversion', 'bollinger_breakout']
        
    def get_all_combinations(self) -> Dict[str, List]:
        """Gera todas as combinações possíveis"""
        combinations = {
            'single': [],
            'dual': [],
            'triple': [],
            'full': []
        }
        
        # Single strategies
        for strategy in self.base_strategies:
            combinations['single'].append([strategy])
        
        # Dual combinations
        for combo in itertools.combinations(self.base_strategies, 2):
            combinations['dual'].append(list(combo))
        
        # Triple combinations
        for combo in itertools.combinations(self.base_strategies, 3):
            combinations['triple'].append(list(combo))
        
        # Full combination
        combinations['full'].append(self.base_strategies.copy())
        
        return combinations
    
    def get_combination_name(self, strategies: List[str]) -> str:
        """Gera nome para combinação de estratégias"""
        if len(strategies) == 1:
            return strategies[0]
        elif len(strategies) == 2:
            return f"dual_mix_{strategies[0][:3]}_{strategies[1][:3]}"
        elif len(strategies) == 3:
            return "triple_mix_all_basic"
        else:
            return "full_mix_all_strategies"

class ReportManager:
    """Gerenciador de relatórios com nomenclatura padronizada"""
    
    def __init__(self):
        self.reports_dir = "reports"
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def generate_report_name(self, strategy_mix: str) -> str:
        """Gera nome do relatório no formato strategy_mix_dd/mm/aa_hh:mm:ss"""
        now = datetime.now()
        timestamp = now.strftime("%d/%m/%y_%H:%M:%S")
        # Substituir caracteres problemáticos para nomes de arquivo
        timestamp_safe = timestamp.replace("/", "-").replace(":", "-")
        return f"{strategy_mix}_{timestamp_safe}"
    
    def save_report(self, data: Dict, strategy_mix: str) -> str:
        """Salva relatório com nomenclatura padronizada"""
        try:
            filename = self.generate_report_name(strategy_mix)
            filepath = os.path.join(self.reports_dir, f"{filename}.json")
            
            # Adicionar metadados
            report_data = {
                'metadata': {
                    'strategy_mix': strategy_mix,
                    'timestamp': datetime.now().isoformat(),
                    'report_name': filename,
                    'generated_by': 'Strategy Factory CLI'
                },
                'data': data
            }
            
            with open(filepath, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            return filepath
        except Exception as e:
            logger.error(f"Erro ao salvar relatório: {e}")
            return None
    
    def list_reports(self) -> List[Dict]:
        """Lista todos os relatórios salvos"""
        reports = []
        
        try:
            for filename in os.listdir(self.reports_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.reports_dir, filename)
                    
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                        
                        reports.append({
                            'filename': filename,
                            'filepath': filepath,
                            'strategy_mix': data.get('metadata', {}).get('strategy_mix', 'Unknown'),
                            'timestamp': data.get('metadata', {}).get('timestamp', 'Unknown'),
                            'validation': data.get('data', {}).get('validation', 'Unknown')
                        })
                    except Exception as e:
                        logger.warning(f"Erro ao ler relatório {filename}: {e}")
        
        except Exception as e:
            logger.error(f"Erro ao listar relatórios: {e}")
        
        return sorted(reports, key=lambda x: x['timestamp'], reverse=True)

class StrategyFactoryEngine:
    """Engine principal da fábrica de estratégias"""
    
    def __init__(self):
        self.api_client = BybitAPIV5RealData()
        self.strategy_engine = RealDataStrategyEngine()
        self.validator = StrategyValidator()
        self.combinator = StrategyCombinator()
        self.report_manager = ReportManager()
        
        # Testar conexão na inicialização
        if not self.api_client.test_connection():
            raise ConnectionError("❌ Não foi possível conectar à API Bybit")
    
    def test_strategy_combination(self, strategies: List[str], symbol: str, timeframe: str,
                                start_date: str, end_date: str, capital_manager: CapitalManager) -> Dict:
        """Testa uma combinação de estratégias"""
        try:
            combination_name = self.combinator.get_combination_name(strategies)
            
            print(f"\n🔄 Testando: {combination_name}")
            print(f"   📊 Estratégias: {', '.join(strategies)}")
            print(f"   💰 Capital: ${capital_manager.config.initial_capital_usd:,.2f}")
            
            start_time = time.time()
            
            # 1. Obter dados históricos
            historical_data = self.api_client.get_historical_klines(
                symbol, timeframe, start_date, end_date
            )
            
            # 2. Reset do capital manager
            capital_manager.reset_capital()
            
            # 3. Aplicar estratégias e combinar sinais
            combined_signals = self._combine_strategy_signals(strategies, historical_data)
            
            # 4. Simular trades
            self._simulate_trades_with_capital(combined_signals, capital_manager)
            
            # 5. Obter métricas
            metrics = capital_manager.get_metrics()
            
            # 6. Validar estratégia
            validation = self.validator.validate_strategy(metrics)
            score = self.validator.calculate_composite_score(metrics)
            
            execution_time = time.time() - start_time
            
            result = {
                'combination_name': combination_name,
                'strategies': strategies,
                'symbol': symbol,
                'timeframe': timeframe,
                'period': f"{start_date}_to_{end_date}",
                'metrics': metrics,
                'validation': validation,
                'composite_score': score,
                'execution_time': execution_time,
                'data_points': len(historical_data),
                'capital_config': capital_manager.config.to_dict()
            }
            
            # Status visual
            status_emoji = {
                'approved': '✅',
                'conditional': '⚠️',
                'rejected': '❌'
            }
            
            print(f"   {status_emoji[validation]} {validation.upper()}: Score {score:.1f}")
            print(f"   💰 ROI: {metrics['roi_percent']:+.2f}% | Win Rate: {metrics['win_rate']:.1%}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro no teste de combinação: {e}")
            return {'error': str(e)}
    
    def _combine_strategy_signals(self, strategies: List[str], data: List[Dict]) -> List[Dict]:
        """Combina sinais de múltiplas estratégias"""
        all_signals = {}
        
        # Aplicar cada estratégia
        for strategy in strategies:
            strategy_func = self.strategy_engine.strategies[strategy]
            config = self.strategy_engine.strategy_configs[strategy]['params']
            signals = strategy_func(data, config)
            all_signals[strategy] = signals
        
        # Combinar sinais
        combined_signals = []
        for i in range(len(data)):
            # Coletar sinais de todas as estratégias para este ponto
            strategy_signals = []
            strategy_strengths = []
            
            for strategy in strategies:
                signal = all_signals[strategy][i]
                if signal['signal'] != 0:
                    strategy_signals.append(signal['signal'])
                    strategy_strengths.append(signal['signal_strength'])
            
            # Combinar sinais (consenso simples)
            if strategy_signals:
                # Sinal final: maioria ou média ponderada
                if len(strategies) == 1:
                    final_signal = strategy_signals[0]
                    final_strength = strategy_strengths[0]
                else:
                    # Consenso por maioria
                    positive_signals = sum(1 for s in strategy_signals if s > 0)
                    negative_signals = sum(1 for s in strategy_signals if s < 0)
                    
                    if positive_signals > negative_signals:
                        final_signal = 1
                    elif negative_signals > positive_signals:
                        final_signal = -1
                    else:
                        final_signal = 0
                    
                    # Força média
                    final_strength = sum(strategy_strengths) / len(strategy_strengths) if strategy_strengths else 0
            else:
                final_signal = 0
                final_strength = 0
            
            combined_signals.append({
                **data[i],
                'signal': final_signal,
                'signal_strength': final_strength,
                'contributing_strategies': len(strategy_signals),
                'strategy_consensus': strategy_signals
            })
        
        return combined_signals
    
    def _simulate_trades_with_capital(self, signals: List[Dict], capital_manager: CapitalManager):
        """Simula trades usando o capital manager"""
        position = None
        stop_loss_pct = 0.015  # 1.5%
        take_profit_pct = 0.03  # 3%
        max_holding_periods = 48
        
        for i, signal in enumerate(signals):
            current_price = float(signal['close'])
            
            # Entrada em nova posição
            if signal['signal'] != 0 and position is None:
                position = {
                    'direction': signal['signal'],
                    'entry_price': current_price,
                    'entry_time': signal['timestamp'],
                    'entry_index': i,
                    'signal_strength': signal['signal_strength']
                }
                
                # Definir níveis de saída
                if signal['signal'] == 1:  # Long
                    position['stop_loss'] = current_price * (1 - stop_loss_pct)
                    position['take_profit'] = current_price * (1 + take_profit_pct)
                else:  # Short
                    position['stop_loss'] = current_price * (1 + stop_loss_pct)
                    position['take_profit'] = current_price * (1 - take_profit_pct)
            
            # Verificar condições de saída
            elif position is not None:
                should_exit = False
                exit_reason = ""
                
                # Stop loss
                if ((position['direction'] == 1 and current_price <= position['stop_loss']) or
                    (position['direction'] == -1 and current_price >= position['stop_loss'])):
                    should_exit = True
                    exit_reason = "stop_loss"
                
                # Take profit
                elif ((position['direction'] == 1 and current_price >= position['take_profit']) or
                      (position['direction'] == -1 and current_price <= position['take_profit'])):
                    should_exit = True
                    exit_reason = "take_profit"
                
                # Sinal contrário
                elif signal['signal'] == -position['direction']:
                    should_exit = True
                    exit_reason = "signal_reversal"
                
                # Tempo máximo em posição
                elif i - position['entry_index'] >= max_holding_periods:
                    should_exit = True
                    exit_reason = "max_time"
                
                # Fechar posição
                if should_exit:
                    capital_manager.execute_trade(
                        entry_price=position['entry_price'],
                        exit_price=current_price,
                        direction=position['direction'],
                        timestamp=signal['timestamp'],
                        exit_reason=exit_reason,
                        stop_loss_percent=stop_loss_pct
                    )
                    position = None

class StrategyFactoryCLI:
    """CLI da Fábrica de Estratégias"""
    
    def __init__(self):
        try:
            self.factory_engine = StrategyFactoryEngine()
            self.symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT', 'SOLUSDT']
            self.timeframes = ['5m', '15m', '30m', '1h', '4h', '1d']
            
            # Períodos históricos
            self.historical_periods = {
                'Q1_2024': {
                    'start': '2024-01-01', 'end': '2024-03-31', 
                    'name': 'Q1 2024 - Bull Market',
                    'context': 'Forte tendência de alta, aprovação ETF Bitcoin'
                },
                'Q2_2024': {
                    'start': '2024-04-01', 'end': '2024-06-30',
                    'name': 'Q2 2024 - Correção', 
                    'context': 'Correção saudável, consolidação'
                },
                'Q3_2024': {
                    'start': '2024-07-01', 'end': '2024-09-30',
                    'name': 'Q3 2024 - Recuperação',
                    'context': 'Recuperação gradual, mercado lateral'
                },
                'Q4_2024': {
                    'start': '2024-10-01', 'end': '2024-12-31',
                    'name': 'Q4 2024 - Rally Final',
                    'context': 'Rally de fim de ano, máximas históricas'
                }
            }
            
            # Carregar configuração de capital
            self.capital_manager = CapitalManager.load_config()
            if self.capital_manager is None:
                config = create_default_capital_config(10000.0)
                self.capital_manager = CapitalManager(config)
                print("💰 Usando configuração padrão de capital: $10,000")
            else:
                print(f"💰 Configuração de capital carregada: ${self.capital_manager.config.initial_capital_usd:,.2f}")
            
        except Exception as e:
            print(f"❌ Erro na inicialização: {e}")
            sys.exit(1)
    
    def display_header(self):
        """Exibe cabeçalho da fábrica"""
        print("\n" + "="*80)
        print("🏭 STRATEGY FACTORY CLI - FÁBRICA DE ESTRATÉGIAS VALIDADAS")
        print("="*80)
        print("✅ Conectado à API Bybit configurada")
        print("🔄 Combinações múltiplas de estratégias")
        print("📊 Validação automática com critérios configuráveis")
        print("💰 Capital livre de $1 - $100,000")
        print("📈 Relatórios padronizados com nomenclatura específica")
        print("🎯 Sweet spot finder para otimização")
        print("="*80)
    
    def display_main_menu(self):
        """Exibe menu principal da fábrica"""
        print("\n🏭 FÁBRICA DE ESTRATÉGIAS - MENU PRINCIPAL")
        print("="*60)
        print("   1️⃣  Configurar Capital ($1 - $100,000)")
        print("   2️⃣  Teste Rápido (Single Strategy)")
        print("   3️⃣  Laboratório de Combinações (Strategy Mix)")
        print("   4️⃣  Validação Completa (All Combinations)")
        print("   5️⃣  Análise de Performance (Sweet Spot Finder)")
        print("   6️⃣  Histórico de Testes")
        print("   7️⃣  Ranking de Estratégias")
        print("   8️⃣  Exportar Relatórios")
        print("   9️⃣  Configurações Avançadas")
        print("   🔍  Listar Estratégias Disponíveis")
        print("   0️⃣  Sair")
        print()
    
    def configure_capital(self):
        """Configurar capital inicial ($1 - $100,000)"""
        print("\n💰 CONFIGURAÇÃO DE CAPITAL INICIAL")
        print("="*50)
        
        current_config = self.capital_manager.config
        print(f"\n📊 CONFIGURAÇÃO ATUAL:")
        print(f"   💰 Capital inicial: ${current_config.initial_capital_usd:,.2f}")
        print(f"   📊 Position size: {current_config.position_size_percent}%")
        print(f"   🔄 Compound interest: {'Sim' if current_config.compound_interest else 'Não'}")
        
        print(f"\n🔧 NOVA CONFIGURAÇÃO:")
        
        # Capital inicial ($1 - $100,000)
        while True:
            try:
                capital_input = input(f"💰 Capital inicial em USD ($1 - $100,000): ").strip()
                if not capital_input:
                    initial_capital = current_config.initial_capital_usd
                    break
                
                initial_capital = float(capital_input)
                if initial_capital < 1.0:
                    print("❌ Capital mínimo: $1")
                    continue
                if initial_capital > 100000.0:
                    print("❌ Capital máximo: $100,000")
                    continue
                break
            except ValueError:
                print("❌ Digite um valor numérico válido")
        
        # Position size
        while True:
            try:
                pos_input = input(f"📊 Position size em % do capital (0.1% - 10%): ").strip()
                if not pos_input:
                    position_size_percent = current_config.position_size_percent
                    break
                
                position_size_percent = float(pos_input)
                if position_size_percent < 0.1:
                    print("❌ Position size mínimo: 0.1%")
                    continue
                if position_size_percent > 10:
                    print("❌ Position size máximo: 10%")
                    continue
                break
            except ValueError:
                print("❌ Digite um valor numérico válido")
        
        # Compound interest
        compound_input = input(f"🔄 Usar compound interest? (s/N): ").strip().lower()
        compound_interest = compound_input == 's'
        
        # Criar nova configuração
        new_config = CapitalConfig(
            initial_capital_usd=initial_capital,
            position_size_percent=position_size_percent,
            compound_interest=compound_interest,
            min_position_size_usd=max(1.0, initial_capital * 0.001),
            max_position_size_usd=min(initial_capital * 0.1, 10000.0),
            risk_per_trade_percent=1.0
        )
        
        # Mostrar resumo
        print(f"\n📋 RESUMO DA NOVA CONFIGURAÇÃO:")
        print(f"   💰 Capital inicial: ${new_config.initial_capital_usd:,.2f}")
        print(f"   📊 Position size: {new_config.position_size_percent}%")
        print(f"   🔄 Compound interest: {'Sim' if new_config.compound_interest else 'Não'}")
        
        # Confirmar
        confirm = input(f"\n✅ Salvar esta configuração? (s/N): ").strip().lower()
        if confirm == 's':
            self.capital_manager = CapitalManager(new_config)
            if self.capital_manager.save_config():
                print(f"✅ Configuração salva com sucesso!")
            else:
                print(f"⚠️  Configuração aplicada mas não foi possível salvar")
        else:
            print(f"❌ Configuração cancelada")
    
    def list_available_strategies(self):
        """Lista todas as estratégias disponíveis"""
        print("\n📋 ESTRATÉGIAS DISPONÍVEIS NO PROJETO MARKET_MANUS")
        print("="*70)
        
        print(f"\n🎯 ESTRATÉGIAS BÁSICAS (Implementadas):")
        strategies = self.factory_engine.strategy_engine.strategy_configs
        for i, (key, config) in enumerate(strategies.items(), 1):
            print(f"   {i}. {config['name']}")
            print(f"      📝 {config['description']}")
            print(f"      ⚠️ Risco: {config['risk_level']}")
            print(f"      📊 Timeframes: {', '.join(config['best_timeframes'])}")
            print(f"      🎯 Condições: {config['market_conditions']}")
            print()
        
        print(f"🔄 ENGINES DE SINERGIA (Documentados):")
        sinergia_engines = [
            ("Market Regime Detector", "Detecta 5 regimes de mercado (Bull/Bear High/Low Vol, Neutral)"),
            ("Strategy Selector", "Seleção dinâmica baseada em performance histórica"),
            ("Consensus Engine", "5 métodos de consenso entre estratégias"),
            ("Adaptive Risk Manager", "Gestão de risco adaptativa por regime"),
            ("Hybrid Strategy Engine", "Engine híbrido principal combinando tudo")
        ]
        
        for i, (name, desc) in enumerate(sinergia_engines, 1):
            print(f"   {i}. {name}")
            print(f"      📝 {desc}")
            print()
        
        print(f"🔬 COMBINAÇÕES POSSÍVEIS:")
        combinations = self.factory_engine.combinator.get_all_combinations()
        total_combinations = sum(len(combos) for combos in combinations.values())
        
        print(f"   📊 Single strategies: {len(combinations['single'])} combinações")
        print(f"   📊 Dual combinations: {len(combinations['dual'])} combinações")
        print(f"   📊 Triple combinations: {len(combinations['triple'])} combinações")
        print(f"   📊 Full combinations: {len(combinations['full'])} combinações")
        print(f"   🎯 TOTAL: {total_combinations} combinações possíveis")
        
        input(f"\n📱 Pressione Enter para continuar...")
    
    def quick_strategy_test(self):
        """Teste rápido de uma estratégia individual"""
        print("\n🚀 TESTE RÁPIDO - SINGLE STRATEGY")
        print("="*50)
        
        # Selecionar estratégia
        strategies = list(self.factory_engine.strategy_engine.strategies.keys())
        print(f"\n🎯 ESTRATÉGIAS DISPONÍVEIS:")
        for i, strategy in enumerate(strategies, 1):
            config = self.factory_engine.strategy_engine.strategy_configs[strategy]
            print(f"   {i}. {config['name']}")
        
        while True:
            try:
                choice = input(f"\n📊 Escolha uma estratégia (1-{len(strategies)}): ").strip()
                strategy_idx = int(choice) - 1
                if 0 <= strategy_idx < len(strategies):
                    selected_strategy = strategies[strategy_idx]
                    break
                else:
                    print(f"❌ Escolha entre 1 e {len(strategies)}")
            except ValueError:
                print("❌ Digite um número válido")
        
        # Configuração rápida
        symbol = 'BTCUSDT'
        timeframe = '15m'
        period = self.historical_periods['Q4_2024']
        
        print(f"\n📊 CONFIGURAÇÃO DO TESTE:")
        print(f"   🎯 Estratégia: {selected_strategy}")
        print(f"   📊 Símbolo: {symbol}")
        print(f"   ⏰ Timeframe: {timeframe}")
        print(f"   📅 Período: {period['name']}")
        print(f"   💰 Capital: ${self.capital_manager.config.initial_capital_usd:,.2f}")
        
        confirm = input(f"\n✅ Executar teste? (s/N): ").strip().lower()
        if confirm != 's':
            return
        
        # Executar teste
        print(f"\n🔄 Executando teste...")
        result = self.factory_engine.test_strategy_combination(
            [selected_strategy], symbol, timeframe, 
            period['start'], period['end'], self.capital_manager
        )
        
        if 'error' in result:
            print(f"❌ Erro: {result['error']}")
            return
        
        # Salvar relatório
        report_path = self.factory_engine.report_manager.save_report(result, selected_strategy)
        
        # Exibir resultados
        self._display_test_results(result)
        
        if report_path:
            print(f"\n💾 Relatório salvo: {os.path.basename(report_path)}")
    
    def strategy_combinations_lab(self):
        """Laboratório de combinações de estratégias"""
        print("\n🔬 LABORATÓRIO DE COMBINAÇÕES - STRATEGY MIX")
        print("="*60)
        
        # Mostrar combinações disponíveis
        combinations = self.factory_engine.combinator.get_all_combinations()
        
        print(f"\n🧪 TIPOS DE COMBINAÇÕES:")
        print(f"   1️⃣ Single Strategies ({len(combinations['single'])} opções)")
        print(f"   2️⃣ Dual Combinations ({len(combinations['dual'])} opções)")
        print(f"   3️⃣ Triple Combinations ({len(combinations['triple'])} opções)")
        print(f"   4️⃣ Full Combination ({len(combinations['full'])} opções)")
        print(f"   5️⃣ Combinação Personalizada")
        
        while True:
            try:
                choice = input(f"\n🔬 Escolha o tipo de combinação (1-5): ").strip()
                if choice in ['1', '2', '3', '4', '5']:
                    break
                else:
                    print("❌ Escolha entre 1 e 5")
            except ValueError:
                print("❌ Digite um número válido")
        
        # Selecionar combinação específica
        if choice == '1':
            selected_combinations = self._select_from_combinations(combinations['single'], "Single Strategies")
        elif choice == '2':
            selected_combinations = self._select_from_combinations(combinations['dual'], "Dual Combinations")
        elif choice == '3':
            selected_combinations = self._select_from_combinations(combinations['triple'], "Triple Combinations")
        elif choice == '4':
            selected_combinations = combinations['full']
        elif choice == '5':
            selected_combinations = self._create_custom_combination()
        
        if not selected_combinations:
            return
        
        # Configuração do teste
        symbol = 'BTCUSDT'
        timeframe = '15m'
        period = self.historical_periods['Q4_2024']
        
        print(f"\n📊 CONFIGURAÇÃO DO LABORATÓRIO:")
        print(f"   🧪 Combinações selecionadas: {len(selected_combinations)}")
        print(f"   📊 Símbolo: {symbol}")
        print(f"   ⏰ Timeframe: {timeframe}")
        print(f"   📅 Período: {period['name']}")
        print(f"   💰 Capital: ${self.capital_manager.config.initial_capital_usd:,.2f}")
        
        confirm = input(f"\n✅ Executar laboratório? (s/N): ").strip().lower()
        if confirm != 's':
            return
        
        # Executar testes
        print(f"\n🔄 Executando {len(selected_combinations)} teste(s)...")
        results = []
        
        for i, combination in enumerate(selected_combinations, 1):
            print(f"\n📊 Teste {i}/{len(selected_combinations)}")
            
            result = self.factory_engine.test_strategy_combination(
                combination, symbol, timeframe,
                period['start'], period['end'], self.capital_manager
            )
            
            if 'error' not in result:
                results.append(result)
                
                # Salvar relatório individual
                combination_name = self.factory_engine.combinator.get_combination_name(combination)
                self.factory_engine.report_manager.save_report(result, combination_name)
        
        # Análise comparativa
        if results:
            self._display_comparative_analysis(results)
    
    def complete_validation(self):
        """Validação completa de todas as combinações"""
        print("\n🎯 VALIDAÇÃO COMPLETA - ALL COMBINATIONS")
        print("="*60)
        
        combinations = self.factory_engine.combinator.get_all_combinations()
        all_combinations = []
        
        # Coletar todas as combinações
        for combo_type, combos in combinations.items():
            all_combinations.extend(combos)
        
        print(f"\n📊 ESCOPO DA VALIDAÇÃO:")
        print(f"   🎯 Total de combinações: {len(all_combinations)}")
        print(f"   📊 Single strategies: {len(combinations['single'])}")
        print(f"   📊 Dual combinations: {len(combinations['dual'])}")
        print(f"   📊 Triple combinations: {len(combinations['triple'])}")
        print(f"   📊 Full combinations: {len(combinations['full'])}")
        
        # Configuração
        symbol = 'BTCUSDT'
        timeframe = '15m'
        period = self.historical_periods['Q4_2024']
        
        print(f"\n⚙️ CONFIGURAÇÃO:")
        print(f"   📊 Símbolo: {symbol}")
        print(f"   ⏰ Timeframe: {timeframe}")
        print(f"   📅 Período: {period['name']}")
        print(f"   💰 Capital: ${self.capital_manager.config.initial_capital_usd:,.2f}")
        
        # Estimativa de tempo
        estimated_time = len(all_combinations) * 30  # 30s por teste
        print(f"   ⏱️ Tempo estimado: {estimated_time//60}min {estimated_time%60}s")
        
        confirm = input(f"\n✅ Executar validação completa? (s/N): ").strip().lower()
        if confirm != 's':
            return
        
        # Executar validação completa
        print(f"\n🔄 Iniciando validação completa...")
        results = []
        approved = []
        conditional = []
        rejected = []
        
        for i, combination in enumerate(all_combinations, 1):
            print(f"\n📊 Validando {i}/{len(all_combinations)}: {combination}")
            
            result = self.factory_engine.test_strategy_combination(
                combination, symbol, timeframe,
                period['start'], period['end'], self.capital_manager
            )
            
            if 'error' not in result:
                results.append(result)
                
                # Classificar resultado
                validation = result['validation']
                if validation == 'approved':
                    approved.append(result)
                elif validation == 'conditional':
                    conditional.append(result)
                else:
                    rejected.append(result)
                
                # Salvar relatório
                combination_name = self.factory_engine.combinator.get_combination_name(combination)
                self.factory_engine.report_manager.save_report(result, combination_name)
        
        # Relatório final da validação
        self._display_validation_summary(results, approved, conditional, rejected)
    
    def sweet_spot_finder(self):
        """Encontra sweet spots nas estratégias"""
        print("\n🎯 SWEET SPOT FINDER - ANÁLISE DE PERFORMANCE")
        print("="*60)
        
        # Verificar se há relatórios para analisar
        reports = self.factory_engine.report_manager.list_reports()
        
        if not reports:
            print("📭 Nenhum teste encontrado para análise.")
            print("💡 Execute alguns testes primeiro usando as opções 2, 3 ou 4.")
            return
        
        print(f"\n📊 DADOS DISPONÍVEIS:")
        print(f"   📋 {len(reports)} teste(s) encontrado(s)")
        
        # Carregar dados dos relatórios
        valid_results = []
        for report in reports:
            try:
                with open(report['filepath'], 'r') as f:
                    data = json.load(f)
                
                if 'data' in data and 'metrics' in data['data']:
                    valid_results.append(data['data'])
            except Exception as e:
                logger.warning(f"Erro ao carregar {report['filename']}: {e}")
        
        if not valid_results:
            print("❌ Nenhum resultado válido encontrado.")
            return
        
        print(f"   ✅ {len(valid_results)} resultado(s) válido(s) carregado(s)")
        
        # Análise de sweet spots
        print(f"\n🔍 ANALISANDO SWEET SPOTS...")
        
        # Ordenar por score composto
        scored_results = []
        for result in valid_results:
            score = self.factory_engine.validator.calculate_composite_score(result['metrics'])
            scored_results.append((result, score))
        
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        # Top 5 sweet spots
        print(f"\n🏆 TOP 5 SWEET SPOTS:")
        for i, (result, score) in enumerate(scored_results[:5], 1):
            metrics = result['metrics']
            combination_name = result.get('combination_name', 'Unknown')
            validation = result.get('validation', 'Unknown')
            
            status_emoji = {
                'approved': '✅',
                'conditional': '⚠️',
                'rejected': '❌'
            }
            
            emoji = status_emoji.get(validation, '❓')
            
            print(f"\n   {i}. {emoji} {combination_name} (Score: {score:.1f})")
            print(f"      💰 ROI: {metrics['roi_percent']:+.2f}%")
            print(f"      🎯 Win Rate: {metrics['win_rate']:.1%}")
            print(f"      📈 Profit Factor: {metrics['profit_factor']:.2f}")
            print(f"      📉 Max Drawdown: {metrics['max_drawdown_percent']:.1f}%")
            print(f"      📊 Trades: {metrics['total_trades']}")
        
        # Análise por categoria
        print(f"\n📊 ANÁLISE POR CATEGORIA:")
        
        # Melhor ROI
        best_roi = max(valid_results, key=lambda x: x['metrics']['roi_percent'])
        print(f"   📈 Melhor ROI: {best_roi['combination_name']} ({best_roi['metrics']['roi_percent']:+.2f}%)")
        
        # Melhor Win Rate
        best_wr = max(valid_results, key=lambda x: x['metrics']['win_rate'])
        print(f"   🎯 Melhor Win Rate: {best_wr['combination_name']} ({best_wr['metrics']['win_rate']:.1%})")
        
        # Menor Drawdown
        best_dd = min(valid_results, key=lambda x: x['metrics']['max_drawdown_percent'])
        print(f"   📉 Menor Drawdown: {best_dd['combination_name']} ({best_dd['metrics']['max_drawdown_percent']:.1f}%)")
        
        # Recomendação final
        if scored_results:
            best_overall = scored_results[0][0]
            print(f"\n🎯 RECOMENDAÇÃO SWEET SPOT:")
            print(f"   🏆 {best_overall['combination_name']}")
            print(f"   📊 Score Composto: {scored_results[0][1]:.1f}/100")
            print(f"   ✅ Status: {best_overall['validation'].upper()}")
        
        input(f"\n📱 Pressione Enter para continuar...")
    
    def _select_from_combinations(self, combinations: List, title: str) -> List:
        """Seleciona combinações específicas de uma lista"""
        print(f"\n🔬 {title.upper()}:")
        
        for i, combo in enumerate(combinations, 1):
            combo_name = self.factory_engine.combinator.get_combination_name(combo)
            print(f"   {i}. {combo_name} ({', '.join(combo)})")
        
        print(f"   A. Todas as {len(combinations)} combinações")
        
        while True:
            choice = input(f"\n📊 Escolha (1-{len(combinations)} ou A): ").strip()
            
            if choice.upper() == 'A':
                return combinations
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(combinations):
                    return [combinations[idx]]
                else:
                    print(f"❌ Escolha entre 1 e {len(combinations)} ou A")
            except ValueError:
                print("❌ Digite um número válido ou A")
    
    def _create_custom_combination(self) -> List:
        """Cria combinação personalizada de estratégias"""
        print(f"\n🎨 COMBINAÇÃO PERSONALIZADA:")
        
        strategies = list(self.factory_engine.strategy_engine.strategies.keys())
        print(f"\n🎯 ESTRATÉGIAS DISPONÍVEIS:")
        for i, strategy in enumerate(strategies, 1):
            print(f"   {i}. {strategy}")
        
        selected = []
        print(f"\n💡 Digite os números das estratégias separados por vírgula (ex: 1,2,3)")
        
        while True:
            choice = input(f"📊 Estratégias: ").strip()
            
            try:
                indices = [int(x.strip()) - 1 for x in choice.split(',')]
                
                if all(0 <= idx < len(strategies) for idx in indices):
                    selected = [strategies[idx] for idx in indices]
                    break
                else:
                    print(f"❌ Todos os números devem estar entre 1 e {len(strategies)}")
            except ValueError:
                print("❌ Digite números separados por vírgula (ex: 1,2,3)")
        
        print(f"\n✅ Combinação selecionada: {', '.join(selected)}")
        return [selected]
    
    def _display_test_results(self, result: Dict):
        """Exibe resultados de um teste individual"""
        metrics = result['metrics']
        
        print(f"\n📊 RESULTADOS DO TESTE")
        print("="*50)
        
        # Status de validação
        validation = result['validation']
        status_emoji = {
            'approved': '✅ APROVADA',
            'conditional': '⚠️ CONDICIONAL',
            'rejected': '❌ REJEITADA'
        }
        
        print(f"🎯 Estratégia: {result['combination_name']}")
        print(f"📊 Status: {status_emoji[validation]}")
        print(f"🏆 Score: {result['composite_score']:.1f}/100")
        
        # Métricas principais
        print(f"\n💰 PERFORMANCE:")
        print(f"   💰 Capital inicial: ${metrics['initial_capital_usd']:,.2f}")
        print(f"   💰 Capital final: ${metrics['final_capital_usd']:,.2f}")
        print(f"   📈 ROI: {metrics['roi_percent']:+.2f}%")
        print(f"   🎯 Win Rate: {metrics['win_rate']:.1%}")
        print(f"   📈 Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"   📉 Max Drawdown: {metrics['max_drawdown_percent']:.1f}%")
        print(f"   📊 Total Trades: {metrics['total_trades']}")
    
    def _display_comparative_analysis(self, results: List[Dict]):
        """Exibe análise comparativa de múltiplos resultados"""
        print(f"\n📊 ANÁLISE COMPARATIVA")
        print("="*60)
        
        # Ordenar por score
        results.sort(key=lambda x: x['composite_score'], reverse=True)
        
        print(f"\n🏆 RANKING POR PERFORMANCE:")
        for i, result in enumerate(results, 1):
            metrics = result['metrics']
            validation = result['validation']
            
            status_emoji = {
                'approved': '✅',
                'conditional': '⚠️',
                'rejected': '❌'
            }
            
            emoji = status_emoji[validation]
            
            print(f"\n   {i}. {emoji} {result['combination_name']}")
            print(f"      🏆 Score: {result['composite_score']:.1f}")
            print(f"      💰 ROI: {metrics['roi_percent']:+.2f}%")
            print(f"      🎯 Win Rate: {metrics['win_rate']:.1%}")
            print(f"      📊 Trades: {metrics['total_trades']}")
        
        # Estatísticas gerais
        approved = [r for r in results if r['validation'] == 'approved']
        conditional = [r for r in results if r['validation'] == 'conditional']
        rejected = [r for r in results if r['validation'] == 'rejected']
        
        print(f"\n📊 RESUMO GERAL:")
        print(f"   ✅ Aprovadas: {len(approved)}")
        print(f"   ⚠️ Condicionais: {len(conditional)}")
        print(f"   ❌ Rejeitadas: {len(rejected)}")
        print(f"   📊 Total testado: {len(results)}")
        
        if approved:
            best = approved[0]
            print(f"\n🏆 MELHOR ESTRATÉGIA:")
            print(f"   🎯 {best['combination_name']}")
            print(f"   🏆 Score: {best['composite_score']:.1f}")
            print(f"   💰 ROI: {best['metrics']['roi_percent']:+.2f}%")
    
    def _display_validation_summary(self, results: List[Dict], approved: List[Dict], 
                                  conditional: List[Dict], rejected: List[Dict]):
        """Exibe resumo da validação completa"""
        print(f"\n📊 RESUMO DA VALIDAÇÃO COMPLETA")
        print("="*60)
        
        print(f"\n🎯 RESULTADOS GERAIS:")
        print(f"   📊 Total testado: {len(results)}")
        print(f"   ✅ Aprovadas: {len(approved)} ({len(approved)/len(results)*100:.1f}%)")
        print(f"   ⚠️ Condicionais: {len(conditional)} ({len(conditional)/len(results)*100:.1f}%)")
        print(f"   ❌ Rejeitadas: {len(rejected)} ({len(rejected)/len(results)*100:.1f}%)")
        
        if approved:
            print(f"\n✅ TOP 3 ESTRATÉGIAS APROVADAS:")
            approved.sort(key=lambda x: x['composite_score'], reverse=True)
            
            for i, result in enumerate(approved[:3], 1):
                metrics = result['metrics']
                print(f"\n   {i}. {result['combination_name']}")
                print(f"      🏆 Score: {result['composite_score']:.1f}")
                print(f"      💰 ROI: {metrics['roi_percent']:+.2f}%")
                print(f"      🎯 Win Rate: {metrics['win_rate']:.1%}")
                print(f"      📈 Profit Factor: {metrics['profit_factor']:.2f}")
        
        if conditional:
            print(f"\n⚠️ ESTRATÉGIAS CONDICIONAIS:")
            for result in conditional[:3]:  # Top 3
                print(f"   • {result['combination_name']} (Score: {result['composite_score']:.1f})")
        
        print(f"\n💡 RECOMENDAÇÃO:")
        if approved:
            best = approved[0]
            print(f"   🏆 Use: {best['combination_name']}")
            print(f"   📊 Melhor score geral: {best['composite_score']:.1f}")
        elif conditional:
            best = max(conditional, key=lambda x: x['composite_score'])
            print(f"   ⚠️ Considere: {best['combination_name']}")
            print(f"   📊 Melhor entre condicionais: {best['composite_score']:.1f}")
        else:
            print(f"   ❌ Nenhuma estratégia recomendada")
            print(f"   💡 Considere ajustar parâmetros ou período de teste")
        
        input(f"\n📱 Pressione Enter para continuar...")
    
    def run(self):
        """Executa o CLI principal"""
        self.display_header()
        
        while True:
            self.display_main_menu()
            
            try:
                choice = input("🔢 Escolha uma opção: ").strip()
                
                if choice == '0':
                    print("\n👋 Obrigado por usar a Strategy Factory!")
                    break
                
                elif choice == '1':
                    self.configure_capital()
                
                elif choice == '2':
                    self.quick_strategy_test()
                
                elif choice == '3':
                    self.strategy_combinations_lab()
                
                elif choice == '4':
                    self.complete_validation()
                
                elif choice == '5':
                    self.sweet_spot_finder()
                
                elif choice == '6':
                    self._show_test_history()
                
                elif choice == '7':
                    print("\n🚧 Ranking de Estratégias em desenvolvimento...")
                
                elif choice == '8':
                    print("\n🚧 Exportar Relatórios em desenvolvimento...")
                
                elif choice == '9':
                    print("\n🚧 Configurações Avançadas em desenvolvimento...")
                
                elif choice.lower() in ['🔍', 'list', 'l']:
                    self.list_available_strategies()
                
                else:
                    print("❌ Opção inválida. Tente novamente.")
                
            except KeyboardInterrupt:
                print("\n\n👋 Saindo...")
                break
            except Exception as e:
                print(f"❌ Erro: {e}")
    
    def _show_test_history(self):
        """Mostra histórico de testes"""
        print("\n📊 HISTÓRICO DE TESTES")
        print("="*50)
        
        reports = self.factory_engine.report_manager.list_reports()
        
        if not reports:
            print("📭 Nenhum teste realizado ainda.")
            return
        
        print(f"\n📋 {len(reports)} teste(s) encontrado(s):")
        
        for i, report in enumerate(reports[:10], 1):  # Mostrar últimos 10
            status_emoji = {
                'approved': '✅',
                'conditional': '⚠️',
                'rejected': '❌',
                'Unknown': '❓'
            }
            
            emoji = status_emoji.get(report['validation'], '❓')
            timestamp = report['timestamp'][:19] if report['timestamp'] != 'Unknown' else 'Unknown'
            
            print(f"   {i}. {emoji} {report['strategy_mix']}")
            print(f"      📅 {timestamp}")
            print(f"      📁 {report['filename']}")
            print()
        
        if len(reports) > 10:
            print(f"   ... e mais {len(reports) - 10} teste(s)")
        
        input(f"\n📱 Pressione Enter para continuar...")

if __name__ == "__main__":
    try:
        cli = StrategyFactoryCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\n👋 Programa interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        sys.exit(1)

