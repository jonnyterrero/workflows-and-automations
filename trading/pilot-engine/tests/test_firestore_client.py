"""Behavior tests for shared Firestore helpers."""

from __future__ import annotations

from typing import Any

import pytest

from lib import firestore_client as subject
from tests.conftest import FakeFirestoreClient


def test_get_firestore_client_initializes_default_app(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = object()
    client = object()
    initialized_with: dict[str, Any] = {}

    def missing_app() -> None:
        raise ValueError

    def initialize_app(*, options: dict[str, str]) -> object:
        initialized_with.update(options)
        return app

    monkeypatch.setenv("FIREBASE_PROJECT_ID", "pilot-engine-test")
    monkeypatch.setattr(subject.firebase_admin, "get_app", missing_app)
    monkeypatch.setattr(subject.firebase_admin, "initialize_app", initialize_app)
    monkeypatch.setattr(subject.firestore, "client", lambda *, app: client)

    assert subject.get_firestore_client() is client
    assert initialized_with == {"projectId": "pilot-engine-test"}


def test_upsert_trade_uses_dedupe_hash_as_document_id(
    firestore_client: FakeFirestoreClient,
) -> None:
    trade: dict[str, Any] = {
        "dedupe_hash": "abc123",
        "pilot": "pelosi",
        "ticker": "NVDA",
        "txn_type": "purchase",
    }

    document_id = subject.upsert_trade(trade, client=firestore_client)
    stored = firestore_client.documents["pilot_trades"]["abc123"]

    assert document_id == "abc123"
    assert stored["ticker"] == "NVDA"
    assert "ingested_at" in stored


def test_upsert_trade_rejects_missing_dedupe_hash(
    firestore_client: FakeFirestoreClient,
) -> None:
    with pytest.raises(ValueError, match="dedupe_hash"):
        subject.upsert_trade({"pilot": "pelosi"}, client=firestore_client)

    assert firestore_client.documents == {}


def test_get_target_weights_filters_by_pilot(
    firestore_client: FakeFirestoreClient,
) -> None:
    firestore_client.documents["target_weights"] = {
        "pelosi_NVDA": {"pilot": "pelosi", "ticker": "NVDA", "weight": 0.6},
        "pelosi_GOOGL": {"pilot": "pelosi", "ticker": "GOOGL", "weight": 0.4},
        "other_NVDA": {"pilot": "other", "ticker": "NVDA", "weight": 1.0},
    }

    assert subject.get_target_weights("pelosi", client=firestore_client) == {
        "GOOGL": 0.4,
        "NVDA": 0.6,
    }


def test_create_batch_forces_pending_status(
    firestore_client: FakeFirestoreClient,
) -> None:
    batch = {
        "sleeve_notional": 50.0,
        "summary_md": "# Proposed batch",
        "orders": [{"ticker": "NVDA", "side": "buy", "notional": 10.0}],
    }

    batch_id = subject.create_batch(
        batch,
        batch_id="batch-1",
        client=firestore_client,
    )
    stored = firestore_client.documents["order_batches"]["batch-1"]

    assert batch_id == "batch-1"
    assert stored["status"] == "pending"
    assert stored["decided_at"] is None
    assert stored["decided_by"] is None
    assert "created_at" in stored


def test_create_batch_rejects_non_pending_input(
    firestore_client: FakeFirestoreClient,
) -> None:
    with pytest.raises(ValueError, match="pending"):
        subject.create_batch(
            {
                "status": "approved",
                "sleeve_notional": 50.0,
                "summary_md": "unsafe",
                "orders": [],
            },
            client=firestore_client,
        )


def test_get_batch_returns_none_for_unknown_id(
    firestore_client: FakeFirestoreClient,
) -> None:
    assert subject.get_batch("missing", client=firestore_client) is None


def test_set_batch_status_records_human_decision(
    firestore_client: FakeFirestoreClient,
) -> None:
    firestore_client.documents["order_batches"] = {
        "batch-1": {"status": "pending", "decided_at": None, "decided_by": None}
    }

    subject.set_batch_status(
        "batch-1",
        "approved",
        decided_by="jonathan",
        client=firestore_client,
    )
    stored = firestore_client.documents["order_batches"]["batch-1"]

    assert stored["status"] == "approved"
    assert stored["decided_by"] == "jonathan"
    assert stored["decided_at"] is not None


@pytest.mark.parametrize("status", ["", "queued", "APPROVED"])
def test_set_batch_status_rejects_unknown_status(
    status: str,
    firestore_client: FakeFirestoreClient,
) -> None:
    with pytest.raises(ValueError, match="status"):
        subject.set_batch_status(
            "batch-1",
            status,
            decided_by="jonathan",
            client=firestore_client,
        )


def test_set_batch_status_requires_actor_for_human_decision(
    firestore_client: FakeFirestoreClient,
) -> None:
    with pytest.raises(ValueError, match="decided_by"):
        subject.set_batch_status(
            "batch-1",
            "approved",
            client=firestore_client,
        )
