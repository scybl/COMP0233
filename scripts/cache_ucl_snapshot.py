#!/usr/bin/env python
"""Cache the UCL Tube Planning web-service data for offline demos."""

from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
import json
import re
from pathlib import Path
from typing import Iterable

import requests


DEFAULT_SERVICE_URL = "https://rse-with-python.arc.ucl.ac.uk/tube-planning"
DEFAULT_OUTPUT_DIR = Path("data/ucl_snapshot")


def slugify(value: str) -> str:
    """Return a compact filesystem-safe slug."""
    value = value.lower().replace("&", "and")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def get(session: requests.Session, base_url: str, service: str, **params):
    """Fetch a service response and raise for HTTP failures."""
    url = f"{base_url.rstrip('/')}/{service.lstrip('/')}"
    response = session.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response


def parse_edge_rows(text: str) -> list[tuple[int, int, float]]:
    """Parse service edge CSV text into typed rows."""
    rows: list[tuple[int, int, float]] = []
    for row in csv.reader(text.splitlines()):
        if not row:
            continue
        start, end, minutes = row
        rows.append((int(start), int(end), float(minutes)))
    return rows


def write_edge_rows(path: Path, rows: Iterable[tuple[int, int, float]]) -> None:
    """Write edge rows as headerless CSV."""
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        for start, end, minutes in rows:
            writer.writerow([start, end, f"{minutes:.10g}"])


def aggregate_equivalent_minutes(
    lines: Iterable[tuple[int, str, list[tuple[int, int, float]]]],
) -> list[tuple[int, int, float]]:
    """Merge per-line travel-time edges into one equivalent edge table.

    The application stores network weights as capacity, estimated from travel
    time as ``capacity = 60 / minutes``. When multiple lines share an edge,
    capacities are additive; this function converts the combined capacity back
    to an equivalent travel-time value so the standard CSV loader can read it.
    """
    capacities: dict[tuple[int, int], float] = {}
    for _line_id, _name, rows in lines:
        for start, end, minutes in rows:
            edge = tuple(sorted((start, end)))
            capacities[edge] = capacities.get(edge, 0.0) + 60.0 / minutes

    combined_rows = []
    for (start, end), capacity in sorted(capacities.items()):
        combined_rows.append((start, end, 60.0 / capacity))
    return combined_rows


def date_range(start: date, end: date) -> Iterable[date]:
    """Yield every date from start to end, inclusive."""
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def cache_snapshot(service_url: str, output_dir: Path) -> dict:
    """Fetch service data and write an offline snapshot."""
    output_dir.mkdir(parents=True, exist_ok=True)
    line_dir = output_dir / "lines"
    proposal_dir = output_dir / "proposals"
    costs_dir = output_dir / "costs"
    line_dir.mkdir(exist_ok=True)
    proposal_dir.mkdir(exist_ok=True)
    costs_dir.mkdir(exist_ok=True)
    for directory in (line_dir, proposal_dir):
        for old_file in directory.glob("*.csv"):
            old_file.unlink()
    for old_file in costs_dir.glob("*.csv"):
        old_file.unlink()
    for old_file in costs_dir.glob("*.fixed-cost"):
        old_file.unlink()

    session = requests.Session()

    index = get(session, service_url, "index/query").json()
    (output_dir / "index.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    stations_csv = get(session, service_url, "stations/query", id="all").text
    (output_dir / "stations.csv").write_text(stations_csv, encoding="utf-8")

    lines = []
    for line_id_text, line_name in sorted(index["lines"].items(), key=lambda item: int(item[0])):
        line_id = int(line_id_text)
        response = get(session, service_url, "line/query", line_identifier=line_id)
        rows = parse_edge_rows(response.text)
        filename = f"{line_id:02d}_{slugify(line_name)}.csv"
        write_edge_rows(line_dir / filename, rows)
        lines.append((line_id, line_name, rows))

    baseline_rows = aggregate_equivalent_minutes(lines)
    write_edge_rows(output_dir / "baseline_network.csv", baseline_rows)

    proposal_files = {}
    for proposal_name in index["proposal names"]:
        response = get(session, service_url, "proposals/routes", route=proposal_name)
        rows = parse_edge_rows(response.text)
        filename = f"{slugify(proposal_name)}.csv"
        write_edge_rows(proposal_dir / filename, rows)
        proposal_files[proposal_name] = f"proposals/{filename}"

    cost_rows = []
    demo_cost = None
    demo_date = "2026-07-01"
    for day in date_range(date(2026, 1, 1), date(2026, 12, 31)):
        day_text = day.isoformat()
        payload = get(session, service_url, "proposals/costs", date=day_text).json()
        cost_row = {
            "construction-date": payload.get("construction-date", day_text),
            "new": float(payload["new"]),
            "ext": float(payload["ext"]),
            "hire": float(payload["hire"]),
            "train": float(payload["train"]),
        }
        cost_rows.append(cost_row)
        if day_text == demo_date:
            demo_cost = cost_row

    costs_csv = costs_dir / "costs_2026.csv"
    with costs_csv.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["construction-date", "new", "ext", "hire", "train"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(cost_rows)

    if demo_cost is None:
        raise RuntimeError(f"Demo cost date was not fetched: {demo_date}")

    (costs_dir / f"{demo_date}.fixed-cost").write_text(
        json.dumps(demo_cost, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    demo_criteria = {
        "essential": [],
        "desirable": [
            {
                "description": "Increase capacity between major terminals and Bloomsbury stations",
                "sources": [48, 155, 156, 189, 271],
                "sinks": [88, 89, 144, 218, 269],
                "weight": 3.0,
            },
            {
                "description": "Prefer proposals with lower total delivery cost",
                "costs": ["total"],
                "budget": 5000,
                "weight": 0.03,
            },
        ],
    }
    (output_dir / "demo_criteria.cfile").write_text(
        json.dumps(demo_criteria, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    manifest = {
        "source": service_url.rstrip("/"),
        "source_note": (
            "UCL RSE Tube Planning service; combines 2017 data with more recent "
            "TfL API-derived sources and includes made-up expansion proposals."
        ),
        "snapshot_contents": {
            "lines": len(lines),
            "stations": int(index["n_stations"]),
            "proposals": len(proposal_files),
            "cost_dates": len(cost_rows),
            "baseline_edges": len(baseline_rows),
        },
        "demo": {
            "network": "baseline_network.csv",
            "costs": f"costs/{demo_date}.fixed-cost",
            "criteria": "demo_criteria.cfile",
            "proposals": proposal_files,
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service-url", default=DEFAULT_SERVICE_URL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    manifest = cache_snapshot(args.service_url, args.output_dir)
    contents = manifest["snapshot_contents"]
    print(
        "Cached UCL snapshot: "
        f"{contents['lines']} lines, "
        f"{contents['stations']} stations, "
        f"{contents['proposals']} proposals, "
        f"{contents['cost_dates']} cost dates."
    )


if __name__ == "__main__":
    main()
