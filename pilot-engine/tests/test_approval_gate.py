"""Tests for the Phase 0 execution approval gate."""

import pytest

from execute.public_client import BatchNotApprovedError, require_approved_batch
from tests.conftest import FakeFirestoreClient


def test_require_approved_batch_rejects_missing_batch(
    firestore_client: FakeFirestoreClient,
) -> None:
    with pytest.raises(BatchNotApprovedError, match="does not exist"):
        require_approved_batch("missing", client=firestore_client)


@pytest.mark.parametrize("status", ["pending", "rejected", "failed", "executed"])
def test_require_approved_batch_rejects_non_approved_status(
    status: str,
    firestore_client: FakeFirestoreClient,
) -> None:
    firestore_client.documents["order_batches"] = {"batch-1": {"status": status, "orders": []}}

    with pytest.raises(BatchNotApprovedError, match=status):
        require_approved_batch("batch-1", client=firestore_client)


def test_require_approved_batch_returns_approved_batch(
    firestore_client: FakeFirestoreClient,
) -> None:
    expected = {"status": "approved", "orders": []}
    firestore_client.documents["order_batches"] = {"batch-1": expected.copy()}

    assert require_approved_batch("batch-1", client=firestore_client) == expected
