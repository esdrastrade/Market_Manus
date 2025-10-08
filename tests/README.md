# 🏭 Market Manus v2.1 - Sistema de Trading Automatizado

[![Version](https://img.shields.io/badge/version-2.1-blue.svg)](https://github.com/esdrastrade/Market_Manus)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![API](https://img.shields.io/badge/API-Binance.US-yellow.svg)](https://binance.us)

## 🎯 Visão Geral

Sistema profissional de trading automatizado integrando **Smart Money Concepts (SMC)** com **análise técnica clássica** através de um sistema de **confluência ponderado**. Desenvolvido para scalping e swing trading com dados reais da Binance.US via WebSocket streaming.

**Objetivo**: Atingir ~80% win rate através de alta confluência entre múltiplos detectores e filtros de regime de mercado.

### ✨ Principais Diferenciais v2.1

- **🔥 Live Streaming WebSocket**: Dados em tempo real via Binance.US com atualização contínua
- **🎨 Rich UI Live**: Interface profissional com 4 painéis atualizando em tempo real sem scroll spam
- **🧠 Smart Money Concepts**: 5 detectores SMC (BOS, CHoCH, Order Blocks, FVG, Liquidity Sweeps)
- **📊 Análise Técnica Clássica**: 7 estratégias (EMA, MACD, RSI, Bollinger, ADX, Stochastic, Fibonacci)
- **⚖️ Confluence Engine**: Sistema de scoring ponderado com pesos configuráveis
- **🛡️ Regime Filters**: ADX, ATR, BB Width para validação de condições de mercado
- **💰 Capital Management**: Position sizing, stop loss/take profit automáticos baseados em ATR
- **📈 Backtesting Robusto**: Engine completo com métricas de performance profissionais

---

## 🚀 Quick Start

### 1. Configuração Inicial

```bash
# Clone o repositório
git clone https://github.com/esdrastrade/Market_Manus.git
cd Market_Manus

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente (Read-Only para segurança)
# Windows PowerShell:
$env:BINANCE_API_KEY="sua_api_key_aqui"
$env:BINANCE_API_SECRET="sua_api_secret_aqui"

# Linux/Mac:
export BINANCE_API_KEY="sua_api_key_aqui"
export BINANCE_API_SECRET="sua_api_secret_aqui"
```

### 2. Primeiro Uso - Live Streaming

```bash
# Execute o sistema
python main.py

# Navegue pelo menu:
# 7️⃣  Executar Confluência em Tempo Real (WebSocket)
# 📊 Escolha: ETH/USDT
# ⏱️  Timeframe: 1 minuto
# 📖 Pressione ENTER para iniciar

# Você verá:
# 🔴 LIVE STREAMING com 4 painéis atualizando em tempo real
# 💰 Preço atual + variação desde última mudança de estado
# 🔍 Confluência: BUY/SELL/HOLD com confidence score
# 📊 Histórico das últimas 5 mudanças de estado
```

---

## 📊 Funcionalidades Principais

### 🔥 Live Streaming WebSocket (NOVO v2.1)

Sistema de streaming em tempo real com arquitetura assíncrona:

**Características**:
- ✅ WebSocket da Binance.US com reconexão automática
- ✅ Rich UI com 4 painéis live (Status, Preço, Confluência, Eventos)
- ✅ Atualização contínua in-place sem scroll spam
- ✅ Bootstrap automático com dados históricos antes de streaming
- ✅ Pipeline assíncrono com Queue e AsyncIO
- ✅ Proteção contra rate limits com controle de mensagens

**Como usar**:
```
Menu Principal → Opção 7 → Escolha ativo → Escolha timeframe → ENTER
```

**Painéis exibidos**:
1. **Status Header**: Provider, símbolo, mensagens recebidas/processadas, reconexões
2. **Preço Atual**: Preço live + variação desde última mudança de estado
3. **Confluência**: Estado atual (↑ BUY, ↓ SELL, • HOLD) + score + top 3 razões
4. **Últimas Mudanças**: Histórico das 5 últimas transições de estado com timestamp

---

### 🧠 Smart Money Concepts (SMC)

Sistema de detecção automática de padrões institucionais:

| Detector | Descrição | Peso Padrão | Uso |
|----------|-----------|-------------|-----|
| **BOS** (Break of Structure) | Quebra de estrutura confirmando continuação de tendência | 1.5x | Entradas pró-tendência |
| **CHoCH** (Change of Character) | Mudança de caráter sinalizando reversão | 1.8x | Reversões de alta probabilidade |
| **Order Blocks** | Zonas de consolidação institucional | 1.3x | Níveis de entrada/stop loss |
| **FVG** (Fair Value Gap) | Gaps de desequilíbrio de preço | 1.2x | Zonas de preenchimento |
| **Liquidity Sweep** | Varredura de stops antes de reversão (retail trap) | 1.6x | Reversões contra varejo |

**Parâmetros configuráveis** (`config/confluence.yaml`):
```yaml
smc:
  min_displacement: 0.001   # 0.1% mínimo para BOS
  min_ob_range: 0          # Range mínimo Order Block
  body_ratio: 0.5          # Ratio corpo/sombra para Sweep
```

---

### 📊 Análise Técnica Clássica

7 estratégias profissionais com parâmetros otimizáveis:

| Estratégia | Descrição | Peso Padrão | Sinal |
|------------|-----------|-------------|-------|
| **EMA Crossover** | Cruzamento de médias móveis (9/21) | 1.0x | Tendência |
| **MACD** | Momentum e divergências | 1.2x | Momentum |
| **RSI Mean Reversion** | Sobrecompra/sobrevenda (30/70) | 0.9x | Reversão |
| **Bollinger Bands** | Volatilidade e breakouts | 1.1x | Volatilidade |
| **ADX Trend Strength** | Força de tendência | 1.4x | Filtro de tendência |
| **Stochastic** | Oscillator de momentum | 0.8x | Timing de entrada |
| **Fibonacci** | Retração automática | 0.7x | Níveis de suporte |

**Parâmetros configuráveis** (`config/confluence.yaml`):
```yaml
ema:
  fast_period: 9
  slow_period: 21

rsi:
  period: 14
  oversold: 30
  overbought: 70

macd:
  fast: 12
  slow: 26
  signal: 9
```

---

### ⚖️ Confluence Engine

Sistema de scoring ponderado que combina SMC + Clássicos:

**Como funciona**:
1. **Coleta sinais** de todos os 12 detectores (5 SMC + 7 Clássicos)
2. **Aplica pesos** individuais configurados em `confluence.yaml`
3. **Calcula score** = Σ (sinal_direção × peso × confidence)
4. **Aplica filtros de regime**:
   - ADX < 20 → Rejeita (tendência fraca)
   - ATR < 0.0001 → Rejeita (volatilidade baixa)
   - BB Width < 0.01 → Rejeita (mercado travado)
5. **Penaliza conflitos**: Se BUY e SELL simultâneos, score × 0.7
6. **Decisão final**:
   - Score > 0.5 → **BUY**
   - Score < -0.5 → **SELL**
   - Caso contrário → **HOLD**

**Thresholds configuráveis**:
```yaml
regime:
  buy_threshold: 0.5
  sell_threshold: -0.5
  conflict_penalty: 0.3
  adx_min: 20
  adx_max: 70
  atr_min: 0.0001
  bb_width_min: 0.01
```

---

### 🔬 Strategy Lab Professional V6

Interface interativa para backtesting e análise:

**Funcionalidades**:
- ✅ **Asset Selection**: BTC/USDT, ETH/USDT, SOL/USDT + personalização
- ✅ **Strategy Configuration**: Configure individualmente cada estratégia
- ✅ **Timeframe Selection**: 1m, 5m, 15m, 1h, 4h
- ✅ **Period Selection**: Datas customizadas para backtesting histórico
- ✅ **Real-Time Test**: Teste com dados live da Binance.US
- ✅ **Historical Backtest**: Simulação em dados históricos
- ✅ **View Results**: Dashboard detalhado de performance
- ✅ **Export Results**: CSV, JSON, TXT para análise externa

**Métricas calculadas**:
- Total Return, Sharpe Ratio, Max Drawdown
- Win Rate, Profit Factor, Average Trade P&L
- Trade Duration, Exit Reasons
- Equity Curve, Drawdown Chart

---

### 💰 Capital Management

Sistema de gestão de risco automatizado:

**Position Sizing**:
```python
position_size = capital × position_size_pct  # Default: 1%
max_position = capital × max_position_size   # Default: 2%
```

**Stop Loss / Take Profit (ATR-based)**:
```python
stop_loss = entry_price - (1.5 × ATR)     # 1.5 ATR abaixo
take_profit_1 = entry_price + (2.5 × ATR) # 2.5 ATR acima (50% exit)
take_profit_2 = FVG_edge                  # Borda do FVG (50% exit)
```

**Break-Even Automático**:
- Move stop para BE após 1.5 ATR de lucro
- Configurable em `config/confluence.yaml`

**Drawdown Protection**:
- Pausa automática se perda diária > 5%
- Reset no novo dia de trading

---

## ⏰ Timeframes Suportados

```
1m    → Scalping ultra-rápido (alta frequência)
5m    → Scalping tradicional
15m   → Swing trading curto
1h    → Análise intraday
4h    → Swing trading longo
1d    → Análise de tendência macro
```

**Recomendações**:
- **Scalping (1m-5m)**: Use ADX > 25 + alta liquidez (BTC, ETH)
- **Swing (15m-4h)**: ADX > 20 + múltiplos FVGs
- **Tendência (1d)**: Foco em BOS + CHoCH confirmados

---

## 📈 Backtesting Engine

Sistema completo de backtesting com gestão de risco:

**Características**:
- ✅ Simulação por candle com slippage e comissões
- ✅ Stop Loss / Take Profit dinâmicos (ATR-based)
- ✅ Position sizing baseado em capital atual
- ✅ Proteção de drawdown diário
- ✅ Exit reasons tracking (SL, TP, Signal Reversal)
- ✅ Equity curve com timestamps

**Como usar**:
```bash
# Menu Principal → Option 1 (Strategy Lab Professional V6)
# → Option 5 (Run Historical Backtest)
# Escolha: BTC/USDT, 1h, 2025-01-01 a 2025-03-01
```

**Métricas exportadas**:
```python
{
  "total_return": 15.7,        # %
  "sharpe_ratio": 2.34,
  "max_drawdown": -8.2,        # %
  "win_rate": 68.5,            # %
  "profit_factor": 2.1,
  "avg_trade": 1.2,            # %
  "total_trades": 127,
  "winning_trades": 87,
  "losing_trades": 40
}
```

---

## 🛠️ Configuração Avançada

### 📝 Arquivo `config/confluence.yaml`

Controle total sobre pesos, thresholds e regras:

```yaml
# Habilitar/desabilitar grupos
use_smc: true
use_classic: true

# Pesos por detector (ajuste para otimizar win rate)
weights:
  SMC:BOS: 1.5
  SMC:CHoCH: 1.8
  SMC:OB: 1.3
  SMC:FVG: 1.2
  SMC:SWEEP: 1.6
  CLASSIC:EMA: 1.0
  CLASSIC:MACD: 1.2
  CLASSIC:RSI: 0.9
  CLASSIC:BB: 1.1
  CLASSIC:ADX: 1.4
  CLASSIC:STOCH: 0.8
  CLASSIC:FIB: 0.7

# Regime filters (críticos para win rate)
regime:
  buy_threshold: 0.5
  sell_threshold: -0.5
  conflict_penalty: 0.3
  adx_min: 20
  adx_max: 70
  atr_min: 0.0001
  bb_width_min: 0.01

# Risk management
risk_management:
  position_size_pct: 0.01
  max_position_size: 0.02
  stop_loss:
    method: "ATR"
    multiplier: 1.5
  take_profit:
    tp1:
      method: "ATR"
      multiplier: 2.5
      exit_pct: 50
    tp2:
      method: "FVG_EDGE"
      exit_pct: 50
```

---

## 🎮 Interface do Sistema

### Menu Principal

```
🏭 MARKET MANUS - MENU PRINCIPAL V6
============================================================
💰 RESUMO FINANCEIRO:
   💵 Capital atual: $100.00
   📊 Position size: $2.00
   📈 P&L total: $+15.30 (+15.3%)
   🎯 Total trades: 42 | Win Rate: 71.4%
   🌐 Status API: 🟢 Online

🎯 MÓDULOS PRINCIPAIS:
   1️⃣  Strategy Lab Professional V6 (8 estratégias)
   2️⃣  Confluence Mode (Sistema de confluência)

🤖 RECURSOS AVANÇADOS:
   3️⃣  Assistente IA (Semantic Kernel)

🔥 CONFLUÊNCIA SMC + CLÁSSICOS:
   7️⃣  Executar Confluência em Tempo Real (WebSocket Live)

⚙️ CONFIGURAÇÕES:
   4️⃣  Capital Dashboard
   5️⃣  Connectivity Status
   6️⃣  Settings

   0️⃣  Sair do sistema
```

### Live Streaming UI (Opção 7)

```
┌─────────────────────────────────────────────────────────────┐
│ 🔴 LIVE STREAMING                                          │
│ Provider: Binance.US │ ETHUSDT │ 1m                       │
│ Msgs: 1,234 recv │ 156 proc │ Reconnections: 0           │
└─────────────────────────────────────────────────────────────┘

┌─ 💰 Preço Atual ──────┐  ┌─ 🔍 Confluência ───────────┐
│ $2,347.82             │  │ Estado: ↑ BUY              │
│ +$12.40 desde mudança │  │ Confidence: 0.78           │
│                       │  │ Score: 0.65                │
│                       │  │                            │
│                       │  │ Top Razões:                │
│                       │  │ • SMC:BOS confirmado       │
│                       │  │ • ADX > 25 (tendência)     │
│                       │  │ • EMA golden cross         │
└───────────────────────┘  └────────────────────────────┘

┌─ 📊 Últimas Mudanças ────────────────────────────────────┐
│ 14:23:45  ↑ BUY   $2,347.82  Conf: 0.78  Score: 0.65   │
│ 14:21:30  • HOLD  $2,335.42  Conf: 0.45  Score: 0.32   │
│ 14:18:12  ↓ SELL  $2,328.10  Conf: 0.82  Score: -0.71  │
│ 14:15:05  • HOLD  $2,340.55  Conf: 0.38  Score: -0.15  │
│ 14:12:48  ↑ BUY   $2,352.20  Conf: 0.65  Score: 0.58   │
└──────────────────────────────────────────────────────────┘

[Atualização contínua | Pressione CTRL+C para parar]
```

---

## 🎯 Roadmap - Caminho para ~80% Win Rate

### ✅ Implementado (v2.1)
- [x] WebSocket streaming com Binance.US
- [x] Rich UI Live com 4 painéis
- [x] 5 detectores SMC (BOS, CHoCH, OB, FVG, SWEEP)
- [x] 7 estratégias clássicas (EMA, MACD, RSI, BB, ADX, STOCH, FIB)
- [x] Confluence engine com pesos configuráveis
- [x] Regime filters (ADX, ATR, BB Width)
- [x] Backtesting com ATR-based SL/TP
- [x] Capital management automático

### 🚀 Próximas Melhorias (Prioritárias)

#### **Fase 1: Otimização de Win Rate (2-3 semanas)**
- [ ] **Walk-Forward Validation**: Validação rolling para evitar overfitting
- [ ] **Métricas Avançadas**: Signal Quality Score, False Positive Rate, Avg Holding Time
- [ ] **Trade Journal Automático**: Logging detalhado com classificação de losses
- [ ] **Slippage & Spread Reais**: Backtesting mais realista com bid/ask spreads

#### **Fase 2: Adaptação Dinâmica (3-4 semanas)**
- [ ] **Pesos Dinâmicos via ML**: Ajuste automático baseado em performance recente
- [ ] **Market Regime Classifier**: Trending vs Range-bound vs High Volatility
- [ ] **Context Filters**: Horário de mercado, correlação entre ativos, news events
- [ ] **Exit Strategy Inteligente**: Trailing stops em FVG edges, time-based exits

#### **Fase 3: Validação e Monitoramento (2-3 semanas)**
- [ ] **Dashboard Web**: Interface gráfica com charts interativos
- [ ] **Performance Heatmaps**: Win rate por hora/dia/detector
- [ ] **Alertas em Tempo Real**: Telegram/Discord notifications para sinais
- [ ] **Paper Trading Extendido**: 30 dias de simulação antes de live

#### **Fase 4: Trading Automatizado (4-6 semanas)**
- [ ] **Order Execution Engine**: Integração com Binance.US orders API
- [ ] **Multi-Symbol Trading**: Gestão de múltiplos pares simultaneamente
- [ ] **Portfolio Rebalancing**: Alocação dinâmica entre ativos
- [ ] **Risk Management Avançado**: Correlation-based position sizing

---

## 📚 Estrutura do Projeto

```
Market_Manus/
├── main.py                                    # Entry point
├── README.md                                  # Documentação (este arquivo)
├── requirements.txt                           # Dependências Python
├── confluence_config_DOWNLOAD_ME.yaml         # Template de configuração
│
├── config/
│   ├── confluence.yaml                        # Configuração de confluência
│   ├── capital_config.json                    # Configuração de capital
│   └── settings.json                          # Settings gerais
│
├── market_manus/
│   ├── __init__.py
│   │
│   ├── cli/
│   │   ├── market_manus_cli_complete_final.py # CLI principal
│   │   ├── STRATEGY_LAB_PROFESSIONAL_V6.py    # Strategy Lab UI
│   │   └── live_view.py                       # Rich UI Live (NOVO v2.1)
│   │
│   ├── data_providers/
│   │   ├── binance_data_provider.py           # REST API Binance.US
│   │   └── market_data_ws.py                  # WebSocket provider (NOVO v2.1)
│   │
│   ├── engines/
│   │   └── stream_runtime.py                  # Async pipeline (NOVO v2.1)
│   │
│   ├── strategies/
│   │   ├── classic_analysis.py                # 7 estratégias clássicas
│   │   └── smc/
│   │       └── patterns.py                    # 5 detectores SMC + ConfluenceEngine
│   │
│   ├── backtest/
│   │   ├── confluence_realtime.py             # RealTimeConfluenceEngine
│   │   └── confluence_backtester.py           # Backtesting engine
│   │
│   ├── agents/
│   │   ├── backtesting_agent_v5.py            # Agente de backtesting
│   │   └── semantic_kernel_agent.py           # Agente de IA
│   │
│   ├── capital/
│   │   └── capital_manager.py                 # Gestão de capital
│   │
│   ├── core/
│   │   └── signal.py                          # Dataclass Signal padronizado
│   │
│   └── strategy_lab/
│       └── assets_manager.py                  # Gerenciador de ativos
│
├── logs/                                      # Logs do sistema
├── reports/                                   # Relatórios exportados
└── tests/                                     # Testes unitários (futuro)
```

---

## 🔒 Segurança e API

### 🛡️ Configuração Segura

**Read-Only Mode** (Recomendado para início):
```bash
# API keys read-only da Binance.US (sem permissão de trading)
# Configure permissions no dashboard: ✅ Read Info, ❌ Enable Trading
BINANCE_API_KEY=your_readonly_key
BINANCE_API_SECRET=your_readonly_secret
```

**Testnet** (Para testes sem risco):
```bash
# Use Binance Testnet para simular trading
# https://testnet.binance.vision/
BINANCE_TESTNET=true
```

### 🔐 Proteções Implementadas

- ✅ **Read-Only API Keys**: Sistema funciona sem permissões de trading
- ✅ **Rate Limiting**: Respeita limites da Binance.US com controle de requisições
- ✅ **Message Control**: Controle de taxa de mensagens no WebSocket
- ✅ **Automatic Reconnection**: Reconexão automática em caso de desconexão
- ✅ **Paper Trading Mode**: Simulação sem execução real de ordens
- ✅ **Drawdown Protection**: Pausa automática em perdas excessivas
- ✅ **Position Limits**: Máximo 2% do capital por posição

---

## 🤝 Contribuição

### Como Contribuir

1. Fork o projeto
2. Crie uma branch para sua feature:
   ```bash
   git checkout -b feature/MelhoriaIncrivel
   ```
3. Commit suas mudanças:
   ```bash
   git commit -m 'feat: Adiciona otimizador de pesos via ML'
   ```
4. Push para a branch:
   ```bash
   git push origin feature/MelhoriaIncrivel
   ```
5. Abra um Pull Request

### Áreas Prioritárias para Contribuição

- 🔬 **Backtesting**: Walk-forward validation, slippage realista
- 🧠 **Machine Learning**: Peso dinâmico, regime classification
- 📊 **Visualização**: Dashboard web, heatmaps de performance
- 🤖 **Automação**: Order execution, multi-symbol trading
- 📝 **Documentação**: Tutoriais, exemplos, tradução

---

## 📧 Contato e Suporte

- **GitHub**: [@esdrastrade](https://github.com/esdrastrade)
- **Email**: esdrastrade@gmail.com
- **Issues**: [GitHub Issues](https://github.com/esdrastrade/Market_Manus/issues)
- **Discussions**: [GitHub Discussions](https://github.com/esdrastrade/Market_Manus/discussions)

---

## ⚠️ Disclaimer Importante

**AVISO LEGAL**: Este software é fornecido **apenas para fins educacionais e de pesquisa**.

### ⚠️ Riscos do Trading de Criptomoedas:

- ❌ **Alta volatilidade**: Preços podem variar drasticamente em minutos
- ❌ **Perda total**: Você pode perder 100% do capital investido
- ❌ **Sem garantias**: Nenhum sistema garante lucros consistentes
- ❌ **Bugs e falhas**: Software pode ter bugs que causem perdas
- ❌ **Market risk**: Condições de mercado imprevisíveis

### ✅ Recomendações de Segurança:

1. **Teste extensivamente** com dados históricos antes de live trading
2. **Use API read-only** para monitoramento sem risco
3. **Comece com capital pequeno** que você pode perder 100%
4. **Paper trading primeiro**: Simule por 30+ dias antes de usar dinheiro real
5. **Nunca invista dinheiro** que você não pode perder
6. **Consulte profissionais**: Considere consultar um consultor financeiro

### 📜 Isenção de Responsabilidade:

Os desenvolvedores **não se responsabilizam** por:
- Perdas financeiras decorrentes do uso deste software
- Bugs, erros ou falhas no sistema
- Decisões de trading baseadas nos sinais gerados
- Problemas com APIs de terceiros (Binance.US, etc.)

**USE POR SUA PRÓPRIA CONTA E RISCO.**

---

## 📄 Licença

Este projeto está licenciado sob a **Licença MIT** - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

<div align="center">

### 🏭 Market Manus v2.1 - Professional Trading System

*Desenvolvido com ❤️ para a comunidade de trading algorítmico*

**🔥 Smart Money Concepts + 📊 Análise Técnica Clássica = 🎯 Alta Probabilidade**

[![GitHub stars](https://img.shields.io/github/stars/esdrastrade/Market_Manus?style=social)](https://github.com/esdrastrade/Market_Manus/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/esdrastrade/Market_Manus?style=social)](https://github.com/esdrastrade/Market_Manus/network)
[![GitHub issues](https://img.shields.io/github/issues/esdrastrade/Market_Manus)](https://github.com/esdrastrade/Market_Manus/issues)

**Last Updated**: October 2025

</div>
