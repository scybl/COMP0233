.PHONY: demo cli ucl-demo route-demo results cache-ucl-snapshot test clean

PYTHON ?= python
PYTEST ?= pytest

demo:
	$(PYTHON) -B -m tube_planning.showcase

cli:
	$(PYTHON) -B -m tube_planning.evaluation --network-file examples/baseline_network.csv --format csv examples/costs.fixed-cost examples/criteria.cfile "examples/proposals/*.csv"

ucl-demo:
	$(PYTHON) -B -m tube_planning.evaluation --network-file data/ucl_snapshot/baseline_network.csv --format csv data/ucl_snapshot/costs/2026-07-01.fixed-cost data/ucl_snapshot/demo_criteria.cfile "data/ucl_snapshot/proposals/*.csv"

route-demo:
	$(PYTHON) -B -m tube_planning.routing --source Highgate --target Waterloo

results:
	mkdir -p examples/results data/ucl_snapshot/results
	$(PYTHON) -B -m tube_planning.evaluation --network-file examples/baseline_network.csv --format csv examples/costs.fixed-cost examples/criteria.cfile "examples/proposals/*.csv" > examples/results/demo_ranking.csv
	$(PYTHON) -B -m tube_planning.evaluation --network-file examples/baseline_network.csv --format json examples/costs.fixed-cost examples/criteria.cfile "examples/proposals/*.csv" > examples/results/demo_ranking.json
	$(PYTHON) -B -m tube_planning.evaluation --network-file data/ucl_snapshot/baseline_network.csv --format csv data/ucl_snapshot/costs/2026-07-01.fixed-cost data/ucl_snapshot/demo_criteria.cfile "data/ucl_snapshot/proposals/*.csv" > data/ucl_snapshot/results/ranking_2026-07-01.csv
	$(PYTHON) -B -m tube_planning.routing --source Highgate --target Waterloo > data/ucl_snapshot/results/route_highgate_waterloo.txt
	$(PYTHON) -B -m tube_planning.routing --source Highgate --target Waterloo --extra-edges data/ucl_snapshot/proposals/goodrum.csv > data/ucl_snapshot/results/route_highgate_waterloo_goodrum.txt

cache-ucl-snapshot:
	$(PYTHON) -B scripts/cache_ucl_snapshot.py

test:
	PYTHONDONTWRITEBYTECODE=1 $(PYTEST) -q -p no:cacheprovider

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache tube_planning.egg-info build dist
