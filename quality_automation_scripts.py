#!/usr/bin/env python3
"""
Market Manus - Scripts de Automação para Qualidade de Código
Automatiza verificações de qualidade, formatação e testes
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json
from datetime import datetime

class CodeQualityManager:
    """Gerenciador de qualidade de código"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.src_dir = self.project_root / "src"
        self.tests_dir = self.project_root / "tests"
        self.quality_report = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log de operações"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.quality_report.append(log_entry)
        print(log_entry)
    
    def run_command(self, command: List[str], description: str) -> Tuple[bool, str]:
        """Executa comando e retorna resultado"""
        try:
            self.log(f"🔄 {description}")
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                self.log(f"✅ {description} - OK")
                return True, result.stdout
            else:
                self.log(f"❌ {description} - FALHOU", "ERROR")
                self.log(f"Erro: {result.stderr}", "ERROR")
                return False, result.stderr
                
        except Exception as e:
            self.log(f"❌ Erro ao executar {description}: {e}", "ERROR")
            return False, str(e)
    
    def install_dev_dependencies(self) -> bool:
        """Instala dependências de desenvolvimento"""
        self.log("📦 Instalando dependências de desenvolvimento...")
        
        dev_packages = [
            "black>=23.0.0",
            "flake8>=6.0.0", 
            "mypy>=1.0.0",
            "isort>=5.12.0",
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "pre-commit>=3.0.0"
        ]
        
        for package in dev_packages:
            success, _ = self.run_command(
                [sys.executable, "-m", "pip", "install", package],
                f"Instalando {package}"
            )
            if not success:
                return False
        
        return True
    
    def format_code_with_black(self) -> bool:
        """Formata código com Black"""
        if not (self.src_dir.exists() or self.tests_dir.exists()):
            self.log("⚠️ Diretórios src/ ou tests/ não encontrados", "WARNING")
            return True
        
        dirs_to_format = []
        if self.src_dir.exists():
            dirs_to_format.append(str(self.src_dir))
        if self.tests_dir.exists():
            dirs_to_format.append(str(self.tests_dir))
        
        return self.run_command(
            [sys.executable, "-m", "black"] + dirs_to_format,
            "Formatando código com Black"
        )[0]
    
    def sort_imports_with_isort(self) -> bool:
        """Ordena imports com isort"""
        if not (self.src_dir.exists() or self.tests_dir.exists()):
            return True
        
        dirs_to_sort = []
        if self.src_dir.exists():
            dirs_to_sort.append(str(self.src_dir))
        if self.tests_dir.exists():
            dirs_to_sort.append(str(self.tests_dir))
        
        return self.run_command(
            [sys.executable, "-m", "isort", "--profile", "black"] + dirs_to_sort,
            "Ordenando imports com isort"
        )[0]
    
    def lint_with_flake8(self) -> bool:
        """Verifica código com flake8"""
        if not (self.src_dir.exists() or self.tests_dir.exists()):
            return True
        
        dirs_to_lint = []
        if self.src_dir.exists():
            dirs_to_lint.append(str(self.src_dir))
        if self.tests_dir.exists():
            dirs_to_lint.append(str(self.tests_dir))
        
        return self.run_command(
            [sys.executable, "-m", "flake8", "--max-line-length=88"] + dirs_to_lint,
            "Verificando código com flake8"
        )[0]
    
    def type_check_with_mypy(self) -> bool:
        """Verifica tipos com mypy"""
        if not self.src_dir.exists():
            return True
        
        return self.run_command(
            [sys.executable, "-m", "mypy", str(self.src_dir)],
            "Verificando tipos com mypy"
        )[0]
    
    def run_tests_with_pytest(self) -> bool:
        """Executa testes com pytest"""
        if not self.tests_dir.exists():
            self.log("⚠️ Diretório tests/ não encontrado", "WARNING")
            return True
        
        return self.run_command(
            [
                sys.executable, "-m", "pytest", 
                str(self.tests_dir),
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=html",
                "-v"
            ],
            "Executando testes com pytest"
        )[0]
    
    def check_security_with_bandit(self) -> bool:
        """Verifica segurança com bandit"""
        # Instalar bandit se não estiver instalado
        self.run_command(
            [sys.executable, "-m", "pip", "install", "bandit"],
            "Instalando bandit"
        )
        
        if not self.src_dir.exists():
            return True
        
        return self.run_command(
            [sys.executable, "-m", "bandit", "-r", str(self.src_dir)],
            "Verificando segurança com bandit"
        )[0]
    
    def generate_requirements_txt(self) -> bool:
        """Gera requirements.txt atualizado"""
        success, output = self.run_command(
            [sys.executable, "-m", "pip", "freeze"],
            "Gerando requirements.txt"
        )
        
        if success:
            # Filtrar apenas pacotes principais
            main_packages = [
                "requests", "pandas", "numpy", "pydantic", 
                "click", "python-dotenv", "pyyaml", "sqlalchemy"
            ]
            
            lines = output.strip().split('\n')
            filtered_lines = []
            
            for line in lines:
                package_name = line.split('==')[0].lower()
                if any(main_pkg in package_name for main_pkg in main_packages):
                    filtered_lines.append(line)
            
            requirements_file = self.project_root / "requirements.txt"
            requirements_file.write_text('\n'.join(filtered_lines) + '\n')
            self.log(f"📄 requirements.txt atualizado com {len(filtered_lines)} pacotes")
        
        return success
    
    def setup_pre_commit_hooks(self) -> bool:
        """Configura pre-commit hooks"""
        return self.run_command(
            [sys.executable, "-m", "pre_commit", "install"],
            "Configurando pre-commit hooks"
        )[0]
    
    def create_quality_config_files(self):
        """Cria arquivos de configuração para ferramentas de qualidade"""
        self.log("⚙️ Criando arquivos de configuração...")
        
        # setup.cfg para flake8
        setup_cfg = '''[flake8]
max-line-length = 88
extend-ignore = E203, W503, E501
exclude = 
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info,
    .venv,
    venv,
    .tox,
    .pytest_cache

[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
    -v
'''
        
        setup_cfg_file = self.project_root / "setup.cfg"
        setup_cfg_file.write_text(setup_cfg)
        self.log("📄 Criado: setup.cfg")
        
        # .coveragerc
        coveragerc = '''[run]
source = src/
omit = 
    */tests/*
    */test_*.py
    */__init__.py
    */conftest.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    @abstract
'''
        
        coveragerc_file = self.project_root / ".coveragerc"
        coveragerc_file.write_text(coveragerc)
        self.log("📄 Criado: .coveragerc")
    
    def run_full_quality_check(self) -> Dict[str, bool]:
        """Executa verificação completa de qualidade"""
        self.log("🔍 Iniciando verificação completa de qualidade...")
        
        checks = [
            ("Dependências", self.install_dev_dependencies),
            ("Configuração", self.create_quality_config_files),
            ("Formatação (Black)", self.format_code_with_black),
            ("Imports (isort)", self.sort_imports_with_isort),
            ("Linting (flake8)", self.lint_with_flake8),
            ("Tipos (mypy)", self.type_check_with_mypy),
            ("Testes (pytest)", self.run_tests_with_pytest),
            ("Segurança (bandit)", self.check_security_with_bandit),
            ("Requirements", self.generate_requirements_txt),
            ("Pre-commit", self.setup_pre_commit_hooks),
        ]
        
        results = {}
        passed = 0
        
        for check_name, check_func in checks:
            try:
                result = check_func()
                results[check_name] = result
                if result:
                    passed += 1
            except Exception as e:
                self.log(f"❌ Erro em {check_name}: {e}", "ERROR")
                results[check_name] = False
        
        # Gerar relatório
        self.generate_quality_report(results, passed, len(checks))
        
        return results
    
    def generate_quality_report(self, results: Dict[str, bool], passed: int, total: int):
        """Gera relatório de qualidade"""
        report_content = f"""# Market Manus - Relatório de Qualidade de Código

**Data:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Score:** {passed}/{total} ({(passed/total)*100:.1f}%)

## 📊 Resultados

"""
        
        for check_name, result in results.items():
            status = "✅ PASSOU" if result else "❌ FALHOU"
            report_content += f"- **{check_name}:** {status}\n"
        
        report_content += f"""
## 📋 Resumo

- **Verificações Passadas:** {passed}
- **Verificações Falhadas:** {total - passed}
- **Score de Qualidade:** {(passed/total)*100:.1f}%

## 🎯 Próximos Passos

"""
        
        if passed == total:
            report_content += """
✅ **Parabéns!** Todas as verificações de qualidade passaram!

Recomendações:
- Manter práticas de código limpo
- Executar verificações regularmente
- Configurar CI/CD para automação
"""
        else:
            report_content += """
⚠️ **Algumas verificações falharam.** Recomendações:

1. Revisar logs de erro acima
2. Corrigir problemas identificados
3. Re-executar verificações
4. Considerar adicionar mais testes
"""
        
        # Salvar relatório
        report_file = self.project_root / "quality_report.md"
        report_file.write_text(report_content)
        
        # Salvar log detalhado
        log_file = self.project_root / "quality_log.txt"
        log_file.write_text("\n".join(self.quality_report))
        
        self.log(f"📄 Relatório salvo em: {report_file}")
        self.log(f"📄 Log detalhado em: {log_file}")
        
        # Exibir resumo
        print("\n" + "="*60)
        print("📊 RELATÓRIO DE QUALIDADE")
        print("="*60)
        print(f"Score: {passed}/{total} ({(passed/total)*100:.1f}%)")
        print("\nResultados:")
        for check_name, result in results.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check_name}")
        print("="*60)


