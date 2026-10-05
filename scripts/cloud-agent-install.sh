#!/usr/bin/env bash
#
# Cloud Agent install script for the Workflows & Automations hub.
#
# Prepares the primary runnable application in this repo — the Trading
# Intelligence Agent (FastAPI + SQLAlchemy data platform) — so a Cursor Cloud
# Agent boots into a ready-to-run state. Safe to re-run: it only updates
# changed dependencies and upserts demo data.
#
# Runs from the repository root (Cursor invokes `install` there).
set -euo pipefail

APP_DIR="trading/trading-intelligence-agent"

echo "==> Ensuring python3 venv support is available"
# The base image's python3 ships without the stdlib venv/ensurepip module.
if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
  sudo apt-get update -qq
  # Install the venv package matching the active python3 minor version.
  PY_MINOR="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  sudo apt-get install -y -qq "python${PY_MINOR}-venv" || sudo apt-get install -y -qq python3-venv
fi

cd "$APP_DIR"

echo "==> Creating virtualenv (.venv) if missing"
if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
. .venv/bin/activate

echo "==> Installing project + dev dependencies (editable)"
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

echo "==> Seeding local SQLite demo database"
export PYTHONPATH="$PWD"
export DEMO_MODE="true"
export DATABASE_URL="sqlite+aiosqlite:///./data/trading_intel.db"
mkdir -p data
python -m scripts.seed_demo_data

echo "==> Install complete. Start the API with: make run-demo"
