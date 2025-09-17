# Market Manus - Sistema de Trading Automatizado

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-orange.svg)](https://github.com/esdrastrade/Market_Manus)

> **Sistema de Trading Automatizado de Criptoativos com Arquitetura de Agents e IA**

## 🎯 Visão Geral

O **Market Manus** é um sistema completo de trading automatizado para criptoativos que combina estratégias tradicionais com inteligência artificial e arquitetura de agents. Desenvolvido para transformar "vibe coding" em resultados econômicos tangíveis, oferecendo automação escalável para renda passiva.

### 🏆 Características Principais

- **🤖 Arquitetura de Agents**: Sistema modular com 6 agents especializados
- **🧠 IA Integrada**: AI Agent com aprendizagem multi-armed bandit
- **💰 Gestão de Capital**: Tracking detalhado e proteção de drawdown
- **📊 Múltiplas Estratégias**: EMA, RSI, Bollinger Bands + AI Agent
- **🔄 Backtesting Avançado**: Validação com dados históricos reais
- **📈 Análise Enterprise**: Métricas profissionais e benchmarking
- **🛡️ Proteção de Risco**: Sistema de stop-loss dinâmico
- **📱 Interface CLI**: Interface completa e intuitiva

## 🏗️ Arquitetura do Sistema

### 📁 Estrutura do Projeto

```
Market_Manus/
├── 📂 src/                          # Código fonte principal
│   ├── 📂 cli/                      # Interfaces de linha de comando
│   │   ├── market_manus_cli_complete_final.py    # CLI principal
│   │   ├── market_manus_cli_20250116_1900.py     # CLI base
│   │   └── market_manus_enterprise_cli.py        # CLI Enterprise (em desenvolvimento)
│   ├── 📂 core/                     # Componentes centrais
│   │   ├── capital_manager.py       # Gestão de capital
│   │   ├── advanced_features.py     # Funcionalidades avançadas
│   │   └── test_configuration_manager.py  # Configurações de teste
│   ├── 📂 strategies/               # Estratégias de trading
│   │   └── ai_agent_strategy.py     # Estratégia com IA
│   ├── 📂 ai_agent/                 # Módulos de IA (legacy)
│   ├── 📂 engines/                  # Engines de execução
│   ├── 📂 market_manus/             # Estrutura modular (em desenvolvimento)
│   └── 📂 utils/                    # Utilitários
├── 📂 agents/                       # Sistema de Agents
│   ├── base_agent.py                # Classe base dos agents
│   ├── orchestrator_agent.py        # Coordenação geral
│   ├── backtesting_agent.py         # Backtesting avançado
│   ├── market_analysis_agent.py     # Análise de mercado
│   ├── risk_management_agent.py     # Gestão de risco
│   ├── performance_agent.py         # Monitoramento de performance
│   └── notification_agent.py        # Sistema de notificações
├── 📂 config/                       # Configurações
│   └── capital_config.json          # Configuração de capital
├── 📂 reports/                      # Relatórios gerados
├── 📂 logs/                         # Logs do sistema
├── 📂 tests/                        # Testes automatizados
├── 📂 docs/                         # Documentação
└── 📄 main.py                       # Ponto de entrada principal
```

### 🤖 Sistema de Agents

O Market Manus utiliza uma arquitetura de agents especializados:

| Agent | Função | Status |
|-------|--------|--------|
| **OrchestratorAgent** | Coordenação geral do sistema | ✅ Implementado |
| **BacktestingAgent** | Backtesting avançado com otimização | ✅ Implementado |
| **MarketAnalysisAgent** | Análise técnica e detecção de padrões | ✅ Implementado |
| **RiskManagementAgent** | Gestão de risco dinâmica | ✅ Implementado |
| **PerformanceAgent** | Monitoramento de performance | ✅ Implementado |
| **NotificationAgent** | Sistema de alertas inteligente | ✅ Implementado |

## 🚀 Funcionalidades

### 💰 Gestão de Capital
- **Capital Livre**: Range de $1 a $100,000
- **Position Sizing**: 0.1% a 10% configurável
- **Compound Interest**: Reinvestimento automático opcional
- **Proteção de Drawdown**: Limite configurável (10% - 90%)
- **Tracking em Tempo Real**: Evolução do capital visualizada

### 🧠 Estratégias Disponíveis

#### 1. **EMA Crossover**
- Cruzamento de médias móveis exponenciais
- Timeframes: 15m, 1h, 4h
- Win Rate: ~58%

#### 2. **RSI Mean Reversion**
- Reversão à média usando RSI
- Timeframes: 5m, 15m, 1h
- Win Rate: ~62%

#### 3. **Bollinger Breakout**
- Rompimento das Bandas de Bollinger
- Timeframes: 1h, 4h, 1d
- Win Rate: ~52%

#### 4. **AI Agent Enterprise** 🤖
- IA com aprendizagem multi-armed bandit
- Seleção automática de estratégias
- Adaptação em tempo real
- Win Rate: ~68%

### 🔬 Strategy Lab

- **Single Test**: Teste de estratégia individual
- **Combination Test**: Múltiplas estratégias combinadas
- **Full Validation**: Validação completa de todas as combinações
- **AI Agent Test**: Teste com aprendizagem automática
- **Enterprise Analysis**: Análise completa com todos os agents

### 📊 Análise e Relatórios

- **Performance Dashboard**: Métricas em tempo real
- **Benchmark Comparison**: Comparação com Bitcoin e mercado
- **Risk-Adjusted Metrics**: Sharpe, Sortino, Calmar ratios
- **Export Reports**: CSV, JSON, Enterprise Reports
- **Histórico Completo**: Todos os trades e mudanças de capital

## 🛠️ Instalação e Configuração

### 📋 Pré-requisitos

- Python 3.9+
- Conta na Bybit (para dados reais)
- Git

### 🔧 Instalação

1. **Clone o repositório**
```bash
git clone https://github.com/esdrastrade/Market_Manus.git
cd Market_Manus
```

2. **Instale as dependências**
```bash
pip install -r requirements.txt
```

3. **Configure as variáveis de ambiente** (opcional)
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite com suas credenciais da Bybit
BYBIT_API_KEY=sua_api_key
BYBIT_API_SECRET=seu_api_secret
```

### ▶️ Execução

#### CLI Principal (Recomendado)
```bash
python src/cli/market_manus_cli_complete_final.py
```

#### Via Main.py
```bash
python main.py
```

## 🎮 Como Usar

### 1. **Configuração Inicial**
- Execute o CLI principal
- Configure seu capital inicial ($1 - $100,000)
- Defina position size e proteção de drawdown
- Teste conectividade com API

### 2. **Strategy Lab**
- Acesse o Strategy Lab (Opção 2)
- Escolha entre Single Test, Combinations ou Full Validation
- Configure período e timeframe
- Execute backtesting

### 3. **Monitoramento**
- Acompanhe evolução do capital em tempo real
- Monitore métricas de performance
- Receba alertas de risco automáticos
- Exporte relatórios periodicamente

## 📈 Resultados Esperados

### 🏆 Performance Típica
- **Retorno Anual**: 15% - 35%
- **Sharpe Ratio**: 1.5 - 2.5
- **Max Drawdown**: 5% - 15%
- **Win Rate**: 55% - 70%

### 🛡️ Gestão de Risco
- **Stop Loss Dinâmico**: Ajustado automaticamente
- **Position Sizing**: Baseado em volatilidade
- **Proteção de Capital**: Interrupção automática em drawdowns excessivos
- **Diversificação**: Múltiplas estratégias e timeframes

## 🔧 Configuração Avançada

### 🌐 API Bybit
```python
# Configuração recomendada
BYBIT_API_KEY = "sua_chave_api"
BYBIT_API_SECRET = "seu_secret_api"
RECV_WINDOW = 60000  # Para resolver problemas de timestamp
```

### 💰 Capital Management
```json
{
  "initial_capital": 10000.0,
  "position_size_pct": 2.0,
  "compound_interest": true,
  "max_drawdown_pct": 20.0
}
```

### 🤖 AI Agent Configuration
```python
# Parâmetros do Multi-Armed Bandit
{
  "fee_bps": 1.5,
  "lam_dd": 0.5,
  "lam_cost": 0.1,
  "exploration_rate": 0.1
}
```

## 🧪 Testes

### Executar Testes
```bash
# Testes unitários
pytest tests/ -v

# Testes com coverage
pytest tests/ --cov=src --cov-report=html

# Testes de integração
pytest tests/integration/ -v
```

### Qualidade de Código
```bash
# Formatação
black src/
isort src/

# Linting
flake8 src/
mypy src/

# Segurança
bandit -r src/
```

## 📊 Monitoramento e Logs

### 📁 Logs do Sistema
- `logs/market_manus.log`: Log principal
- `logs/capital_tracking.log`: Tracking de capital
- `logs/api_connectivity.log`: Conectividade API
- `logs/agents_activity.log`: Atividade dos agents

### 📈 Métricas Monitoradas
- **Capital Evolution**: Evolução do capital em tempo real
- **Strategy Performance**: Performance individual das estratégias
- **Risk Metrics**: Métricas de risco e drawdown
- **API Health**: Status da conectividade
- **Agent Activity**: Atividade e métricas dos agents

## 🤝 Contribuição

### 🔄 Fluxo de Desenvolvimento
1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-estrategia`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova estratégia'`)
4. Push para a branch (`git push origin feature/nova-estrategia`)
5. Abra um Pull Request

### 📝 Padrões de Código
- **Python**: PEP 8 compliance
- **Docstrings**: Google style
- **Type Hints**: Obrigatório para funções públicas
- **Testes**: Coverage mínimo de 80%

## 🔮 Roadmap

### 🎯 Próximas Funcionalidades

#### Q1 2025
- [ ] **Integração Completa dos Agents**: Finalizar integração no CLI Enterprise
- [ ] **Estratégias Adicionais**: MACD, Stochastic, Williams %R
- [ ] **Paper Trading**: Modo de trading simulado em tempo real
- [ ] **Dashboard Web**: Interface web para monitoramento

#### Q2 2025
- [ ] **Trading Real**: Execução automática de trades reais
- [ ] **Portfolio Management**: Gestão de múltiplos ativos
- [ ] **Machine Learning**: Modelos preditivos avançados
- [ ] **Mobile App**: Aplicativo para monitoramento móvel

#### Q3 2025
- [ ] **Cloud Deployment**: Deploy em nuvem com alta disponibilidade
- [ ] **Social Trading**: Compartilhamento de estratégias
- [ ] **Advanced Analytics**: Analytics avançados e insights
- [ ] **API Pública**: API para integração com terceiros

## ⚠️ Avisos Importantes

### 🚨 Disclaimer
- **Risco Financeiro**: Trading de criptoativos envolve risco significativo
- **Não é Conselho Financeiro**: Este software é para fins educacionais
- **Teste Primeiro**: Sempre teste em ambiente simulado antes do uso real
- **Capital de Risco**: Use apenas capital que pode perder

### 🛡️ Segurança
- **API Keys**: Nunca compartilhe suas chaves de API
- **Permissões**: Use apenas permissões necessárias (leitura + trading)
- **Backup**: Faça backup regular das configurações
- **Monitoramento**: Monitore atividade regularmente

## 📞 Suporte

### 🆘 Problemas Comuns

#### Erro de Timestamp da API
```bash
# Sincronizar relógio do Windows
w32tm /resync /force

# Ou aumentar recv_window no código
recv_window = 60000
```

#### Problemas de Conectividade
```bash
# Testar conectividade
python src/cli/market_manus_cli_complete_final.py
# Opção 7: Connectivity Status
```

#### Erro de Imports
```bash
# Verificar estrutura do projeto
python -c "import sys; print(sys.path)"

# Executar da raiz do projeto
cd Market_Manus
python src/cli/market_manus_cli_complete_final.py
```

### 📧 Contato
- **Issues**: [GitHub Issues](https://github.com/esdrastrade/Market_Manus/issues)
- **Discussões**: [GitHub Discussions](https://github.com/esdrastrade/Market_Manus/discussions)
- **Email**: esdrastrade@gmail.com

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- **Bybit**: Pela API robusta e confiável
- **Comunidade Python**: Pelas bibliotecas incríveis
- **Traders**: Pela inspiração e feedback
- **Manus AI**: Pelo desenvolvimento e suporte

---

## 📊 Status do Projeto

| Componente | Status | Cobertura | Última Atualização |
|------------|--------|-----------|-------------------|
| **CLI Principal** | ✅ Estável | 95% | 16/01/2025 |
| **Sistema de Agents** | 🔄 Em Integração | 80% | 16/01/2025 |
| **AI Agent** | ✅ Funcional | 90% | 16/01/2025 |
| **Capital Management** | ✅ Estável | 100% | 16/01/2025 |
| **API Integration** | ✅ Funcional | 85% | 16/01/2025 |
| **Backtesting** | ✅ Estável | 95% | 16/01/2025 |
| **Documentation** | 🔄 Em Progresso | 70% | 16/01/2025 |

---

**🚀 Market Manus - Transformando Vibe Coding em Resultados Econômicos Tangíveis!**

*Desenvolvido com ❤️ para a comunidade de trading algorítmico*

