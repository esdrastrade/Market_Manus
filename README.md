# Sistema de Scalping Automatizado

**Autor:** Manus AI  
**Versão:** 1.0  
**Data:** 17 de Julho de 2025  

## Visão Geral

Sistema completo de trading algorítmico para scalping em criptomoedas, utilizando agentes Python coordenados por scripts PowerShell, com versionamento automático no GitHub e sugestões de melhorias para implementação manual via Neovim.

## Características Principais

- 🤖 **Agentes Python Especializados**: 6 agentes com responsabilidades específicas
- ⚡ **Estratégias de Scalping**: EMA Triple, Bollinger+RSI, Volume Breakout
- 🛡️ **Gestão de Risco Avançada**: Position sizing dinâmico e controle de drawdown
- 📊 **Monitoramento em Tempo Real**: Dashboard interativo no terminal
- 🔄 **Melhoria Contínua**: Sugestões automáticas de otimização
- 📝 **Versionamento Automático**: Commits automáticos e backup no GitHub

## Arquitetura

### Agentes Python

- **MarketAnalysisAgent**: Análise OHLC e geração de sinais (5 min)
- **RiskManagementAgent**: Monitoramento de riscos (1 min)
- **NotificationAgent**: Alertas e relatórios (event-driven)
- **PerformanceAgent**: Métricas e otimização (6 horas)
- **BacktestingAgent**: Validação de estratégias (manual)
- **OrchestratorAgent**: Coordenação geral (contínuo)

### Scripts PowerShell

- **deploy.ps1**: Deployment e inicialização
- **monitor.ps1**: Monitoramento contínuo com dashboard
- **backup.ps1**: Backup e versionamento
- **optimize.ps1**: Aplicação de melhorias

## Estrutura do Projeto

```
scalping-trading-system/
├── agents/                 # Agentes Python
├── config/                 # Arquivos de configuração
├── scripts/                # Scripts PowerShell
├── data/                   # Dados e logs
│   ├── historical/         # Dados históricos
│   ├── logs/              # Logs do sistema
│   ├── reports/           # Relatórios HTML
│   ├── signals/           # Sinais de trading
│   ├── metrics/           # Métricas de performance
│   ├── alerts/            # Alertas de risco
│   └── suggestions/       # Sugestões de melhoria
├── tests/                 # Testes unitários e integração
├── docs/                  # Documentação
└── requirements.txt       # Dependências Python
```

## Instalação Rápida

### Pré-requisitos

- Python 3.11+
- PowerShell 7+
- Git
- Windows Terminal (recomendado)
- Neovim (para implementar sugestões)

### Setup

1. **Clone o repositório**:
```bash
git clone https://github.com/esdrastrade/Market_Manus.git
cd Market_Manus
```

2. **Execute o deployment**:
```powershell
.\scripts\deploy.ps1 -Environment development
```

3. **Inicie o monitoramento**:
```powershell
.\scripts\monitor.ps1 -Dashboard
```

## Configuração

### Configuração Básica

Edite `config/trading_config.json`:

```json
{
  "trading": {
    "symbols": ["BTC/USDT", "ETH/USDT"],
    "timeframe": "5m",
    "risk_per_trade": 0.02,
    "max_drawdown": 0.10
  },
  "strategies": {
    "ema_triple": {"periods": [8, 13, 21], "weight": 0.4},
    "bollinger_rsi": {"bb_period": 20, "rsi_period": 14, "weight": 0.4},
    "breakout": {"volume_threshold": 1.5, "weight": 0.2}
  }
}
```

### Configuração de Risco

Edite `config/risk_parameters.json`:

```json
{
  "max_drawdown": 0.10,
  "risk_per_trade": 0.02,
  "stop_loss_percentage": 0.005,
  "take_profit_percentage": 0.010,
  "max_positions": 3
}
```

## Uso

### Comandos Principais

```powershell
# Deployment completo
.\scripts\deploy.ps1 -Environment production

# Monitoramento com dashboard
.\scripts\monitor.ps1 -Dashboard -RefreshInterval 30

# Verificar sugestões de melhoria
.\scripts\monitor.ps1 -CheckSuggestions

# Aplicar otimizações automaticamente
.\scripts\optimize.ps1 -AutoApply -BacktestFirst

# Backup completo
.\scripts\backup.ps1 -IncludeData -UploadToGitHub
```

### Implementação Manual de Sugestões

Quando os agentes geram sugestões de melhoria:

1. Execute `.\scripts\monitor.ps1 -CheckSuggestions`
2. Veja as sugestões com arquivos e linhas específicas
3. Use Neovim para implementar: `nvim config/trading_config.json +8`
4. Teste com backtest: `python agents/backtesting_agent.py`

## Estratégias de Trading

### EMA Triple Crossover (40% peso)

Alinhamento de médias móveis exponenciais:
- **Compra**: EMA8 > EMA13 > EMA21
- **Venda**: EMA8 < EMA13 < EMA21

