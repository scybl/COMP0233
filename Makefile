.PHONY: demo cli ucl-demo cache-ucl-snapshot test clean

PYTHON ?= python
PYTEST ?= pytest

demo:
	$(PYTHON) -B -m tube_planning.showcase

cli:
	$(PYTHON) -B -m tube_planning.evaluation --network-file examples/baseline_network.csv --format csv examples/costs.fixed-cost examples/criteria.cfile "examples/proposals/*.csv"

ucl-demo:
	$(PYTHON) -B -m tube_planning.evaluation --network-file data/ucl_snapshot/baseline_network.csv --format csv data/ucl_snapshot/costs/2026-07-01.fixed-cost data/ucl_snapshot/demo_criteria.cfile "data/ucl_snapshot/proposals/*.csv"

cache-ucl-snapshot:
	$(PYTHON) -B scripts/cache_ucl_snapshot.py

test:
	PYTHONDONTWRITEBYTECODE=1 $(PYTEST) -q -p no:cacheprovider

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache tube_planning.egg-info build dist
