# 🏭 Market Manus - Sistema de Trading Automatizado

[![Version](https://img.shields.io/badge/version-2.1-blue.svg)](https://github.com/esdrastrade/Market_Manus)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![API](https://img.shields.io/badge/API-Bybit-orange.svg)](https://bybit.com)

## 🎯 Visão Geral

Sistema profissional de trading automatizado com **IA integrada**, **análise técnica avançada** e **capital management** robusto. Desenvolvido para scalping e swing trading com dados reais da Bybit.

### ✨ Principais Diferenciais
- **📊 Strategy Lab Professional**: Testes com dados reais da API Bybit
- **🔄 Sistema de Confluência**: Combine RSI + EMA + Bollinger Bands + AI Agent
- **💰 Capital Management**: Proteção de drawdown e position sizing automático
- **⚡ Real Time vs Historical**: Análise comparativa para validação
- **🎯 7 Timeframes**: De 1 minuto a 1 dia para máxima flexibilidade

## 🚀 Quick Start

### 1. Configuração Inicial
```bash
# Clone o repositório
git clone https://github.com/esdrastrade/Market_Manus.git
cd Market_Manus

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
# Windows: Configurar BYBIT_API_KEY e BYBIT_API_SECRET nas variáveis de ambiente
```

### 2. Primeiro Uso
```bash
# Execute o sistema
python main.py

# Siga o fluxo:
# 1. Menu Principal → Strategy Lab Professional
# 2. Asset Selection → Escolha Bitcoin ou Ethereum
# 3. Strategy Configuration → Selecione EMA Crossover
# 4. Real Time Test → Veja análise em tempo real!
```

## 📊 Funcionalidades Principais

### 🔬 Strategy Lab Professional
- **Asset Selection**: 10 criptoativos com preços em tempo real
- **Strategy Configuration**: 4 estratégias configuráveis
- **Real Time Testing**: Análise com dados da Bybit por 30-60 segundos
- **Historical Data Testing**: Backtesting com períodos personalizados
- **Comparison Testing**: Validação de consistência

### 🎯 Sistema de Confluência
- **Modo ALL**: Todas as estratégias devem concordar
- **Modo MAJORITY**: Maioria das estratégias decide
- **Modo WEIGHTED**: Pesos personalizados para cada estratégia
- **Modo ANY**: Qualquer estratégia pode gerar sinal

### 💰 Capital Management
- **Position Sizing**: Automático baseado no capital configurado
- **Proteção de Drawdown**: Interrompe operações em perdas excessivas
- **Compound Interest**: Reinvestimento automático dos lucros
- **Dashboard Detalhado**: Acompanhamento em tempo real

## 📈 Indicadores Técnicos Disponíveis

### 🎯 Estratégias Implementadas
| Indicador | Descrição | Configurável |
|-----------|-----------|--------------|
| **RSI Mean Reversion** | Reversão à média com níveis de sobrecompra/sobrevenda | ✅ Período, Overbought, Oversold |
| **EMA Crossover** | Cruzamento de médias móveis exponenciais | ✅ EMA rápida, EMA lenta |
| **Bollinger Bands** | Bandas de volatilidade com breakouts | ✅ Período, Desvio padrão |
| **AI Agent** | Multi-armed bandit com aprendizado automático | ✅ Parâmetros de aprendizado |

### ⏰ Timeframes Suportados
```
1 minuto    → Scalping ultra-rápido
5 minutos   → Scalping tradicional
15 minutos  → Swing trading curto
30 minutos  → Swing trading médio
1 hora      → Análise intraday
4 horas     → Swing trading longo
1 dia       → Análise de tendência
```

## 🎮 Interface do Sistema

### 📱 Menu Principal
```
🏭 MARKET MANUS - SISTEMA DE TRADING AUTOMATIZADO
════════════════════════════════════════════════
💰 Capital Dashboard      → Visão detalhada do capital
🔬 Strategy Lab          → Análise profissional
🎯 Confluence Lab        → Combinar estratégias
📊 Simulate Trades       → Simulação de operações
📈 Performance Analysis  → Análise de performance
⚙️  Advanced Settings    → Configurações avançadas
```

### 🔬 Strategy Lab Interface
```
STRATEGY LAB PROFESSIONAL - ANÁLISE CONFIÁVEL
═══════════════════════════════════════════════
💰 Capital atual: $10,000.00
📊 Position size: $1,000.00 (10.0%)
📋 Ativo: BTCUSDT ($115,472.60)
🎯 Estratégia: EMA Crossover (12/26)
⏰ Timeframe: 5 minutos
```

## 📊 Exemplos de Uso

### 🎯 Teste de Estratégia Simples
```python
# 1. Selecionar Bitcoin
Asset: BTCUSDT
Price: $115,472.60
Volume: $207M (24h)

# 2. Configurar EMA Crossover
Fast EMA: 12 períodos
Slow EMA: 26 períodos
Timeframe: 5 minutos

# 3. Executar Real Time Test
Duration: 60 segundos
Signals: 8 detected
Strength: 73.2% average
```

### 🔄 Teste de Confluência
```python
# Configuração ALL mode
RSI: Oversold (28.3) → BUY ✅
EMA: Golden Cross → BUY ✅
Bollinger: Lower band bounce → BUY ✅

Result: STRONG BUY (95.8% confidence)
Position: $1,000 (10% of capital)
```

## 🛠️ Configuração Avançada

### 🔧 Parâmetros Customizáveis

#### RSI Mean Reversion
```python
period = 14          # Período de cálculo
overbought = 70      # Nível de sobrecompra
oversold = 30        # Nível de sobrevenda
```

#### EMA Crossover
```python
fast_ema = 12        # EMA rápida
slow_ema = 26        # EMA lenta
signal_threshold = 0.5  # Limiar de sinal
```

#### Bollinger Bands
```python
period = 20          # Período das bandas
std_dev = 2.0        # Desvio padrão
```

### 💰 Capital Management
```python
initial_capital = 10000    # Capital inicial
position_size = 0.10       # 10% por operação
max_drawdown = 0.50        # Máximo 50% de perda
compound_interest = True   # Reinvestir lucros
```

## 📈 Análise de Performance

### 📊 Métricas Disponíveis
- **Total Return**: Retorno total em %
- **Sharpe Ratio**: Relação risco/retorno
- **Max Drawdown**: Maior perda consecutiva
- **Win Rate**: Taxa de acerto
- **Profit Factor**: Relação lucro/prejuízo
- **Average Trade**: Resultado médio por trade

### 📋 Relatórios Exportáveis
- **CSV**: Dados brutos para análise
- **JSON**: Estrutura completa dos resultados
- **TXT**: Relatório formatado para leitura

## 🤖 Integração com IA

### 🧠 Multi-Armed Bandit
Sistema de aprendizado que otimiza automaticamente os parâmetros das estratégias baseado nos resultados históricos.

### 📚 Dados de Treinamento
- **Indicadores técnicos**: RSI, EMA, Bollinger
- **Dados de mercado**: Preço, volume, volatilidade
- **Contexto temporal**: Hora, dia, sessão de mercado
- **Resultados históricos**: Performance de cada configuração

## 🔒 Segurança e Risk Management

### 🛡️ Proteções Implementadas
- **Stop Loss automático**: Baseado na volatilidade
- **Position sizing dinâmico**: Ajustado ao capital atual
- **Drawdown protection**: Pausa automática em perdas excessivas
- **API rate limiting**: Respeita limites da Bybit

### 🔐 Configuração de API
```bash
# Variáveis de ambiente necessárias
BYBIT_API_KEY=sua_api_key_aqui
BYBIT_API_SECRET=sua_api_secret_aqui

# Testnet (recomendado para testes)
BYBIT_TESTNET=true
```

## 📚 Estrutura do Projeto

```
Market_Manus/
├── main.py                          # Ponto de entrada
├── README.md                        # Esta documentação
├── requirements.txt                 # Dependências Python
├── .env.example                     # Template de configuração
├── market_manus/
│   ├── __init__.py
│   ├── cli/
│   │   └── market_manus_cli_complete_final.py  # CLI principal
│   └── strategy_lab/
│       └── assets_manager.py        # Gerenciador de ativos
├── config/
│   ├── settings.json               # Configurações salvas
│   └── selected_assets.json        # Ativos selecionados
├── logs/                           # Logs do sistema
├── reports/                        # Relatórios exportados
└── tests/                          # Testes unitários
```

## 🎯 Roadmap

### 📅 Próximas Funcionalidades
- [ ] **Indicadores adicionais**: MACD, Stochastic, Williams %R, ADX
- [ ] **Deep Learning**: Redes neurais para predição de preços
- [ ] **Trading automatizado**: Execução automática de ordens
- [ ] **Dashboard web**: Interface gráfica via navegador
- [ ] **Múltiplas exchanges**: Binance, OKX, Coinbase
- [ ] **Análise de sentimento**: Integração com news e social media

### 🚀 Cronograma Estimado
- **Fase 1** (2-3 semanas): Indicadores adicionais
- **Fase 2** (3-4 semanas): Deep Learning básico
- **Fase 3** (2-3 semanas): Trading automatizado
- **Fase 4** (4-6 semanas): IA avançada e dashboard web

## 🤝 Contribuição

### 🛠️ Como Contribuir
1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### 📧 Contato
- **GitHub**: [@esdrastrade](https://github.com/esdrastrade)
- **Email**: esdrastrade@gmail.com

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## ⚠️ Disclaimer

**AVISO IMPORTANTE**: Este software é fornecido apenas para fins educacionais e de pesquisa. Trading de criptomoedas envolve riscos significativos e você pode perder todo o seu capital investido. Sempre:

- Use apenas capital que você pode perder
- Teste extensivamente antes de usar capital real
- Comece com valores pequenos
- Nunca invista mais do que pode perder
- Considere consultar um consultor financeiro

Os desenvolvedores não se responsabilizam por perdas financeiras decorrentes do uso deste software.

---

<div align="center">

**🏭 Market Manus v2.1 - Professional Trading System**

*Desenvolvido com ❤️ para a comunidade de trading*

[![GitHub stars](https://img.shields.io/github/stars/esdrastrade/Market_Manus?style=social)](https://github.com/esdrastrade/Market_Manus/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/esdrastrade/Market_Manus?style=social)](https://github.com/esdrastrade/Market_Manus/network)

</div>
#   M a r k e t   M a n u s   v 2 . 1   -   U p d a t e d   0 9 / 2 1 / 2 0 2 5   1 9 : 2 0 : 2 7  
 