"""Firebase / Firestore initialization and client factory."""
from __future__ import annotations

import os
from typing import Any

import structlog

logger = structlog.get_logger()

_firebase_app = None
_firestore_client = None


def _init_firebase() -> None:
    global _firebase_app, _firestore_client
    if _firebase_app is not None:
        return

    import firebase_admin
    from firebase_admin import credentials, firestore_async

    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")

    if emulator_host:
        # Local emulator — no credentials needed
        logger.info("firebase_using_emulator", host=emulator_host)
        _firebase_app = firebase_admin.initialize_app(options={"projectId": project_id or "demo-trading-intel"})
    elif service_account_path and os.path.exists(service_account_path):
        cred = credentials.Certificate(service_account_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("firebase_initialized", source="service_account_file")
    elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        cred = credentials.ApplicationDefault()
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("firebase_initialized", source="application_default")
    else:
        # Demo mode — use emulator on default port or raise helpful error
        demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        if demo_mode:
            os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8080")
            logger.warning("firebase_demo_mode_no_credentials")
            _firebase_app = firebase_admin.initialize_app(options={"projectId": "demo-trading-intel"})
        else:
            raise EnvironmentError(
                "Firebase credentials not found. Set one of:\n"
                "  FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/serviceAccount.json\n"
                "  GOOGLE_APPLICATION_CREDENTIALS=/path/to/serviceAccount.json\n"
                "  FIRESTORE_EMULATOR_HOST=localhost:8080  (for local dev)\n"
                "  DEMO_MODE=true  (auto-uses emulator)"
            )

    _firestore_client = firestore_async.client()


def get_db() -> Any:
    """FastAPI dependency — returns the async Firestore client."""
    if _firestore_client is None:
        _init_firebase()
    return _firestore_client


def get_firestore_client() -> Any:
    """Return the async Firestore client (used by background jobs)."""
    if _firestore_client is None:
        _init_firebase()
    return _firestore_client


async def create_tables() -> None:
    """No-op for Firebase — Firestore creates collections automatically."""
    _init_firebase()
    logger.info("firebase_ready")


# Compat shim so background services can use `async with AsyncSessionLocal() as db`
# pattern without changes. Returns the Firestore client directly.
class _FirestoreSessionFactory:
    """Context manager that yields the Firestore client — matches SQLAlchemy AsyncSessionLocal interface."""

    def __call__(self) -> "_FirestoreSessionFactory":
        return self

    async def __aenter__(self) -> Any:
        return get_firestore_client()

    async def __aexit__(self, *_: Any) -> None:
        pass  # No cleanup needed for Firestore


AsyncSessionLocal = _FirestoreSessionFactory()
