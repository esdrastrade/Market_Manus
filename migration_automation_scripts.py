#!/usr/bin/env python3
"""
Market Manus - Scripts de Automação para Migração
Automatiza a reestruturação completa do projeto seguindo melhores práticas
"""

import os
import shutil
import subprocess
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional
import re
from datetime import datetime

class MarketManusMigrator:
    """Automatiza a migração do projeto Market Manus"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.backup_dir = self.project_root / "backup_before_migration"
        self.migration_log = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log de operações"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.migration_log.append(log_entry)
        print(log_entry)
    
    def create_backup(self):
        """Cria backup completo do estado atual"""
        self.log("🔄 Criando backup do estado atual...")
        
        try:
            # Criar diretório de backup
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            self.backup_dir.mkdir(parents=True)
            
            # Copiar arquivos importantes
            important_files = [
                "*.py", "*.json", "*.md", "*.txt", "*.yml", "*.yaml"
            ]
            
            for pattern in important_files:
                for file in self.project_root.glob(pattern):
                    if file.is_file():
                        shutil.copy2(file, self.backup_dir)
            
            # Copiar diretórios importantes
            important_dirs = ["src", "config", "agents", "reports"]
            for dir_name in important_dirs:
                src_dir = self.project_root / dir_name
                if src_dir.exists():
                    shutil.copytree(src_dir, self.backup_dir / dir_name)
            
            self.log(f"✅ Backup criado em: {self.backup_dir}")
            return True
            
        except Exception as e:
            self.log(f"❌ Erro ao criar backup: {e}", "ERROR")
            return False
    
    def create_directory_structure(self):
        """Cria nova estrutura de diretórios"""
        self.log("🏗️ Criando nova estrutura de diretórios...")
        
        directories = [
            # Source code
            "src/market_manus",
            "src/market_manus/core",
            "src/market_manus/strategies", 
            "src/market_manus/engines",
            "src/market_manus/data",
            "src/market_manus/data/providers",
            "src/market_manus/ai",
            "src/market_manus/cli",
            "src/market_manus/cli/commands",
            "src/market_manus/utils",
            
            # Tests
            "tests",
            "tests/unit",
            "tests/unit/test_core",
            "tests/unit/test_strategies",
            "tests/unit/test_engines",
            "tests/unit/test_data",
            "tests/integration",
            "tests/fixtures",
            
            # Configuration
            "config",
            
            # Data
            "data",
            "data/historical",
            "data/cache", 
            "data/exports",
            
            # Logs
            "logs",
            
            # Scripts
            "scripts",
            
            # Documentation
            "docs",
            "docs/api",
            "docs/guides",
            "docs/examples",
            
            # CI/CD
            ".github",
            ".github/workflows"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            self.log(f"📁 Criado: {directory}")
        
        # Criar arquivos __init__.py
        init_dirs = [
            "src/market_manus",
            "src/market_manus/core",
            "src/market_manus/strategies",
            "src/market_manus/engines", 
            "src/market_manus/data",
            "src/market_manus/data/providers",
            "src/market_manus/ai",
            "src/market_manus/cli",
            "src/market_manus/cli/commands",
            "src/market_manus/utils",
            "tests",
            "tests/unit",
            "tests/integration",
            "tests/fixtures"
        ]
        
        for init_dir in init_dirs:
            init_file = self.project_root / init_dir / "__init__.py"
            init_file.touch()
            self.log(f"📄 Criado: {init_dir}/__init__.py")
    
    def migrate_files(self):
        """Migra arquivos para nova estrutura"""
        self.log("📦 Migrando arquivos para nova estrutura...")
        
        # Mapeamento de arquivos: origem -> destino
        file_migrations = {
            # Core components
            "capital_manager.py": "src/market_manus/core/capital_manager.py",
            "test_configuration_manager.py": "src/market_manus/core/config_manager.py",
            "advanced_features.py": "src/market_manus/core/advanced_features.py",
            
            # CLI files
            "src/cli/market_manus_cli_complete_final.py": "src/market_manus/cli/main.py",
            "src/cli/backtest_cli_enhanced.py": "src/market_manus/cli/commands/backtest.py",
            
            # Test files
            "test_enhanced_cli.py": "tests/unit/test_cli.py",
            "test_strategy_factory.py": "tests/unit/test_strategies.py",
            
            # Config files
            "config/capital_config.json": "config/capital.json"
        }
        
        for source, destination in file_migrations.items():
            source_path = self.project_root / source
            dest_path = self.project_root / destination
            
            if source_path.exists():
                # Criar diretório de destino se não existir
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copiar arquivo
                shutil.copy2(source_path, dest_path)
                self.log(f"📄 Migrado: {source} → {destination}")
            else:
                self.log(f"⚠️ Arquivo não encontrado: {source}", "WARNING")
    
    def create_config_files(self):
        """Cria arquivos de configuração modernos"""
        self.log("⚙️ Criando arquivos de configuração...")
        
        # pyproject.toml
        pyproject_content = '''[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "market-manus"
version = "1.0.0"
description = "Sistema de Trading Automatizado para Criptoativos"
authors = [{name = "Esdras", email = "esdras@example.com"}]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.9"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Financial and Insurance Industry",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dependencies = [
    "requests>=2.28.0",
    "pandas>=1.5.0",
    "numpy>=1.24.0",
    "pydantic>=1.10.0",
    "click>=8.1.0",
    "python-dotenv>=1.0.0",
    "pyyaml>=6.0",
    "sqlalchemy>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
    "isort>=5.12.0",
    "pre-commit>=3.0.0",
]
docs = [
    "sphinx>=5.0.0",
    "sphinx-rtd-theme>=1.2.0",
    "myst-parser>=0.18.0",
]

[project.scripts]
market-manus = "market_manus.cli.main:main"

[tool.black]
line-length = 88
target-version = ['py39']
include = '\\.pyi?$'
extend-exclude = '''
/(
  # directories
  \\.eggs
  | \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["market_manus"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--cov=src/market_manus",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-fail-under=80",
]

[tool.coverage.run]
source = ["src/market_manus"]
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__init__.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
'''
        
        pyproject_file = self.project_root / "pyproject.toml"
        pyproject_file.write_text(pyproject_content)
        self.log("📄 Criado: pyproject.toml")
        
        # .env.example
        env_example = '''# Market Manus Configuration
# Copy this file to .env and fill in your values

# API Configuration
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_api_secret_here
BYBIT_TESTNET=true

# Database
DATABASE_URL=sqlite:///data/market_manus.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/market_manus.log

# Trading
DEFAULT_CAPITAL=1000.0
DEFAULT_POSITION_SIZE=2.0
MAX_DRAWDOWN=50.0

# AI Agent
AI_LEARNING_RATE=0.1
AI_EXPLORATION_RATE=0.2
'''
        
        env_file = self.project_root / ".env.example"
        env_file.write_text(env_example)
        self.log("📄 Criado: .env.example")
        
        # .gitignore
        gitignore_content = '''# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
.pybuilder/
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
Pipfile.lock

# poetry
poetry.lock

# pdm
.pdm.toml

# PEP 582
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/

# PyCharm
.idea/

# VS Code
.vscode/

# Project specific
data/historical/*
data/cache/*
data/exports/*
logs/*.log
backup_before_migration/
*.db
*.sqlite
*.sqlite3

# OS specific
.DS_Store
Thumbs.db
'''
        
        gitignore_file = self.project_root / ".gitignore"
        gitignore_file.write_text(gitignore_content)
        self.log("📄 Criado: .gitignore")
        
        # requirements.txt
        requirements = '''requests>=2.28.0
pandas>=1.5.0
numpy>=1.24.0
pydantic>=1.10.0
click>=8.1.0
python-dotenv>=1.0.0
pyyaml>=6.0
sqlalchemy>=2.0.0
'''
        
        req_file = self.project_root / "requirements.txt"
        req_file.write_text(requirements)
        self.log("📄 Criado: requirements.txt")
        
        # requirements-dev.txt
        requirements_dev = '''pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
isort>=5.12.0
pre-commit>=3.0.0
sphinx>=5.0.0
sphinx-rtd-theme>=1.2.0
'''
        
        req_dev_file = self.project_root / "requirements-dev.txt"
        req_dev_file.write_text(requirements_dev)
        self.log("📄 Criado: requirements-dev.txt")
    
    def create_ci_cd_workflows(self):
        """Cria workflows de CI/CD"""
        self.log("🔄 Criando workflows de CI/CD...")
        
        # GitHub Actions CI
        ci_workflow = '''name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Lint with flake8
      run: |
        flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
    
    - name: Format check with black
      run: |
        black --check src/ tests/
    
    - name: Import sort check with isort
      run: |
        isort --check-only src/ tests/
    
    - name: Type check with mypy
      run: |
        mypy src/
    
    - name: Test with pytest
      run: |
        pytest tests/ --cov=src/market_manus --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
'''
        
        ci_file = self.project_root / ".github" / "workflows" / "ci.yml"
        ci_file.write_text(ci_workflow)
        self.log("📄 Criado: .github/workflows/ci.yml")
        
        # Pre-commit configuration
        precommit_config = '''repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files
    -   id: check-json
    -   id: check-merge-conflict
    -   id: debug-statements

-   repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
    -   id: black
        language_version: python3

-   repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
    -   id: isort
        args: ["--profile", "black"]

-   repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
    -   id: flake8
        args: [--max-line-length=88]

-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.1
    hooks:
    -   id: mypy
        additional_dependencies: [types-requests, types-PyYAML]
'''
        
        precommit_file = self.project_root / ".pre-commit-config.yaml"
        precommit_file.write_text(precommit_config)
        self.log("📄 Criado: .pre-commit-config.yaml")
    
    def fix_imports(self):
        """Corrige imports para nova estrutura"""
        self.log("🔧 Corrigindo imports para nova estrutura...")
        
        # Mapeamento de imports antigos -> novos
        import_mappings = {
            "from capital_manager import": "from market_manus.core.capital_manager import",
            "import capital_manager": "import market_manus.core.capital_manager",
            "from test_configuration_manager import": "from market_manus.core.config_manager import",
            "from advanced_features import": "from market_manus.core.advanced_features import",
        }
        
        # Encontrar arquivos Python
        python_files = list(self.project_root.rglob("*.py"))
        
        for py_file in python_files:
            if "backup_before_migration" in str(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                original_content = content
                
                # Aplicar mapeamentos
                for old_import, new_import in import_mappings.items():
                    content = content.replace(old_import, new_import)
                
                # Salvar se houve mudanças
                if content != original_content:
                    py_file.write_text(content, encoding='utf-8')
                    self.log(f"🔧 Imports corrigidos em: {py_file.relative_to(self.project_root)}")
                    
            except Exception as e:
                self.log(f"⚠️ Erro ao corrigir imports em {py_file}: {e}", "WARNING")
    
    def create_documentation_templates(self):
        """Cria templates de documentação"""
        self.log("📚 Criando templates de documentação...")
        
        # README.md principal
        readme_content = '''# Market Manus

🏭 **Sistema de Trading Automatizado para Criptoativos**

Sistema completo para automação de estratégias de trading, com suporte a múltiplas estratégias, aprendizagem de máquina e proteção de capital.

## ✨ Características

- 🤖 **AI Agent** com aprendizagem multi-armed bandit
- 📊 **Múltiplas Estratégias** (EMA, RSI, Bollinger, AI)
- 🛡️ **Proteção de Capital** com drawdown automático
- 📈 **Backtesting** com dados reais da Bybit
- 🔄 **Trading Automatizado** com execução em tempo real
- 📱 **CLI Intuitivo** para configuração e monitoramento
- 📊 **Relatórios Detalhados** em CSV/JSON
- 🌐 **API Integration** com Bybit

## 🚀 Instalação Rápida

```bash
# Clone o repositório
git clone https://github.com/esdrastrade/Market_Manus.git
cd Market_Manus

# Instalar dependências
pip install -r requirements.txt

# Configurar ambiente
cp .env.example .env
# Edite .env com suas credenciais

# Executar CLI
python -m market_manus.cli.main
```

## 📖 Documentação

- [Guia de Instalação](docs/guides/installation.md)
- [Configuração](docs/guides/configuration.md)
- [Estratégias](docs/guides/strategies.md)
- [API Reference](docs/api/)

## 🤝 Contribuição

Contribuições são bem-vindas! Veja [CONTRIBUTING.md](CONTRIBUTING.md) para detalhes.

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja [LICENSE](LICENSE) para detalhes.
'''
        
        readme_file = self.project_root / "README.md"
        readme_file.write_text(readme_content)
        self.log("📄 Criado: README.md")
        
        # CHANGELOG.md
        changelog_content = '''# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-16

### Added
- ✨ Sistema completo de trading automatizado
- 🤖 AI Agent com multi-armed bandit
- 📊 Múltiplas estratégias de trading
- 🛡️ Proteção automática de drawdown
- 📈 Engine de backtesting
- 🌐 Integração com API Bybit
- 📱 CLI intuitivo e completo
- 📊 Sistema de relatórios
- 🔧 Configuração flexível
- 🧪 Testes automatizados

### Changed
- 🏗️ Reestruturação completa do projeto
- 📦 Organização modular do código
- 🔧 Configuração centralizada
- 📚 Documentação completa

### Fixed
- 🐛 Correção de imports
- 🔧 Configuração de ambiente
- 📊 Cálculos de métricas
- 🔄 Fluxo de execução
'''
        
        changelog_file = self.project_root / "CHANGELOG.md"
        changelog_file.write_text(changelog_content)
        self.log("📄 Criado: CHANGELOG.md")
    
    def run_full_migration(self):
        """Executa migração completa"""
        self.log("🚀 Iniciando migração completa do Market Manus...")
        
        steps = [
            ("Backup", self.create_backup),
            ("Estrutura", self.create_directory_structure),
            ("Migração", self.migrate_files),
            ("Configuração", self.create_config_files),
            ("CI/CD", self.create_ci_cd_workflows),
            ("Imports", self.fix_imports),
            ("Documentação", self.create_documentation_templates),
        ]
        
        success_count = 0
        for step_name, step_func in steps:
            self.log(f"🔄 Executando: {step_name}")
            try:
                if step_func():
                    success_count += 1
                    self.log(f"✅ {step_name} concluído")
                else:
                    self.log(f"❌ {step_name} falhou", "ERROR")
            except Exception as e:
                self.log(f"❌ Erro em {step_name}: {e}", "ERROR")
        
        # Salvar log de migração
        log_file = self.project_root / "migration_log.txt"
        log_file.write_text("\n".join(self.migration_log))
        
        self.log(f"🎉 Migração concluída! {success_count}/{len(steps)} etapas bem-sucedidas")
        self.log(f"📄 Log salvo em: {log_file}")
        
        return success_count == len(steps)


def main():
    """Função principal"""
    print("🏭 Market Manus - Automação de Migração")
    print("="*50)
    
    migrator = MarketManusMigrator()
    
    # Confirmar execução
    response = input("🤔 Deseja executar a migração completa? (s/N): ")
    if not response.lower().startswith('s'):
        print("❌ Migração cancelada pelo usuário")
        return
    
    # Executar migração
    success = migrator.run_full_migration()
    
    if success:
        print("\n🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("📋 Próximos passos:")
        print("   1. Revisar arquivos migrados")
        print("   2. Testar imports: python -c 'import market_manus'")
        print("   3. Executar testes: pytest tests/")
        print("   4. Fazer commit: git add . && git commit -m 'feat: Reestruturação completa'")
        print("   5. Executar CLI: python -m market_manus.cli.main")
    else:
        print("\n⚠️ Migração concluída com alguns erros")
        print("📄 Verifique migration_log.txt para detalhes")


if __name__ == "__main__":
    main()

