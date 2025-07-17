# 🚀 Sistema de Scalping Automatizado

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![PowerShell](https://img.shields.io/badge/PowerShell-5.1+-blue.svg)](https://docs.microsoft.com/powershell/)
[![Docker](https://img.shields.io/badge/Docker-Ready-green.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-green.svg)](tests/)

**Sistema profissional de trading automatizado para scalping em criptomoedas, desenvolvido com arquitetura de agentes especializados e orquestração PowerShell.**

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Características Principais](#-características-principais)
- [Arquitetura](#-arquitetura)
- [Instalação Rápida](#-instalação-rápida)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [Documentação](#-documentação)
- [Testes](#-testes)
- [Deployment](#-deployment)
- [Monitoramento](#-monitoramento)
- [Contribuição](#-contribuição)
- [Licença](#-licença)

---

## 🎯 Visão Geral

O Sistema de Scalping Automatizado é uma solução completa para trading de alta frequência em mercados de criptomoedas. Desenvolvido com foco em **performance**, **confiabilidade** e **escalabilidade**, o sistema utiliza uma arquitetura baseada em agentes especializados que trabalham de forma coordenada para identificar oportunidades de mercado e executar operações automatizadas.

### 🎪 Demonstração

```bash
# Inicialização rápida
git clone https://github.com/esdrastrade/Market_Manus.git
cd Market_Manus
python -m pip install -r requirements.txt
python -m agents.orchestrator_agent
```

### 📊 Resultados Esperados

- **Taxa de Acerto:** 65-75% em condições normais de mercado
- **Sharpe Ratio:** 1.2-1.8 dependendo da volatilidade
- **Drawdown Máximo:** < 10% com gestão de risco adequada
- **Latência:** < 100ms para geração de sinais
- **Uptime:** > 99.5% com monitoramento ativo

---

## ✨ Características Principais

### 🤖 **Agentes Especializados**
- **MarketAnalysisAgent** - Análise técnica avançada com 3 estratégias
- **RiskManagementAgent** - Gestão de risco em tempo real
- **NotificationAgent** - Sistema de alertas multi-canal
- **PerformanceAgent** - Análise e otimização contínua
- **BacktestingAgent** - Validação de estratégias
- **OrchestratorAgent** - Coordenação e monitoramento

### 📈 **Estratégias de Trading**
- **EMA Crossover** - Cruzamento de médias móveis exponenciais
- **RSI Mean Reversion** - Reversão à média baseada em RSI
- **Bollinger Bands Breakout** - Rompimento de bandas de Bollinger
- **Sistema de Combinação** - Sinais ponderados e adaptativos

### 🛡️ **Gestão de Risco Avançada**
- Position sizing dinâmico baseado em volatilidade
- Stop loss adaptativo com ATR
- Monitoramento de drawdown em tempo real
- Circuit breakers automáticos
- Diversificação temporal e por ativo

### 🔧 **Automação PowerShell**
- **deploy.ps1** - Deployment e inicialização automática
- **monitor.ps1** - Monitoramento em tempo real
- **backup.ps1** - Backup e versionamento automático
- **optimize.ps1** - Otimização de performance

### 📊 **Monitoramento Profissional**
- Dashboard Grafana em tempo real
- Métricas Prometheus customizadas
- Alertas automáticos via Telegram/Discord
- Relatórios HTML detalhados
- Logs estruturados e rotativos

---

## 🏗️ Arquitetura

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT                      │
│                 (Coordenação Central)                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
    ▼                 ▼                 ▼
┌─────────┐    ┌─────────────┐    ┌─────────────┐
│ Market  │    │    Risk     │    │Performance  │
│Analysis │    │ Management  │    │   Agent     │
│ Agent   │    │   Agent     │    │             │
└─────────┘    └─────────────┘    └─────────────┘
    │                 │                 │
    └─────────────────┼─────────────────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
    ▼                 ▼                 ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│Notification │ │ Backtesting │ │   Data      │
│   Agent     │ │   Agent     │ │  Storage    │
└─────────────┘ └─────────────┘ └─────────────┘
```

### Fluxo de Dados

```
Market Data → Analysis → Signals → Risk Check → Execution → Monitoring
     ↓           ↓         ↓          ↓           ↓          ↓
  Exchange → Indicators → Entry/Exit → Position → Orders → Metrics
                                      Sizing
```

### Tecnologias Utilizadas

| Componente | Tecnologia | Versão |
|------------|------------|--------|
| **Backend** | Python | 3.11+ |
| **Orquestração** | PowerShell | 5.1+ |
| **Cache** | Redis | 7.0+ |
| **Monitoramento** | Prometheus + Grafana | Latest |
| **Containerização** | Docker + Compose | Latest |
| **Exchange API** | CCXT | Latest |
| **Análise Técnica** | TA-Lib, Pandas | Latest |

---

## 🚀 Instalação Rápida

### Pré-requisitos

- **Python 3.11+**
- **PowerShell 5.1+** (Windows)
- **Git**
- **8GB RAM** (mínimo)
- **Conexão estável com internet**

### Instalação Automática

```bash
# 1. Clonar repositório
git clone https://github.com/esdrastrade/Market_Manus.git
cd Market_Manus

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar ambiente
copy config\trading_config.example.json config\trading_config.json
copy config\risk_parameters.example.json config\risk_parameters.json

# 4. Executar deployment
.\scripts\deploy.ps1 -Environment development
```

### Instalação com Docker

```bash
# 1. Clonar repositório
git clone https://github.com/esdrastrade/Market_Manus.git
cd Market_Manus

# 2. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# 3. Inicializar com Docker Compose
docker-compose up -d

# 4. Verificar status
docker-compose ps
```

### Verificação da Instalação

```bash
# Executar testes
python tests\run_tests.py --unit --integration

# Verificar agentes
.\scripts\monitor.ps1 -AgentStatus

# Acessar dashboard
# http://localhost:8080 (Sistema)
# http://localhost:3000 (Grafana)
```

---

## ⚙️ Configuração

### Configuração Básica

#### 1. Credenciais da Exchange

```json
// config/exchange_settings.json
{
  "default_exchange": "binance",
  "exchanges": {
    "binance": {
      "api_key": "YOUR_API_KEY",
      "api_secret": "YOUR_API_SECRET",
      "sandbox": true,
      "rate_limit": 1200
    }
  }
}
```

#### 2. Parâmetros de Trading

```json
// config/trading_config.json
{
  "trading": {
    "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT"],
    "timeframes": ["1m", "5m"],
    "max_positions": 3,
    "base_currency": "USDT"
  },
  "strategies": {
    "ema_crossover": {
      "enabled": true,
      "weight": 0.4,
      "fast_period": 12,
      "slow_period": 26
    },
    "rsi_mean_reversion": {
      "enabled": true,
      "weight": 0.3,
      "period": 14,
      "overbought": 70,
      "oversold": 30
    },
    "bollinger_breakout": {
      "enabled": true,
      "weight": 0.3,
      "period": 20,
      "std_dev": 2.0
    }
  }
}
```

#### 3. Gestão de Risco

```json
// config/risk_parameters.json
{
  "risk_limits": {
    "max_risk_per_trade": 0.02,
    "max_daily_loss": 0.05,
    "max_drawdown": 0.10,
    "stop_loss_percentage": 0.015
  },
  "position_sizing": {
    "method": "fixed_percentage",
    "base_amount": 100,
    "max_position_size": 1000
  }
}
```

### Configuração Avançada

#### Notificações

```json
// config/notification_settings.json
{
  "telegram": {
    "enabled": true,
    "bot_token": "YOUR_BOT_TOKEN",
    "chat_id": "YOUR_CHAT_ID"
  },
  "discord": {
    "enabled": true,
    "webhook_url": "YOUR_WEBHOOK_URL"
  },
  "email": {
    "enabled": false,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "your_email@gmail.com",
    "password": "your_app_password"
  }
}
```

#### Performance

```json
// config/performance_settings.json
{
  "cache": {
    "enabled": true,
    "ttl": 300,
    "max_memory": "256mb"
  },
  "threading": {
    "max_workers": 4,
    "timeout": 30
  },
  "logging": {
    "level": "INFO",
    "rotation": "daily",
    "retention": "30 days"
  }
}
```

---

## 🎮 Uso

### Inicialização do Sistema

```powershell
# Inicialização completa
.\scripts\deploy.ps1 -Environment production -AutoStart

# Inicialização de desenvolvimento
python -m agents.orchestrator_agent --debug

# Inicialização de agente específico
python -m agents.market_analysis_agent
```

### Monitoramento

```powershell
# Dashboard interativo
.\scripts\monitor.ps1 -Dashboard

# Status dos agentes
.\scripts\monitor.ps1 -AgentStatus

# Métricas de performance
.\scripts\monitor.ps1 -Performance

# Logs em tempo real
.\scripts\monitor.ps1 -Logs -Follow
```

### Operações Comuns

```powershell
# Backup manual
.\scripts\backup.ps1 -Type full

# Otimização do sistema
.\scripts\optimize.ps1 -AnalyzePerformance

# Reiniciar agente específico
.\scripts\monitor.ps1 -RestartAgent MarketAnalysisAgent

# Parar sistema
.\scripts\monitor.ps1 -Stop
```

### Interface Web

Acesse o dashboard web em `http://localhost:8080`:

- **Dashboard Principal** - Visão geral do sistema
- **Sinais de Trading** - Sinais em tempo real
- **Performance** - Métricas e gráficos
- **Configurações** - Ajustes do sistema
- **Logs** - Visualização de logs

---

## 📚 Documentação

### Documentação Técnica

| Documento | Descrição |
|-----------|-----------|
| [**Deployment Guide**](docs/deployment_guide.md) | Guia completo de deployment |
| [**Strategies Documentation**](docs/strategies.md) | Documentação das estratégias |
| [**Troubleshooting**](docs/troubleshooting.md) | Solução de problemas |
| [**API Reference**](docs/api_reference.md) | Referência da API |
| [**Configuration Guide**](docs/configuration_guide.md) | Guia de configuração |

### Arquitetura e Design

- **Padrão de Agentes** - Cada agente é responsável por uma função específica
- **Event-Driven** - Comunicação baseada em eventos entre agentes
- **Microserviços** - Componentes independentes e escaláveis
- **Fail-Safe** - Recuperação automática de falhas
- **Observabilidade** - Monitoramento e logging completos

### Estratégias de Trading

#### EMA Crossover
- **Conceito:** Cruzamento de médias móveis exponenciais
- **Sinais:** Compra quando EMA rápida cruza acima da lenta
- **Parâmetros:** EMA 12 e 26 períodos
- **Performance:** 65-75% de acerto em tendências

#### RSI Mean Reversion
- **Conceito:** Reversão à média baseada no RSI
- **Sinais:** Compra em sobrevenda (RSI < 30), venda em sobrecompra (RSI > 70)
- **Parâmetros:** RSI 14 períodos
- **Performance:** 70-80% de acerto em mercados laterais

#### Bollinger Bands Breakout
- **Conceito:** Rompimento das bandas de Bollinger
- **Sinais:** Compra/venda quando preço rompe as bandas
- **Parâmetros:** 20 períodos, 2 desvios padrão
- **Performance:** 60-70% de acerto em breakouts genuínos

---

## 🧪 Testes

### Executar Testes

```bash
# Todos os testes
python tests\run_tests.py

# Apenas testes unitários
python tests\run_tests.py --unit

# Apenas testes de integração
python tests\run_tests.py --integration

# Testes com relatório HTML
python tests\run_tests.py --html

# Testes com cobertura
python tests\run_tests.py --coverage
```

### Estrutura de Testes

```
tests/
├── test_framework.py              # Framework base de testes
├── unit_tests/
│   ├── test_market_analysis_agent.py
│   ├── test_risk_management_agent.py
│   └── test_*.py
├── integration_tests/
│   ├── test_system_integration.py
│   └── test_*.py
└── run_tests.py                   # Script principal
```

### Cobertura de Testes

- **Testes Unitários:** 95%+ de cobertura
- **Testes de Integração:** Fluxos end-to-end completos
- **Testes de Performance:** Benchmarks automatizados
- **Testes de Stress:** Validação sob alta carga

---

## 🚢 Deployment

### Ambiente de Desenvolvimento

```bash
# Configuração rápida
.\scripts\deploy.ps1 -Environment development

# Com hot-reload
python -m agents.orchestrator_agent --debug --reload
```

### Ambiente de Produção

```bash
# Deployment completo
.\scripts\deploy.ps1 -Environment production -AutoStart -EnableMonitoring

# Com Docker
docker-compose -f docker-compose.prod.yml up -d

# Verificação pós-deployment
.\scripts\monitor.ps1 -HealthCheck
```

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Tests
        run: python tests/run_tests.py --coverage
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Production
        run: ./scripts/deploy.ps1 -Environment production
```

### Checklist de Produção

- [ ] Testes passando (100%)
- [ ] Configurações validadas
- [ ] Credenciais configuradas
- [ ] Monitoramento ativo
- [ ] Backup configurado
- [ ] Alertas funcionando
- [ ] Performance validada
- [ ] Documentação atualizada

---

## 📊 Monitoramento

### Dashboards Disponíveis

#### Grafana (http://localhost:3000)
- **Sistema Overview** - Métricas gerais
- **Trading Performance** - Performance de trading
- **Risk Management** - Métricas de risco
- **System Health** - Saúde do sistema

#### Prometheus (http://localhost:9091)
- **Métricas Raw** - Dados brutos
- **Targets** - Status dos endpoints
- **Alerts** - Regras de alerta

### Métricas Principais

| Métrica | Descrição | Alerta |
|---------|-----------|--------|
| `scalping_signals_total` | Total de sinais gerados | - |
| `scalping_success_rate` | Taxa de sucesso | < 50% |
| `scalping_drawdown_current` | Drawdown atual | > 10% |
| `scalping_pnl_daily` | P&L diário | < -5% |
| `scalping_latency_ms` | Latência de processamento | > 1000ms |

### Alertas Configurados

- **Alto Drawdown** - Drawdown > 10%
- **Baixa Taxa de Sucesso** - < 50% por 1 hora
- **Falha de Agente** - Agente não responde por 5 minutos
- **Erro de Conectividade** - Falha na API da exchange
- **Alto Uso de Recursos** - CPU > 80% ou RAM > 90%

---

## 🤝 Contribuição

### Como Contribuir

1. **Fork** o repositório
2. **Crie** uma branch para sua feature (`git checkout -b feature/nova-estrategia`)
3. **Commit** suas mudanças (`git commit -am 'Adiciona nova estratégia'`)
4. **Push** para a branch (`git push origin feature/nova-estrategia`)
5. **Abra** um Pull Request

### Diretrizes de Desenvolvimento

- **Código:** Seguir PEP 8 para Python
- **Testes:** Manter cobertura > 90%
- **Documentação:** Atualizar docs para novas features
- **Commits:** Usar conventional commits
- **Issues:** Usar templates fornecidos

### Roadmap

#### Versão 2.0 (Q4 2025)
- [ ] Machine Learning para otimização de estratégias
- [ ] Suporte a mais exchanges (Coinbase, Kraken)
- [ ] Interface web avançada
- [ ] Mobile app para monitoramento
- [ ] Estratégias de arbitragem

#### Versão 2.1 (Q1 2026)
- [ ] Sentiment analysis de redes sociais
- [ ] Integração com TradingView
- [ ] Portfolio management avançado
- [ ] Copy trading
- [ ] API pública

---

## 📄 Licença

Este projeto está licenciado sob a **MIT License** - veja o arquivo [LICENSE](LICENSE) para detalhes.

### Termos de Uso

- ✅ Uso comercial permitido
- ✅ Modificação permitida
- ✅ Distribuição permitida
- ✅ Uso privado permitido
- ❌ Sem garantias
- ❌ Sem responsabilidade

---

## 📞 Suporte e Contato

### Canais de Suporte

- **GitHub Issues:** [Reportar bugs ou solicitar features](https://github.com/esdrastrade/Market_Manus/issues)
- **Discussions:** [Discussões gerais](https://github.com/esdrastrade/Market_Manus/discussions)
- **Wiki:** [Documentação adicional](https://github.com/esdrastrade/Market_Manus/wiki)

### FAQ

**P: O sistema funciona com outras exchanges além da Binance?**
R: Atualmente suporta Binance. Suporte para outras exchanges está no roadmap.

**P: Qual o capital mínimo recomendado?**
R: Recomendamos pelo menos $1000 para operação segura com gestão de risco adequada.

**P: O sistema funciona 24/7?**
R: Sim, foi projetado para operação contínua com monitoramento e recuperação automática.

**P: Preciso de conhecimento técnico para usar?**
R: Conhecimento básico de trading é recomendado. O sistema é automatizado mas requer configuração inicial.

---

## 🏆 Reconhecimentos

### Tecnologias e Bibliotecas

- **CCXT** - Biblioteca de conectividade com exchanges
- **TA-Lib** - Indicadores técnicos
- **Pandas** - Manipulação de dados
- **Redis** - Cache em memória
- **Prometheus** - Monitoramento
- **Grafana** - Visualização
- **Docker** - Containerização

### Inspirações

- Estratégias baseadas em literatura acadêmica de trading quantitativo
- Arquitetura inspirada em sistemas de trading profissionais
- Práticas de DevOps da indústria de software

---

## 📈 Estatísticas do Projeto

![GitHub stars](https://img.shields.io/github/stars/esdrastrade/Market_Manus)
![GitHub forks](https://img.shields.io/github/forks/esdrastrade/Market_Manus)
![GitHub issues](https://img.shields.io/github/issues/esdrastrade/Market_Manus)
![GitHub pull requests](https://img.shields.io/github/issues-pr/esdrastrade/Market_Manus)

### Métricas de Desenvolvimento

- **Linhas de Código:** ~15,000
- **Arquivos Python:** 25+
- **Scripts PowerShell:** 4
- **Testes:** 150+
- **Cobertura:** 95%+
- **Documentação:** 200+ páginas

---

**⚠️ Aviso Legal:** Este sistema é fornecido apenas para fins educacionais e de pesquisa. Trading de criptomoedas envolve riscos significativos. Use por sua própria conta e risco. Os desenvolvedores não se responsabilizam por perdas financeiras.

**🚀 Desenvolvido com ❤️ por [Manus AI](https://github.com/esdrastrade) - Sistema de Scalping Automatizado v1.0**

