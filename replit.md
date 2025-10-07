# Market Manus - Trading Automation System

## Overview
Market Manus is an automated trading system for scalping and swing trading, utilizing real-time market data from Binance.US. It integrates AI, advanced technical analysis (including Smart Money Concepts), and robust capital management to achieve a high win rate through intelligent signal confluence. The project aims to provide a professional-grade tool for automated trading with a focus on intelligent market analysis and strategic execution, providing a comprehensive solution for automated market analysis and trade execution.

## User Preferences
I prefer to receive comprehensive and detailed explanations, ensuring a thorough understanding of all concepts and decisions. Please do not make changes to the `data/` folder, as it is reserved for historical data caching. Additionally, refrain from modifying files within the `config/` directory without explicit instructions, as these contain sensitive configuration settings.

## System Architecture
The system is a CLI/TUI application built with Python 3.11, structured around modular components for market analysis, strategy execution, and user interaction.

### UI/UX Decisions
The system features a professional-grade, real-time interactive console-based UI/UX with a multi-panel layout for live streaming visualization, including a Header, Metrics, optional Paper Trading panel, Body, and Footer. It incorporates an alert system with visual highlights and optional audio for strong signals. A paper trading simulator offers a virtual execution environment with real-time P&L, automatic Stop Loss/Take Profit, and trade statistics. The Narrative UI presents market sentiment data in natural language (Portuguese) using progressive disclosure. The `rich` library is utilized for advanced terminal UI rendering, including tables, panels, and color-coded status indicators.

### Technical Implementations
The core architecture is modular, featuring components for market sentiment analysis, a diverse Strategy Lab (17 strategies including 5 Smart Money Concepts), a Confluence Lab with 22 Recommended Combinations, a Data Provider, and a Capital Manager.

Key technical aspects include:
- **Market Sentiment Analysis**: Aggregates data from various sources (Fear & Greed Index, CoinGecko, Bybit, CoinGlass, CryptoPanic, Santiment, Glassnode, Google Trends) to generate a composite "Market Prognosis."
- **ICT Framework v2.0**: A professional-grade implementation of Inner Circle Trader methodology structured around Market Structure, Context, Narrative, and Setup.
- **Confluence System**: Combines SMC detectors with 12 classic technical strategies. It features a weighted scoring engine with regime filters and conflict penalties, offering 22 Professional Recommended Combinations organized by market condition.
- **Market Context Analyzer**: A regime detection system that analyzes historical data to identify BULLISH, BEARISH, or CORRECTION conditions, adjusting strategy weights accordingly.
- **Volume Filter Pipeline**: Implements statistical volume-based signal filtering using Z-scores.
- **Data Handling**: Features unlimited historical data fetching via intelligent batching, a Parquet-based caching system for historical data, and robust real-time data streaming via Binance.US WebSocket.
- **Strategy Execution**: RealtimeStrategyEngine supports parallel execution of all selected strategies (`asyncio.gather()`) for low latency.
- **Scalping Mode**: A configurable preset optimizing parameters for short timeframes (1m-5m).

### Feature Specifications
- **Strategy Lab V6**: Offers 17 professional trading strategies (12 classic, 5 SMC) with real-time and historical testing capabilities. Newly added strategies include Parabolic SAR, VWAP, VWAP+Volume Combo, and CPR (Central Pivot Range).
- **Confluence Lab**: Supports combining strategies using ALL, MAJORITY, WEIGHTED, and ANY modes. It features 22 Recommended Combinations categorized by market regime (Trending, Ranging, Scalping, Reversal, Breakout, Institutional/Smart Money, High Confidence Ultra), each targeting 70-80%+ win rates with specific timeframe recommendations.
- **Supported Timeframes**: Ranges from 1 minute to 1 day for flexible analysis and trading.

## External Dependencies
The project integrates with the following external services and Python libraries:

- **Binance.US API**: Real-time and historical market data.
- **OpenAI API**: Optional integration for AI-powered features.
- **Python Libraries**:
    - `requests`, `httpx`, `websockets`: HTTP and WebSocket communication.
    - `pandas`, `numpy`: Data manipulation and analysis.
    - `pyarrow`: Parquet file support for historical data caching.
    - `python-dotenv`: Environment variable management.
    - `semantic-kernel`, `openai`: AI integration.
    - `ccxt`: Cryptocurrency exchange interaction.
    - `ta-lib`: Technical analysis indicators.
    - `tenacity`: Retry logic with exponential backoff.
    - `cachetools`: In-memory caching.
    - `pydantic`: Data validation.
    - `rich`: Terminal UI rendering.
    - `pytrends`: Google Trends data (optional).