# Market Manus - Trading Automation System

## Overview
Market Manus is a professional automated trading system that integrates AI, advanced technical analysis, and robust capital management. It is designed for scalping and swing trading, utilizing real-time market data from Binance.US. The project aims to achieve a high win rate through intelligent signal confluence, combining Smart Money Concepts (SMC) with classic technical strategies.

## User Preferences
*No specific user preferences recorded yet*

## System Architecture
The system is a CLI/TUI application built with Python 3.11. Its core architecture revolves around several key components:

### Core Components
- **Strategy Lab V6**: Contains 8 professional trading strategies, supporting real-time and historical testing, and asset selection.
- **Confluence Mode**: Allows combining multiple strategies using four modes: ALL, MAJORITY, WEIGHTED, and ANY.
- **Data Provider**: Integrates with Binance.US API for real-time and historical market data.
- **Capital Manager**: Handles position sizing automation, drawdown protection, and performance tracking.
- **Confluence System**: A new architecture combining Smart Money Concepts (SMC) detectors (BOS, CHOCH, Order Blocks, FVG, Liquidity Sweeps) with 7 Classic Technical Strategies (EMA Crossover, MACD, RSI Mean Reversion, Bollinger Bands, ADX Trend Strength, Stochastic, Fibonacci). It uses a weighted scoring engine with regime filters (ADX, ATR, BB Width) and conflict penalties to generate high-probability trade signals.

### UI/UX Decisions
The system operates as a console-based CLI/TUI application, providing an interactive menu for users to select assets, timeframes, and execute strategies.

### Technical Implementations
- **Signal Model**: A standardized `Signal` dataclass is used across all detectors, capturing action, confidence, reasons, tags, metadata, and timestamp.
- **Regime Filters**: Signals are rejected if market conditions (e.g., ADX < 15, ATR < min, BB Width < min) are unfavorable.
- **Conflict Penalty**: A 50% score reduction is applied when both BUY and SELL signals exist simultaneously to prevent whipsaw trades.
- **Backtesting & Real-time Execution**: Dedicated modules for backtesting with per-candle logging and real-time execution with data-driven rate-limiting and state-change notifications.

### Supported Timeframes
The system supports multiple timeframes ranging from 1 minute (scalping) to 1 day (trend analysis).

## External Dependencies
The project integrates with the following external services and libraries:

- **Binance.US API**: For real-time and historical market data.
- **OpenAI API**: Optional integration for AI-powered features.
- **Python Libraries**:
    - `requests` for HTTP communication.
    - `pandas`, `numpy` for data manipulation and analysis.
    - `python-dotenv` for environment variable management.
    - `semantic-kernel`, `openai` for AI integration.
    - `ccxt` for cryptocurrency exchange interaction.
    - `ta-lib` for technical analysis indicators.