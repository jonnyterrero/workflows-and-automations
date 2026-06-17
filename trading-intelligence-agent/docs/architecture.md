# System Architecture

## Overview

Trading Intelligence Agent is a modular Python monorepo organized as a data platform with intelligence layers on top.

```
Data Sources → Providers → Collectors → Storage → Processing → Engines → API
```

## Service Boundaries

```
apps/
├── api_service/       FastAPI — HTTP interface to all features
├── scheduler_service/ APScheduler — daily/periodic data jobs
├── collector_service/ Intraday crypto/market data collection
└── worker_service/    AI research job runner (briefings, signals)
```

## Package Layer

```
packages/
├── core_models/       Pydantic + SQLAlchemy models (source of truth)
├── storage/           Database session, repositories (CRUD)
├── data_providers/    Abstract provider interfaces + demo implementations
│   └── demo/          Fixture data providers (no API keys needed)
├── market_data/       Equity/ETF OHLCV ingestion orchestration
├── macro_data/        Macro indicator ingestion
├── crypto_exchanges/  Crypto OHLCV/ticker/orderbook ingestion
├── filings/           SEC EDGAR filing fetcher
├── social_intel/      Ticker extraction, sentiment scoring
├── news_intel/        News collection and sentiment aggregation
├── normalization/     Data normalization, deduplication, hashing
├── analytics/         Technical indicators (SMA, EMA, RSI, MACD, BB, ATR)
├── signal_engine/     Composite signal scoring with configurable weights
├── risk_engine/       Risk flag detection per asset class
├── ai_research/       LLM adapter (OpenAI/Anthropic), briefing/report generation
├── backtesting/       Signal replay against stored prices
└── observability/     Structured logging (structlog)
```

## Data Flow

1. **Ingestion**: Providers fetch raw data → stored in `raw_payloads` (hash-deduplicated)
2. **Normalization**: Raw data → typed models → upserted into normalized tables
3. **Processing**: Ticker extraction, sentiment scoring applied to news/social
4. **Signal Generation**: TechnicalAnalyzer + SentimentScorer + MacroCollector → SignalScorer → Signal
5. **Research**: LLMAdapter reads evidence from DB → generates DailyBriefing / AssetResearchReport
6. **API**: FastAPI routes expose all data to clients

## Storage Design

- **SQLite** (local MVP): single file at `data/trading_intel.db`
- **PostgreSQL** (production): set via `DATABASE_URL` env var
- Raw payloads: never deleted, hash-deduplicated, parse status tracked
- Time-series design: `market_prices` has `(asset_id, timestamp, interval, source)` unique constraint
- JSON fields for lists (tickers_mentioned, evidence_ids, risk_flags) — acceptable for MVP

## Provider Pattern

All data providers implement abstract base classes from `packages/data_providers/base.py`.
Adding a new provider means:
1. Subclass the appropriate base (e.g., `BaseMarketDataProvider`)
2. Implement required abstract methods
3. Register with `ProviderRegistry`

Demo mode is enabled only when `DEMO_MODE=true` — otherwise the app uses any configured live providers.

## AI/RAG Flow

```
User Request
    → API route
    → DB query for evidence (news, social, macro, signals, prices)
    → Context assembled as structured text with evidence IDs
    → LLMAdapter.complete_json(system_prompt, user_prompt)
    → Response validated against Pydantic schema
    → Stored in DB with evidence_ids
    → Returned via API
```

The system never invents evidence IDs — all citations must come from the context provided.
