.PHONY: demo cli tfl-demo route-demo results cache-tfl-snapshot test clean

PYTHON ?= python
PYTEST ?= pytest

demo:
	$(PYTHON) -B -m tube_planning.showcase

cli:
	$(PYTHON) -B -m tube_planning.evaluation --network-file examples/baseline_network.csv --format csv examples/costs.fixed-cost examples/criteria.cfile "examples/proposals/*.csv"

tfl-demo:
	$(PYTHON) -B -m tube_planning.evaluation --network-file data/tfl_snapshot/baseline_network.csv --format csv data/tfl_snapshot/costs/2026-07-01.fixed-cost data/tfl_snapshot/demo_criteria.cfile "data/tfl_snapshot/proposals/*.csv"

route-demo:
	$(PYTHON) -B -m tube_planning.routing --source Highgate --target Waterloo

results:
	mkdir -p examples/results data/tfl_snapshot/results
	$(PYTHON) -B -m tube_planning.evaluation --network-file examples/baseline_network.csv --format csv examples/costs.fixed-cost examples/criteria.cfile "examples/proposals/*.csv" > examples/results/demo_ranking.csv
	$(PYTHON) -B -m tube_planning.evaluation --network-file examples/baseline_network.csv --format json examples/costs.fixed-cost examples/criteria.cfile "examples/proposals/*.csv" > examples/results/demo_ranking.json
	$(PYTHON) -B -m tube_planning.evaluation --network-file data/tfl_snapshot/baseline_network.csv --format csv data/tfl_snapshot/costs/2026-07-01.fixed-cost data/tfl_snapshot/demo_criteria.cfile "data/tfl_snapshot/proposals/*.csv" > data/tfl_snapshot/results/ranking_2026-07-01.csv
	$(PYTHON) -B -m tube_planning.routing --source Highgate --target Waterloo > data/tfl_snapshot/results/route_highgate_waterloo.txt
	$(PYTHON) -B -m tube_planning.routing --source Highgate --target Waterloo --extra-edges data/tfl_snapshot/proposals/goodrum.csv > data/tfl_snapshot/results/route_highgate_waterloo_goodrum.txt

cache-tfl-snapshot:
	@if [ -z "$(SERVICE_URL)" ]; then echo "Set SERVICE_URL to a compatible planning service endpoint."; exit 1; fi
	$(PYTHON) -B scripts/cache_tfl_snapshot.py --service-url "$(SERVICE_URL)"

test:
	PYTHONDONTWRITEBYTECODE=1 $(PYTEST) -q -p no:cacheprovider

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache tube_planning.egg-info build dist
