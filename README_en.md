# TubePlanner

[中文](README.md)

TubePlanner is a public-transport route planning and proposal-evaluation tool built around TfL network data. It includes a local TfL-derived snapshot with stations, lines, candidate extensions, and simulated cost data for London Underground, light rail, and related rail services.

The project converts London Underground, light rail, and related rail connections into weighted graphs for estimated best-route planning, shortest travel-time comparison, and cross-city capacity evaluation. It focuses on offline planning analysis and does not provide live congestion or interchange updates.

## Features

- Converts stations and connections into graph structures with travel-time and capacity weight semantics.
- Uses BFS and Edmonds-Karp maximum flow to evaluate proposal capacity gains.
- Uses Dijkstra's algorithm to estimate the shortest route between stations and compare changes after adding proposal edges.
- Supports essential criteria, desirable criteria, and fixed-cost configuration.
- Outputs results as text, CSV, or JSON.

## Results

| Item | Result |
| --- | --- |
| TfL snapshot network | 446 stations, 535 equivalent links |
| Candidate proposals | 7 |
| Cost date | 2026-07-01 |
| Top proposal | `thameslink` |
| Route example | `Highgate -> Waterloo` |
| Baseline shortest travel time | `22.00 minutes` |
| With `goodrum` proposal | `15.00 minutes` |
| Ranking output | `data/tfl_snapshot/results/ranking_2026-07-01.csv` |
| Route output | `data/tfl_snapshot/results/route_highgate_waterloo.txt` |

Ranking sample:

```csv
rank,proposal,score,essential_passed
1,thameslink,223.32,True
2,weaving_cross,198.75,True
3,holborn_star,197.84,True
```

Route sample:

```text
Source: Highgate (123)
Target: Waterloo (271)
Estimated travel time: 22.00 minutes
Route:
Highgate -> Archway -> Tufnell park -> Kentish town -> Camden town -> Euston -> Warren street -> Goodge street -> Tottenham court road -> Leicester square -> Charing cross -> Embankment -> Waterloo
```

## Quick Start

```bash
bash scripts/setup_env.sh
bash scripts/run_tfl_snapshot.sh
```

Reuse an existing conda environment:

```bash
conda run -n codex_python bash scripts/run_tfl_snapshot.sh
```

Run the small offline example:

```bash
bash scripts/run_demo.sh
```

Run the shortest-route example:

```bash
python -m tube_planning.routing --source Highgate --target Waterloo
python -m tube_planning.routing --source Highgate --target Waterloo --extra-edges data/tfl_snapshot/proposals/goodrum.csv
```

Run the TfL snapshot CLI directly:

```bash
python -m tube_planning.evaluation --network-file data/tfl_snapshot/baseline_network.csv --format csv data/tfl_snapshot/costs/2026-07-01.fixed-cost data/tfl_snapshot/demo_criteria.cfile "data/tfl_snapshot/proposals/*.csv"
```

More run examples:

```bash
make cli
make tfl-demo
make route-demo
make results
python -m tube_planning.evaluation --network-file examples/baseline_network.csv --format json examples/costs.fixed-cost examples/criteria.cfile "examples/proposals/*.csv"
```

Expected output files:

- `examples/results/demo_ranking.csv`
- `examples/results/demo_ranking.json`
- `data/tfl_snapshot/results/ranking_2026-07-01.csv`
- `data/tfl_snapshot/results/route_highgate_waterloo.txt`
- `data/tfl_snapshot/results/route_highgate_waterloo_goodrum.txt`

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`

## Data Notes

- `data/tfl_snapshot/` is a local TfL-derived snapshot.
- The snapshot includes lines, station indices, candidate proposals, and 2026 cost data; candidate extensions and costs are simulated for offline planning analysis.
- `examples/` is a small synthetic example that does not depend on external services.
- To refresh the snapshot, run `python scripts/cache_tfl_snapshot.py --service-url <compatible-service-url>`.
- For live mode, set `TUBE_PLANNING_WEB_SERVICE` and use `--live-costings` or `--routes`.

## Project Layout

```text
tube_planning/        Core package
data/tfl_snapshot/    Local TfL-derived snapshot
data/tfl_snapshot/results/  TfL snapshot output examples
examples/             Example data
examples/results/     Small example output files
tests/                Tests
scripts/              Setup and run scripts
```

## Tests

```bash
pytest -q
```
