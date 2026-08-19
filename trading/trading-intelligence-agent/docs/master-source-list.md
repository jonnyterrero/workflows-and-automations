# Master Source List — Trading Intelligence Agent

> Consolidated from research sessions (2026-06-13, 2026-06-17, 2026-07-20) and the live codebase
> (`docs/data-sources.md`, `config/crypto_rss_feeds.yaml`, `packages/data_providers/live/`).
> This file exists so the source/scraper list isn't scattered across chat history anymore.
> Last consolidated: 2026-07-31

## Status legend
- ✅ **Live** — provider is coded and wired into the pipeline (`packages/data_providers/live/`)
- 🔑 **Key saved, not wired** — API key exists in `Trading Bot.md` notes but no adapter uses it yet
- ⏳ **Planned** — discussed/recommended, no key or code yet
- 🚫 **Blocked** — attempted, currently broken (see notes)

---

## 1. Web Scrapers Evaluated (X/Twitter + Reddit)

From the 2026-06-17 "public web scrapers" research session — used when official API access was hard to get.

| # | Tool | Target | Type | Notes |
|---|------|--------|------|-------|
| 1 | TWINT | X/Twitter | Python scraper, no API key | Breaks periodically as X changes HTML/JS |
| 2 | Twikit | X/Twitter | Python client using X's web APIs | More maintained than TWINT |
| 3 | Playwright / Selenium (custom) | X/Twitter | Headless browser automation | Needs rotating proxies at scale |
| 4 | X Twitter Scraper (Chrome extension) | X/Twitter | Browser extension | Manual/small-scale exports |
| 5 | Scrape Creators – X API | X/Twitter | Paid hosted scraping API | Stays on "public data only" side |
| 6 | Old Bird v2 (RapidAPI) | X/Twitter | Third-party API emulating old Twitter API | Higher ToS/legal risk |
| 7 | Masa X-Scraper | X/Twitter | Student-friendly search API | Free key for academic/student use |
| 8 | YARS (Yet Another Reddit Scraper) | Reddit | Python package, public `.json` endpoints | ✅ Selected as primary Reddit scraper |
| 9 | Pushshift / Pushshift Services | Reddit | Historical archive API | Good for bulk historical pulls |
| 10 | Reddit Toolbox | Reddit | Local desktop tool, mimics browser session | Heavier, more resilient to WAF bans |

**Decision at the time:** YARS for Reddit; Masa X-Scraper or Scrape Creators for low-maintenance X access, Twikit + Playwright if willing to maintain it yourself.

---

## 2. Market Data & Fundamentals APIs

