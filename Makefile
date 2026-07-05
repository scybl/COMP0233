.PHONY: demo cli test clean

PYTHON ?= python
PYTEST ?= pytest

demo:
	$(PYTHON) -B -m tube_planning.showcase

cli:
	$(PYTHON) -B -m tube_planning.evaluation --network-file examples/baseline_network.csv --format csv examples/costs.fixed-cost examples/criteria.cfile "examples/proposals/*.csv"

test:
	PYTHONDONTWRITEBYTECODE=1 $(PYTEST) -q -p no:cacheprovider

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache tube_planning.egg-info build dist
