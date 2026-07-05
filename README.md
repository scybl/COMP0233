# Tube Planning

[中文版本](README.zh.md)

Tube Planning is a Python project for evaluating public-transport network extension proposals. It reads a baseline network and one or more candidate extensions from CSV edge tables, converts travel-time data into graph capacity, evaluates each proposal against cost and flow criteria, and returns a deterministic ranking.

## Functionality

The project models a transport network as an adjacency matrix, where each station is a node and each connection is an edge. Candidate proposals are represented as additional edge tables and can be merged with the baseline network for evaluation.

The evaluation pipeline combines two kinds of criteria. Cost criteria use fixed infrastructure and operating-cost assumptions to check whether a proposal stays within a planning budget. Performance criteria use breadth-first search and Edmonds-Karp maximum flow to estimate how much capacity a proposal adds between selected source and sink stations, including multi-source, multi-sink, and sufficient-flow scenarios.

The package can be used in three ways: a one-command offline showcase, a CLI that ranks proposal files and outputs text/CSV/JSON, and a Python API for integrating the network and scoring logic into other scripts.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Run the one-command showcase:

```bash
python -m tube_planning.showcase
```

Or use the project shortcut:

```bash
make demo
```

Expected output:

```text
Tube Planning Showcase
======================
Baseline network: 6 stations, 6 connections
Scenario: rank candidate extensions by cost and flow performance

Rank  Proposal                   Score  Essential
----------------------------------------------------
1     central_connector         149.40  pass
2     crosslink                  97.40  pass
```

After installation, the same showcase is also available as:

```bash
tube-planning-showcase
```

## CLI Usage

Run the bundled example through the CLI:

```bash
python -m tube_planning.evaluation --network-file examples/baseline_network.csv --format csv examples/costs.fixed-cost examples/criteria.cfile "examples/proposals/*.csv"
```

Output:

```csv
rank,proposal,score,essential_passed
1,central_connector,149.40,True
2,crosslink,97.40,True
```

Installed CLI form:

```bash
evaluate-proposals --network-file examples/baseline_network.csv --format json examples/costs.fixed-cost examples/criteria.cfile "examples/proposals/*.csv"
```

Useful options:

- `--network-file PATH`: use a local baseline network CSV.
- `--format {text,csv,json}`: choose the output format.
- `-o, --output-file PATH`: write rankings to a file.

The bundled CLI scenario can also be run with:

```bash
make cli
```

## Python API Example

This example evaluates the bundled proposals programmatically:

```python
from pathlib import Path

from tube_planning.criteria.group import CriteriaGroup
from tube_planning.evaluation import evaluate_proposals, rank_proposals
from tube_planning.networks import Network, Proposal
from tube_planning.utils import adjacency_from_edges, read_edge_csv, read_fixed_costs

root = Path(".")
example_dir = root / "examples"

baseline_rows = read_edge_csv(example_dir / "baseline_network.csv")
baseline = Network(
    adj_mat=adjacency_from_edges(baseline_rows, weights_are_travel_times=True)
)

criteria = CriteriaGroup.from_file(example_dir / "criteria.cfile")
costs = read_fixed_costs(example_dir / "costs.fixed-cost")
proposals = [
    Proposal.from_file(path, name=path.stem)
    for path in sorted((example_dir / "proposals").glob("*.csv"))
]

records = evaluate_proposals(proposals, criteria, baseline, costs)
ranked = rank_proposals(records)

for rank, record in enumerate(ranked, start=1):
    print(rank, record["proposal"].name, round(record["score"], 2))
```

Expected result:

```text
1 central_connector 149.4
2 crosslink 97.4
```

## Input Files

Network and proposal CSV files use this edge-table format:

```text
station_i,station_j,travel_time_minutes
```

Travel times are converted to capacity with:

```text
capacity = 60 / travel_time_minutes
```

Criteria are defined in JSON `.cfile` files. Fixed costs are defined in JSON `.fixed-cost` files. The `examples/` folder contains a complete offline scenario.

## Project Layout

```text
tube_planning/        Core package
  flow.py             Flow representation and safe augmentation
  networks/           Network and proposal graph models
  criteria/           Cost and performance scoring
  evaluation.py       CLI ranking pipeline
  showcase.py         Offline demonstration entry point
examples/             Offline dataset for the showcase
tests/                Pytest suite for algorithms and pipeline behaviour
```

## Test

```bash
pytest -q
```

Shortcut:

```bash
make test
```
