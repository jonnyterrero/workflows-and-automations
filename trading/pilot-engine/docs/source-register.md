# Source register

| Source ID | Name | URL | Type | Reliability | Status |
|---|---|---|---|---|---|
| `capitol_trades` | Capitol Trades | https://www.capitoltrades.com/ | scraper | B | Planned |
| `edgar` | SEC EDGAR | https://www.sec.gov/edgar | filing | A | Planned |
| `quiver` | Quiver Quantitative | https://www.quiverquant.com/ | API | B | Optional fallback |
| `apify` | Apify Capitol Trades Scraper | https://apify.com/ | managed scraper | B | Optional fallback |

Runtime health, timestamps, parser-break alerts, and operational notes belong in
the Firestore `source_register` collection. Reliability grades must be revisited
when the implementation or upstream source changes.
