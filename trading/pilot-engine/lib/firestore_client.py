"""Server-only Firestore access through the Firebase Admin SDK."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any, Protocol
from uuid import uuid4

import firebase_admin
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

ALLOWED_BATCH_STATUSES = frozenset({"pending", "approved", "rejected", "executed", "failed"})


class DocumentSnapshot(Protocol):
    """Subset of a Firestore document snapshot used by this project."""

    exists: bool

    def to_dict(self) -> dict[str, Any] | None:
        """Return the document payload."""


class DocumentReference(Protocol):
    """Subset of a Firestore document reference used by this project."""

    def set(self, data: dict[str, Any], *, merge: bool = False) -> Any:
        """Create or merge document data."""

    def create(self, data: dict[str, Any]) -> Any:
        """Create a document only when it does not already exist."""

    def get(self) -> DocumentSnapshot:
        """Fetch the current document snapshot."""

    def update(self, data: dict[str, Any]) -> Any:
        """Update fields on an existing document."""


class Query(Protocol):
    """Subset of a Firestore query used by this project."""

    def where(self, *, filter: Any) -> Query:
        """Add a structured field filter."""

    def stream(self) -> Any:
        """Stream matching document snapshots."""


class CollectionReference(Query, Protocol):
    """Subset of a Firestore collection reference used by this project."""

    def document(self, document_id: str) -> DocumentReference:
        """Address a document by ID."""


class FirestoreClient(Protocol):
    """Structural interface implemented by Firestore and test clients."""

    def collection(self, name: str) -> CollectionReference:
        """Address a top-level collection."""


def get_firestore_client() -> FirestoreClient:
    """Return an Admin SDK Firestore client using application-default credentials."""
    try:
        app = firebase_admin.get_app()
    except ValueError:
        project_id = (
            os.getenv("FIREBASE_PROJECT_ID")
            or os.getenv("GOOGLE_CLOUD_PROJECT")
            or os.getenv("GCLOUD_PROJECT")
        )
        if project_id:
            app = firebase_admin.initialize_app(options={"projectId": project_id})
        else:
            app = firebase_admin.initialize_app()
    return firestore.client(app=app)


def upsert_trade(
    trade: Mapping[str, Any],
    *,
    client: FirestoreClient | None = None,
) -> str:
    """Upsert one normalized trade using its dedupe hash as the document ID."""
    dedupe_hash = _require_document_id(trade.get("dedupe_hash"), "dedupe_hash")
    payload = dict(trade)
    payload.pop("dedupe_hash")
    payload.setdefault("ingested_at", firestore.SERVER_TIMESTAMP)

    database = client or get_firestore_client()
    database.collection("pilot_trades").document(dedupe_hash).set(payload, merge=True)
    return dedupe_hash


def get_target_weights(
    pilot: str,
    *,
    client: FirestoreClient | None = None,
) -> dict[str, float]:
    """Return ticker-to-weight values for one pilot."""
    pilot_id = _require_nonempty_string(pilot, "pilot")
    database = client or get_firestore_client()
    query = database.collection("target_weights").where(filter=FieldFilter("pilot", "==", pilot_id))

    weights: dict[str, float] = {}
    for snapshot in query.stream():
        payload = snapshot.to_dict()
        if payload is None:
            continue
        ticker = _require_nonempty_string(payload.get("ticker"), "ticker")
        weight = payload.get("weight")
        if isinstance(weight, bool) or not isinstance(weight, (int, float)):
            raise ValueError(f"target weight for {ticker} must be numeric")
        weights[ticker] = float(weight)
    return weights


def create_batch(
    batch: Mapping[str, Any],
    *,
    batch_id: str | None = None,
    client: FirestoreClient | None = None,
) -> str:
    """Create a new pending order batch without permitting implicit approval."""
    requested_status = batch.get("status", "pending")
    if requested_status != "pending":
        raise ValueError("new order batches must have pending status")

    sleeve_notional = batch.get("sleeve_notional")
    if (
        isinstance(sleeve_notional, bool)
        or not isinstance(sleeve_notional, (int, float))
        or sleeve_notional < 0
    ):
        raise ValueError("sleeve_notional must be a non-negative number")
    summary_md = _require_nonempty_string(batch.get("summary_md"), "summary_md")
    orders = batch.get("orders")
    if not isinstance(orders, list) or not all(isinstance(order, Mapping) for order in orders):
        raise ValueError("orders must be a list of mappings")

    document_id = _require_document_id(batch_id or str(uuid4()), "batch_id")
    payload = {
        "status": "pending",
        "created_at": firestore.SERVER_TIMESTAMP,
        "decided_at": None,
        "decided_by": None,
        "sleeve_notional": float(sleeve_notional),
        "summary_md": summary_md,
        "orders": [dict(order) for order in orders],
    }

    database = client or get_firestore_client()
    database.collection("order_batches").document(document_id).create(payload)
    return document_id


def get_batch(
    batch_id: str,
    *,
    client: FirestoreClient | None = None,
) -> dict[str, Any] | None:
    """Fetch an order batch or return ``None`` when it does not exist."""
    document_id = _require_document_id(batch_id, "batch_id")
    database = client or get_firestore_client()
    snapshot = database.collection("order_batches").document(document_id).get()
    if not snapshot.exists:
        return None
    return snapshot.to_dict()


def set_batch_status(
    batch_id: str,
    status: str,
    *,
    decided_by: str | None = None,
    client: FirestoreClient | None = None,
) -> None:
    """Set a validated batch status and record explicit human decisions."""
    document_id = _require_document_id(batch_id, "batch_id")
    if status not in ALLOWED_BATCH_STATUSES:
        raise ValueError(f"unsupported batch status: {status!r}")

    update: dict[str, Any] = {"status": status}
    if status in {"approved", "rejected"}:
        update["decided_by"] = _require_nonempty_string(decided_by, "decided_by")
        update["decided_at"] = firestore.SERVER_TIMESTAMP
    elif status == "pending":
        update["decided_by"] = None
        update["decided_at"] = None

    database = client or get_firestore_client()
    database.collection("order_batches").document(document_id).update(update)


def _require_document_id(value: Any, field_name: str) -> str:
    document_id = _require_nonempty_string(value, field_name)
    if "/" in document_id:
        raise ValueError(f"{field_name} cannot contain '/'")
    return document_id


def _require_nonempty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()
