"""Tests for Firestore rules, indexes, and emulator configuration."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

PROJECT_ROOT = Path(__file__).parents[1]
FIREBASE_DIR = PROJECT_ROOT / "firebase"


def test_firestore_rules_deny_all_client_access() -> None:
    rules = (FIREBASE_DIR / "firestore.rules").read_text(encoding="utf-8")

    assert "allow read, write: if false;" in rules
    assert "allow read, write: if true;" not in rules


def test_firestore_indexes_match_declared_queries() -> None:
    config = json.loads(
        (FIREBASE_DIR / "firestore.indexes.json").read_text(encoding="utf-8")
    )

    actual = {
        (
            index["collectionGroup"],
            tuple((field["fieldPath"], field["order"]) for field in index["fields"]),
        )
        for index in config["indexes"]
    }
    expected = {
        ("pilot_trades", (("pilot", "ASCENDING"), ("filed_date", "DESCENDING"))),
        ("pilot_trades", (("ticker", "ASCENDING"), ("txn_date", "DESCENDING"))),
        ("validation_log", (("pilot", "ASCENDING"), ("signal_date", "DESCENDING"))),
    }

    assert actual == expected
    assert config["fieldOverrides"] == []


@pytest.mark.integration
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_firestore_emulator_denies_unauthenticated_clients(method: str) -> None:
    emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")
    if not emulator_host:
        pytest.skip("Firestore emulator is not running")

    project_id = os.getenv("FIREBASE_PROJECT_ID", "demo-pilot-engine")
    documents_url = (
        f"http://{emulator_host}/v1/projects/{project_id}"
        "/databases/(default)/documents/pilot_trades"
    )
    request = Request(
        documents_url,
        data=b'{"fields":{"ticker":{"stringValue":"BLOCKED"}}}'
        if method == "POST"
        else None,
        headers={"Content-Type": "application/json"},
        method=method,
    )

    with pytest.raises(HTTPError) as error:
        urlopen(request, timeout=5)

    assert error.value.code == 403
