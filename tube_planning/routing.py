"""Shortest-route helpers for TubePlanner travel-time networks."""

from __future__ import annotations

from dataclasses import dataclass
import csv
import glob
import io
import json
from pathlib import Path
import re
import sys
from typing import Iterable

import numpy as np

from tube_planning._exceptions import TubePlanningError
from tube_planning.networks.network import Network
from tube_planning.utils import CLIParser, read_edge_csv


DEFAULT_STATIONS_FILE = "data/tfl_snapshot/stations.csv"
DEFAULT_LINE_PATTERN = "data/tfl_snapshot/lines/*.csv"


@dataclass(frozen=True)
class StationLookup:
    """Mappings used to resolve station names and indices."""

    names_by_id: dict[int, str]
    ids_by_name: dict[str, int]


@dataclass(frozen=True)
class RouteResult:
    """A shortest-route result produced by Dijkstra."""

    source: int
    target: int
    total_minutes: float
    path: list[int]


def normalise_station_name(name: str) -> str:
    """Normalise a station name for case-insensitive lookup."""
    return re.sub(r"\s+", " ", name.strip().lower())


def load_station_lookup(stations_file: str | Path) -> StationLookup:
    """Load station index/name mappings from the snapshot station CSV."""
    path = Path(stations_file)
    if not path.exists():
        raise TubePlanningError(f"Station file not found: {path}")

    names_by_id: dict[int, str] = {}
    ids_by_name: dict[str, int] = {}
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            station_id = int(row["station index"])
            station_name = row["station name"].strip()
            names_by_id[station_id] = station_name
            ids_by_name[normalise_station_name(station_name)] = station_id

    if not names_by_id:
        raise TubePlanningError(f"Station file contains no stations: {path}")

    return StationLookup(names_by_id=names_by_id, ids_by_name=ids_by_name)


def resolve_station(identifier: str | int, lookup: StationLookup) -> int:
    """Resolve a station index or case-insensitive station name."""
    if isinstance(identifier, int):
        station_id = identifier
    else:
        value = str(identifier).strip()
        if value.isdigit():
            station_id = int(value)
        else:
            key = normalise_station_name(value)
            if key not in lookup.ids_by_name:
                raise TubePlanningError(f"Unknown station: {identifier}")
            station_id = lookup.ids_by_name[key]

    if station_id not in lookup.names_by_id:
        raise TubePlanningError(f"Unknown station index: {station_id}")
    return station_id


def expand_edge_patterns(patterns: Iterable[str | Path]) -> list[Path]:
    """Expand one or more CSV file patterns into sorted paths."""
    paths: list[Path] = []
    for pattern in patterns:
        matches = sorted(glob.glob(str(pattern)))
        if not matches:
            path = Path(pattern)
            if path.exists():
                matches = [str(path)]
        if not matches:
            raise TubePlanningError(f"No edge files matched: {pattern}")
        paths.extend(Path(match) for match in matches)
    return paths


def travel_time_network_from_files(
    edge_files: Iterable[str | Path],
    *,
    n_nodes: int | None = None,
) -> Network:
    """Build a travel-time ``Network`` from one or more edge CSV files.

    Duplicate station pairs are merged by keeping the shortest travel time.
    This preserves the meaning needed by Dijkstra, while the main proposal
    evaluator can still use its capacity-conversion path separately.
    """
    edge_times: dict[tuple[int, int], float] = {}
    max_node = -1 if n_nodes is None else n_nodes - 1

    for edge_file in edge_files:
        path = Path(edge_file)
        rows = read_edge_csv(path, source=str(path))
        for start, end, minutes in rows:
            if start == end:
                raise TubePlanningError("Self-loop edges are not supported.")
            if start < 0 or end < 0:
                raise TubePlanningError("Station indices must be non-negative.")
            if minutes <= 0:
                raise TubePlanningError("Travel times must be positive.")

            max_node = max(max_node, start, end)
            edge = tuple(sorted((start, end)))
            edge_times[edge] = min(minutes, edge_times.get(edge, minutes))

    if not edge_times:
        raise TubePlanningError("No travel-time edges were loaded.")

    adjacency_matrix = np.zeros((max_node + 1, max_node + 1), dtype=float)
    for (start, end), minutes in edge_times.items():
        adjacency_matrix[start, end] = minutes
        adjacency_matrix[end, start] = minutes

    return Network(adj_mat=adjacency_matrix)


