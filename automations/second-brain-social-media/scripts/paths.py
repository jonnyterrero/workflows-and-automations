"""Resolve the local social-brain DATA folder.

Pipeline scripts live in this public repo. Generated archives, content packs,
and raw platform exports never do.

Override order:
  1. SOCIAL_BRAIN_ROOT env var
  2. ../config.local.json  {"data_root": "...", "vault": "..."}
  3. Default machine path if it exists
  4. This scripts/ folder, only if someone copied the scripts into a working dir
"""
from __future__ import annotations

import json
import os
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
LAYER_DIR = SCRIPTS_DIR.parent

DEFAULT_DATA_ROOT = Path(r"C:\Users\JTerr\Downloads\Social media clone")
DEFAULT_VAULT = Path(
    r"C:\Users\JTerr\OneDrive\Programming Projects\Heartwire\heartwire"
    r"\The Batcave\05 Jonnys HQ\Social Media Second Brain"
)


def _local_config() -> dict:
    cfg = LAYER_DIR / "config.local.json"
    if not cfg.exists():
        return {}
    try:
        payload = json.loads(cfg.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid {cfg}: {exc}") from exc
    return payload if isinstance(payload, dict) else {}


def data_root() -> Path:
    env = os.environ.get("SOCIAL_BRAIN_ROOT")
    if env:
        return Path(env).expanduser().resolve()

    cfg_root = _local_config().get("data_root")
    if cfg_root:
        return Path(cfg_root).expanduser().resolve()

    if DEFAULT_DATA_ROOT.exists():
        return DEFAULT_DATA_ROOT.resolve()

    # Copied-into-working-folder fallback (legacy layout).
    if (SCRIPTS_DIR / "content_pack").exists() or any(SCRIPTS_DIR.glob("instagram-*")):
        return SCRIPTS_DIR

    raise SystemExit(
        "Social-brain data folder not found. Set SOCIAL_BRAIN_ROOT, or copy "
        "config.example.json to config.local.json and set data_root, or drop "
        f"exports at {DEFAULT_DATA_ROOT}"
    )


def vault_dir() -> Path:
    env = os.environ.get("SOCIAL_BRAIN_VAULT")
    if env:
        return Path(env).expanduser().resolve()
    cfg_vault = _local_config().get("vault")
    if cfg_vault:
        return Path(cfg_vault).expanduser().resolve()
    return DEFAULT_VAULT
