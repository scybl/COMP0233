# Examples

This folder contains a complete offline scenario for evaluating transport network extension proposals. It is designed to run without any external API or live transport data.

## Scenario

The baseline network has six stations connected by six existing links. The task is to rank two candidate extensions using a mix of infrastructure cost, operating cost, and cross-city flow capacity.

Candidate proposals:

- `central_connector`: adds two short internal links, improving route choices through the middle of the network.
- `crosslink`: adds an end-to-end shortcut plus one local link, improving connectivity but with a lower weighted score in this scenario.

Expected ranking:

```text
1 central_connector 149.40
2 crosslink          97.40
```

## Files

- `baseline_network.csv`: current network as an edge table.
- `proposals/*.csv`: candidate extension edge tables.
- `criteria.cfile`: essential and desirable evaluation criteria.
- `costs.fixed-cost`: fixed infrastructure and operating cost assumptions.

## Run

```bash
make demo
```

Run the same data directly through the CLI:

```bash
make cli
```

Equivalent Python module command:

```bash
python -m tube_planning.evaluation --network-file examples/baseline_network.csv --format csv examples/costs.fixed-cost examples/criteria.cfile "examples/proposals/*.csv"
```

## CSV Format

Network and proposal files use the edge-table format:

```text
station_i,station_j,travel_time_minutes
```

Travel times are converted to capacity as:

```text
capacity = 60 / travel_time_minutes
```
