# Risk Methodology

## Risk Flags

Each signal and research report includes a list of risk flags. Flags reduce confidence scores and warn users before acting on signals.

### General Flags

| Flag | Trigger |
|------|---------|
| High volatility | 20-day annualized vol > 40% |
| Extreme volatility | Vol > 60% |
| Overbought | RSI > 75 |
| Oversold | RSI < 25 |
| Insufficient evidence | Fewer than 2 evidence items |
| Contradictory evidence | News bullish, social bearish (or vice versa) |
| Social hype spike | >40% of posts flagged as spam/hype |
| Extreme positive sentiment | >60% of posts highly bullish |
| High-credibility negative news | Fraud/default/delisting keywords in credible source |
| Low data quality | No news or social data available |

### Asset-Class Specific Flags

**Bonds / Bond ETFs:**
- Duration/rate sensitivity in rising-rate environments
- Yield curve shape risk (inverted = recession risk)
- Credit spread risk (not yet implemented in MVP)

**Crypto:**
- Exchange-specific risk (not modeled in MVP)
- Liquidity risk (not modeled in MVP)
- On-chain risk (not implemented in MVP)
- Extreme volatility (>80% annualized)
- FOMO alert when >70% posts extremely bullish

**Equities:**
- Earnings/event risk (not yet automated)
- Regulatory risk (detected via news keywords)
- Sector rotation risk (not yet implemented)

## Risk Flag Severity

Risk flags are advisory only. They indicate:
- Higher uncertainty in the signal
- Recommended caution before acting
- Need for additional research

**A signal with many risk flags should not be dismissed, but should trigger deeper investigation.**

## Known Limitations

1. **False positives**: Technical flags (RSI overbought) can persist for extended periods in trending markets
2. **Sentiment manipulation**: Social sentiment can be manipulated; always cross-reference with news
3. **Data gaps**: Flags only fire when data is available — missing data produces fewer flags, not safer signals
4. **No position sizing**: Risk flags do not model portfolio risk or position sizing
5. **No correlation analysis**: Multiple positions in correlated assets amplify risk — not modeled
