#!/usr/bin/env python3
"""
TEST CONFIGURATION MANAGER - Gerenciador de configurações de teste
Controle completo sobre período, timeframe, símbolo e outras configurações
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json

class TestConfiguration:
    """Configuração de um teste de estratégia"""
    
    def __init__(self):
        self.symbol = 'BTCUSDT'
        self.timeframe = '15m'
        self.start_date = '2024-10-01'
        self.end_date = '2024-12-31'
        self.period_name = 'Q4 2024 - Rally Final'
        self.period_context = 'Rally de fim de ano, máximas históricas'
    
    def to_dict(self) -> Dict:
        """Converte configuração para dicionário"""
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'period_name': self.period_name,
            'period_context': self.period_context
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TestConfiguration':
        """Cria configuração a partir de dicionário"""
        config = cls()
        config.symbol = data.get('symbol', 'BTCUSDT')
        config.timeframe = data.get('timeframe', '15m')
        config.start_date = data.get('start_date', '2024-10-01')
        config.end_date = data.get('end_date', '2024-12-31')
        config.period_name = data.get('period_name', 'Período Personalizado')
        config.period_context = data.get('period_context', 'Período definido pelo usuário')
        return config

class TestConfigurationManager:
    """Gerenciador de configurações de teste com controle completo"""
    
    def __init__(self):
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT', 'SOLUSDT', 'DOGEUSDT', 'AVAXUSDT']
        self.timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d']
        
        # Períodos pré-definidos
        self.predefined_periods = {
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
            },
            'H1_2024': {
                'start': '2024-01-01', 'end': '2024-06-30',
                'name': 'H1 2024 - Primeiro Semestre',
                'context': 'Bull market seguido de correção'
            },
            'H2_2024': {
                'start': '2024-07-01', 'end': '2024-12-31',
                'name': 'H2 2024 - Segundo Semestre',
                'context': 'Recuperação e rally final'
            },
            'FULL_2024': {
                'start': '2024-01-01', 'end': '2024-12-31',
                'name': '2024 Completo',
                'context': 'Ano completo com todos os regimes'
            },
            'LAST_30D': {
                'start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'end': datetime.now().strftime('%Y-%m-%d'),
                'name': 'Últimos 30 Dias',
                'context': 'Período recente para análise atual'
            },
            'LAST_90D': {
                'start': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
                'end': datetime.now().strftime('%Y-%m-%d'),
                'name': 'Últimos 90 Dias',
                'context': 'Trimestre recente para análise atual'
            }
        }
    
    def select_symbol(self) -> str:
        """Interface para seleção de símbolo"""
        print(f"\n📊 SELEÇÃO DE SÍMBOLO:")
        
        for i, symbol in enumerate(self.symbols, 1):
            print(f"   {i}. {symbol}")
        
        while True:
            try:
                choice = input(f"\n📊 Escolha um símbolo (1-{len(self.symbols)}) [padrão: 1-BTCUSDT]: ").strip()
                
                if not choice:  # Padrão
                    return self.symbols[0]
                
                idx = int(choice) - 1
                if 0 <= idx < len(self.symbols):
                    return self.symbols[idx]
                else:
                    print(f"❌ Escolha entre 1 e {len(self.symbols)}")
            except ValueError:
                print("❌ Digite um número válido")
    
    def select_timeframe(self) -> str:
        """Interface para seleção de timeframe"""
        print(f"\n⏰ SELEÇÃO DE TIMEFRAME:")
        
        # Agrupar timeframes por categoria
        categories = {
            'Scalping': ['1m', '3m', '5m'],
            'Intraday': ['15m', '30m', '1h', '2h'],
            'Swing': ['4h', '6h', '12h'],
            'Position': ['1d']
        }
        
        for category, frames in categories.items():
            print(f"\n   📈 {category}:")
            for frame in frames:
                idx = self.timeframes.index(frame) + 1
                print(f"      {idx}. {frame}")
        
        while True:
            try:
                choice = input(f"\n⏰ Escolha um timeframe (1-{len(self.timeframes)}) [padrão: 4-15m]: ").strip()
                
                if not choice:  # Padrão
                    return '15m'
                
                idx = int(choice) - 1
                if 0 <= idx < len(self.timeframes):
                    return self.timeframes[idx]
                else:
                    print(f"❌ Escolha entre 1 e {len(self.timeframes)}")
            except ValueError:
                print("❌ Digite um número válido")
    
    def select_period(self) -> Tuple[str, str, str, str]:
        """Interface para seleção de período"""
        print(f"\n📅 SELEÇÃO DE PERÍODO:")
        print(f"   1️⃣ Períodos Pré-definidos")
        print(f"   2️⃣ Período Personalizado")
        
        while True:
            choice = input(f"\n📅 Escolha o tipo de período (1-2): ").strip()
            
            if choice == '1':
                return self._select_predefined_period()
            elif choice == '2':
                return self._select_custom_period()
            else:
                print("❌ Escolha 1 ou 2")
    
    def _select_predefined_period(self) -> Tuple[str, str, str, str]:
        """Seleção de período pré-definido"""
        print(f"\n📅 PERÍODOS PRÉ-DEFINIDOS:")
        
        periods_list = list(self.predefined_periods.items())
        
        for i, (key, period) in enumerate(periods_list, 1):
            print(f"   {i}. {period['name']}")
            print(f"      📅 {period['start']} a {period['end']}")
            print(f"      📝 {period['context']}")
            print()
        
        while True:
            try:
                choice = input(f"\n📅 Escolha um período (1-{len(periods_list)}) [padrão: 4-Q4 2024]: ").strip()
                
                if not choice:  # Padrão
                    period = self.predefined_periods['Q4_2024']
                    return period['start'], period['end'], period['name'], period['context']
                
                idx = int(choice) - 1
                if 0 <= idx < len(periods_list):
                    key, period = periods_list[idx]
                    return period['start'], period['end'], period['name'], period['context']
                else:
                    print(f"❌ Escolha entre 1 e {len(periods_list)}")
            except ValueError:
                print("❌ Digite um número válido")
    
    def _select_custom_period(self) -> Tuple[str, str, str, str]:
        """Seleção de período personalizado"""
        print(f"\n📅 PERÍODO PERSONALIZADO:")
        print(f"💡 Formato de data: YYYY-MM-DD (ex: 2024-01-01)")
        
        # Data de início
        while True:
            start_date = input(f"\n📅 Data de início: ").strip()
            if self._validate_date(start_date):
                break
            else:
                print("❌ Formato inválido. Use YYYY-MM-DD")
        
        # Data de fim
        while True:
            end_date = input(f"📅 Data de fim: ").strip()
            if self._validate_date(end_date):
                if end_date >= start_date:
                    break
                else:
                    print("❌ Data de fim deve ser posterior à data de início")
            else:
                print("❌ Formato inválido. Use YYYY-MM-DD")
        
        # Nome do período
        period_name = input(f"\n📝 Nome do período [opcional]: ").strip()
        if not period_name:
            period_name = f"Período {start_date} a {end_date}"
        
        # Contexto do período
        period_context = input(f"📝 Contexto/descrição [opcional]: ").strip()
        if not period_context:
            period_context = "Período personalizado definido pelo usuário"
        
        return start_date, end_date, period_name, period_context
    
    def _validate_date(self, date_str: str) -> bool:
        """Valida formato de data"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def configure_test(self) -> TestConfiguration:
        """Interface completa para configuração de teste"""
        print(f"\n⚙️ CONFIGURAÇÃO DE TESTE")
        print("="*50)
        
        config = TestConfiguration()
        
        # Seleção de símbolo
        config.symbol = self.select_symbol()
        
        # Seleção de timeframe
        config.timeframe = self.select_timeframe()
        
        # Seleção de período
        config.start_date, config.end_date, config.period_name, config.period_context = self.select_period()
        
        # Resumo da configuração
        print(f"\n📋 RESUMO DA CONFIGURAÇÃO:")
        print(f"   📊 Símbolo: {config.symbol}")
        print(f"   ⏰ Timeframe: {config.timeframe}")
        print(f"   📅 Período: {config.period_name}")
        print(f"   📅 Datas: {config.start_date} a {config.end_date}")
        print(f"   📝 Contexto: {config.period_context}")
        
        # Confirmação
        confirm = input(f"\n✅ Confirmar configuração? (s/N): ").strip().lower()
        if confirm != 's':
            print(f"❌ Configuração cancelada")
            return None
        
        return config
    
    def quick_configure(self, symbol: str = None, timeframe: str = None, period_key: str = None) -> TestConfiguration:
        """Configuração rápida com valores padrão"""
        config = TestConfiguration()
        
        if symbol:
            config.symbol = symbol
        
        if timeframe:
            config.timeframe = timeframe
        
        if period_key and period_key in self.predefined_periods:
            period = self.predefined_periods[period_key]
            config.start_date = period['start']
            config.end_date = period['end']
            config.period_name = period['name']
            config.period_context = period['context']
        
        return config
    
    def save_configuration(self, config: TestConfiguration, filename: str = 'test_config.json'):
        """Salva configuração em arquivo"""
        try:
            with open(filename, 'w') as f:
                json.dump(config.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar configuração: {e}")
            return False
    
    def load_configuration(self, filename: str = 'test_config.json') -> Optional[TestConfiguration]:
        """Carrega configuração de arquivo"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            return TestConfiguration.from_dict(data)
        except Exception as e:
            print(f"❌ Erro ao carregar configuração: {e}")
            return None

if __name__ == "__main__":
    # Teste do gerenciador de configurações
    manager = TestConfigurationManager()
    
    print("🧪 TESTANDO TEST CONFIGURATION MANAGER")
    print("="*50)
    
    # Teste de configuração rápida
    print("\n1️⃣ Teste de configuração rápida:")
    quick_config = manager.quick_configure('ETHUSDT', '1h', 'Q3_2024')
    print(f"   📊 Símbolo: {quick_config.symbol}")
    print(f"   ⏰ Timeframe: {quick_config.timeframe}")
    print(f"   📅 Período: {quick_config.period_name}")
    
    # Teste de salvamento/carregamento
    print("\n2️⃣ Teste de salvamento/carregamento:")
    if manager.save_configuration(quick_config, 'test_config_example.json'):
        print("   ✅ Configuração salva")
        
        loaded_config = manager.load_configuration('test_config_example.json')
        if loaded_config:
            print("   ✅ Configuração carregada")
            print(f"   📊 Símbolo carregado: {loaded_config.symbol}")
        
        # Limpeza
        import os
        os.remove('test_config_example.json')
    
    print(f"\n✅ Teste concluído!")

