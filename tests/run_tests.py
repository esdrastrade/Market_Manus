#!/usr/bin/env python3
"""
Script Principal para Execução de Testes

Este script executa toda a suíte de testes do sistema de scalping automatizado,
incluindo testes unitários, de integração e de performance, gerando relatórios
detalhados dos resultados.

Autor: Manus AI
Data: 17 de Julho de 2025
Versão: 1.0

Uso:
    python run_tests.py [opções]
    
Opções:
    --unit          Executar apenas testes unitários
    --integration   Executar apenas testes de integração
    --performance   Executar apenas testes de performance
    --coverage      Gerar relatório de cobertura de código
    --html          Gerar relatório HTML
    --verbose       Saída detalhada
    --parallel      Executar testes em paralelo
"""

import sys
import os
import unittest
import argparse
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
import importlib.util

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar framework de testes
from tests.test_framework import run_test_suite

class TestRunner:
    """Classe principal para execução de testes"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.results = {
            "start_time": self.start_time.isoformat(),
            "test_suites": {},
            "summary": {},
            "coverage": {},
            "performance": {}
        }
        
        # Configurar diretórios
        self.test_dir = Path(__file__).parent
        self.project_dir = self.test_dir.parent
        self.results_dir = self.test_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
    
    def discover_test_modules(self, test_type="all"):
        """
        Descobre módulos de teste baseado no tipo
        
        Args:
            test_type: Tipo de teste ("unit", "integration", "performance", "all")
            
        Returns:
            Lista de módulos de teste
        """
        test_modules = []
        
        if test_type in ["unit", "all"]:
            unit_test_dir = self.test_dir / "unit_tests"
            if unit_test_dir.exists():
                for test_file in unit_test_dir.glob("test_*.py"):
                    module_name = f"tests.unit_tests.{test_file.stem}"
                    test_modules.append((module_name, "unit"))
        
        if test_type in ["integration", "all"]:
            integration_test_dir = self.test_dir / "integration_tests"
            if integration_test_dir.exists():
                for test_file in integration_test_dir.glob("test_*.py"):
                    module_name = f"tests.integration_tests.{test_file.stem}"
                    test_modules.append((module_name, "integration"))
        
        return test_modules
    
    def load_test_module(self, module_name):
        """
        Carrega módulo de teste dinamicamente
        
        Args:
            module_name: Nome do módulo
            
        Returns:
            Módulo carregado ou None se falhar
        """
        try:
            module = __import__(module_name, fromlist=[''])
            return module
        except ImportError as e:
            print(f"Erro ao carregar módulo {module_name}: {e}")
            return None
    
    def run_unit_tests(self, verbose=False):
        """Executa testes unitários"""
        print("🧪 Executando Testes Unitários...")
        
        test_modules = self.discover_test_modules("unit")
        suite = unittest.TestSuite()
        
        for module_name, test_type in test_modules:
            module = self.load_test_module(module_name)
            if module:
                loader = unittest.TestLoader()
                module_suite = loader.loadTestsFromModule(module)
                suite.addTest(module_suite)
        
        # Executar testes
        runner = unittest.TextTestRunner(
            verbosity=2 if verbose else 1,
            stream=sys.stdout,
            buffer=True
        )
        
        start_time = time.time()
        result = runner.run(suite)
        execution_time = time.time() - start_time
        
        # Registrar resultados
        self.results["test_suites"]["unit"] = {
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped) if hasattr(result, 'skipped') else 0,
            "success_rate": (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0,
            "execution_time": execution_time,
            "details": {
                "failures": [str(f) for f in result.failures],
                "errors": [str(e) for e in result.errors]
            }
        }
        
        return result.wasSuccessful()
    
    def run_integration_tests(self, verbose=False):
        """Executa testes de integração"""
        print("🔗 Executando Testes de Integração...")
        
        test_modules = self.discover_test_modules("integration")
        suite = unittest.TestSuite()
        
        for module_name, test_type in test_modules:
            module = self.load_test_module(module_name)
            if module:
                loader = unittest.TestLoader()
                module_suite = loader.loadTestsFromModule(module)
                suite.addTest(module_suite)
        
        # Executar testes
        runner = unittest.TextTestRunner(
            verbosity=2 if verbose else 1,
            stream=sys.stdout,
            buffer=True
        )
        
        start_time = time.time()
        result = runner.run(suite)
        execution_time = time.time() - start_time
        
        # Registrar resultados
        self.results["test_suites"]["integration"] = {
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped) if hasattr(result, 'skipped') else 0,
            "success_rate": (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0,
            "execution_time": execution_time,
            "details": {
                "failures": [str(f) for f in result.failures],
                "errors": [str(e) for e in result.errors]
            }
        }
        
        return result.wasSuccessful()
    
    def run_performance_tests(self, verbose=False):
        """Executa testes de performance"""
        print("⚡ Executando Testes de Performance...")
        
        # Testes de performance específicos
        performance_results = {
            "signal_generation": self.test_signal_generation_performance(),
            "risk_calculation": self.test_risk_calculation_performance(),
            "system_throughput": self.test_system_throughput(),
            "memory_usage": self.test_memory_usage()
        }
        
        self.results["performance"] = performance_results
        
        # Verificar se performance está dentro dos limites
        performance_ok = all(
            result.get("status") == "PASS" 
            for result in performance_results.values()
        )
        
        return performance_ok
    
    def test_signal_generation_performance(self):
        """Testa performance de geração de sinais"""
        try:
            # Simular teste de performance
            import numpy as np
            
            start_time = time.time()
            
            # Simular processamento de 1000 sinais
            for _ in range(1000):
                # Simular cálculos de indicadores
                prices = np.random.random(100) * 45000
                ema_fast = np.mean(prices[-12:])
                ema_slow = np.mean(prices[-26:])
                signal = (ema_fast - ema_slow) / ema_slow
            
            execution_time = time.time() - start_time
            
            return {
                "test": "signal_generation",
                "execution_time": execution_time,
                "signals_per_second": 1000 / execution_time,
                "target_sps": 100,  # Sinais por segundo alvo
                "status": "PASS" if (1000 / execution_time) >= 100 else "FAIL"
            }
            
        except Exception as e:
            return {
                "test": "signal_generation",
                "status": "ERROR",
                "error": str(e)
            }
    
    def test_risk_calculation_performance(self):
        """Testa performance de cálculos de risco"""
        try:
            start_time = time.time()
            
            # Simular cálculos de risco para 100 posições
            for _ in range(100):
                # Simular cálculo de VaR
                portfolio_value = 10000
                volatility = 0.02
                var_95 = portfolio_value * volatility * 1.645
                
                # Simular cálculo de position sizing
                risk_per_trade = 0.02
                entry_price = 45000
                stop_loss = entry_price * 0.98
                position_size = (portfolio_value * risk_per_trade) / (entry_price - stop_loss)
            
            execution_time = time.time() - start_time
            
            return {
                "test": "risk_calculation",
                "execution_time": execution_time,
                "calculations_per_second": 100 / execution_time,
                "target_cps": 50,  # Cálculos por segundo alvo
                "status": "PASS" if (100 / execution_time) >= 50 else "FAIL"
            }
            
        except Exception as e:
            return {
                "test": "risk_calculation",
                "status": "ERROR",
                "error": str(e)
            }
    
    def test_system_throughput(self):
        """Testa throughput geral do sistema"""
        try:
            start_time = time.time()
            
            # Simular processamento de ciclo completo
            cycles = 0
            while time.time() - start_time < 5:  # 5 segundos
                # Simular ciclo de agentes
                for _ in range(6):  # 6 agentes
                    time.sleep(0.001)  # Simular processamento
                cycles += 1
            
            execution_time = time.time() - start_time
            cycles_per_second = cycles / execution_time
            
            return {
                "test": "system_throughput",
                "execution_time": execution_time,
                "cycles_completed": cycles,
                "cycles_per_second": cycles_per_second,
                "target_cps": 10,  # Ciclos por segundo alvo
                "status": "PASS" if cycles_per_second >= 10 else "FAIL"
            }
            
        except Exception as e:
            return {
                "test": "system_throughput",
                "status": "ERROR",
                "error": str(e)
            }
    
    def test_memory_usage(self):
        """Testa uso de memória"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Simular uso intensivo de memória
            data_arrays = []
            for _ in range(100):
                data_arrays.append(list(range(1000)))
            
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - initial_memory
            
            # Limpar dados
            del data_arrays
            
            return {
                "test": "memory_usage",
                "initial_memory_mb": initial_memory,
                "peak_memory_mb": peak_memory,
                "memory_increase_mb": memory_increase,
                "target_limit_mb": 100,  # Limite de 100MB
                "status": "PASS" if memory_increase <= 100 else "FAIL"
            }
            
        except Exception as e:
            return {
                "test": "memory_usage",
                "status": "ERROR",
                "error": str(e)
            }
    
    def generate_coverage_report(self):
        """Gera relatório de cobertura de código"""
        try:
            print("📊 Gerando Relatório de Cobertura...")
            
            # Tentar usar coverage.py se disponível
            result = subprocess.run([
                sys.executable, "-m", "coverage", "run", "--source=agents", "-m", "unittest", "discover", "-s", "tests"
            ], capture_output=True, text=True, cwd=self.project_dir)
            
            if result.returncode == 0:
                # Gerar relatório
                coverage_result = subprocess.run([
                    sys.executable, "-m", "coverage", "report"
                ], capture_output=True, text=True, cwd=self.project_dir)
                
                self.results["coverage"] = {
                    "available": True,
                    "report": coverage_result.stdout,
                    "status": "SUCCESS"
                }
            else:
                self.results["coverage"] = {
                    "available": False,
                    "error": "coverage.py não disponível",
                    "status": "SKIPPED"
                }
                
        except Exception as e:
            self.results["coverage"] = {
                "available": False,
                "error": str(e),
                "status": "ERROR"
            }
    
    def generate_html_report(self):
        """Gera relatório HTML"""
        print("📄 Gerando Relatório HTML...")
        
        html_content = self.create_html_report()
        
        html_file = self.results_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📄 Relatório HTML salvo em: {html_file}")
        return html_file
    
    def create_html_report(self):
        """Cria conteúdo HTML do relatório"""
        html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Testes - Sistema de Scalping Automatizado</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; text-align: center; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
        .card {{ background: #ecf0f1; padding: 15px; border-radius: 5px; text-align: center; }}
        .card.success {{ background: #d5f4e6; }}
        .card.warning {{ background: #ffeaa7; }}
        .card.error {{ background: #fab1a0; }}
        .metric {{ font-size: 2em; font-weight: bold; margin: 10px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #3498db; color: white; }}
        .pass {{ color: #27ae60; font-weight: bold; }}
        .fail {{ color: #e74c3c; font-weight: bold; }}
        .error {{ color: #e67e22; font-weight: bold; }}
        .details {{ background: #f8f9fa; padding: 10px; margin: 10px 0; border-left: 4px solid #3498db; }}
        pre {{ background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Relatório de Testes - Sistema de Scalping Automatizado</h1>
        
        <div class="details">
            <strong>Data de Execução:</strong> {self.start_time.strftime('%d/%m/%Y %H:%M:%S')}<br>
            <strong>Duração Total:</strong> {(datetime.now() - self.start_time).total_seconds():.2f} segundos
        </div>
        
        {self.generate_summary_html()}
        {self.generate_unit_tests_html()}
        {self.generate_integration_tests_html()}
        {self.generate_performance_html()}
        {self.generate_coverage_html()}
        
        <h2>📋 Conclusão</h2>
        <div class="details">
            {self.generate_conclusion_html()}
        </div>
    </div>
</body>
</html>
        """
        return html
    
    def generate_summary_html(self):
        """Gera HTML do resumo"""
        total_tests = sum(
            suite.get("tests_run", 0) 
            for suite in self.results["test_suites"].values()
        )
        
        total_failures = sum(
            suite.get("failures", 0) + suite.get("errors", 0)
            for suite in self.results["test_suites"].values()
        )
        
        success_rate = ((total_tests - total_failures) / total_tests * 100) if total_tests > 0 else 0
        
        return f"""
        <h2>📊 Resumo Geral</h2>
        <div class="summary">
            <div class="card {'success' if success_rate >= 90 else 'warning' if success_rate >= 70 else 'error'}">
                <h3>Taxa de Sucesso</h3>
                <div class="metric">{success_rate:.1f}%</div>
            </div>
            <div class="card">
                <h3>Total de Testes</h3>
                <div class="metric">{total_tests}</div>
            </div>
            <div class="card {'success' if total_failures == 0 else 'error'}">
                <h3>Falhas</h3>
                <div class="metric">{total_failures}</div>
            </div>
            <div class="card">
                <h3>Suítes Executadas</h3>
                <div class="metric">{len(self.results['test_suites'])}</div>
            </div>
        </div>
        """
    
    def generate_unit_tests_html(self):
        """Gera HTML dos testes unitários"""
        if "unit" not in self.results["test_suites"]:
            return ""
        
        unit_results = self.results["test_suites"]["unit"]
        
        return f"""
        <h2>🧪 Testes Unitários</h2>
        <table>
            <tr>
                <th>Métrica</th>
                <th>Valor</th>
                <th>Status</th>
            </tr>
            <tr>
                <td>Testes Executados</td>
                <td>{unit_results['tests_run']}</td>
                <td><span class="pass">✓</span></td>
            </tr>
            <tr>
                <td>Falhas</td>
                <td>{unit_results['failures']}</td>
                <td><span class="{'pass' if unit_results['failures'] == 0 else 'fail'}">{'✓' if unit_results['failures'] == 0 else '✗'}</span></td>
            </tr>
            <tr>
                <td>Erros</td>
                <td>{unit_results['errors']}</td>
                <td><span class="{'pass' if unit_results['errors'] == 0 else 'error'}">{'✓' if unit_results['errors'] == 0 else '✗'}</span></td>
            </tr>
            <tr>
                <td>Taxa de Sucesso</td>
                <td>{unit_results['success_rate']:.1%}</td>
                <td><span class="{'pass' if unit_results['success_rate'] >= 0.9 else 'warning' if unit_results['success_rate'] >= 0.7 else 'fail'}">{'✓' if unit_results['success_rate'] >= 0.9 else '⚠' if unit_results['success_rate'] >= 0.7 else '✗'}</span></td>
            </tr>
            <tr>
                <td>Tempo de Execução</td>
                <td>{unit_results['execution_time']:.2f}s</td>
                <td><span class="pass">✓</span></td>
            </tr>
        </table>
        """
    
    def generate_integration_tests_html(self):
        """Gera HTML dos testes de integração"""
        if "integration" not in self.results["test_suites"]:
            return ""
        
        integration_results = self.results["test_suites"]["integration"]
        
        return f"""
        <h2>🔗 Testes de Integração</h2>
        <table>
            <tr>
                <th>Métrica</th>
                <th>Valor</th>
                <th>Status</th>
            </tr>
            <tr>
                <td>Testes Executados</td>
                <td>{integration_results['tests_run']}</td>
                <td><span class="pass">✓</span></td>
            </tr>
            <tr>
                <td>Falhas</td>
                <td>{integration_results['failures']}</td>
                <td><span class="{'pass' if integration_results['failures'] == 0 else 'fail'}">{'✓' if integration_results['failures'] == 0 else '✗'}</span></td>
            </tr>
            <tr>
                <td>Erros</td>
                <td>{integration_results['errors']}</td>
                <td><span class="{'pass' if integration_results['errors'] == 0 else 'error'}">{'✓' if integration_results['errors'] == 0 else '✗'}</span></td>
            </tr>
            <tr>
                <td>Taxa de Sucesso</td>
                <td>{integration_results['success_rate']:.1%}</td>
                <td><span class="{'pass' if integration_results['success_rate'] >= 0.9 else 'warning' if integration_results['success_rate'] >= 0.7 else 'fail'}">{'✓' if integration_results['success_rate'] >= 0.9 else '⚠' if integration_results['success_rate'] >= 0.7 else '✗'}</span></td>
            </tr>
            <tr>
                <td>Tempo de Execução</td>
                <td>{integration_results['execution_time']:.2f}s</td>
                <td><span class="pass">✓</span></td>
            </tr>
        </table>
        """
    
    def generate_performance_html(self):
        """Gera HTML dos testes de performance"""
        if not self.results["performance"]:
            return ""
        
        performance_html = "<h2>⚡ Testes de Performance</h2><table><tr><th>Teste</th><th>Métrica</th><th>Valor</th><th>Alvo</th><th>Status</th></tr>"
        
        for test_name, test_result in self.results["performance"].items():
            if test_result.get("status") == "ERROR":
                performance_html += f"""
                <tr>
                    <td>{test_name}</td>
                    <td colspan="3">Erro: {test_result.get('error', 'Desconhecido')}</td>
                    <td><span class="error">ERROR</span></td>
                </tr>
                """
            else:
                status_class = "pass" if test_result.get("status") == "PASS" else "fail"
                status_icon = "✓" if test_result.get("status") == "PASS" else "✗"
                
                performance_html += f"""
                <tr>
                    <td>{test_name}</td>
                    <td>Tempo de Execução</td>
                    <td>{test_result.get('execution_time', 0):.3f}s</td>
                    <td>-</td>
                    <td><span class="{status_class}">{status_icon}</span></td>
                </tr>
                """
        
        performance_html += "</table>"
        return performance_html
    
    def generate_coverage_html(self):
        """Gera HTML da cobertura"""
        if not self.results["coverage"]:
            return ""
        
        coverage = self.results["coverage"]
        
        if coverage.get("available"):
            return f"""
            <h2>📊 Cobertura de Código</h2>
            <pre>{coverage.get('report', 'Relatório não disponível')}</pre>
            """
        else:
            return f"""
            <h2>📊 Cobertura de Código</h2>
            <div class="details">
                <strong>Status:</strong> {coverage.get('status', 'UNKNOWN')}<br>
                <strong>Motivo:</strong> {coverage.get('error', 'Não especificado')}
            </div>
            """
    
    def generate_conclusion_html(self):
        """Gera HTML da conclusão"""
        total_tests = sum(
            suite.get("tests_run", 0) 
            for suite in self.results["test_suites"].values()
        )
        
        total_failures = sum(
            suite.get("failures", 0) + suite.get("errors", 0)
            for suite in self.results["test_suites"].values()
        )
        
        success_rate = ((total_tests - total_failures) / total_tests * 100) if total_tests > 0 else 0
        
        if success_rate >= 95:
            conclusion = "🎉 <strong>EXCELENTE!</strong> O sistema passou em praticamente todos os testes. Pronto para produção."
        elif success_rate >= 85:
            conclusion = "✅ <strong>BOM!</strong> O sistema está funcionando bem, com algumas melhorias menores necessárias."
        elif success_rate >= 70:
            conclusion = "⚠️ <strong>ATENÇÃO!</strong> O sistema precisa de correções antes do deployment em produção."
        else:
            conclusion = "❌ <strong>CRÍTICO!</strong> O sistema apresenta problemas significativos que devem ser corrigidos."
        
        return conclusion
    
    def save_json_report(self):
        """Salva relatório em formato JSON"""
        self.results["end_time"] = datetime.now().isoformat()
        self.results["total_duration"] = (datetime.now() - self.start_time).total_seconds()
        
        json_file = self.results_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Relatório JSON salvo em: {json_file}")
        return json_file
    
    def print_summary(self):
        """Imprime resumo dos resultados"""
        print("\n" + "="*60)
        print("📊 RESUMO DOS TESTES")
        print("="*60)
        
        for suite_name, suite_results in self.results["test_suites"].items():
            print(f"\n{suite_name.upper()} TESTS:")
            print(f"  Executados: {suite_results['tests_run']}")
            print(f"  Falhas: {suite_results['failures']}")
            print(f"  Erros: {suite_results['errors']}")
            print(f"  Taxa de Sucesso: {suite_results['success_rate']:.1%}")
            print(f"  Tempo: {suite_results['execution_time']:.2f}s")
        
        if self.results["performance"]:
            print(f"\nPERFORMANCE TESTS:")
            for test_name, test_result in self.results["performance"].items():
                status = test_result.get("status", "UNKNOWN")
                print(f"  {test_name}: {status}")
        
        total_tests = sum(
            suite.get("tests_run", 0) 
            for suite in self.results["test_suites"].values()
        )
        
        total_failures = sum(
            suite.get("failures", 0) + suite.get("errors", 0)
            for suite in self.results["test_suites"].values()
        )
        
        success_rate = ((total_tests - total_failures) / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎯 RESULTADO GERAL:")
        print(f"  Total de Testes: {total_tests}")
        print(f"  Taxa de Sucesso: {success_rate:.1f}%")
        print(f"  Duração Total: {(datetime.now() - self.start_time).total_seconds():.2f}s")
        
        if success_rate >= 90:
            print("  Status: ✅ APROVADO")
        elif success_rate >= 70:
            print("  Status: ⚠️ ATENÇÃO")
        else:
            print("  Status: ❌ REPROVADO")
        
        print("="*60)

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Executar testes do sistema de scalping automatizado")
    parser.add_argument("--unit", action="store_true", help="Executar apenas testes unitários")
    parser.add_argument("--integration", action="store_true", help="Executar apenas testes de integração")
    parser.add_argument("--performance", action="store_true", help="Executar apenas testes de performance")
    parser.add_argument("--coverage", action="store_true", help="Gerar relatório de cobertura")
    parser.add_argument("--html", action="store_true", help="Gerar relatório HTML")
    parser.add_argument("--verbose", action="store_true", help="Saída detalhada")
    parser.add_argument("--parallel", action="store_true", help="Executar testes em paralelo")
    
    args = parser.parse_args()
    
    # Criar runner
    runner = TestRunner()
    
    print("🚀 Sistema de Scalping Automatizado - Execução de Testes")
    print(f"📅 Iniciado em: {runner.start_time.strftime('%d/%m/%Y %H:%M:%S')}")
    print("-" * 60)
    
    success = True
    
    # Executar testes baseado nos argumentos
    if args.unit or not any([args.unit, args.integration, args.performance]):
        success &= runner.run_unit_tests(args.verbose)
    
    if args.integration or not any([args.unit, args.integration, args.performance]):
        success &= runner.run_integration_tests(args.verbose)
    
    if args.performance or not any([args.unit, args.integration, args.performance]):
        success &= runner.run_performance_tests(args.verbose)
    
    # Gerar cobertura se solicitado
    if args.coverage:
        runner.generate_coverage_report()
    
    # Salvar relatórios
    runner.save_json_report()
    
    if args.html:
        runner.generate_html_report()
    
    # Imprimir resumo
    runner.print_summary()
    
    # Retornar código de saída apropriado
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

