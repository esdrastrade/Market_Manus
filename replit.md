# Market Manus - Trading Automation System

## Overview
Market Manus is an automated trading system designed for scalping and swing trading using real-time market data from Binance.US. It integrates AI, advanced technical analysis (including Smart Money Concepts), and robust capital management to achieve a high win rate through intelligent signal confluence. The project aims to provide a professional-grade tool for automated trading with a focus on intelligent market analysis and strategic execution.

## Recent Changes (October 2025)
### Phase 1 Quick Corrections - COMPLETED ✅
- **Directional Trading Signals**: All strategies (classic and SMC) now return BUY/SELL directional signals instead of generic "BUY" only. Confluence system uses `VoteData` class to aggregate directional votes with proper type safety.
- **SHORT Position Trading**: Paper trading simulator now supports SHORT positions with inverted SL/TP logic, enabling bidirectional backtesting.
- **Realistic SL/TP Evaluation**: Simulator uses high/low intrabar data to validate stop-loss and take-profit levels, with absolute priority for stop execution in case of gaps (when both SL/TP are touched in same candle).
- **Real OHLCV Data for SMC**: Removed fake `open=close` workaround, all SMC strategies now receive complete OHLCV data with real open prices.
- **Type Safety Improvements**: Reduced LSP errors from 21 to 8, with remaining errors being non-critical typing warnings.

### Phase 2 ICT Enhancements & Trading Costs - COMPLETED ✅
- **OTE (Optimal Trade Entry)**: Implemented fibonacci-based entry zones (62%, 70.5%, 79% retracements) for precision entries in narrative.py. Calculates bullish/bearish OTE zones with optimal entry bands for high-probability setups.
- **CE (Consequent Encroachment)**: Added midpoint (50%) calculation for ranges as target zones and decision levels. Used for partial profit targets and retest entries in ICT methodology.
- **Premium/Discount Zones**: Full implementation of value area classification dividing ranges into 5 zones (Premium High 75-100%, Premium Med 50-75%, Equilibrium 45-55%, Discount Med 25-45%, Discount Low 0-25%). Provides directional bias (premium favors SHORT, discount favors LONG) with automatic price classification.
- **Narrative Enrichment**: `enrich_narrative_with_ote_ce()` helper adds OTE/CE/Premium-Discount data to MarketNarrative.meta with confluence-based strength adjustments (e.g., Discount + OTE Bullish increases signal strength).
- **FeeModel Class**: Professional trading cost simulator in capital_manager.py with configurable maker/taker fees and slippage. Three presets available: LIVE (Binance 0.1%/0.1% + 0.05% slippage), CONSERVATIVE (0.15%/0.15% + 0.2% slippage), OPTIMISTIC (0.075%/0.075% + 0% slippage). Correctly applies slippage only to taker orders (market orders), not maker orders (limit orders).
- **Cost Calculation Methods**: `calculate_entry_cost()`, `calculate_exit_cost()`, `calculate_total_trade_cost()`, and `apply_costs_to_pnl()` for accurate net P&L computation with separate maker/taker handling.
- **ConfluenceEngineAdapter**: Created adapter pattern mapping current strategies to ConfluenceEngine detector interface for future migration (migration deferred to avoid large refactoring).
- **Bug Fixes**: Corrected Premium/Discount equilibrium classification (45%-55% now properly neutral), fixed slippage application (taker-only), and improved type safety across codebase.

### Phase 2 Visual Transparency Features - COMPLETED ✅
- **ICT Market Context Panel**: Real-time visual display showing Premium/Discount classification (color-coded: red for Premium, green for Discount, yellow for Equilibrium), current price zone, active OTE status (BULLISH/BEARISH), and CE level (50% midpoint). Integrated into live streaming UI for immediate market context awareness.
- **Trading Costs Panel**: Transparent breakdown of paper trading performance displaying current equity, position status (open/closed), unrealized P&L, and detailed last trade analysis showing Gross P&L → Trading Costs (fees+slippage) → Net P&L. Win rate with total trades count provides confidence metrics.
- **Enhanced StreamState**: Expanded state tracking to include ICT narrative data (ict_premium_discount, ict_ote_active, ict_ote_type, ict_ce_level, ict_price_in_zone) and paper trading metrics (paper_equity, paper_position_open, paper_unrealized_pnl, paper_last_trade_gross/costs/net, paper_win_rate, paper_total_trades).
- **Live Data Integration**: Automatic extraction of ICT data from signal.meta['narrative'] and paper trading metrics from engine.state, ensuring real-time accuracy with safe attribute checking and fallback values.
- **Color-Coded Transparency**: Intuitive visual feedback using green for profitable/bullish conditions, red for losses/bearish, and yellow for neutral/equilibrium states across all panels.

