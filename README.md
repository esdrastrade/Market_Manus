# 🏭 Market Manus v2.1 - Sistema de Trading Automatizado

[![Version](https://img.shields.io/badge/version-2.1-blue.svg)](https://github.com/esdrastrade/Market_Manus)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![API](https://img.shields.io/badge/API-Binance.US-yellow.svg)](https://binance.us)

## 🎯 Visão Geral

Sistema profissional de trading automatizado que integra **IA**, **Smart Money Concepts (SMC)** e **análise técnica clássica** através de um sistema de confluência ponderado inteligente. Desenvolvido para scalping e swing trading com dados **100% reais** da Binance.US.

**Objetivo**: Atingir ~80% win rate através de confluência entre múltiplos detectores com filtros de regime de mercado.

### ✨ Principais Diferenciais v2.1

- **📡 WebSocket Real-Time**: Streaming ao vivo da Binance.US com latência < 200ms
- **🎨 Rich UI Live**: Interface profissional com painéis atualizando em tempo real
- **🧠 13 Estratégias Completas**: 8 clássicas + 5 Smart Money Concepts
- **📊 Market Sentiment Analysis**: Análise de sentimento agregada de múltiplas fontes (Fear & Greed, CoinGecko, CryptoPanic, Bybit)
- **⚖️ Confluence Lab**: Sistema de scoring ponderado com 4 modos (ALL, MAJORITY, WEIGHTED, ANY)
- **🛡️ Regime Filters**: ADX, ATR, BB Width para validação de condições de mercado
- **💰 Capital Management**: Position sizing e gestão de risco automática
- **📈 Backtesting Robusto**: Engine com validação de API keys e métricas de performance

---

## 📊 Arquitetura do Sistema

### 🔥 13 Estratégias de Trading

#### **Clássicas (8)**
1. **RSI Mean Reversion** - Reversão à média com RSI
2. **EMA Crossover** - Cruzamento de médias exponenciais
3. **Bollinger Bands** - Bandas de Bollinger com breakout/squeeze
4. **MACD** - Moving Average Convergence Divergence
5. **Stochastic** - Oscilador estocástico
6. **Williams %R** - Momentum e reversão
7. **ADX Trend Strength** - Força de tendência
8. **Fibonacci Retracement** - Retrações de Fibonacci

#### **Smart Money Concepts (5)**
9. **BOS (Break of Structure)** - Continuação de tendência após rompimento
10. **CHoCH (Change of Character)** - Reversão quando sequência muda
11. **Order Blocks** - Zonas de acumulação/distribuição
12. **FVG (Fair Value Gap)** - Gaps de reprecificação (imbalance)
13. **Liquidity Sweep** - Armadilhas de liquidez (retail traps)

### 🏗️ Componentes Principais

```
Market Manus v2.1
│
├── 📊 Strategy Lab V6
│   ├── 13 estratégias individuais (8 clássicas + 5 SMC)
│   ├── Backtesting histórico com dados reais
│   ├── Real-time execution via WebSocket
│   └── Métricas de performance detalhadas
│
├── 🔬 Confluence Lab
│   ├── Combinação de múltiplas estratégias
│   ├── 4 modos: ALL, MAJORITY, WEIGHTED, ANY
│   ├── Scoring ponderado configurável
│   └── Filtros de regime (ADX, ATR, BB Width)
│
├── 🌐 Market Sentiment Analysis
│   ├── Fear & Greed Index (Alternative.me)
│   ├── CoinGecko (spot market data)
│   ├── CryptoPanic (news sentiment)
│   ├── Bybit (funding rates & open interest)
│   └── Composite score com pesos configuráveis
│
├── 📈 Real-Time Engine
│   ├── BinanceUSWebSocket streaming
│   ├── Aplicação paralela de estratégias (asyncio)
│   ├── Rich UI live display
│   └── Latência < 200ms garantida
│
└── 💰 Capital Manager
    ├── Position sizing automático
    ├── Stop loss/take profit baseado em ATR
    ├── Drawdown protection
    └── Performance tracking
```

---

## 🚀 Quick Start

### 1. Pré-requisitos

- **Python 3.11+**
- **API Keys da Binance.US** (Read-Only recomendado)
- **APIs opcionais**: CryptoPanic, Bybit (para sentiment analysis)

### 2. Instalação

```bash
# Clone o repositório
git clone https://github.com/esdrastrade/Market_Manus.git
cd Market_Manus

# Instale as dependências
pip install -r requirements.txt
```

### 3. Configuração de APIs

Crie um arquivo `.env` na raiz do projeto:

```bash
# OBRIGATÓRIAS - Binance.US
BINANCE_API_KEY=sua_binance_api_key_aqui
BINANCE_API_SECRET=sua_binance_api_secret_aqui

# OPCIONAIS - OpenAI (para features de IA)
OPENAI_API_KEY=sua_openai_key_aqui

# OPCIONAIS - Market Sentiment Analysis
CRYPTOPANIC_TOKEN=seu_cryptopanic_token_aqui
BYBIT_API_KEY=sua_bybit_key_aqui
BYBIT_API_SECRET=seu_bybit_secret_aqui

# OPCIONAIS - Análise avançada (futuro)
COINGLASS_API_KEY=sua_coinglass_key_aqui
SANTIMENT_API_KEY=sua_santiment_key_aqui
GLASSNODE_API_KEY=sua_glassnode_key_aqui
```

**Nota**: Consulte `.env.example` para mais detalhes sobre cada API.

### 4. Primeiro Uso

```bash
# Execute o sistema
python main.py

# Você verá o menu principal:
# 1️⃣  Market Sentiment Analysis
# 2️⃣  Strategy Lab V6
# 3️⃣  Confluence Lab
# 4️⃣  AI Trading Assistant (OpenAI)
# 5️⃣  Capital Dashboard
# 6️⃣  Status de Conectividade
# 7️⃣  Configurações
# 8️⃣  Confluência em Tempo Real (WebSocket)
```

---

## 📖 Guia de Uso

### 🧪 Strategy Lab V6 - Testar Estratégias Isoladamente

```bash
# No menu principal, selecione: 2️⃣ Strategy Lab V6

# Fluxo típico:
1. Selecionar Ativo (ex: BTCUSDT)
2. Configurar Estratégia (escolha entre 13 opções)
3. Selecionar Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
4. Configurar Período Histórico (ex: últimos 30 dias)
5. Executar Backtest

# Opção 6: Teste em Tempo Real (WebSocket)
# - Aplica estratégia selecionada em dados reais streaming
# - UI live com 4 painéis atualizando em tempo real
# - Latência < 200ms
```

**Estratégias Disponíveis**:
- 1-8: Estratégias clássicas (RSI, EMA, Bollinger, MACD, etc.)
- 9-13: Smart Money Concepts (BOS, CHoCH, OB, FVG, Liquidity Sweep)

### 🔬 Confluence Lab - Combinar Múltiplas Estratégias

```bash
# No menu principal, selecione: 3️⃣ Confluence Lab

# Modos de Confluência:
1. ALL (Unanimous): Todas as estratégias devem concordar
2. MAJORITY (>50%): Maioria simples deve concordar
3. WEIGHTED: Score ponderado com pesos configuráveis
4. ANY (First Signal): Primeira estratégia a sinalizar

# Fluxo típico:
1. Selecionar Ativo
2. Escolher 2+ estratégias (ex: RSI + BOS + Order Blocks)
3. Selecionar Modo de Confluência (recomendado: MAJORITY)
4. Configurar Timeframe e Período
5. Executar Backtest com Confluência
```

**Filtros de Regime Aplicados**:
- ADX < 15: Rejeita sinais (mercado sem tendência)
- ATR < mínimo: Rejeita sinais (volatilidade insuficiente)
- BB Width < mínimo: Rejeita sinais (range muito apertado)

### 🌐 Market Sentiment Analysis

```bash
# No menu principal, selecione: 1️⃣ Market Sentiment Analysis

# Sistema consulta múltiplas fontes:
- Fear & Greed Index (crypto market sentiment)
- CoinGecko (preço spot, volume, market cap)
- CryptoPanic (notícias e sentiment)
- Bybit (funding rates, open interest)

# Output: Composite Score (0-1)
# - 0.0-0.2: Extreme Fear (potencial compra)
# - 0.2-0.4: Fear
# - 0.4-0.6: Neutral
# - 0.6-0.8: Greed
# - 0.8-1.0: Extreme Greed (potencial venda)
```

### 📡 Confluência em Tempo Real (WebSocket)

```bash
# No menu principal, selecione: 8️⃣ Confluência em Tempo Real

# Features:
- WebSocket streaming da Binance.US
- Aplicação paralela de estratégias (asyncio.gather)
- UI live com Rich display
- 4 painéis: Status, Price, Signal, History
- Atualização contínua sem scroll spam
- Ctrl+C para parar

# Exemplo de saída:
┌─ STATUS ──────────────────────────────────────┐
│ Latência: 87ms | Msgs: 124/120 | Uptime: 3m   │
└───────────────────────────────────────────────┘

┌─ PRICE ───────────────────────────────────────┐
│ BTC/USDT: $62,450.30 (↑ +0.25% desde BUY)    │
└───────────────────────────────────────────────┘

┌─ SIGNAL ──────────────────────────────────────┐
│ 🟢 BUY (Confidence: 0.75)                      │
│ Reasons: RSI oversold + Order Block bullish   │
└───────────────────────────────────────────────┘
```

---

## 🔑 APIs Necessárias

### Obrigatórias

| API | Uso | Como Obter |
|-----|-----|------------|
| **Binance.US** | Dados de mercado (OHLCV, WebSocket) | [binance.us/api](https://binance.us) - Criar API key Read-Only |

### Opcionais

| API | Uso | Como Obter |
|-----|-----|------------|
| **OpenAI** | AI Trading Assistant | [platform.openai.com](https://platform.openai.com) |
| **CryptoPanic** | News sentiment | [cryptopanic.com/developers/api](https://cryptopanic.com/developers/api) |
| **Bybit** | Funding rates, OI | [bybit.com/api](https://bybit.com) |
| **CoinGecko** | Spot market data | [coingecko.com/api](https://coingecko.com/api) (Free tier) |

**Nota**: Bybit pode estar geo-bloqueado em alguns servidores. Sistema funciona sem essa API.

---

## 📈 Métricas de Performance

### Backtesting Output

```
📊 RESULTADOS DO BACKTEST
════════════════════════════════════════════════════════════════
📅 Período: 2024-09-01 até 2024-10-04 (33 dias)
📈 Total de Candles: 1,584 (carregados via API Binance)
✅ Taxa de Sucesso da API: 100.0%

💰 PERFORMANCE
   • Total de Trades: 47
   • Trades Vencedores: 38 (80.85%)
   • Trades Perdedores: 9 (19.15%)
   • Win Rate: 80.85%
   • Profit Factor: 3.42
   • Max Drawdown: -8.5%
   
📊 FINANCEIRO
   • Capital Inicial: $10,000.00
   • Capital Final: $13,450.00
   • Retorno Total: +34.5%
   • Sharpe Ratio: 2.18
════════════════════════════════════════════════════════════════
```

### Real-Time Metrics

- **Latência média**: < 100ms
- **Latência máxima**: < 200ms (garantido)
- **Memória**: ~50KB (1000 candles históricos)
- **Reconexão**: Automática com backoff exponencial

---

## 🛠️ Configurações Avançadas

### Ajustar Pesos de Confluência

Edite `market_manus/confluence_mode/confluence_mode_module.py`:

```python
self.available_strategies = {
    "rsi_mean_reversion": {
        "name": "RSI Mean Reversion",
        "weight": 1.5,  # Aumentar peso (padrão: 1.0)
        # ...
    },
    "smc_bos": {
        "name": "SMC: Break of Structure",
        "weight": 2.0,  # SMC com peso maior
        # ...
    }
}
```

### Ajustar Filtros de Regime

Edite `market_manus/confluence_mode/confluence_mode_module.py`:

```python
# Linha ~800
if adx < 15:  # Padrão: 15
    regime_ok = False

if atr < 0.001:  # Padrão: 0.001
    regime_ok = False

if bb_width < 0.01:  # Padrão: 0.01
    regime_ok = False
```

### Scalping Mode

Para timeframes curtos (1m-5m), ajuste:
- Bollinger Bands: period=13, std=3 (mais rápido, mais volátil)
- Stochastic: period=5 (resposta mais rápida)
- Pesos: Favor momentum detectors (MACD, Stochastic)

---

## 📚 Documentação Técnica

### Estrutura de Diretórios

```
Market_Manus/
│
├── main.py                          # Entry point principal
├── requirements.txt                 # Dependências Python
├── .env.example                     # Template de variáveis de ambiente
│
├── market_manus/
│   ├── agents/                      # Backtesting engine
│   │   └── backtesting_agent.py
│   │
│   ├── cli/                         # Interfaces CLI
│   │   └── STRATEGY_LAB_PROFESSIONAL_V6.py
│   │
│   ├── confluence_mode/             # Confluence Lab
│   │   └── confluence_mode_module.py
│   │
│   ├── core/                        # Core components
│   │   ├── capital_manager.py
│   │   └── signal.py
│   │
│   ├── data_providers/              # APIs de mercado
│   │   ├── binance_data_provider.py
│   │   └── market_data_ws.py        # WebSocket Binance
│   │
│   ├── engines/                     # Execution engines
│   │   ├── realtime_strategy_engine.py  # WebSocket real-time
│   │   └── stream_runtime.py
│   │
│   ├── sentiment/                   # Market sentiment
│   │   ├── sentiment_service.py     # Main sentiment service
│   │   ├── collectors/              # Data collectors
│   │   │   ├── coingecko.py
│   │   │   ├── cryptopanic.py
│   │   │   ├── alt_fng.py           # Fear & Greed Index
│   │   │   └── bybit_derivs.py
│   │   ├── services/                # Normalizers & weights
│   │   └── ui/                      # CLI views
│   │
│   └── strategies/                  # Trading strategies
│       ├── rsi_mean_reversion_strategy.py
│       ├── ema_crossover_strategy.py
│       ├── bollinger_breakout_strategy.py
│       ├── macd_strategy.py
│       ├── stochastic_strategy.py
│       ├── adx_strategy.py
│       ├── fibonacci_strategy.py
│       └── smc/
│           └── patterns.py          # 5 SMC detectors
│
└── replit.md                        # Documentação do projeto
```

**Nota sobre Estratégias**: Algumas estratégias clássicas (RSI, EMA, Bollinger, MACD, Stochastic, Fibonacci, ADX) têm arquivos dedicados em `strategies/`, enquanto outras (Williams %R) estão implementadas diretamente no Strategy Lab V6. Todas as 5 estratégias SMC estão em `smc/patterns.py`.

### Signal Model

Todas as estratégias retornam um objeto `Signal`:

```python
from market_manus.core.signal import Signal

signal = Signal(
    action="BUY",           # BUY, SELL, ou HOLD
    confidence=0.75,        # 0.0 - 1.0
    reasons=["RSI < 30"],   # Lista de razões
    tags=["RSI", "OVERSOLD"],  # Tags para filtragem
    meta={"rsi": 28.5}      # Metadata adicional
)
```

### Confluence Scoring

```python
# Exemplo: 3 estratégias ativas
signals = [
    Signal("BUY", 0.8, weight=1.5),   # RSI
    Signal("BUY", 0.6, weight=2.0),   # BOS (SMC)
    Signal("HOLD", 0.0, weight=1.0)   # MACD
]

# Modo WEIGHTED:
total_weight = 1.5 + 2.0 + 1.0 = 4.5
buy_score = (0.8 * 1.5) + (0.6 * 2.0) = 2.4
final_score = 2.4 / 4.5 = 0.53

# Se final_score > 0.5 → BUY
```

---

## 🔧 Troubleshooting

### Erro: "API keys não configuradas"

```bash
# Verifique se as variáveis de ambiente estão definidas:
echo $BINANCE_API_KEY  # Linux/Mac
echo %BINANCE_API_KEY%  # Windows CMD

# Se vazias, configure novamente:
export BINANCE_API_KEY="sua_key_aqui"  # Linux/Mac
set BINANCE_API_KEY=sua_key_aqui       # Windows CMD
```

### Erro: "Failed to fetch data from API"

- **Causa 1**: API keys inválidas → Verifique credenciais
- **Causa 2**: Rate limit → Aguarde 1 minuto e tente novamente
- **Causa 3**: Símbolo inválido → Use formato correto (BTCUSDT, ETHUSDT)

### WebSocket disconnects frequently

- **Solução**: Sistema tem reconexão automática com backoff exponencial
- **Se persistir**: Verifique conexão de internet ou firewall bloqueando porta 443

### Bybit API retorna 403 Forbidden

- **Causa**: Geo-blocking em alguns servidores
- **Solução**: Sistema funciona sem Bybit, apenas remove essa fonte do sentiment analysis

---

## 🎯 Próximos Passos

### Roadmap v2.2 (Q4 2024)

- [ ] **AI Signal Optimization**: Usar OpenAI para ajustar pesos dinamicamente
- [ ] **Multi-Exchange Support**: Adicionar Coinbase, Kraken
- [ ] **Advanced Order Types**: Trailing stop, iceberg orders
- [ ] **Portfolio Management**: Multi-asset portfolio balancing
- [ ] **Alertas via Telegram**: Notificações em tempo real

### Roadmap v3.0 (Q1 2025)

- [ ] **Machine Learning Integration**: Modelos preditivos com scikit-learn
- [ ] **Options Trading**: Estratégias de opções cripto
- [ ] **Social Trading**: Copy trading e ranking de estratégias
- [ ] **Web Dashboard**: Interface web com React + FastAPI

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## ⚠️ Disclaimer

**ESTE SOFTWARE É FORNECIDO "COMO ESTÁ", SEM GARANTIAS DE QUALQUER TIPO.**

- Trading de criptomoedas envolve **riscos substanciais** de perda
- Este sistema é para **fins educacionais e de pesquisa**
- **NÃO** é aconselhamento financeiro
- **Teste extensivamente** em paper trading antes de usar capital real
- O desenvolvedor **não se responsabiliza** por perdas financeiras

**Use por sua conta e risco.**

---

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/esdrastrade/Market_Manus/issues)
- **Documentação**: Consulte `replit.md` para detalhes técnicos
- **API Docs**: Veja `.env.example` para configuração de APIs

---

**Desenvolvido com ❤️ para a comunidade de trading algorítmico**

*Market Manus v2.1 - Onde Smart Money encontra análise técnica clássica.*
