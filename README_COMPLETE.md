# 🚀 Market Manus - Sistema de Trading Completo

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Bybit](https://img.shields.io/badge/Bybit-API-orange)](https://bybit.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**Sistema profissional de trading com Strategy Lab, Confluence Mode e gestão de capital integrada.**

## 🎯 Funcionalidades Principais

### 🧪 Strategy Lab
- **Testes individuais** de estratégias com dados reais da Bybit
- **Backtesting honesto** com cálculo correto de P&L e fees
- **Otimização de parâmetros** (em desenvolvimento)
- **Comparação de estratégias** lado a lado
- **Exportação de relatórios** detalhados

### 🎯 Confluence Mode
- **6 modos de confluência**: Unanimous, Majority, Any, Weighted, Consensus, Custom
- **Multi-seleção de estratégias** para análise combinada
- **Ajuste de força mínima** para filtrar sinais fracos
- **Análise em tempo real** (em desenvolvimento)
- **Backtesting de confluência** com métricas avançadas

### 💰 Capital Management
- **Tracking automático** de P&L e ROI
- **Proteção contra drawdown** (50% máximo)
- **Position sizing inteligente** baseado em risco
- **Histórico completo** de trades
- **Persistência de dados** em SQLite

### 🔌 Integração Bybit
- **Dados reais** via API REST
- **Cache inteligente** para otimização
- **Rate limiting** respeitoso
- **Suporte a testnet** para testes seguros
- **Fallback para dados simulados**

## 📊 Estratégias Incluídas

| Estratégia | Tipo | Risco | Timeframes |
|------------|------|-------|------------|
| **RSI Mean Reversion** | Oscillator | Medium | 5m, 15m, 30m, 1h |
| **EMA Crossover** | Trend Following | Low | 15m, 30m, 1h, 4h |
| **Bollinger Breakout** | Volatility | High | 5m, 15m, 30m |
| **MACD Strategy** | Momentum | Medium | 30m, 1h, 4h |
| **Stochastic** | Oscillator | Medium | 15m, 30m, 1h |
| **Williams %R** | Oscillator | High | 5m, 15m, 30m |
| **ADX Strategy** | Trend Strength | Low | 1h, 4h, 1d |
| **Fibonacci** | Support/Resistance | Medium | 30m, 1h, 4h |

## 🚀 Instalação Rápida

### Pré-requisitos
- Python 3.8 ou superior
- Conta Bybit (testnet recomendado para testes)

### 1. Clone o Repositório
```bash
git clone https://github.com/seu-usuario/market-manus.git
cd market-manus
```

### 2. Instale Dependências
```bash
# Instalação mínima
pip install pandas numpy requests pybit python-dotenv

# Ou instalação completa
pip install -r requirements_complete.txt
```

### 3. Configure Credenciais (Opcional)
```bash
# Crie arquivo .env
echo "BYBIT_API_KEY=sua_api_key" > .env
echo "BYBIT_API_SECRET=seu_api_secret" >> .env
echo "BYBIT_TESTNET=true" >> .env
```

### 4. Execute o Sistema
```bash
python main.py
```

## 🎮 Uso Básico

### Menu Principal
```
🎛️ MENU PRINCIPAL
--------------------------------------------------
🧪 LABORATÓRIO:
   1️⃣  Strategy Lab - Testes Individuais
   2️⃣  Confluence Mode - Testes Combinados

💼 GESTÃO:
   3️⃣  Capital Dashboard
   4️⃣  Teste de Conectividade
   5️⃣  Configurações

📊 RELATÓRIOS:
   6️⃣  Relatórios e Exportação
   7️⃣  Status do Sistema
   8️⃣  Ajuda
```

### Exemplo: Teste de Estratégia Individual

1. **Selecione Strategy Lab** (opção 1)
2. **Configure o ativo** (ex: BTCUSDT)
3. **Escolha timeframe** (ex: 1h)
4. **Selecione estratégia** (ex: RSI Mean Reversion)
5. **Defina período** (ex: últimos 30 dias)
6. **Execute o teste**

### Exemplo: Confluence Mode

1. **Selecione Confluence Mode** (opção 2)
2. **Multi-seleção de estratégias** (ex: RSI + EMA + Bollinger)
3. **Configure modo** (ex: Majority)
4. **Ajuste força mínima** (ex: 30%)
5. **Execute backtest de confluência**

## 📈 Resultados de Exemplo

```
📊 RESULTADOS DO BACKTEST
==================================================
💰 Capital Inicial: $10,000.00
💰 Capital Final: $10,847.50
📈 Retorno Total: +$847.50
📊 ROI: +8.48%
📉 Drawdown Máximo: 12.3%

🔢 Total de Trades: 23
✅ Trades Vencedores: 15
❌ Trades Perdedores: 8
🎯 Taxa de Acerto: 65.2%
💸 Total de Fees: $46.20

📊 Sharpe Ratio: 1.34
💪 Profit Factor: 2.18
💚 Ganho Médio: +$89.30
💔 Perda Média: -$41.20
```

## 🔧 Configuração Avançada

### Personalizar Estratégias

Crie sua própria estratégia implementando a interface `BaseStrategy`:

```python
from base_strategy import BaseStrategy
import pandas as pd

class MinhaEstrategia(BaseStrategy):
    def __init__(self):
        super().__init__(
            name="minha_estrategia",
            description="Minha Estratégia Personalizada",
            risk_level="medium"
        )
    
    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        # Sua lógica aqui
        df['signal'] = 0  # 1=buy, -1=sell, 0=hold
        df['strength'] = 0.5  # 0.0-1.0
        return df
```

### Configurar Capital Management

```python
# Ajustar risco por trade
capital_manager.config.risk_per_trade = 0.02  # 2%

# Definir máximo por trade
capital_manager.config.max_per_trade = 1000.0  # $1000

# Configurar drawdown máximo
capital_manager.config.max_drawdown = 0.3  # 30%
```

## 📁 Estrutura do Projeto

```
market-manus/
├── main.py                          # Ponto de entrada principal
├── market_manus_cli_complete.py     # CLI completo
├── strategy_contract.py             # Contrato de estratégias
├── bybit_provider.py               # Provider de dados Bybit
├── capital_persistence.py          # Gestão de capital
├── strategy_lab.py                 # Laboratório de estratégias
├── requirements_complete.txt       # Dependências
├── README.md                       # Documentação
├── .env.example                    # Exemplo de configuração
├── logs/                          # Logs do sistema
├── reports/                       # Relatórios exportados
├── data/                         # Cache de dados
└── market_manus/                 # Módulos organizados
    ├── strategies/               # Estratégias individuais
    ├── core/                    # Componentes centrais
    ├── data_providers/          # Provedores de dados
    └── utils/                   # Utilitários
```

## 🧪 Testes

Execute o teste completo do sistema:

```bash
python test_complete_system_final.py
```

Resultado esperado:
```
🎉 TODOS OS TESTES PASSARAM!
✅ Sistema Market Manus está funcionando corretamente
🚀 Pronto para uso!
```

## 🔒 Segurança

- **Nunca** compartilhe suas credenciais da API
- Use **testnet** para desenvolvimento e testes
- Configure permissões **somente leitura** na API
- O sistema **não executa trades reais** automaticamente
- Proteção automática contra **drawdown excessivo**

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-estrategia`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova estratégia'`)
4. Push para a branch (`git push origin feature/nova-estrategia`)
5. Abra um Pull Request

