# Signal Methodology

## Overview

The signal engine produces composite scores from -100 to +100 for each asset, covering multiple evidence types. Every score is decomposable — you can trace exactly which sub-scores drove the final output.

## Composite Score Formula

```
Composite = Σ(weight_i × component_i) - penalties
```

Where each component is in [-1.0, +1.0] and the final score is scaled to [-100, +100].

### Component Weights (configurable in `config/signal_weights.yaml`)

| Component | Default Weight | Source |
|-----------|---------------|--------|
| market_trend | 0.20 | Technical analysis (SMA, trend) |
| momentum | 0.10 | RSI, MACD |
| volume | 0.08 | Volume confirmation |
| volatility | 0.05 | Penalty for high-vol assets |
| news_sentiment | 0.18 | Credibility-weighted news |
| social_sentiment | 0.10 | Reddit/social (spam-filtered) |
| macro_alignment | 0.12 | Rate/growth/VIX regime |
| fundamental | 0.10 | P/E, earnings, revenue |
| event_catalyst | 0.07 | Upcoming events, announcements |

### Penalties

| Penalty | Default | Applied When |
|---------|---------|-------------|
| risk_penalty | 0.15/flag | Each risk flag found |
| contradiction | 0.10 | News and social conflict |
| low_confidence | 0.05 | Fewer than 2 evidence items |

## Direction Classification

| Score Range | Direction |
|-------------|-----------|
| > +15 | BULLISH |
| -15 to +15 | NEUTRAL |
| < -15 | BEARISH |
| Mixed strong evidence | MIXED |

## Confidence Score (0 to 1)

Confidence reflects evidence quality, not signal correctness:
- Scales with evidence count (capped at 1.0)
- Reduced by contradicting evidence (-30%)
- Reduced by >3 risk flags (-20%)
- Never guarantees correct price prediction

## Evidence Tracing

Every signal stores `evidence_ids` — a list of database record IDs (news articles, social posts, macro data) that contributed to the signal. Use `GET /signals/{signal_id}/evidence` to retrieve the full evidence chain.

## Limitations

- Technical indicators are lagging by definition
- Sentiment analysis is lexicon-based, not ML-based in MVP
- Fundamental data is not available without paid provider
- Social signals are noisy and subject to manipulation
- Macro alignment is a heuristic, not a causal model
- **Do not trade purely on these signals**
