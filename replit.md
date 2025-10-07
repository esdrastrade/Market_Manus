# Market Manus - Trading Automation System

## Overview
Market Manus is an automated trading system for scalping and swing trading, utilizing real-time market data from Binance.US. It integrates AI, advanced technical analysis (including Smart Money Concepts), and robust capital management to achieve a high win rate through intelligent signal confluence. The project aims to provide a professional-grade tool for automated trading with a focus on intelligent market analysis and strategic execution, providing a comprehensive solution for automated market analysis and trade execution.

## User Preferences
I prefer to receive comprehensive and detailed explanations, ensuring a thorough understanding of all concepts and decisions. Please do not make changes to the `data/` folder, as it is reserved for historical data caching. Additionally, refrain from modifying files within the `config/` directory without explicit instructions, as these contain sensitive configuration settings.

## System Architecture
The system offers dual interfaces (CLI/Web) built with Python 3.11, structured around modular components for market analysis, strategy execution, and user interaction. Users can choose their preferred interface at startup via `python main.py`.

### Dual Interface System
- **CLI Mode**: Professional-grade terminal interface with real-time visualization using the `rich` library
- **Web Interface**: Modern browser-based dashboard with responsive design and real-time updates
- **Startup Selection**: Interactive menu allows choosing between CLI or Web interface at launch
- **Shared Backend**: Both interfaces utilize the same core trading engine and modules

### UI/UX Decisions

#### CLI/TUI Interface
The CLI features a professional-grade, real-time interactive console-based UI/UX with a multi-panel layout for live streaming visualization, including a Header, Metrics, optional Paper Trading panel, Body, and Footer. It incorporates an alert system with visual highlights and optional audio for strong signals. A paper trading simulator offers a virtual execution environment with real-time P&L, automatic Stop Loss/Take Profit, and trade statistics. The Narrative UI presents market sentiment data in natural language (Portuguese) using progressive disclosure. The `rich` library is utilized for advanced terminal UI rendering, including tables, panels, and color-coded status indicators.

#### Web Interface (v2.0 - UPDATED)
- **Framework**: Flask + Flask-SocketIO for real-time WebSocket communication
- **Frontend**: Bootstrap 5, responsive design, professional dark theme
- **Theme**: Complete dark mode with GitHub-inspired color palette (#0d1117 primary, #1c2128 cards)
- **Pages**:
  * **Dashboard**: Real-time metrics, capital status, market overview, sentiment analysis
  * **Strategy Lab**: Visual selection of 17 strategies (12 classic + 5 SMC) with interactive cards
  * **Confluence Lab**: Browse and filter 22 recommended combinations by category/mode/timeframe
  * **Backtest**: REAL backtest execution with Binance historical data, dynamic results (ROI, win rate, trades)
  * **Performance**: Historical performance tracking with Chart.js graphs, database-driven metrics
- **Features**:
  * Real-time updates via WebSocket
  * REST API endpoints: `/api/backtest` (POST), `/api/performance/summary`, `/api/performance/export/<id>`
  * Dynamic backtest execution using ConfluenceModeModule (same engine as CLI)
  * Results persistence in SQLite via PerformanceHistoryRepository
  * AI toggles (Manus AI Premium + Semantic Kernel Advisor) with real integration
  * Responsive design for desktop and mobile
  * Professional dark theme with custom scrollbars, hover effects, and color-coded metrics
- **Technical Implementation**:
  * Backtest endpoint executes real strategies on historical OHLCV data from Binance
  * Volume filter pipeline applied to signals
  * Confluence calculation with BUY/SELL direction tracking
  * Trade simulation with realistic Stop Loss (0.5%) and Take Profit (1.0%)
  * Results saved to database with strategy contributions
- **Access**: http://localhost:5000 when Web mode is selected

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
    - `flask`, `flask-socketio`, `flask-cors`: Web interface framework and real-time communication.
### Phase 4 Manus AI Premium Integration - COMPLETED ✅
- **Manus AI Integration Module** (market_manus/ai/manus_ai_integration.py): Full integration of Manus AI autonomous agent for premium market analysis:
  * **ManusAIAnalyzer Class**: Core AI analyzer with market context analysis, signal enhancement, and intelligent insights
  * **API Integration**: Secure connection to Manus AI API (https://api.manus.im) with token-based authentication
  * **Market Context Analysis**: AI-powered regime detection (trending/ranging/volatile), signal quality assessment, and risk level evaluation
  * **Signal Enhancement**: Automatic adjustment of strategy weights based on AI confidence (1.2x boost for high confidence, 0.7x reduction for low confidence/warnings)
  * **Intelligent Insights**: Natural language explanations of market conditions and AI recommendations
- **Premium AI Toggle in Confluence Lab**: New option 11 in main menu for on/off control:
  * **Status Display**: Shows AI Premium status (ATIVO/DESATIVADO) and availability (checks MANUS_AI_API_KEY)
  * **Interactive Toggle**: User-friendly activation/deactivation with confirmation prompt
  * **Feature Explanation**: Clear description of AI capabilities (regime analysis, signal quality, risk identification, weight adjustment, contextual insights)
  * **Fallback System**: Graceful degradation when AI is disabled or unavailable
- **AI Layer Permeating All Processing**: AI analysis integrated into every stage of strategy execution:
  * **Pre-Processing**: Market context analysis before strategy signals
  * **Signal Processing**: AI evaluation of strategy votes and confluence
  * **Post-Processing**: Weight adjustment and confidence boosting based on AI recommendations
  * **Metadata Enrichment**: Every signal tagged with AI analysis (regime, quality, risk, confidence)
- **Environment Configuration**: 
  * **.env.example Updated**: Added MANUS_AI_API_KEY with instructions (https://manus.im, 1,000 free credits + 300 daily)
  * **Secret Management**: Integrated with Replit Secrets for secure API key storage
  * **Auto-Detection**: System automatically detects and enables AI when key is present
- **User Benefits**:
  * **Higher Accuracy**: AI-enhanced signal quality and reduced false positives
  * **Context Awareness**: Market regime understanding improves strategy selection
  * **Risk Management**: AI identifies high-risk conditions and adjusts accordingly
  * **Educational Value**: Natural language insights explain market dynamics
  * **Free to Use**: 1,000 credits + 300 daily credits available at no cost