### Phase 2 Historical Data Caching System - COMPLETED ✅
- **HistoricalDataCache Integration**: Fully integrated Parquet-based caching system in both Confluence Lab and Strategy Lab V6, drastically reducing API calls by storing historical data locally in `data/` directory (C:\Users\Esdras\scalping-trading-system\data).
- **Cache-First Architecture**: Modified `_fetch_historical_klines()` in both modules to check cache BEFORE making API calls. Cache HIT returns stored data instantly with visual feedback ("✅ Cache HIT: {cache_key}"), while Cache MISS triggers API fetch followed by automatic cache save ("📥 Cache MISS: buscando API...").
- **Session Statistics Tracking**: Added `cache_stats` dictionary tracking hits, misses, and API calls saved per session, providing transparency on cache efficiency.
- **CLI Cache Management Menu**: New "📁 Dados Históricos Salvos" menu option (option 6️⃣ in Confluence Lab, option 9️⃣ in Strategy Lab) with 4 submenu options:
  * 📊 Ver dados salvos (Rich Table: símbolo, interval, período, candles, tamanho, data)
  * 🗑️ Limpar cache específico (select by number)
  * 🧹 Limpar todo cache (with confirmation)
  * 📈 Estatísticas de uso (files, space, hits/misses)
- **Metadata Management**: Automatic cache metadata tracking in `cache_metadata.json` including symbol, interval, date range, candle count, file size, and cache timestamp.
- **Smart Key Generation**: Unique cache keys based on symbol+interval+start_date+end_date ensuring precise cache matching and avoiding stale data issues.

## User Preferences
*No specific user preferences recorded yet*

## System Architecture
The system is a CLI/TUI application built with Python 3.11, structured around modular components for market analysis, strategy execution, and user interaction.

### UI/UX Decisions
The system features a professional-grade, real-time interactive console-based UI/UX. Key elements include:
- **Live Streaming Visualization**: A multi-panel layout (Header, Metrics, Optional Paper Trading, Body, Footer) provides real-time updates of market data, strategy signals, and performance metrics.
- **Alert System**: Visual highlights and optional audio alerts for strong signals, with dynamic UI changes to draw attention to critical events.
- **Paper Trading Simulator**: A virtual trade execution environment with real-time P&L, automatic Stop Loss/Take Profit, and comprehensive trade statistics.
- **Narrative UI**: Natural language presentation (in Portuguese) of market sentiment data, transforming technical indicators into contextual storytelling with progressive disclosure and dynamic adaptation to market conditions.
- **Rich Display**: Utilization of the `rich` library for advanced terminal UI rendering, including tables, panels, and color-coded status indicators.

### Technical Implementations
- **Core Architecture**: Features a modular design with components for market sentiment analysis, a diverse Strategy Lab (13 strategies including 5 Smart Money Concepts), Confluence Lab, Data Provider, and Capital Manager.
- **Market Sentiment Analysis**: A modular system aggregating data from various sources (Fear & Greed Index, CoinGecko, Bybit, CoinGlass, CryptoPanic, Santiment, Glassnode, Google Trends) to generate a composite "Market Prognosis." It includes dynamic asset resolution and news sentiment analysis.
- **ICT Framework v2.0**: A professional-grade implementation of Inner Circle Trader methodology, structured into four pillars: Market Structure (BOS, CHoCH, Order Blocks, Liquidity Sweep), Context (Regime Detection, FVG, Strength Scoring), Narrative (Liquidity, Killzones, HTF Context, Judas Swing), and Setup (Entry Models, SL/TP, Setup Scoring). An orchestrator manages sequential analysis and filtering.
- **Confluence System**: Combines SMC detectors with 10 classic technical strategies (including 3 new scalping-optimized detectors: MA Ribbon, Momentum Combo, Pivot Points). It uses a weighted scoring engine with regime filters and conflict penalties for high-probability signal generation.
- **Market Context Analyzer**: A regime detection system that analyzes historical data (MA slope, ADX, ATR) to identify BULLISH, BEARISH, or CORRECTION conditions, auto-adjusting strategy weights for context-aware execution.
- **Volume Filter Pipeline**: Implements statistical volume-based signal filtering using Z-scores to reject low-volume signals and amplify high-volume ones, applied after strategy signals but before confluence scoring.
- **Data Handling**: Features unlimited historical data fetching via intelligent batching, a Parquet-based caching system for historical data, and robust real-time data streaming via Binance.US WebSocket with automatic reconnection and exponential backoff.
- **Strategy Execution**: RealtimeStrategyEngine supports parallel execution of all selected strategies (`asyncio.gather()`) for low latency. Signals are standardized using a `Signal` dataclass.
- **Scalping Mode**: A configurable preset optimizing parameters for short timeframes (1m-5m) with specific indicator settings and adjusted weights.
- **Strategy Explanations**: Comprehensive documentation (Markdown files) for all 13 strategies covering logic, triggers, parameters, and best practices.

### Feature Specifications
- **Strategy Lab V6**: Offers 13 professional trading strategies (8 classic, 5 SMC) with real-time and historical testing capabilities, including API key validation and detailed metrics display.
- **Confluence Lab**: Supports combining strategies using ALL, MAJORITY, WEIGHTED, and ANY modes, with real-time execution displaying live confluence signals.
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