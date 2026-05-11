#!/usr/bin/env bash
# Local dev convenience.
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt
export PYTHONPATH="$PWD/src"

case "${1:-repl}" in
  repl)    python -m agent_trio.runner "${@:2}" ;;
  serve)   python -m agent_trio.server ;;
  test)    pytest -q tests ;;
  *) echo "usage: $0 {repl|serve|test} [args...]"; exit 1 ;;
esac
