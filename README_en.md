# TubePlanner

[中文](README.md)

TubePlanner evaluates public-transport network extension proposals. It reads a baseline network and candidate extensions from CSV edge tables, then ranks proposals using cost constraints and maximum-flow metrics.

![TubePlanner ranking preview](docs/images/showcase-preview.svg)

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
examples/             Example data
tests/                Tests
scripts/              Setup and run scripts
docs/images/          README result image
```

## Tests

```bash
pytest -q
```
