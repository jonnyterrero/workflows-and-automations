"""Dossier persistence and the decision journal.

Every dossier write also lands a timestamped snapshot. That history is what
makes point-in-time backtesting possible later: a future model can be trained
on exactly the evidence that existed on the decision date, which is the only
way to avoid look-ahead bias. Overwriting in place would quietly destroy the
dataset before it is ever collected.
"""
from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fdr.config import get_settings
from fdr.schemas import AssetDossier, DecisionJournalEntry, Vote


def _data_dir() -> Path:
    path = get_settings().data_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def _dossier_dir(symbol: str) -> Path:
    path = _data_dir() / "dossiers" / symbol.upper()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _journal_path() -> Path:
    return _data_dir() / "decision_journal.jsonl"


def save_dossier(dossier: AssetDossier) -> dict[str, Any]:
    """Persist a dossier as current, and archive an immutable snapshot."""
    directory = _dossier_dir(dossier.symbol)
    payload = dossier.model_dump(mode="json")

    # Microsecond precision, plus a collision guard: two saves in the same
    # instant must produce two snapshots. Overwriting would silently destroy
    # the history that point-in-time backtesting depends on.
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    snapshot_path = directory / f"{stamp}.json"
    suffix = 1
    while snapshot_path.exists():
        snapshot_path = directory / f"{stamp}-{suffix}.json"
        suffix += 1
    snapshot_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    (directory / "latest.json").write_text(json.dumps(payload, indent=2, sort_keys=True))

    return {
        "symbol": dossier.symbol,
        "saved": True,
        "snapshot": str(snapshot_path),
        "research_status": dossier.research_status.value,
    }


def load_dossier(symbol: str) -> AssetDossier | None:
    path = _dossier_dir(symbol) / "latest.json"
    if not path.exists():
        return None
    return AssetDossier.model_validate_json(path.read_text())


def load_snapshots(symbol: str) -> list[Path]:
    """Archived snapshots, oldest first."""
    directory = _dossier_dir(symbol)
    return sorted(p for p in directory.glob("*.json") if p.name != "latest.json")


def load_previous_dossier(symbol: str) -> AssetDossier | None:
    """The state before the most recent write — the baseline for change detection."""
    snapshots = load_snapshots(symbol)
    if len(snapshots) < 2:
        return None
    return AssetDossier.model_validate_json(snapshots[-2].read_text())


def record_decision(
    user_id: str,
    symbol: str,
    vote: Vote | str,
    what_was_believed: str,
    risks_accepted: list[str] | None = None,
    expected_horizon_months: int | None = None,
    invalidation_conditions: list[str] | None = None,
) -> dict[str, Any]:
    """Append a decision, snapshotting the dossier as it stood at the time.

    Votes are recorded per user and never aggregated here. Group consensus is
    deliberately not computed at write time so the UI can withhold it until a
    user has committed their own judgement, which is what keeps the vote
    independent rather than anchored.
    """
    dossier = load_dossier(symbol)
    entry = DecisionJournalEntry(
        entry_id=str(uuid.uuid4()),
        user_id=user_id,
        symbol=symbol.upper(),
        vote=Vote(vote) if isinstance(vote, str) else vote,
        what_was_believed=what_was_believed,
        supporting_evidence=dossier.all_evidence() if dossier else [],
        risks_accepted=risks_accepted or [],
        expected_horizon_months=expected_horizon_months,
        invalidation_conditions=(
            invalidation_conditions
            if invalidation_conditions is not None
            else (dossier.what_would_invalidate if dossier else [])
        ),
        dossier_snapshot=dossier.model_dump(mode="json") if dossier else {},
    )

    with _journal_path().open("a") as handle:
        handle.write(json.dumps(entry.model_dump(mode="json"), sort_keys=True) + "\n")

    return {"entry_id": entry.entry_id, "symbol": entry.symbol, "vote": entry.vote.value}


def list_decisions(symbol: str | None = None, user_id: str | None = None) -> list[dict[str, Any]]:
    path = _journal_path()
    if not path.exists():
        return []

    rows: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if symbol and row.get("symbol") != symbol.upper():
            continue
        if user_id and row.get("user_id") != user_id:
            continue
        rows.append(row)
    return rows
