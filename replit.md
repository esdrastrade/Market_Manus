# Market Manus - Trading Automation System

## Overview
Market Manus v2.1 is a professional automated trading system with integrated AI, advanced technical analysis, and robust capital management. Developed for scalping and swing trading with real data from Bybit API.

**Current State:** Successfully imported and configured for Replit environment
**Last Updated:** October 1, 2025

## Project Type
- **Language:** Python 3.11
- **Type:** CLI/TUI Application (Console-based Trading System)
- **Framework:** Custom CLI with interactive menus
- **APIs:** Bybit (trading), OpenAI (optional AI features)

## Quick Start

### Running the Application
The CLI is configured to run automatically. You can also manually run:
```bash
python main.py
```

### Initial Setup Required
1. **Configure API Keys** (Required for full functionality):
   - Edit `.env` file
   - Add your Bybit API credentials:
     ```
     BYBIT_API_KEY=your_api_key_here
     BYBIT_API_SECRET=your_api_secret_here
     BYBIT_TESTNET=true
     ```
   - Optional: Add OpenAI API key for AI features:
     ```
     OPENAI_API_KEY=your_openai_key_here
     ```

2. **First Run**:
   - The system will initialize with default capital ($10,000)
   - Access Strategy Lab Professional V6 with 8 strategies
   - Test strategies with real-time or historical data

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
   - Bybit API integration
   - Real-time market data
   - Historical data retrieval

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

### Required Environment Variables
- `BYBIT_API_KEY` - Bybit API key (required)
- `BYBIT_API_SECRET` - Bybit API secret (required)
- `BYBIT_TESTNET` - Use testnet (true/false)

### Optional Environment Variables
- `OPENAI_API_KEY` - OpenAI API for AI features
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

### 2025-10-01: Replit Environment Setup
- Installed Python 3.11
- Installed all dependencies from requirements.txt
- Created .env from template
- Configured CLI workflow for console output
- System ready for use (requires API keys for full functionality)

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
1. **API Keys Required**: System requires valid Bybit API credentials for full functionality
2. **API Connection**: Without valid credentials, data provider will be disconnected
3. **OpenAI Optional**: AI assistant features require OpenAI API key
4. **LSP Warning**: Minor LSP diagnostic for dotenv import (false positive - import works correctly)

## Next Steps for Users
1. Add Bybit API credentials to `.env` file
2. Test with testnet first (BYBIT_TESTNET=true)
3. Run a simple strategy test in Strategy Lab
4. Explore confluence mode for combined strategies
5. Review backtesting reports in `/reports` directory

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
