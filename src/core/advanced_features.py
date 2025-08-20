#!/usr/bin/env python3
"""
ADVANCED FEATURES - Funcionalidades avançadas para Strategy Factory V2
Ranking de Estratégias, Exportar Relatórios e Configurações Avançadas
"""

import json
import os
import csv
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class StrategyRanking:
    """Sistema de ranking de estratégias"""
    
    def __init__(self, report_manager):
        self.report_manager = report_manager
        self.ranking_criteria = {
            'composite_score': {'weight': 0.4, 'name': 'Score Composto'},
            'roi_percent': {'weight': 0.25, 'name': 'ROI (%)'},
            'win_rate': {'weight': 0.2, 'name': 'Win Rate'},
            'profit_factor': {'weight': 0.15, 'name': 'Profit Factor'}
        }
    
    def generate_ranking(self) -> List[Dict]:
        """Gera ranking completo das estratégias"""
        reports = self.report_manager.list_reports()
        
        if not reports:
            return []
        
        # Carregar dados dos relatórios
        strategies_data = []
        for report in reports:
            try:
                with open(report['filepath'], 'r') as f:
                    data = json.load(f)
                
                if 'data' in data and 'metrics' in data['data']:
                    strategy_data = {
                        'name': data['data'].get('combination_name', 'Unknown'),
                        'validation': data['data'].get('validation', 'unknown'),
                        'composite_score': data['data'].get('composite_score', 0),
                        'metrics': data['data']['metrics'],
                        'test_config': data['data'].get('test_config', {}),
                        'timestamp': data['metadata'].get('timestamp', ''),
                        'filename': report['filename']
                    }
                    strategies_data.append(strategy_data)
            except Exception as e:
                continue
        
        # Calcular ranking score
        for strategy in strategies_data:
            strategy['ranking_score'] = self._calculate_ranking_score(strategy)
        
        # Ordenar por ranking score
        strategies_data.sort(key=lambda x: x['ranking_score'], reverse=True)
        
        return strategies_data
    
    def _calculate_ranking_score(self, strategy: Dict) -> float:
        """Calcula score de ranking baseado em múltiplos critérios"""
        metrics = strategy['metrics']
        
        # Normalizar métricas (0-1)
        normalized_scores = {}
        
        # Score composto (já normalizado 0-100)
        normalized_scores['composite_score'] = strategy['composite_score'] / 100.0
        
        # ROI (normalizar -50% a +50% para 0-1)
        roi = max(-50, min(50, metrics['roi_percent']))
        normalized_scores['roi_percent'] = (roi + 50) / 100.0
        
        # Win Rate (já 0-1)
        normalized_scores['win_rate'] = metrics['win_rate']
        
        # Profit Factor (normalizar 0-3 para 0-1)
        pf = max(0, min(3, metrics['profit_factor']))
        normalized_scores['profit_factor'] = pf / 3.0
        
        # Calcular score ponderado
        ranking_score = 0
        for criterion, config in self.ranking_criteria.items():
            if criterion in normalized_scores:
                ranking_score += normalized_scores[criterion] * config['weight']
        
        return ranking_score * 100  # Converter para 0-100
    
    def display_ranking(self, strategies: List[Dict], top_n: int = 10):
        """Exibe ranking das estratégias"""
        print(f"\n🏆 RANKING DE ESTRATÉGIAS (TOP {min(top_n, len(strategies))})")
        print("="*80)
        
        if not strategies:
            print("📭 Nenhuma estratégia encontrada para ranking.")
            return
        
        # Cabeçalho
        print(f"{'Pos':<4} {'Status':<3} {'Estratégia':<25} {'Score':<8} {'ROI':<8} {'Win%':<6} {'PF':<6}")
        print("-" * 80)
        
        # Top estratégias
        for i, strategy in enumerate(strategies[:top_n], 1):
            metrics = strategy['metrics']
            
            status_emoji = {
                'approved': '✅',
                'conditional': '⚠️',
                'rejected': '❌',
                'unknown': '❓'
            }
            
            emoji = status_emoji.get(strategy['validation'], '❓')
            name = strategy['name'][:24]  # Truncar nome se muito longo
            score = f"{strategy['ranking_score']:.1f}"
            roi = f"{metrics['roi_percent']:+.1f}%"
            win_rate = f"{metrics['win_rate']:.1%}"
            profit_factor = f"{metrics['profit_factor']:.2f}"
            
            print(f"{i:<4} {emoji:<3} {name:<25} {score:<8} {roi:<8} {win_rate:<6} {profit_factor:<6}")
        
        # Estatísticas do ranking
        approved = [s for s in strategies if s['validation'] == 'approved']
        conditional = [s for s in strategies if s['validation'] == 'conditional']
        rejected = [s for s in strategies if s['validation'] == 'rejected']
        
        print(f"\n📊 ESTATÍSTICAS DO RANKING:")
        print(f"   📊 Total analisado: {len(strategies)}")
        print(f"   ✅ Aprovadas: {len(approved)} ({len(approved)/len(strategies)*100:.1f}%)")
        print(f"   ⚠️ Condicionais: {len(conditional)} ({len(conditional)/len(strategies)*100:.1f}%)")
        print(f"   ❌ Rejeitadas: {len(rejected)} ({len(rejected)/len(strategies)*100:.1f}%)")
        
        if strategies:
            best = strategies[0]
            print(f"\n🏆 CAMPEÃ ABSOLUTA:")
            print(f"   🎯 {best['name']}")
            print(f"   🏆 Ranking Score: {best['ranking_score']:.1f}")
            print(f"   💰 ROI: {best['metrics']['roi_percent']:+.2f}%")
            print(f"   🎯 Win Rate: {best['metrics']['win_rate']:.1%}")
    
    def get_category_leaders(self, strategies: List[Dict]) -> Dict:
        """Identifica líderes por categoria"""
        if not strategies:
            return {}
        
        leaders = {}
        
        # Melhor ROI
        best_roi = max(strategies, key=lambda x: x['metrics']['roi_percent'])
        leaders['best_roi'] = best_roi
        
        # Melhor Win Rate
        best_win_rate = max(strategies, key=lambda x: x['metrics']['win_rate'])
        leaders['best_win_rate'] = best_win_rate
        
        # Melhor Profit Factor
        best_pf = max(strategies, key=lambda x: x['metrics']['profit_factor'])
        leaders['best_profit_factor'] = best_pf
        
        # Menor Drawdown
        best_dd = min(strategies, key=lambda x: x['metrics']['max_drawdown_percent'])
        leaders['best_drawdown'] = best_dd
        
        # Mais trades
        most_trades = max(strategies, key=lambda x: x['metrics']['total_trades'])
        leaders['most_trades'] = most_trades
        
        return leaders