| Source | Status | Key/Env Var | Notes |
|---|---|---|---|
| Polygon.io | ✅ Live | `POLYGON_API_KEY` | US equities/options intraday + historical, [Python client](https://github.com/pssolanki111/polygon) |
| Alpha Vantage (equities) | ✅ Live | `ALPHA_VANTAGE_API_KEY` | Free tier, 5 req/min, 500/day |
| Alpha Vantage (crypto) | ✅ Live | same key | Separate adapter in repo |
| Finnhub (fundamentals) | ✅ Live | `FINNHUB_API_KEY` | Fundamentals, earnings, IPO calendar |
| Coinbase Exchange (public data) | ✅ Live | none required | Public market-data endpoints |
| Coinbase Advanced Trade API | 🔑 Key saved | key + secret in `Trading Bot.md` | Execution + WebSocket, not wired |
| Tiingo | ⏳ Planned | — | Clean EOD/intraday, IEX real-time feed |
| Financial Modeling Prep (FMP) | ⏳ Planned | — | Screener API, spreadsheet plugins |
| EODHD | ⏳ Planned | — | Stocks/ETFs/options screener |
| MarketData.app | ⏳ Planned | — | Options chain + spreadsheet plugins |
| CoinAPI | ⏳ Planned | — | Quant-grade crypto data across venues |
| Binance | ⏳ Planned | — | 1200 req/min free read-only |
| Alpaca (paper) | ⏳ Planned | — | Phase 6 broker integration target |

## 3. Screening & Idea Generation

| Source | Status | Notes |
|---|---|---|
| Finviz / Finviz Elite | ⏳ Planned | Daily screens; unofficial Python wrappers exist |
| ValueInvesting.io | ⏳ Planned | DCF/EPV valuation-tilted signals |
| Finsheet | ⏳ Planned | Institutional data inside Excel/Sheets |
| QuantPedia tools directory | ⏳ Planned | Broader market-API ecosystem reference |

## 4. News & Market Commentary

| Source | Status | Notes |
|---|---|---|
| NewsAPI.org | ✅ Live | `NEWS_API_KEY`, free dev tier, 100 req/day |
| RSS: Reuters, Bloomberg Markets, Yahoo | ✅ Live | `rss_news.py` |
| Finnhub news | ✅ Live | `finnhub_news.py` |
| Benzinga (Pro/APIs) | ⏳ Planned | Structured, timestamped headlines |
| MarketWatch | ⏳ Planned (RSS only) | Do not HTML-scrape — RSS feeds only |
| TheStreet | ⏳ Planned | Direct scraping blocked by anti-bot; use licensed aggregator |
| Seeking Alpha | ⏳ Planned | Articles + community commentary |
| Yahoo Finance | ⏳ Planned | Broad daily coverage |
| FinURLs | ⏳ Planned | Finance/business news aggregator |
| PiQSuite | ⏳ Planned | Aggregates multiple feeds + press releases |
| The Fly on the Wall | ⏳ Planned | Aggregator |
| Hudson Labs | ⏳ Planned | SEC-derived AI news |
| Google News | ⏳ Planned | General aggregator |
| NewsNow | ⏳ Planned | RSS-style aggregator |
| Bloomberg Business | ⏳ Planned | Already tracked manually |
| Fox Business | ⏳ Planned | Already tracked manually |
| CNN Business | ⏳ Planned | Already tracked manually |
| Nasdaq | ⏳ Planned | Already tracked manually |

## 5. Filings & Regulatory

| Source | Status | Notes |
|---|---|---|
| SEC EDGAR (live submissions API, CIK lookup) | ✅ Live | `sec_api_filings.py`, User-Agent header required |
| sec-api.io | 🔑 Key saved | Key in `Trading Bot.md`; full-text search across 150+ form types |
| EDGAR Online (enriched) | ⏳ Planned | Filings + ownership/insider data |
| BoredReading | ⏳ Planned | 10-K/10-Q feed reader |
| AlphaResearch | ⏳ Planned | AI search over filings |
| SEC press releases (RSS) | ⏳ Planned | `sec.gov/news/pressreleases.rss` |
| CFTC press releases (RSS) | ⏳ Planned | `cftc.gov/RSS/RSSGP/rssgp.xml` |

## 6. IPO / Pre-IPO Tracking

| Source | Status | Notes |
|---|---|---|
| IPO Scoop calendar | ✅ Live | `iposcoop_calendar.py` |
| Renaissance Capital IPO Center/IPO Pro | ⏳ Planned | Full pipeline, calendar, pre-IPO reports |
| RobotWealth free IPO calendar | ⏳ Planned | Built on Finnhub IPO endpoints |
| Xignite IPO Calendar API | ⏳ Planned | Dedicated IPO pipeline/schedule API |

## 7. Macro & Rates

| Source | Status | Notes |
|---|---|---|
| FRED API (St. Louis Fed) | ✅ Live | `fred.py`, `FRED_API_KEY` saved |
| US Treasury data | ⏳ Planned | No key required |

## 8. Social & Sentiment

| Source | Status | Notes |
|---|---|---|
| Reddit API (public JSON search) | ✅ Live | `reddit_social.py` |
| X/Twitter API v2 | 🚫 Blocked | Bearer token returns 401 — regenerate at developer.x.com, verify via `POST /admin/setup/x/verify` |
| Commonstock | ⏳ Planned | Community tied to real brokerage performance |
| Seeking Alpha community | ⏳ Planned | Comment-thread sentiment |
| (10 scrapers above) | — | Fallback path if official API access stays blocked |

## 9. Insider & Politician Trade Tracking

| Source | Status | Notes |
|---|---|---|
| EDGAR insider transactions / 13F | ⏳ Planned | Form 4 + institutional holdings |
| Congressional/politician PTR trade feeds | ⏳ Planned | Also available via Perplexity Finance connector (`finance_politician_trades`) |

## 10. Knowledge Base (for agent explanations, not signals)

| Source | Status |
|---|---|
| Investopedia | ⏳ Planned |
| Morningstar | ⏳ Planned |
| Motley Fool | ⏳ Planned |

## 11. Editorial "Best Investments" Context — soft signal only, not ground truth

| Source | Status |
|---|---|
| Fidelity | ⏳ Planned |
| NerdWallet | ⏳ Planned |

## 12. Crypto RSS Intelligence Catalog

Live in `config/crypto_rss_feeds.yaml`, loaded via `crypto_feeds_catalog.py`.

| Feed | Category | Reliability (1-10) | Monitor |
|---|---|---|---|
| CoinDesk | Breaking news | 8 | daily |
| The Block | Breaking news | 9 | daily |
| Bloomberg Crypto | Breaking news | 10 | daily |
| CryptoPotato | Breaking news | 6 | daily |
| Cointelegraph | Breaking news | 7 | daily |
| Decrypt | Breaking news | 7 | daily |
| Bitcoin Magazine | Breaking news | 7 | weekly |
| CryptoSlate | Breaking news | 7 | daily |
| Blockworks | Breaking news | 9 | daily |
| Immunefi Blog | Security/exploits | 9 | event-driven |
| Halborn Blog | Security/exploits | 8 | daily |
| SEC Press Releases | Regulatory | 10 | event-driven |
| CFTC Press Releases | Regulatory | 10 | event-driven |
| Ethereum Foundation Blog | Protocol dev | 10 | weekly |
| Uniswap Governance | Protocol dev | 9 | event-driven |

## 13. Crypto On-Chain / Paid API Integrations — Planned

Listed in `crypto_rss_feeds.yaml` under `api_integrations`, not yet scraped/wired.

| Source | Group | Reliability | Env Var / Note |
|---|---|---|---|
| Glassnode | On-chain | 9 | `GLASSNODE_API_KEY` |
| Nansen | On-chain | 8 | `NANSEN_API_KEY` |
| CryptoQuant | On-chain | 8 | `CRYPTOQUANT_API_KEY` |
| Santiment | On-chain | 8 | `SANTIMENT_API_KEY` |
| DeFiLlama | DeFi fundamentals | 9 | public API available |
| Token Terminal | DeFi fundamentals | 9 | `TOKEN_TERMINAL_API_KEY` |
| CoinGlass | Derivatives | 8 | public API limited |
| Laevitas | Derivatives | 9 | `LAEVITAS_API_KEY` |
| Blockworks Crypto ETF Dashboard | ETF flows | 9 | dashboard, no RSS |
| BTC ETF Fund Flow | ETF flows | 7 | dashboard, no RSS |
| Chainalysis | Compliance | 10 | reports only, public |

## 14. Crypto Rule-Based Trading Bots (separate from the research agent)

Evaluated as DCA/rebalancing assistants for the experimental crypto sleeve — not the decision-support agent itself.

| Bot | Notes |
|---|---|
| Pionex | Built-in exchange bots |
| Bitsgap | Cross-exchange bot platform |
| 3Commas | Popular DCA/grid bot suite |
| Cryptohopper | Cloud-based bot platform |

---

## Keys already saved (per `Trading Bot.md` in The-Batcave vault)

FRED, Alpha Vantage, X.com (developer/secret/bearer), NewsAPI, Finnhub, sec-api.io, Polygon, Coinbase (key + secret). Do not commit these values to this repo — they live only in the private notes vault.

## Legal / ToS reminders (from `docs/data-sources.md`)

- SEC EDGAR: public, free — include a User-Agent with contact email.
- Reddit: official API only for auth-gated content; public JSON scraping (YARS) is the accepted fallback.
- MarketWatch: RSS only, do not HTML-scrape.
- TheStreet: direct scraping blocked by anti-bot — use a licensed aggregator instead of bypassing it.
- IPO Scoop: public calendar currently allows basic access per `robots.txt` — keep crawl rate conservative.
- Never bypass robots.txt, login walls, or anti-bot systems; never redistribute raw data against provider ToS.

## Next steps to close the gap between "planned" and "live"

1. Regenerate the X/Twitter bearer token and verify via `POST /admin/setup/x/verify` (currently 🚫 blocked).
2. Wire the already-keyed sources: Coinbase Advanced Trade API, sec-api.io.
3. Pick one screener (Finviz Elite is the strongest candidate) and one deeper news API (Benzinga) to close the biggest coverage gaps.
4. DeFiLlama has a free public API and no blocker — lowest-effort next crypto integration.
