"""Firestore test doubles with in-memory document behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest


@dataclass
class FakeSnapshot:
    id: str
    data: dict[str, Any] | None

    @property
    def exists(self) -> bool:
        return self.data is not None

    def to_dict(self) -> dict[str, Any] | None:
        return None if self.data is None else self.data.copy()


class FakeDocumentReference:
    def __init__(self, documents: dict[str, dict[str, Any]], document_id: str) -> None:
        self._documents = documents
        self.id = document_id

    def set(self, data: dict[str, Any], *, merge: bool = False) -> None:
        if merge:
            self._documents.setdefault(self.id, {}).update(data)
        else:
            self._documents[self.id] = data.copy()

    def create(self, data: dict[str, Any]) -> None:
        if self.id in self._documents:
            raise ValueError(f"document {self.id} already exists")
        self._documents[self.id] = data.copy()

    def get(self) -> FakeSnapshot:
        data = self._documents.get(self.id)
        return FakeSnapshot(self.id, None if data is None else data.copy())

    def update(self, data: dict[str, Any]) -> None:
        if self.id not in self._documents:
            raise KeyError(self.id)
        self._documents[self.id].update(data)


class FakeCollectionReference:
    def __init__(self, documents: dict[str, dict[str, Any]]) -> None:
        self._documents = documents
        self._filters: list[tuple[str, str, Any]] = []

    def document(self, document_id: str) -> FakeDocumentReference:
        return FakeDocumentReference(self._documents, document_id)

    def where(self, *, filter: Any) -> FakeCollectionReference:
        query = FakeCollectionReference(self._documents)
        query._filters = [
            *self._filters,
            (filter.field_path, filter.op_string, filter.value),
        ]
        return query

    def stream(self) -> list[FakeSnapshot]:
        snapshots = []
        for document_id, data in self._documents.items():
            if all(self._matches(data, item) for item in self._filters):
                snapshots.append(FakeSnapshot(document_id, data.copy()))
        return snapshots

    @staticmethod
    def _matches(data: dict[str, Any], item: tuple[str, str, Any]) -> bool:
        field, operator, value = item
        if operator != "==":
            raise NotImplementedError(operator)
        return data.get(field) == value


class FakeFirestoreClient:
    def __init__(self) -> None:
        self.documents: dict[str, dict[str, dict[str, Any]]] = {}

    def collection(self, name: str) -> FakeCollectionReference:
        return FakeCollectionReference(self.documents.setdefault(name, {}))


@pytest.fixture
def firestore_client() -> FakeFirestoreClient:
    return FakeFirestoreClient()
