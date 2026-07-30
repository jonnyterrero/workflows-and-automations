# Four-Agent Investment Research System

This module adds a bounded, auditable investment-research workflow using the OpenAI Agents SDK.

## Agents

1. **Theme Scout** — identifies structural drivers, beneficiary pathways, competing beneficiaries, and hype risk.
2. **Evidence Analyst** — verifies measurable exposure using supplied evidence and classifies it as proven, partially proven, or unproven.
3. **Risk and Valuation Analyst** — red-teams valuation, embedded expectations, concentration, downside cases, and thesis invalidation.
4. **Investment Committee Manager** — synthesizes the three reports into one structured dossier and conservative research status.

The three specialists run concurrently. The committee manager runs only after all three structured reports are available.

## Safety boundary

The workflow does not place orders and does not output direct buy/sell instructions. It requires human review, preserves evidence IDs, treats missing valuation data as a gap, and rejects guaranteed-return language through SDK guardrails.

## Installation

Requirements:

- Python 3.12+
- An OpenAI API key for live agent runs
- No API key is required for the deterministic offline demonstration
- GitHub CLI is optional but recommended for branch, pull-request, and repository verification workflows

### Windows GitHub CLI setup

Install GitHub CLI from PowerShell or Windows Terminal:

```powershell
winget install --id GitHub.cli
```

Open a new terminal after installation, then authenticate and verify the connection:

```powershell
gh --version
gh auth login
gh auth status
```

Choose `GitHub.com`, select HTTPS, and complete browser authentication when prompted.

From the repository root:

```bash
cd trading-intelligence-agent
python -m venv .venv
```

Activate the environment:

```bash
# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install the application and development dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
cp .env.example .env
```

On Windows PowerShell, replace the final command with:

```powershell
Copy-Item .env.example .env
```

## Offline demo

The offline demo uses deterministic scoring and synthetic evidence fixtures. It verifies installation, schemas, route wiring, and dossier output without calling a model.

```bash
make run-committee-demo
```

Equivalent command:

```bash
DEMO_MODE=true python -m scripts.run_investment_committee_demo
```

Windows PowerShell:

```powershell
$env:DEMO_MODE="true"
python -m scripts.run_investment_committee_demo
```

Custom demonstration:

```bash
python -m scripts.run_investment_committee_demo \
  --symbol NVDA \
  --theme "AI infrastructure"
```

Expected output is a JSON dossier containing:

- research status
- committee summary
- seven-dimensional scorecard
- bull, base, and bear cases
- first rejection
- thesis invalidation conditions
- next research steps
- evidence IDs
- unresolved questions

The default fixture should normally return `valuation_gated` because it intentionally omits a live valuation dataset.

## Live Agents SDK demo

Edit `.env`:

```dotenv
DEMO_MODE=false
OPENAI_API_KEY=your_key_here
OPENAI_AGENTS_MODEL=gpt-5.4-mini
OPENAI_AGENTS_TRACE_INCLUDE_SENSITIVE_DATA=false
```

Run:

```bash
make run-committee-live
```

Equivalent command:

```bash
python -m scripts.run_investment_committee_demo --live
```

The Agents SDK trace groups all specialist and committee runs under the requested symbol. To disable trace export completely:

```dotenv
OPENAI_AGENTS_DISABLE_TRACING=1
```

## API demo

Start the API:

```bash
make run-demo
```

Open:

- Dashboard: `http://localhost:8000/`
- OpenAPI: `http://localhost:8000/docs`

Offline committee request:

```bash
curl -X POST "http://localhost:8000/research/committee?offline_demo=true" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NVDA",
    "asset_name": "NVIDIA",
    "asset_class": "stock",
    "theme": "AI infrastructure",
    "horizon_years": 7,
    "existing_positions": ["VOO", "QQQM", "SMH"],
    "question": "Does this candidate deserve deeper long-term research?",
    "evidence": [
      {
        "evidence_id": "FILING-1",
        "source_name": "Annual filing fixture",
        "source_type": "primary_fixture",
        "summary": "Theme-linked demand increased, but valuation was not supplied.",
        "reliability": 0.9,
        "freshness_days": 10
      }
    ]
  }'
```

For a live run, set `DEMO_MODE=false`, configure `OPENAI_API_KEY`, and omit `offline_demo=true`.

## Tests

```bash
make test-unit
```

Focused test:

```bash
pytest tests/unit/test_investment_agents.py -v
```

The unit suite validates:

- ticker and portfolio-position normalization
- evidence-quality bounds
- overlap detection
- deterministic dossier generation
- missing-evidence rejection
- human-review language

## Source files

```text
packages/investment_agents/
├── __init__.py
├── agents.py
├── guardrails.py
├── models.py
├── orchestrator.py
└── tools.py

scripts/run_investment_committee_demo.py
tests/unit/test_investment_agents.py
```

## Next integration work

The current API accepts an evidence bundle explicitly. The next production step is to build a repository-backed evidence assembler that pulls current filings, fundamentals, market valuation, ETF holdings, and portfolio positions from the existing storage layer before calling the agents.