class TestGenerator:
    """Gerador automático de testes básicos"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.src_dir = self.project_root / "src"
        self.tests_dir = self.project_root / "tests"
    
    def generate_basic_tests(self):
        """Gera testes básicos para módulos existentes"""
        if not self.src_dir.exists():
            print("⚠️ Diretório src/ não encontrado")
            return
        
        # Criar estrutura de testes
        self.tests_dir.mkdir(exist_ok=True)
        (self.tests_dir / "unit").mkdir(exist_ok=True)
        (self.tests_dir / "integration").mkdir(exist_ok=True)
        
        # Criar conftest.py
        conftest_content = '''"""
Configuração global para testes
"""
import pytest
from pathlib import Path

@pytest.fixture
def project_root():
    """Retorna o diretório raiz do projeto"""
    return Path(__file__).parent.parent

@pytest.fixture
def sample_config():
    """Configuração de exemplo para testes"""
    return {
        "initial_capital": 1000.0,
        "position_size_pct": 2.0,
        "max_drawdown_pct": 50.0
    }
'''
        
        conftest_file = self.tests_dir / "conftest.py"
        conftest_file.write_text(conftest_content)
        
        # Gerar testes para módulos Python
        python_files = list(self.src_dir.rglob("*.py"))
        for py_file in python_files:
            if py_file.name == "__init__.py":
                continue
            
            self.generate_test_for_module(py_file)
    
    def generate_test_for_module(self, module_path: Path):
        """Gera teste básico para um módulo"""
        relative_path = module_path.relative_to(self.src_dir)
        test_path = self.tests_dir / "unit" / f"test_{relative_path.name}"
        
        # Template básico de teste
        test_content = f'''"""
