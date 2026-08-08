# TubePlanner

[中文](README.md)

TubePlanner is a public-transport line planning and evaluation tool built around TfL network data. It uses a local snapshot from the UCL RSE Tube Planning Web Service, converts London Underground, light rail, and related rail connections into a weighted graph, and converts station-to-station travel times into network capacity.

The project compares how candidate line extensions affect route choice and cross-city transport capacity. Given a baseline network, candidate proposals, cost configuration, and scoring criteria, it computes maximum-flow gains and delivery-cost performance, then produces reproducible proposal rankings.

## Features

- Converts stations and connections into graph structures and travel times into capacities.
- Uses BFS and Edmonds-Karp maximum flow to evaluate proposal capacity gains.
- Supports essential criteria, desirable criteria, and fixed-cost configuration.
- Outputs results as text, CSV, or JSON.

## Results

| Item | Result |
| --- | --- |
| UCL snapshot network | 446 stations, 535 equivalent links |
| Candidate proposals | 7 |
| Cost date | 2026-07-01 |
| Top proposal | `thameslink` |
| Output file | `data/ucl_snapshot/results/ranking_2026-07-01.csv` |

Sample output:

```csv
rank,proposal,score,essential_passed
1,thameslink,223.32,True
2,weaving_cross,198.75,True
3,holborn_star,197.84,True
```

## Quick Start

```bash
bash scripts/setup_env.sh
bash scripts/run_ucl_snapshot.sh
```

Reuse an existing conda environment:

```bash
conda run -n codex_python bash scripts/run_ucl_snapshot.sh
```

Run the small offline example:

```bash
bash scripts/run_demo.sh
```

Run the UCL snapshot CLI directly:

```bash
python -m tube_planning.evaluation --network-file data/ucl_snapshot/baseline_network.csv --format csv data/ucl_snapshot/costs/2026-07-01.fixed-cost data/ucl_snapshot/demo_criteria.cfile "data/ucl_snapshot/proposals/*.csv"
```

More run examples:

```bash
make cli
make ucl-demo
make results
python -m tube_planning.evaluation --network-file examples/baseline_network.csv --format json examples/costs.fixed-cost examples/criteria.cfile "examples/proposals/*.csv"
```

Expected output files:

- `examples/results/demo_ranking.csv`
- `examples/results/demo_ranking.json`
- `data/ucl_snapshot/results/ranking_2026-07-01.csv`

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`

## Data Notes

- `data/ucl_snapshot/` is a local snapshot from the UCL RSE Tube Planning Web Service.
- The snapshot includes lines, station indices, candidate proposals, and 2026 cost data; the service states that it combines 2017 data with newer TfL API-derived sources, and that candidate proposals are simulated.
- `examples/` is a small synthetic example that does not depend on external services.
- To refresh the snapshot, run `python scripts/cache_ucl_snapshot.py`.
- For live mode, set `TUBE_PLANNING_WEB_SERVICE` and use `--live-costings` or `--routes`.

## Project Layout

```text
tube_planning/        Core package
data/ucl_snapshot/    Local UCL service snapshot
data/ucl_snapshot/results/  UCL snapshot output examples
examples/             Example data
examples/results/     Small example output files
tests/                Tests
scripts/              Setup and run scripts
```

## Tests

```bash
pytest -q
```
