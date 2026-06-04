"""Storage backend — re-exports Firebase client as the canonical DB interface.

All services import from this module so switching backends only requires
changing this file (and firebase_db.py).
"""
from packages.storage.firebase_db import (
    AsyncSessionLocal,
    create_tables,
    get_db,
    get_firestore_client,
)

__all__ = ["AsyncSessionLocal", "create_tables", "get_db", "get_firestore_client"]
