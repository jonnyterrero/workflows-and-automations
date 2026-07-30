.PHONY: help setup test lint format validate provision provision-dry run changes clean

PYTHON := python3
export PYTHONPATH := $(shell pwd)/src

help:
	@echo "setup          Install dependencies (editable, with dev extras)"
	@echo "test           Run the test suite (offline, no keys required)"
	@echo "lint           Ruff check"
	@echo "format         Ruff format and autofix"
	@echo "validate       Check agent definitions without calling the API"
	@echo "provision-dry  Print the agent payloads that would be created"
	@echo "provision      Create or update the agents and environment"
	@echo "run SYMBOL=X   Research one ticker end to end"
	@echo "changes SYMBOL=X   Report what changed since the last review"

setup:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest tests/ -q

lint:
	ruff check .

format:
	ruff format .
	ruff check --fix .

validate:
	@$(PYTHON) -c "import sys; sys.path.insert(0,'src'); \
from fdr import definitions; \
problems = definitions.validate_all(); \
print('\n'.join(problems) if problems else 'agent definitions valid'); \
sys.exit(1 if problems else 0)"

provision-dry:
	$(PYTHON) scripts/provision_agents.py --dry-run

provision:
	$(PYTHON) scripts/provision_agents.py

run:
	@test -n "$(SYMBOL)" || (echo "usage: make run SYMBOL=NVDA" && exit 1)
	$(PYTHON) scripts/run_research.py --symbol $(SYMBOL)

changes:
	@test -n "$(SYMBOL)" || (echo "usage: make changes SYMBOL=NVDA" && exit 1)
	$(PYTHON) scripts/run_research.py --changes $(SYMBOL)

clean:
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage build dist
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
