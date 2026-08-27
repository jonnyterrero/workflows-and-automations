"""Tests for source-register seeding."""

from firebase.seed import seed_sources
from tests.conftest import FakeFirestoreClient


def test_seed_sources_is_idempotent(
    firestore_client: FakeFirestoreClient,
) -> None:
    assert seed_sources(client=firestore_client) == 4
    assert seed_sources(client=firestore_client) == 4

    sources = firestore_client.documents["source_register"]
    assert set(sources) == {"apify", "capitol_trades", "edgar", "quiver"}
    assert sources["edgar"]["reliability"] == "A"
    assert all(source["last_ok"] is None for source in sources.values())
