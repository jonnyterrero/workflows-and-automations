#!/usr/bin/env python3
"""Run eval fixtures against live Managed Agents and record transcripts.

Sessions park on `always_ask` tools: the agent emits `agent.tool_use`, the
session goes idle, and nothing further happens until a `user.tool_confirmation`
event arrives. This runner answers those automatically so a suite can run
unattended, and records every decision it made.

The runner does not grade. It captures the response so a human (or a separate
judge pass) can compare it against `expected_output`.

  python scripts/run_evals.py --skill trading-agent
  python scripts/run_evals.py --skill deep-researcher --ids adversarial-1,adversarial-2
  python scripts/run_evals.py --all --tool-policy deny
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
AGENT_IDS = ROOT / "dist" / "agent_ids.json"
RESULTS = ROOT / "dist" / "eval_results"

POLL_SECONDS = 5
MAX_POLLS = 60
DENY_MESSAGE = (
    "Tool denied by the eval harness. Your skills are already attached as "
    "context; answer from them directly."
)


def load_agent_ids() -> dict:
    if not AGENT_IDS.exists():
        raise SystemExit(
            f"Missing {AGENT_IDS}. Run deploy_agents.py --phase specialists --execute first."
        )
    return json.loads(AGENT_IDS.read_text(encoding="utf-8"))


def pending_tool_use_ids(client, session_id: str, answered: set[str]) -> list[str]:
    """Tool-use events still waiting on a confirmation."""
    out = []
    for ev in client.beta.sessions.events.list(session_id):
        if getattr(ev, "type", "") in ("agent.tool_use", "agent.mcp_tool_use"):
            eid = getattr(ev, "id", None)
            if eid and eid not in answered:
                out.append(eid)
    return out


def collect_text(client, session_id: str, seen: set[str]) -> list[str]:
    texts = []
    for ev in client.beta.sessions.events.list(session_id):
        if getattr(ev, "type", "") != "agent.message":
            continue
        eid = getattr(ev, "id", None)
        if eid in seen:
            continue
        seen.add(eid)
        for blk in getattr(ev, "content", None) or []:
            if getattr(blk, "type", "") == "text":
                texts.append(blk.text)
    return texts


def session_idle(client, session_id: str) -> bool:
    kinds = [getattr(e, "type", "") for e in client.beta.sessions.events.list(session_id)]
    if not kinds:
        return False
    for k in reversed(kinds):
        if k.startswith("session.status_"):
            return k == "session.status_idle"
    return False


def run_one(client, agent_id: str, env_id: str, case: dict, policy: str) -> dict:
    session = client.beta.sessions.create(
        agent={"type": "agent", "id": agent_id},
        environment_id=env_id,
        title=f"eval {case['id']}",
    )
    client.beta.sessions.events.send(
        session.id,
        events=[{"type": "user.message", "content": [{"type": "text", "text": case["prompt"]}]}],
    )

    seen: set[str] = set()
    answered: set[str] = set()
    texts: list[str] = []
    tool_calls: list[str] = []

    for _ in range(MAX_POLLS):
        time.sleep(POLL_SECONDS)
        texts += collect_text(client, session.id, seen)

        for tid in pending_tool_use_ids(client, session.id, answered):
            answered.add(tid)
            tool_calls.append(tid)
            event = {
                "type": "user.tool_confirmation",
                "tool_use_id": tid,
                "result": policy,
            }
            if policy == "deny":
                event["deny_message"] = DENY_MESSAGE
            try:
                client.beta.sessions.events.send(session.id, events=[event])
            except Exception as exc:  # already resolved, or not awaiting confirmation
                tool_calls[-1] = f"{tid} (confirm failed: {type(exc).__name__})"

        if texts and session_idle(client, session.id):
            break

    return {
        "id": case["id"],
        "prompt": case["prompt"],
        "expected_output": case.get("expected_output", ""),
        "response": "\n".join(texts).strip(),
        "session_id": session.id,
        "tool_confirmations": {"policy": policy, "count": len(tool_calls)},
        "status": "responded" if texts else "no_response",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Run eval fixtures against live agents")
    ap.add_argument("--skill", help="Skill slug, e.g. trading-agent")
    ap.add_argument("--all", action="store_true", help="Run every eval file with a live agent")
    ap.add_argument(
        "--coordinator",
        action="store_true",
        help="Run evals/team-routing.json against the coordinator (delegates to subagents; slow)",
    )
    ap.add_argument("--ids", help="Comma-separated eval ids to run (default: all in the file)")
    ap.add_argument(
        "--tool-policy",
        choices=("deny", "allow"),
        default="deny",
        help="How to answer always_ask tool confirmations (default: deny)",
    )
    args = ap.parse_args()

    if not args.skill and not args.all and not args.coordinator:
        raise SystemExit("Pass --skill <slug>, --all, or --coordinator")
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set")

    import anthropic

    client = anthropic.Anthropic()
    ids = load_agent_ids()
    specialists = ids["specialists"]

    envs = list(client.beta.environments.list())
    if not envs:
        raise SystemExit("No environment available. Create one in Console first.")
    env_id = envs[0].id

    RESULTS.mkdir(parents=True, exist_ok=True)
    summary = []

    if args.coordinator:
        coord = ids.get("coordinator")
        if not coord:
            raise SystemExit("No coordinator in agent_ids.json. Run --phase coordinator --execute.")
        path = EVALS / "team-routing.json"
        raw = json.loads(path.read_text(encoding="utf-8"))["evals"]
        # team-routing.json predates the per-skill schema: no ids, `expected` not
        # `expected_output`. Normalize so results match every other result file.
        cases = [
            {
                "id": c.get("id") or f"routing-{i}",
                "prompt": c["prompt"],
                "expected_output": c.get("expected_output") or c.get("expected", ""),
            }
            for i, c in enumerate(raw, 1)
        ]
        if args.ids:
            wanted = {i.strip() for i in args.ids.split(",")}
            cases = [c for c in cases if c["id"] in wanted]
        print(f"\n=== coordinator ({len(cases)} cases) -> {coord['agent_id']} ===")
        results = []
        for case in cases:
            res = run_one(client, coord["agent_id"], env_id, case, args.tool_policy)
            results.append(res)
            flag = "ok " if res["status"] == "responded" else "NONE"
            print(f"  [{flag}] {res['id']}  ({res['tool_confirmations']['count']} tool confirms)")
        out = RESULTS / "coordinator.json"
        out.write_text(
            json.dumps({"skill": "coordinator", "results": results}, indent=2), encoding="utf-8"
        )
        summary.append(("coordinator", sum(r["status"] == "responded" for r in results), len(results)))
        print(f"  wrote {out.relative_to(ROOT)}")
        slugs = []
    elif args.all:
        slugs = [p.stem for p in sorted(EVALS.glob("*.json")) if p.stem in specialists]
    else:
        slugs = [args.skill]

    for slug in slugs:
        path = EVALS / f"{slug}.json"
        if not path.exists():
            print(f"SKIP {slug}: no eval file")
            continue
        if slug not in specialists:
            print(f"SKIP {slug}: no live agent id")
            continue

        cases = json.loads(path.read_text(encoding="utf-8"))["evals"]
        if args.ids:
            wanted = {i.strip() for i in args.ids.split(",")}
            cases = [c for c in cases if c["id"] in wanted]

        agent_id = specialists[slug]["agent_id"]
        print(f"\n=== {slug} ({len(cases)} cases) -> {agent_id} ===")
        results = []
        for case in cases:
            res = run_one(client, agent_id, env_id, case, args.tool_policy)
            results.append(res)
            flag = "ok " if res["status"] == "responded" else "NONE"
            print(f"  [{flag}] {res['id']}  ({res['tool_confirmations']['count']} tool confirms)")

        out = RESULTS / f"{slug}.json"
        out.write_text(json.dumps({"skill": slug, "results": results}, indent=2), encoding="utf-8")
        summary.append((slug, sum(r["status"] == "responded" for r in results), len(results)))
        print(f"  wrote {out.relative_to(ROOT)}")

    print("\n=== summary ===")
    for slug, ok, total in summary:
        print(f"{slug}: {ok}/{total} responded")
    print("\nResponses are recorded, not graded. Review against expected_output.")


if __name__ == "__main__":
    main()