## 📋 Roadmap

### ✅ Implementado
- [x] Strategy Lab completo
- [x] Confluence Mode com 6 modos
- [x] Capital Management robusto
- [x] Integração Bybit API
- [x] 8 estratégias profissionais
- [x] Backtesting honesto
- [x] CLI intuitivo

### 🔄 Em Desenvolvimento
- [ ] Análise em tempo real
- [ ] Otimização de parâmetros
- [ ] WebSocket para dados live
- [ ] Interface web (dashboard)
- [ ] Mais estratégias (ML/AI)
- [ ] Alertas e notificações

### 🎯 Planejado
- [ ] Integração com outras exchanges
- [ ] Trading automatizado (com aprovação)
- [ ] Análise de sentimento
- [ ] Backtesting walk-forward
- [ ] Portfolio management

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/market-manus/issues)
- **Documentação**: [Wiki](https://github.com/seu-usuario/market-manus/wiki)
- **Logs**: Verifique `logs/market_manus.log`

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## ⚠️ Disclaimer

**Este software é apenas para fins educacionais e de pesquisa. Trading de criptomoedas envolve riscos significativos. Nunca invista mais do que pode perder. Os desenvolvedores não são responsáveis por perdas financeiras.**

---

**Desenvolvido com ❤️ para a comunidade de trading**

🚀 **Market Manus** - *Transformando dados em decisões inteligentes*