class ReportExporter:
    """Sistema de exportação de relatórios"""
    
    def __init__(self, report_manager):
        self.report_manager = report_manager
        self.export_dir = Path("exports")
        self.export_dir.mkdir(exist_ok=True)
    
    def export_to_csv(self, filename: str = None) -> str:
        """Exporta relatórios para CSV"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"strategy_reports_{timestamp}.csv"
        
        filepath = self.export_dir / filename
        
        # Carregar dados dos relatórios
        reports = self.report_manager.list_reports()
        data_rows = []
        
        for report in reports:
            try:
                with open(report['filepath'], 'r') as f:
                    data = json.load(f)
                
                if 'data' in data and 'metrics' in data['data']:
                    strategy_data = data['data']
                    metrics = strategy_data['metrics']
                    test_config = strategy_data.get('test_config', {})
                    
                    row = {
                        'strategy_name': strategy_data.get('combination_name', 'Unknown'),
                        'validation': strategy_data.get('validation', 'unknown'),
                        'composite_score': strategy_data.get('composite_score', 0),
                        'roi_percent': metrics['roi_percent'],
                        'win_rate': metrics['win_rate'],
                        'profit_factor': metrics['profit_factor'],
                        'max_drawdown_percent': metrics['max_drawdown_percent'],
                        'total_trades': metrics['total_trades'],
                        'initial_capital_usd': metrics['initial_capital_usd'],
                        'final_capital_usd': metrics['final_capital_usd'],
                        'symbol': test_config.get('symbol', 'N/A'),
                        'timeframe': test_config.get('timeframe', 'N/A'),
                        'period_name': test_config.get('period_name', 'N/A'),
                        'start_date': test_config.get('start_date', 'N/A'),
                        'end_date': test_config.get('end_date', 'N/A'),
                        'timestamp': data['metadata'].get('timestamp', ''),
                        'filename': report['filename']
                    }
                    data_rows.append(row)
            except Exception as e:
                continue
        
        # Escrever CSV
        if data_rows:
            df = pd.DataFrame(data_rows)
            df.to_csv(filepath, index=False)
            return str(filepath)
        
        return None
    
    def export_to_excel(self, filename: str = None) -> str:
        """Exporta relatórios para Excel com múltiplas abas"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"strategy_reports_{timestamp}.xlsx"
        
        filepath = self.export_dir / filename
        
        # Carregar dados dos relatórios
        reports = self.report_manager.list_reports()
        all_data = []
        approved_data = []
        conditional_data = []
        rejected_data = []
        
        for report in reports:
            try:
                with open(report['filepath'], 'r') as f:
                    data = json.load(f)
                
                if 'data' in data and 'metrics' in data['data']:
                    strategy_data = data['data']
                    metrics = strategy_data['metrics']
                    test_config = strategy_data.get('test_config', {})
                    
                    row = {
                        'Estratégia': strategy_data.get('combination_name', 'Unknown'),
                        'Validação': strategy_data.get('validation', 'unknown'),
                        'Score Composto': strategy_data.get('composite_score', 0),
                        'ROI (%)': metrics['roi_percent'],
                        'Win Rate (%)': metrics['win_rate'] * 100,
                        'Profit Factor': metrics['profit_factor'],
                        'Max Drawdown (%)': metrics['max_drawdown_percent'],
                        'Total Trades': metrics['total_trades'],
                        'Capital Inicial ($)': metrics['initial_capital_usd'],
                        'Capital Final ($)': metrics['final_capital_usd'],
                        'Símbolo': test_config.get('symbol', 'N/A'),
                        'Timeframe': test_config.get('timeframe', 'N/A'),
                        'Período': test_config.get('period_name', 'N/A'),
                        'Data Início': test_config.get('start_date', 'N/A'),
                        'Data Fim': test_config.get('end_date', 'N/A'),
                        'Timestamp': data['metadata'].get('timestamp', ''),
                        'Arquivo': report['filename']
                    }
                    
                    all_data.append(row)
                    
                    # Separar por validação
                    validation = strategy_data.get('validation', 'unknown')
                    if validation == 'approved':
                        approved_data.append(row)
                    elif validation == 'conditional':
                        conditional_data.append(row)
                    elif validation == 'rejected':
                        rejected_data.append(row)
                        
            except Exception as e:
                continue
        
        # Criar Excel com múltiplas abas
        if all_data:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Aba principal com todos os dados
                df_all = pd.DataFrame(all_data)
                df_all.to_excel(writer, sheet_name='Todos os Testes', index=False)
                
                # Aba com aprovadas
                if approved_data:
                    df_approved = pd.DataFrame(approved_data)
                    df_approved.to_excel(writer, sheet_name='Aprovadas', index=False)
                
                # Aba com condicionais
                if conditional_data:
                    df_conditional = pd.DataFrame(conditional_data)
                    df_conditional.to_excel(writer, sheet_name='Condicionais', index=False)
                
                # Aba com rejeitadas
                if rejected_data:
                    df_rejected = pd.DataFrame(rejected_data)
                    df_rejected.to_excel(writer, sheet_name='Rejeitadas', index=False)
                
                # Aba com resumo estatístico
                summary_data = {
                    'Métrica': ['Total de Testes', 'Aprovadas', 'Condicionais', 'Rejeitadas', 
                               'Taxa de Aprovação (%)', 'ROI Médio (%)', 'Win Rate Médio (%)'],
                    'Valor': [
                        len(all_data),
                        len(approved_data),
                        len(conditional_data),
                        len(rejected_data),
                        len(approved_data) / len(all_data) * 100 if all_data else 0,
                        sum(row['ROI (%)'] for row in all_data) / len(all_data) if all_data else 0,
                        sum(row['Win Rate (%)'] for row in all_data) / len(all_data) if all_data else 0
                    ]
                }
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Resumo', index=False)
            
            return str(filepath)
        
        return None
    
    def export_summary_report(self, filename: str = None) -> str:
        """Exporta relatório resumo em texto"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"strategy_summary_{timestamp}.txt"
        
        filepath = self.export_dir / filename
        
        # Carregar dados dos relatórios
        reports = self.report_manager.list_reports()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("RELATÓRIO RESUMO - STRATEGY FACTORY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Total de testes: {len(reports)}\n\n")
            
            # Estatísticas gerais
            approved = 0
            conditional = 0
            rejected = 0
            total_roi = 0
            total_win_rate = 0
            valid_tests = 0
            
            for report in reports:
                try:
                    with open(report['filepath'], 'r') as rf:
                        data = json.load(rf)
                    
                    if 'data' in data and 'metrics' in data['data']:
                        strategy_data = data['data']
                        validation = strategy_data.get('validation', 'unknown')
                        
                        if validation == 'approved':
                            approved += 1
                        elif validation == 'conditional':
                            conditional += 1
                        elif validation == 'rejected':
                            rejected += 1
                        
                        metrics = strategy_data['metrics']
                        total_roi += metrics['roi_percent']
                        total_win_rate += metrics['win_rate']
                        valid_tests += 1
                        
                except Exception:
                    continue
            
            f.write("ESTATÍSTICAS GERAIS:\n")
            f.write(f"  Aprovadas: {approved}\n")
            f.write(f"  Condicionais: {conditional}\n")
            f.write(f"  Rejeitadas: {rejected}\n")
            
            if valid_tests > 0:
                f.write(f"  Taxa de aprovação: {approved/valid_tests*100:.1f}%\n")
                f.write(f"  ROI médio: {total_roi/valid_tests:.2f}%\n")
                f.write(f"  Win rate médio: {total_win_rate/valid_tests:.1%}\n")
            
            f.write("\n" + "=" * 50 + "\n")
        
        return str(filepath)

class AdvancedConfiguration:
    """Sistema de configurações avançadas"""
    
    def __init__(self):
        self.config_file = "advanced_config.json"
        self.default_config = {
            'validation_criteria': {
                'approved': {
                    'min_roi_percent': 5.0,
                    'min_win_rate': 0.55,
                    'max_drawdown_percent': 15.0,
                    'min_profit_factor': 1.2,
                    'min_trades': 10
                },
                'conditional': {
                    'min_roi_percent': 2.0,
                    'min_win_rate': 0.50,
                    'max_drawdown_percent': 20.0,
                    'min_profit_factor': 1.0,
                    'min_trades': 5
                }
            },
            'score_weights': {
                'roi_weight': 0.30,
                'win_rate_weight': 0.25,
                'profit_factor_weight': 0.25,
                'drawdown_weight': 0.20
            },
            'risk_management': {
                'max_position_size_percent': 10.0,
                'max_risk_per_trade_percent': 5.0,
                'stop_loss_percent': 2.0,
                'take_profit_percent': 4.0
            },
            'data_settings': {
                'default_symbol': 'BTCUSDT',
                'default_timeframe': '15m',
                'default_period': 'Q4_2024',
                'max_candles_per_request': 1000
            }
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Carrega configurações do arquivo"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                return self.default_config.copy()
        except Exception:
            return self.default_config.copy()
    
    def save_config(self) -> bool:
        """Salva configurações no arquivo"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception:
            return False
    
    def display_current_config(self):
        """Exibe configuração atual"""
        print("\n⚙️ CONFIGURAÇÕES AVANÇADAS ATUAIS")
        print("=" * 60)
        
        print("\n✅ CRITÉRIOS DE VALIDAÇÃO:")
        approved = self.config['validation_criteria']['approved']
        conditional = self.config['validation_criteria']['conditional']
        
        print(f"  Aprovada:")
        print(f"    ROI mínimo: {approved['min_roi_percent']}%")
        print(f"    Win rate mínimo: {approved['min_win_rate']:.1%}")
        print(f"    Drawdown máximo: {approved['max_drawdown_percent']}%")
        print(f"    Profit factor mínimo: {approved['min_profit_factor']}")
        print(f"    Trades mínimos: {approved['min_trades']}")
        
        print(f"  Condicional:")
        print(f"    ROI mínimo: {conditional['min_roi_percent']}%")
        print(f"    Win rate mínimo: {conditional['min_win_rate']:.1%}")
        print(f"    Drawdown máximo: {conditional['max_drawdown_percent']}%")
        print(f"    Profit factor mínimo: {conditional['min_profit_factor']}")
        print(f"    Trades mínimos: {conditional['min_trades']}")
        
        print("\n🏆 PESOS DO SCORE COMPOSTO:")
        weights = self.config['score_weights']
        print(f"  ROI: {weights['roi_weight']:.1%}")
        print(f"  Win Rate: {weights['win_rate_weight']:.1%}")
        print(f"  Profit Factor: {weights['profit_factor_weight']:.1%}")
        print(f"  Drawdown: {weights['drawdown_weight']:.1%}")
        
        print("\n🛡️ GESTÃO DE RISCO:")
        risk = self.config['risk_management']
        print(f"  Position size máximo: {risk['max_position_size_percent']}%")
        print(f"  Risco máximo por trade: {risk['max_risk_per_trade_percent']}%")
        print(f"  Stop loss padrão: {risk['stop_loss_percent']}%")
        print(f"  Take profit padrão: {risk['take_profit_percent']}%")
        
        print("\n📊 CONFIGURAÇÕES DE DADOS:")
        data = self.config['data_settings']
        print(f"  Símbolo padrão: {data['default_symbol']}")
        print(f"  Timeframe padrão: {data['default_timeframe']}")
        print(f"  Período padrão: {data['default_period']}")
        print(f"  Máx candles por request: {data['max_candles_per_request']}")
    
    def configure_validation_criteria(self):
        """Configura critérios de validação"""
        print("\n✅ CONFIGURAR CRITÉRIOS DE VALIDAÇÃO")
        print("=" * 50)
        
        # Configurar critérios para aprovada
        print("\n🏆 CRITÉRIOS PARA APROVADA:")
        approved = self.config['validation_criteria']['approved']
        
        try:
            roi = float(input(f"ROI mínimo (%) [{approved['min_roi_percent']}]: ") or approved['min_roi_percent'])
            win_rate = float(input(f"Win rate mínimo (0-1) [{approved['min_win_rate']}]: ") or approved['min_win_rate'])
            drawdown = float(input(f"Drawdown máximo (%) [{approved['max_drawdown_percent']}]: ") or approved['max_drawdown_percent'])
            profit_factor = float(input(f"Profit factor mínimo [{approved['min_profit_factor']}]: ") or approved['min_profit_factor'])
            trades = int(input(f"Trades mínimos [{approved['min_trades']}]: ") or approved['min_trades'])
            
            self.config['validation_criteria']['approved'] = {
                'min_roi_percent': roi,
                'min_win_rate': win_rate,
                'max_drawdown_percent': drawdown,
                'min_profit_factor': profit_factor,
                'min_trades': trades
            }
        except ValueError:
            print("❌ Valores inválidos, mantendo configuração atual")
            return
        
        # Configurar critérios para condicional
        print("\n⚠️ CRITÉRIOS PARA CONDICIONAL:")
        conditional = self.config['validation_criteria']['conditional']
        
        try:
            roi = float(input(f"ROI mínimo (%) [{conditional['min_roi_percent']}]: ") or conditional['min_roi_percent'])
            win_rate = float(input(f"Win rate mínimo (0-1) [{conditional['min_win_rate']}]: ") or conditional['min_win_rate'])
            drawdown = float(input(f"Drawdown máximo (%) [{conditional['max_drawdown_percent']}]: ") or conditional['max_drawdown_percent'])
            profit_factor = float(input(f"Profit factor mínimo [{conditional['min_profit_factor']}]: ") or conditional['min_profit_factor'])
            trades = int(input(f"Trades mínimos [{conditional['min_trades']}]: ") or conditional['min_trades'])
            
            self.config['validation_criteria']['conditional'] = {
                'min_roi_percent': roi,
                'min_win_rate': win_rate,
                'max_drawdown_percent': drawdown,
                'min_profit_factor': profit_factor,
                'min_trades': trades
            }
        except ValueError:
            print("❌ Valores inválidos, mantendo configuração atual")
            return
        
        if self.save_config():
            print("✅ Critérios de validação atualizados!")
        else:
            print("❌ Erro ao salvar configurações")
    
    def configure_score_weights(self):
        """Configura pesos do score composto"""
        print("\n🏆 CONFIGURAR PESOS DO SCORE COMPOSTO")
        print("=" * 50)
        print("💡 Os pesos devem somar 1.0 (100%)")
        
        weights = self.config['score_weights']
        
        try:
            roi_weight = float(input(f"Peso do ROI (0-1) [{weights['roi_weight']}]: ") or weights['roi_weight'])
            win_rate_weight = float(input(f"Peso do Win Rate (0-1) [{weights['win_rate_weight']}]: ") or weights['win_rate_weight'])
            pf_weight = float(input(f"Peso do Profit Factor (0-1) [{weights['profit_factor_weight']}]: ") or weights['profit_factor_weight'])
            dd_weight = float(input(f"Peso do Drawdown (0-1) [{weights['drawdown_weight']}]: ") or weights['drawdown_weight'])
            
            # Verificar se soma 1.0
            total = roi_weight + win_rate_weight + pf_weight + dd_weight
            if abs(total - 1.0) > 0.01:
                print(f"❌ Pesos devem somar 1.0, atual: {total:.3f}")
                return
            
            self.config['score_weights'] = {
                'roi_weight': roi_weight,
                'win_rate_weight': win_rate_weight,
                'profit_factor_weight': pf_weight,
                'drawdown_weight': dd_weight
            }
            
            if self.save_config():
                print("✅ Pesos do score atualizados!")
            else:
                print("❌ Erro ao salvar configurações")
                
        except ValueError:
            print("❌ Valores inválidos, mantendo configuração atual")
    
    def reset_to_defaults(self):
        """Reseta configurações para padrão"""
        confirm = input("⚠️ Resetar todas as configurações para padrão? (s/N): ").strip().lower()
        
        if confirm == 's':
            self.config = self.default_config.copy()
            if self.save_config():
                print("✅ Configurações resetadas para padrão!")
            else:
                print("❌ Erro ao salvar configurações")
        else:
            print("❌ Reset cancelado")

if __name__ == "__main__":
    # Teste das funcionalidades avançadas
    print("🧪 TESTANDO FUNCIONALIDADES AVANÇADAS")
    print("=" * 50)
    
    # Teste de configurações avançadas
    print("\n1️⃣ Teste de configurações avançadas:")
    config = AdvancedConfiguration()
    print("   ✅ Configurações carregadas")
    
    print(f"\n✅ Teste concluído!")

