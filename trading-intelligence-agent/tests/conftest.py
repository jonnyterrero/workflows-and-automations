"""Pytest configuration and shared fixtures."""
from __future__ import annotations

import os
import pytest
import pytest_asyncio

# Use Firestore emulator for all tests
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8080")
os.environ.setdefault("FIREBASE_PROJECT_ID", "demo-trading-intel")
os.environ.setdefault("LOG_LEVEL", "WARNING")


@pytest_asyncio.fixture(scope="session")
async def firebase_init():
    """Initialize Firebase once for the test session."""
    from packages.storage.firebase_db import _init_firebase
    _init_firebase()


@pytest_asyncio.fixture
async def db_session(firebase_init):
    """Provide a Firestore client per test."""
    from packages.storage.firebase_db import get_firestore_client
    return get_firestore_client()