Testes para {relative_path}
"""
import pytest
from unittest.mock import Mock, patch

# TODO: Adicionar imports específicos do módulo


class Test{relative_path.stem.title().replace('_', '')}:
    """Testes para {relative_path.stem}"""
    
    def test_module_imports(self):
        """Testa se o módulo pode ser importado"""
        # TODO: Adicionar import real do módulo
        assert True
    
    def test_basic_functionality(self):
        """Testa funcionalidade básica"""
        # TODO: Implementar teste real
        assert True
    
    @pytest.mark.parametrize("input_value,expected", [
        (1, 1),
        (2, 2),
    ])
    def test_parametrized(self, input_value, expected):
        """Teste parametrizado de exemplo"""
        # TODO: Implementar teste real
        assert input_value == expected
    
    def test_error_handling(self):
        """Testa tratamento de erros"""
        # TODO: Implementar teste de erro
        assert True
'''
        
        test_path.write_text(test_content)
        print(f"📄 Teste gerado: {test_path}")


def main():
    """Função principal"""
    print("🔍 Market Manus - Automação de Qualidade de Código")
    print("="*60)
    
    # Opções
    print("Opções disponíveis:")
    print("1. Verificação completa de qualidade")
    print("2. Apenas formatação (Black + isort)")
    print("3. Apenas linting (flake8)")
    print("4. Apenas testes (pytest)")
    print("5. Gerar testes básicos")
    print("6. Configurar pre-commit")
    
    choice = input("\n🔢 Escolha uma opção (1-6): ").strip()
    
    quality_manager = CodeQualityManager()
    
    if choice == "1":
        # Verificação completa
        results = quality_manager.run_full_quality_check()
        
    elif choice == "2":
        # Apenas formatação
        quality_manager.format_code_with_black()
        quality_manager.sort_imports_with_isort()
        
    elif choice == "3":
        # Apenas linting
        quality_manager.lint_with_flake8()
        
    elif choice == "4":
        # Apenas testes
        quality_manager.run_tests_with_pytest()
        
    elif choice == "5":
        # Gerar testes
        test_generator = TestGenerator()
        test_generator.generate_basic_tests()
        
    elif choice == "6":
        # Pre-commit
        quality_manager.setup_pre_commit_hooks()
        
    else:
        print("❌ Opção inválida")
        return
    
    print("\n✅ Operação concluída!")


if __name__ == "__main__":
    main()

