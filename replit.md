# Market Manus - Trading Automation System

## Overview
Market Manus is a professional automated trading system that integrates AI, advanced technical analysis, and robust capital management. It is designed for scalping and swing trading, utilizing real-time market data from Binance.US. The project aims to achieve a high win rate through intelligent signal confluence, combining Smart Money Concepts (SMC) with classic technical strategies.

## User Preferences
*No specific user preferences recorded yet*

## System Architecture
The system is a CLI/TUI application built with Python 3.11. Its core architecture revolves around several key components:

### Core Components
- **Market Sentiment Analysis (NEW - Oct 2025)**: Modular sentiment aggregation system consulting multiple reliable APIs/sources to provide a composite "Market Prognosis" for selected assets:
  - **Data Sources**: Fear & Greed Index (Alternative.me), CoinGecko (spot market data), Bybit (funding/OI), CoinGlass (open interest), CryptoPanic (news sentiment), Santiment (social metrics), Glassnode (on-chain), Google Trends (search interest)
  - **Normalization**: All signals normalized to 0-1 scale with weighted composite scoring
  - **Caching**: TTL-based in-memory cache (60s) to prevent API hammering
  - **CoinGecko Dynamic Resolution (Oct 2025)**: Universal crypto asset support via intelligent search:
    - Automatic resolution of ANY Binance symbol to CoinGecko ID via search API
    - TTL-based cache (1h, 500 items) prevents rate limit violations
    - Intelligent symbol extraction (strips USDT/USDC/USD suffixes)
    - Graceful error handling for rate limits and unsupported assets
    - No fallback to Bitcoin - accurate "not-found" errors
  - **CryptoPanic Integration (Oct 2025)**: News sentiment analysis via CryptoPanic API v2:
    - Fetches 20+ recent news headlines per asset with vote counts
    - Dynamic sentiment scoring: positive/(positive+negative) with neutral fallback
    - 15% weight in composite score calculation
    - Captures top 5 headlines for narrative context
    - Automatic retry with exponential backoff for reliability
  - **Narrative UI (Oct 2025)**: Natural language presentation transforming technical data into storytelling format:
    - Auto-generated market narratives in Portuguese explaining sentiment context
    - Progressive disclosure: header → interpretation panel → technical details
    - Dynamic storytelling adapting to market conditions (panic, fear, neutral, optimism, greed)
    - Macroeconomic context section with news headlines and sentiment analysis
    - Contextual recommendations based on composite score
    - Color-coded status indicators with Rich panels and tables
- **Strategy Lab V6**: Contains 8 professional trading strategies, supporting real-time and historical testing, and asset selection.
- **Confluence Lab**: Allows combining multiple strategies using four modes: ALL, MAJORITY, WEIGHTED, and ANY.
- **Data Provider**: Integrates with Binance.US API for real-time and historical market data.
- **Capital Manager**: Handles position sizing automation, drawdown protection, and performance tracking.
- **Confluence System**: A new architecture combining Smart Money Concepts (SMC) detectors (BOS, CHOCH, Order Blocks, FVG, Liquidity Sweeps) with **10 Classic Technical Strategies** including 3 new scalping-optimized detectors:
  - **Original 7**: EMA Crossover, MACD, RSI Mean Reversion, Bollinger Bands, ADX Trend Strength, Stochastic, Fibonacci
  - **NEW Scalping Detectors (Oct 2025)**: 
    - **MA Ribbon (5-8-13 SMAs)**: Detects trend alignment for scalping with spread threshold filtering
    - **Momentum Combo (RSI+MACD)**: High-probability signals combining momentum indicators
    - **Pivot Points**: Objective support/resistance levels with automatic daily calculations
  - Uses weighted scoring engine with regime filters (ADX, ATR, BB Width) and conflict penalties to generate high-probability trade signals.

### UI/UX Decisions
The system operates as a console-based CLI/TUI application, providing an interactive menu for users to select assets, timeframes, and execute strategies.

**Live Streaming Visualization (NEW - Oct 2025)**:
- Rich UI with live-updating panels showing real-time market data without scroll spam
- WebSocket streaming from Binance.US for sub-second latency
- Four-panel layout: Status header, Price panel, Confluence analysis, Recent events
- Visual indicators for BUY (↑ green), SELL (↓ red), HOLD (• yellow) states
- Real-time display of confidence scores, reasons, and detector tags

### Technical Implementations
- **Signal Model**: A standardized `Signal` dataclass is used across all detectors, capturing action, confidence, reasons, tags, metadata, and timestamp.
- **Regime Filters**: Signals are rejected if market conditions (e.g., ADX < 15, ATR < min, BB Width < min) are unfavorable.
- **Conflict Penalty**: A 50% score reduction is applied when both BUY and SELL signals exist simultaneously to prevent whipsaw trades.
- **Backtesting & Real-time Execution**: Dedicated modules for backtesting with per-candle logging and real-time execution with data-driven rate-limiting and state-change notifications.
- **Unlimited Historical Data Fetch (NEW - Oct 2025)**: Intelligent batching system that fetches ALL candles for any date range, automatically chunking requests in 500-1000 candle batches to respect API limits while ensuring complete historical coverage.
- **Scalping Mode (NEW - Oct 2025)**: Configurable preset optimizing parameters for short timeframes (1m-5m):
  - MA Ribbon with alignment threshold filtering (rejects flat markets)
  - Bollinger Bands: 13-period, 3SD (faster, more volatile)
  - Stochastic: 5-period (faster response)
  - Adjusted weights favoring momentum and pivot detectors
  - All scalping detectors based on Investopedia professional strategies
- **WebSocket Streaming (NEW)**: Binance.US WebSocket integration with automatic reconnection, exponential backoff + jitter, and debouncing (1s micro-batches).
- **Async Pipeline**: AsyncIO-based runtime with Queue-based message coalescing, preventing rate limit violations while maintaining real-time responsiveness.
- **Rich UI Live View**: Terminal UI using `rich` library with Live display, updating panels in-place without scrolling, showing latency, message counts, and processing metrics.
- **Real-Time Strategy Execution (NEW - Oct 2025)**: Complete replacement of simulated data with real WebSocket execution:
  - **RealtimeStrategyEngine**: New engine (`market_manus/engines/realtime_strategy_engine.py`) integrating WebSocket + parallel strategies + live UI
  - **Parallel Strategy Application**: All selected strategies execute simultaneously using `asyncio.gather()` for < 200ms latency
  - **Live Rich UI**: Four-panel layout (header, price, confluence signal, individual strategies) updating in real-time without scroll
  - **Bootstrap + Stream**: Loads 500 historical candles for indicator initialization, then streams live data
  - **Robust Error Handling**: Automatic WebSocket reconnection, graceful strategy failures, validated configurations
  - **Supported Strategies**: 6 classic (RSI, EMA, Bollinger, MACD, Stochastic, ADX) + 5 SMC patterns (BOS, CHoCH, OB, FVG, Liquidity Sweep)
  - **Confluence Labs**: ALL (unanimous), ANY (first signal), MAJORITY (>50% agreement)
  - **Integration**: Available in Strategy Lab V6 via "Teste em Tempo Real" menu option

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
    - `httpx`, `websockets` for async HTTP and WebSocket communication.
    - `tenacity` for retry logic with exponential backoff.
    - `cachetools` for in-memory caching.
    - `pydantic` for data validation.
    - `rich` for terminal UI rendering.
    - `pytrends` (optional) for Google Trends data.