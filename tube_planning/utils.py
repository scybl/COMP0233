import json
import csv
import io
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Iterable

import numpy as np

from tube_planning._exceptions import TubePlanningError


FIXED_COST_KEYS = ("new", "ext", "hire", "train")
EdgeRow = tuple[int, int, float]


class CLIParser(ArgumentParser):
    """
    A custom subclass of ``argparse.ArgumentParser``,
    which changes the default behaviour on an error in CLI parsing to print the
    command-line help, as opposed to throwing an error to stderr.
    """

    def error(self, message):
        sys.stderr.write(
            f"ERROR parsing input arguments.\n{message}\nRefer to CLI usage below:\n\n"
        )
        self.print_help()
        sys.exit(2)


def normalise_fixed_costs(data: dict, *, source: str = "fixed cost data") -> dict[str, float]:
    """Validate and normalise fixed-cost data.

    The project uses four unit-cost coefficients throughout the package:
    ``new``, ``ext``, ``hire``, and ``train``. Extra keys are ignored so that
    web-service responses and local files can carry metadata without breaking
    the evaluation pipeline.
    """
    if not isinstance(data, dict):
        raise TubePlanningError(f"{source} must be a JSON object.")

    missing = [key for key in FIXED_COST_KEYS if key not in data]
    if missing:
        raise TubePlanningError(f"{source} is missing required keys: {missing}")

    try:
        return {key: float(data[key]) for key in FIXED_COST_KEYS}
    except (TypeError, ValueError) as exc:
        raise TubePlanningError(f"{source} contains non-numeric cost values: {exc}") from exc


def parse_edge_csv(
    text: str,
    *,
    source: str = "CSV data",
    strict: bool = True,
) -> list[EdgeRow]:
    """Parse ``station_i, station_j, weight`` rows from CSV text.

    Parameters
    ----------
    text:
        CSV text to parse.
    source:
        Human-readable label used in error messages.
    strict:
        If ``True``, malformed rows raise ``TubePlanningError``. If ``False``,
        malformed rows are skipped; this is useful for tolerant web-service
        aggregation where one bad line should not discard an entire network.
    """
    rows: list[EdgeRow] = []
    reader = csv.reader(io.StringIO(text))

    for line_number, row in enumerate(reader, start=1):
        if not row or all(not value.strip() for value in row):
            continue
        if len(row) != 3:
            if strict:
                raise TubePlanningError(
                    f"{source} line {line_number} must contain exactly three values."
                )
            continue
        try:
            start = int(row[0].strip())
            end = int(row[1].strip())
            weight = float(row[2].strip())
        except (TypeError, ValueError) as exc:
            if strict:
                raise TubePlanningError(
                    f"{source} line {line_number} contains invalid edge data."
                ) from exc
            continue
        rows.append((start, end, weight))

    if not rows:
        raise TubePlanningError(f"{source} contains no valid edges.")

    return rows


def read_edge_csv(path: Path, *, source: str | None = None) -> list[EdgeRow]:
    """Read a local CSV edge table into validated integer/float rows."""
    if not isinstance(path, Path):
        raise TubePlanningError("CSV file must be a pathlib.Path object.")
    if not path.exists():
        raise TubePlanningError(f"File {path} does not exist.")
    return parse_edge_csv(path.read_text(encoding="utf-8"), source=source or str(path))


def adjacency_from_edges(
    rows: Iterable[EdgeRow],
    *,
    weights_are_travel_times: bool = True,
    accumulate_duplicates: bool = False,
) -> np.ndarray:
    """Build an adjacency matrix from an edge table.

    Travel-time rows are converted to a trains-per-hour capacity using
    ``60 / minutes``. Duplicate undirected edges are rejected by default for
    proposals, while service aggregation can opt into accumulation.
    """
    edge_rows = list(rows)
    if not edge_rows:
        raise TubePlanningError("Edge table contains no valid edges.")

    max_station = -1
    seen_edges: set[tuple[int, int]] = set()

    for start, end, weight in edge_rows:
        if start < 0 or end < 0:
            raise TubePlanningError("Station indices must be non-negative.")
        if start == end:
            raise TubePlanningError("Self-loop edges are not supported.")
        if weight <= 0:
            raise TubePlanningError("Edge weights must be positive numbers.")

        edge = tuple(sorted((start, end)))
        if edge in seen_edges and not accumulate_duplicates:
            raise TubePlanningError("Duplicate or contradictory edges detected.")
        seen_edges.add(edge)
        max_station = max(max_station, start, end)

    adjacency_matrix = np.zeros((max_station + 1, max_station + 1), dtype=float)
    for start, end, weight in edge_rows:
        capacity = 60.0 / weight if weights_are_travel_times else weight
        if accumulate_duplicates:
            adjacency_matrix[start, end] += capacity
            adjacency_matrix[end, start] += capacity
        else:
            adjacency_matrix[start, end] = capacity
            adjacency_matrix[end, start] = capacity

    return adjacency_matrix


def read_fixed_costs(file):
    """
    Read and validate fixed cost values from a JSON file.

    The file must contain exactly the keys: ``"new"``, ``"ext"``, ``"hire"``,
    and ``"train"``, and all values must be convertible to floats.

    Parameters
    ----------
    file : Path
        Path to the JSON file containing fixed-cost definitions.

    Returns
    -------
    dict[str, float]
        A dictionary with the four required cost keys mapped to float values.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the file contains invalid JSON or non-numeric values.
    KeyError
        If required cost keys are missing.
    """
    if not isinstance(file, Path):
        file = Path(file)
    if not file.exists():
        raise FileNotFoundError(f"File not found: {file}")

    try:
        with file.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise ValueError(f"Invalid JSON in fixed cost file: {e}")

    try:
        return normalise_fixed_costs(data, source=str(file))
    except TubePlanningError as e:
        if "missing required keys" in str(e):
            raise KeyError(str(e)) from e
        raise ValueError(f"Unable to convert cost values to float: {e}")