### Bollinger Bands + RSI (40% peso)

Sobrecompra/sobrevenda confirmada:
- **Compra**: Preço < 10% da faixa BB + RSI < 30
- **Venda**: Preço > 90% da faixa BB + RSI > 70

### Volume Breakout (20% peso)

Breakouts confirmados por volume:
- **Compra/Venda**: Rompimento + Volume > 1.5x média

## Gestão de Risco

### Position Sizing Dinâmico

```
Position Size = Account Balance × Risk Per Trade × Signal Confidence × Drawdown Adjustment
```

### Controles de Drawdown

- **5%**: Reduz position sizing em 50%
- **8%**: Pausa trading automático
- **10%**: Shutdown do sistema

### Stop Loss Dinâmico

- **Base**: 0.3% - 0.5% do preço
- **Ajuste por volatilidade**: ±20% baseado no ATR
- **Trailing**: Ativado após 0.2% de lucro

## Monitoramento

### Dashboard Terminal

```
╔══════════════════════════════════════════════════════════════╗
║                    SCALPING SYSTEM MONITOR                  ║
║                    2025-07-17 15:30:00                      ║
╚══════════════════════════════════════════════════════════════╝

🤖 STATUS DOS AGENTES:
   🟢 MarketAnalysisAgent
   🟢 RiskManagementAgent
   🟢 PerformanceAgent
   🟢 Orchestrator

📊 MÉTRICAS ATUAIS:
   💰 P&L Atual: $1,250.75
   📈 Win Rate: 62%
   📉 Drawdown: 3.2%
   🔄 Trades Hoje: 45

💡 SUGESTÕES PENDENTES:
   🔧 MarketAnalysisAgent: Ajustar RSI para 25 (win rate baixo)
   📁 Arquivo: config/trading_config.json
   ⌨️  Editar: nvim config/trading_config.json +8
```

### Métricas de Performance

- **Win Rate**: Percentual de trades vencedores
- **Profit Factor**: Relação lucro/prejuízo
- **Sharpe Ratio**: Retorno ajustado ao risco
- **Max Drawdown**: Maior perda consecutiva
- **Avg Trade Duration**: Duração média dos trades

## Segurança

### Proteção de Dados

- API keys em variáveis de ambiente
- Logs sanitizados (sem dados financeiros)
- Backup com criptografia AES-256
- Auditoria completa de operações

### Failsafe Mechanisms

- Circuit breakers para condições anômalas
- Shutdown automático em perdas excessivas
- Validação de sanidade em inputs
- Rollback automático de mudanças problemáticas

## Troubleshooting

### Problemas Comuns

**Agente não está rodando**:
```powershell
# Verificar scheduled tasks
Get-ScheduledTask -TaskName "Scalping*"

# Reiniciar agente específico
.\scripts\deploy.ps1 -Environment development
```

**Sem sinais sendo gerados**:
```powershell
# Verificar logs
Get-Content data/logs/agents.log -Tail 50

# Testar agente manualmente
python agents/market_analysis_agent.py
```

**Performance baixa**:
```powershell
# Verificar sugestões
.\scripts\monitor.ps1 -CheckSuggestions

# Executar backtest
python agents/backtesting_agent.py
```

## Desenvolvimento

### Adicionando Nova Estratégia

1. Edite `agents/market_analysis_agent.py`
2. Implemente método `calculate_new_strategy()`
3. Adicione peso em `config/trading_config.json`
4. Execute testes: `python -m pytest tests/`

### Criando Novo Agente

1. Herde de `BaseAgent` em `agents/base_agent.py`
2. Implemente métodos obrigatórios
3. Adicione scheduled task em `scripts/deploy.ps1`
4. Configure monitoramento em `scripts/monitor.ps1`

## Contribuição

1. Fork o repositório
2. Crie branch para feature: `git checkout -b feature/nova-estrategia`
3. Commit mudanças: `git commit -m "feat: adicionar estratégia MACD"`
4. Push para branch: `git push origin feature/nova-estrategia`
5. Abra Pull Request

## Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Suporte

- **Issues**: [GitHub Issues](https://github.com/esdrastrade/Market_Manus/issues)
- **Documentação**: [Wiki](https://github.com/esdrastrade/Market_Manus/wiki)
- **Discussões**: [GitHub Discussions](https://github.com/esdrastrade/Market_Manus/discussions)

## Roadmap

- [ ] Integração com múltiplas exchanges
- [ ] Machine Learning para otimização de parâmetros
- [ ] Interface web para monitoramento
- [ ] Suporte para outros ativos (forex, ações)
- [ ] Backtesting com dados tick-by-tick
- [ ] Otimização de portfolio multi-ativo

---

**⚠️ Aviso de Risco**: Trading de criptomoedas envolve riscos significativos. Este software é fornecido "como está" sem garantias. Use apenas capital que você pode perder.