def find_shortest_route(
    source: str | int,
    target: str | int,
    *,
    edge_files: Iterable[str | Path],
    stations_file: str | Path = DEFAULT_STATIONS_FILE,
) -> tuple[RouteResult, StationLookup]:
    """Find the fastest route between two stations using Dijkstra."""
    lookup = load_station_lookup(stations_file)
    source_id = resolve_station(source, lookup)
    target_id = resolve_station(target, lookup)
    network = travel_time_network_from_files(
        edge_files,
        n_nodes=max(lookup.names_by_id) + 1,
    )
    total_minutes, path = network.shortest_path(source_id, target_id)
    return (
        RouteResult(
            source=source_id,
            target=target_id,
            total_minutes=total_minutes,
            path=path,
        ),
        lookup,
    )


def format_route(
    result: RouteResult,
    lookup: StationLookup,
    *,
    output_format: str = "text",
) -> str:
    """Format a route result as text, CSV, or JSON."""
    path_names = [lookup.names_by_id.get(node, str(node)) for node in result.path]
    payload = {
        "source": lookup.names_by_id.get(result.source, str(result.source)),
        "target": lookup.names_by_id.get(result.target, str(result.target)),
        "source_id": result.source,
        "target_id": result.target,
        "total_minutes": round(result.total_minutes, 2),
        "path": path_names,
        "path_ids": result.path,
    }

    if output_format == "json":
        return json.dumps(payload, indent=2)

    if output_format == "csv":
        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(
            ["source", "target", "total_minutes", "station_indices", "stations"]
        )
        writer.writerow(
            [
                payload["source"],
                payload["target"],
                f"{result.total_minutes:.2f}",
                " > ".join(str(node) for node in result.path),
                " > ".join(path_names),
            ]
        )
        return output.getvalue().rstrip("\n")

    lines = [
        f"Source: {payload['source']} ({result.source})",
        f"Target: {payload['target']} ({result.target})",
        f"Estimated travel time: {result.total_minutes:.2f} minutes",
        "Route:",
        " -> ".join(path_names),
    ]
    return "\n".join(lines)


def build_parser() -> CLIParser:
    """Build the route-planning command parser."""
    parser = CLIParser(
        prog="tube-route",
        description=(
            "Find the estimated fastest route between two stations using "
            "Dijkstra's algorithm."
        ),
    )
    parser.add_argument("--source", required=True, help="Source station name or index.")
    parser.add_argument("--target", required=True, help="Target station name or index.")
    parser.add_argument(
        "--stations",
        default=DEFAULT_STATIONS_FILE,
        help="Station lookup CSV. Defaults to the bundled TfL snapshot.",
    )
    parser.add_argument(
        "--lines",
        nargs="+",
        default=[DEFAULT_LINE_PATTERN],
        help="One or more travel-time edge CSV files or glob patterns.",
    )
    parser.add_argument(
        "--extra-edges",
        nargs="*",
        default=[],
        help="Optional extra edge CSV files, such as candidate proposal routes.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "csv", "json"),
        default="text",
        help="Output format.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for the ``tube-route`` command."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        edge_files = expand_edge_patterns([*args.lines, *args.extra_edges])
        result, lookup = find_shortest_route(
            args.source,
            args.target,
            edge_files=edge_files,
            stations_file=args.stations,
        )
        print(format_route(result, lookup, output_format=args.format))
    except TubePlanningError as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        sys.exit(2)


if __name__ == "__main__":
    main()
