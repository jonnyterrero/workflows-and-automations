# Agent Trio

Three specialized agents on the OpenAI Agents SDK, wired together with handoffs, guardrails, and a single FastAPI runner that ships to AWS Fargate.

| Agent | Role | Key tools |
|---|---|---|
| **Atlas** (second brain / secretary) | Tasks, notes, daily briefs, and the front-door router | `add_task`, `list_tasks`, `complete_task`, `add_note`, `search_notes`, `daily_brief` |
| **TradeDesk** (day-trading decision support) | Real-time quotes, technical/fundamental read, sentiment, risk-sized trade plans | `get_quote`, `get_price_history`, `get_fundamentals`, `get_market_news`, `get_social_sentiment`, `position_sizing` |
| **Scholar** (deep research / homework) | Literature search, source verification, structured Markdown reports | `search_arxiv`, `search_semantic_scholar`, `fetch_url`, `save_report` |

Atlas owns the conversation by default and hands off to TradeDesk or Scholar when the request is out of scope.

## Architecture

```
                user
                 │
                 ▼
            ┌──────────┐    handoff: transfer_to_TradeDesk   ┌──────────────┐
            │  Atlas   │ ────────────────────────────────────►│  TradeDesk   │
            │ (router) │ ────────────────────────────────────►│   Scholar    │
            └──────────┘    handoff: transfer_to_Scholar      └──────────────┘
                 │
                 │  function tools (Notion / local JSON store)
                 ▼
          tasks · notes · daily brief
```

Guardrails:
- **Input** on TradeDesk: blocks personalized financial-advice asks ("what should I do with my 401k").
- **Output** on TradeDesk: requires a risk-disclosure block on directive trade calls.
- **Input** on Scholar: blocks academic-integrity violations (taking exams, impersonation).

Both guardrails are LLM-classifier agents wired with `@input_guardrail` / `@output_guardrail`.

## Project layout

```
agent-trio/
├── src/agent_trio/
│   ├── agents/                # Agent definitions (Atlas, TradeDesk, Scholar)
│   ├── tools/                 # Function tools per domain
│   ├── guardrails/            # Input + output guardrails
│   ├── common/                # Settings, logging
│   ├── runner.py              # CLI / REPL
│   └── server.py              # FastAPI HTTP server
├── deploy/aws/
│   ├── cloudformation.yaml    # ECS Fargate + ALB + IAM + SSM-backed secrets
│   └── deploy.sh              # Build → ECR push → CFN deploy
├── scripts/dev.sh             # Local venv + repl/serve/test
├── tests/test_smoke.py
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Quick start (local)

```bash
cp .env.example .env       # add OPENAI_API_KEY
./scripts/dev.sh repl                                # talk to Atlas
./scripts/dev.sh repl --agent trading                # talk to TradeDesk directly
./scripts/dev.sh repl --agent research -p "review of CoCrMo wear in TKA implants"
./scripts/dev.sh serve                               # FastAPI on :8080
./scripts/dev.sh test                                # smoke tests
```

HTTP example:

```bash
curl -s localhost:8080/chat \
  -H "Authorization: Bearer $API_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"agent":"atlas","message":"add a task to review NVDA earnings, due tomorrow, high priority","session_id":"u-dijon"}'
```

## Deploy to AWS (ECS Fargate behind an ALB)

One-time prep:

```bash
aws configure
aws ssm put-parameter --name /agent-trio/OPENAI_API_KEY --type SecureString --value sk-...
aws ssm put-parameter --name /agent-trio/API_AUTH_TOKEN --type SecureString --value "$(openssl rand -hex 24)"
```

Deploy:

```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=123456789012
export VPC_ID=vpc-xxxxxxx
export SUBNET_IDS=subnet-aaa,subnet-bbb     # 2+ AZs

./deploy/aws/deploy.sh
```

The script builds a `linux/amd64` image, pushes to ECR, deploys the CloudFormation stack (`deploy/aws/cloudformation.yaml`), waits for the service to stabilize, and prints the public ALB URL.

What the stack provisions:
- ECS Fargate cluster + service (1 task default, easy to scale via `DesiredCount`)
- Application Load Balancer with `/health` checks
- IAM execution role with `ssm:GetParameter` access to `/agent-trio/*`
- CloudWatch log group `/ecs/agent-trio` (14-day retention)
- Security groups limiting service ingress to the ALB

## Customizing

- **Swap data feeds.** `src/agent_trio/tools/market_tools.py` uses `yfinance` so the starter is keyless. Replace function bodies with Polygon, Alpaca, or IEX without touching the agent.
- **Real Notion.** Set `NOTION_API_KEY` + `NOTION_TASKS_DB_ID` and the tools transparently dual-write to your database. With keys absent, everything stays in `/tmp/agent_trio_store`.
- **Stronger model.** Set `AGENT_MODEL_STRONG=gpt-4.1` (or `gpt-5` once available to your account) — used by TradeDesk and Scholar.
- **Persistent sessions across restarts.** `SQLiteSession(session_id)` already persists conversation memory locally. For multi-instance ECS, swap to a Postgres-backed session implementation or front the ALB with sticky sessions.

## Notes for production

- Add WAF in front of the ALB if you expose `/chat` publicly.
- Move secrets from SSM Parameter Store to AWS Secrets Manager if you need automatic rotation.
- Wire `traces` to OpenAI's tracing UI (set `OPENAI_API_KEY` and the SDK uploads automatically) or pipe to your own collector.
- For burst traffic, set `MaximumPercent: 200` deploys + autoscaling on `CPUUtilization` >= 60%.

## License

MIT.
