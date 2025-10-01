# Market Manus - Trading Automation System

## Overview
Market Manus v2.1 is a professional automated trading system with integrated AI, advanced technical analysis, and robust capital management. Developed for scalping and swing trading with real data from Binance.US API.

**Current State:** Successfully imported and configured for Replit environment with real market data
**Last Updated:** October 1, 2025

## Project Type
- **Language:** Python 3.11
- **Type:** CLI/TUI Application (Console-based Trading System)
- **Framework:** Custom CLI with interactive menus
- **APIs:** Binance.US (trading data), OpenAI (optional AI features)

## Quick Start

### Running the Application
The CLI is configured to run automatically. You can also manually run:
```bash
python main.py
```

### Initial Setup Required
1. **Configure API Keys** (Already configured via Replit Secrets):
   - Binance API credentials (configured):
     - `BINANCE_API_KEY` - Read-only API key
     - `BINANCE_API_SECRET` - API secret
   - Optional: OpenAI API key for AI features (configured):
     - `OPENAI_API_KEY` - For AI assistant features

2. **First Run**:
   - The system will initialize with default capital ($10,000)
   - ✅ **Connected to Binance.US** - Real market data available
   - Access Strategy Lab Professional V6 with 8 strategies
   - Test strategies with real-time market data from Binance.US

## Project Architecture

### Core Components
1. **Strategy Lab V6** (`market_manus/strategy_lab/`)
   - 8 professional trading strategies
   - Real-time and historical testing
   - Asset selection manager

2. **Confluence Mode** (`market_manus/confluence_mode/`)
   - Combine multiple strategies
   - 4 modes: ALL, MAJORITY, WEIGHTED, ANY

3. **Data Provider** (`market_manus/data_providers/`)
   - Binance.US API integration (active)
   - Real-time market data from Binance.US
   - Historical data retrieval with k-lines
   - Bybit provider available (blocked on Replit)

4. **Capital Manager** (`market_manus/core/`)
   - Position sizing automation
   - Drawdown protection
   - Performance tracking

### Available Strategies
1. **RSI Mean Reversion** - Oversold/overbought reversals
2. **EMA Crossover** - Moving average crossovers
3. **Bollinger Bands Breakout** - Volatility breakouts
4. **MACD** - Momentum analysis
5. **Stochastic Oscillator** - Momentum indicator
6. **Williams %R** - Overbought/oversold indicator
7. **ADX** - Trend strength
8. **Fibonacci Retracement** - Support/resistance levels

### Supported Timeframes
- 1 minute (scalping)
- 5 minutes (scalping)
- 15 minutes (short swing)
- 30 minutes (medium swing)
- 1 hour (intraday)
- 4 hours (long swing)
- 1 day (trend analysis)

## Directory Structure
```
Market_Manus/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (API keys)
├── market_manus/          # Main package
│   ├── agents/            # Trading agents
│   ├── cli/              # CLI interfaces
│   ├── confluence_mode/  # Strategy confluence
│   ├── core/             # Core managers
│   ├── data_providers/   # API integrations
│   ├── strategies/       # Trading strategies
│   └── strategy_lab/     # Strategy testing lab
├── config/               # Configuration files
├── logs/                 # System logs
├── reports/             # Backtest reports
└── tests/               # Test suite
```

## Environment Configuration

### Required Environment Variables (via Replit Secrets)
- `BINANCE_API_KEY` - Binance API key (✅ configured)
- `BINANCE_API_SECRET` - Binance API secret (✅ configured)

### Optional Environment Variables
- `OPENAI_API_KEY` - OpenAI API for AI features (✅ configured)
- `DATABASE_URL` - Database connection
- `LOG_LEVEL` - Logging level (INFO, DEBUG, etc.)

### Default Settings
- Initial Capital: $10,000
- Position Size: 2% (configurable)
- Max Drawdown: 50%

## Workflows

### Market Manus CLI
- **Command:** `python main.py`
- **Type:** Console/TUI application
- **Purpose:** Interactive trading system interface
- **Output:** Console-based menu system

## User Preferences
*No specific user preferences recorded yet*

## Recent Changes

### 2025-10-01: Binance.US Integration & Real Data Connection
- ✅ **Migrated from Bybit to Binance.US** (Bybit/Binance.com blocked on Replit)
- ✅ **Created BinanceDataProvider** - Complete API integration
- ✅ **Configured Binance.US API keys** via Replit Secrets (secure)
- ✅ **Real market data working** - Confirmed BTC price: $117,003.95
- ✅ **All strategies compatible** with Binance data format
- Updated main.py to use Binance as primary data source
- System fully functional with live market data

### 2025-10-01: Initial Replit Environment Setup
- Installed Python 3.11
- Installed all dependencies from requirements.txt
- Created .env from template
- Configured CLI workflow for console output

### Original Features (from import)
- 8 professional trading strategies
- Strategy Lab Professional V6
- Confluence Mode with 4 combination methods
- Real-time Bybit API integration
- Capital management system
- Backtesting capabilities
- 7 timeframe support

## Dependencies
Main packages installed:
- `requests` - HTTP requests
- `pandas`, `numpy` - Data analysis
- `python-dotenv` - Environment variables
- `semantic-kernel`, `openai` - AI integration
- `matplotlib`, `seaborn`, `plotly` - Visualization
- `fastapi`, `uvicorn` - Web framework (for future features)
- `ccxt` - Crypto exchange library
- `ta-lib` - Technical analysis
- `scikit-learn` - Machine learning

## Known Issues & Limitations
1. **Binance.US Only**: Binance.com and Bybit are geo-blocked on Replit servers
2. **OpenAI Optional**: AI assistant features require OpenAI API key
3. **LSP Warnings**: Minor LSP diagnostics (type hints) - not affecting functionality
4. **Read-Only API**: Current Binance API keys are read-only (no trading execution)

## Next Steps for Users
1. ✅ **System Ready** - Binance.US connected with real data
2. **Test strategies** - Use Strategy Lab to test with live BTC/ETH prices
3. **Run backtests** - Historical data available via Binance k-lines
4. **Explore Confluence Mode** - Combine multiple strategies for stronger signals
5. **Review reports** - Check `/reports` directory for backtest results
6. **Optional**: Upgrade to trading-enabled API keys for order execution

## Support & Documentation
- Main README: See `README.md` for detailed Portuguese documentation
- Deployment Guide: `docs/deployment_guide.md`
- Strategy Guide: `docs/strategies.md`
- Troubleshooting: `docs/troubleshooting.md`
- GitHub: https://github.com/esdrastrade/Market_Manus

## Security Notes
- Never commit `.env` file (already in .gitignore)
- API keys are loaded from environment variables
- Use testnet for initial testing
- Review all strategies before live trading
- Start with small capital amounts

## Disclaimer
This is an educational trading system. Trading cryptocurrencies involves significant risk. Always:
- Use testnet first
- Start with small amounts
- Never invest more than you can afford to lose
- Consider consulting a financial advisor
