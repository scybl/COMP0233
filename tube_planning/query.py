from datetime import date as _date
from datetime import datetime
import os

import requests

from tube_planning._exceptions import TubePlanningError
from tube_planning.networks.network import Network
from tube_planning.networks.proposal import Proposal
from tube_planning.utils import (
    adjacency_from_edges,
    normalise_fixed_costs,
    parse_edge_csv,
)


DEFAULT_TIMEOUT = 10.0


def _VALID_SERVICES() -> tuple[str, ...]:
    """Return a tuple of strings, corresponding to the web services that
    can be queried.

    We use a function, rather than a module-scoped variable, to avoid
    complications that may arise from unintentional edits to a module-
    scoped variable.

    THIS FUNCTION IS PROVIDED TO YOU, AND DOES NOT NEED TO BE TESTED IN
    YOUR TEST SUITE.
    """
    return (
        "index/query",
        "line/query",
        "stations/query",
        "proposals/routes",
        "proposals/costs",
    )


def _WEB_SERVICE() -> str:
    """Return the configured root address of the web service.

    We use a function, rather than a module-scoped variable, to avoid
    complications that may arise from unintentional edits to a module-
    scoped variable.

    THIS FUNCTION IS PROVIDED TO YOU, AND DOES NOT NEED TO BE TESTED IN
    YOUR TEST SUITE.
    """
    return os.environ.get(
        "TUBE_PLANNING_WEB_SERVICE",
        "https://transport-planning-service.example/tube-planning",
    )


def send_query(service: str, *, timeout: float = DEFAULT_TIMEOUT, **query_params):
    """Send a GET request to a configured web-service endpoint.

    The helper validates that ``service`` is one of the allowed endpoints
    returned by ``_VALID_SERVICES()``, constructs the full URL using
    ``_WEB_SERVICE()``, and forwards ``query_params`` to
    ``requests.get(..., params=...)``.

    Parameters
    ----------
    service : str
        Service path to query (e.g. ``'line/query'`` or
        ``'proposals/costs'``). Must be one of the strings returned by
        ``_VALID_SERVICES()``.
    **query_params : dict, optional
        Keyword query parameters forwarded to ``requests.get``.

    Returns
    -------
    requests.Response
        The raw response object when the HTTP status code is < 400.

    Raises
    ------
    TubePlanningError
        If ``service`` is not supported or if the HTTP response status code is
        >= 400. The error message includes the failing URL and status code.

    Notes
    -----
    This function does not parse or modify the response body; callers should
    use ``response.json()`` or ``response.text`` as appropriate.

    Examples
    --------
    >>> resp = send_query('line/query', line_identifier=3)
    >>> resp.status_code
    200
    >>> print(resp.text[:100])
    "..."
    """
    # Validate the requested service
    if service not in _VALID_SERVICES():
        raise TubePlanningError(
            f"The web-service does not provide the requested service: "
            f"{service}"
        )

    base = _WEB_SERVICE().rstrip("/")
    endpoint = service.lstrip("/")
    url = f"{base}/{endpoint}"

    try:
        response = requests.get(url, params=query_params, timeout=timeout)
    except requests.RequestException as exc:
        raise TubePlanningError(f"Request to {url} failed: {exc}") from exc

    if response.status_code >= 400:
        raise TubePlanningError(
            f"Request to {url} failed with status code "
            f"{response.status_code}"
        )

    return response


def _json_error_message(response) -> str | None:
    """Return an error/message string from a JSON response, if present."""
    try:
        payload = response.json()
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None

    message = payload.get("message") or payload.get("error")
    return message if isinstance(message, str) else None


def _looks_like_not_found(message: str | None) -> bool:
    """Whether a service message indicates that iteration should stop."""
    if not message:
        return False
    lowered = message.lower()
    return (
        "not a line" in lowered
        or "not recognised" in lowered
        or "not recognized" in lowered
        or "error in query" in lowered
    )


def fetch_tfl_network(max_lines: int | None = None) -> Network:
    """Assemble the current TFL network by fetching per-line CSVs from the
    web-service.

    The web service exposes a ``line/query`` endpoint that returns CSV rows
    of the form ``station_i, station_j, travel_time_minutes`` for a
    requested line. This function iterates ``line_identifier`` starting at
    ``0`` and continues until the service indicates that an identifier is
    not available (either via an HTTP error or a JSON message describing
    the error).

    For each valid CSV row the travel time (minutes) is converted to a
    weight in trains per hour via ``w = 60.0 / travel_time_minutes``
    and the undirected edge is added to a combined adjacency
    matrix. Duplicate edges are accumulated by summing weights symmetrically.

    Returns
    -------
    Network
        A ``Network`` instance with ``adjacency_matrix`` set to the
        combined adjacency matrix (weights in trains/hour).

    Notes
    -----
    - The function ignores malformed CSV rows and non-positive travel times.
    - The function relies on ``send_query`` which will raise
      ``TubePlanningError`` for HTTP errors; JSON error messages returned
      with HTTP 200 are detected and used to stop iteration.

    Examples
    --------
    >>> net = fetch_tfl_network()
    >>> net.n_nodes
    446
    """

    all_rows = []
    line_identifier = 0
    while True:
        if max_lines is not None and line_identifier >= max_lines:
            break
        try:
            resp = send_query("line/query", line_identifier=line_identifier)
        except TubePlanningError:
            if line_identifier == 0:
                raise
            break

        message = _json_error_message(resp)
        if _looks_like_not_found(message):
            if line_identifier == 0:
                raise TubePlanningError(message)
            break

        try:
            line_rows = parse_edge_csv(
                resp.text,
                source=f"line {line_identifier} response",
                strict=False,
            )
        except TubePlanningError:
            if line_identifier == 0:
                raise
        else:
            all_rows.extend(line_rows)

        line_identifier += 1

    if not all_rows:
        raise TubePlanningError("No valid TfL network edges were returned.")

    adjacency_matrix = adjacency_from_edges(
        all_rows,
        weights_are_travel_times=True,
        accumulate_duplicates=True,
    )
    return Network(adj_mat=adjacency_matrix)


def fetch_fixed_costs(date):
    """Fetch fixed proposal costs for a construction date in 2026.

    Parameters
    ----------
    date : str
        Date string in ``YYYY-MM-DD`` format. Must lie within 2026-01-01 and
        2026-12-31 inclusive.

    Returns
    -------
    dict[str, float]
        Dictionary with keys ``'new'``, ``'ext'``, ``'hire'``, and
        ``'train'`` mapped to their float values.

    Raises
    ------
    TubePlanningError
        If ``date`` is not in the expected format, not in 2026, if the
        web-service response is not valid JSON, or if required keys are
        missing from the response.

    Notes
    -----
    The web-service endpoint `proposals/costs` is queried with the provided
    construction date; the service is expected to return a JSON object
    containing the required keys.
    """
    # Validate input format YYYY-MM-DD and that the date lies within 2026
    try:
        d = datetime.strptime(date, "%Y-%m-%d").date()
    except Exception as exc:
        raise TubePlanningError(
            f"date must be a string in YYYY-MM-DD format: {exc}"
        )

    start = _date(2026, 1, 1)
    end = _date(2026, 12, 31)
    if d < start or d > end:
        raise TubePlanningError(
            "date must be within 2026-01-01 and 2026-12-31 inclusive"
        )

    resp = send_query("proposals/costs", **{"construction-date": date})

    try:
        data = resp.json()
    except Exception as exc:
        raise TubePlanningError(f"failed to parse JSON response: {exc}")

    return normalise_fixed_costs(data, source="fixed-cost service response")


def fetch_proposed_line(proposal_name):
    """Fetch a proposed route by name and return it as a ``Proposal``.

    Parameters
    ----------
    proposal_name : str
        Name of the proposal (sent as the ``route`` parameter to the
        ``proposals/routes`` endpoint).

    Returns
    -------
    Proposal
        A ``Proposal`` instance constructed from the CSV text returned by the
        web-service. Travel times from the CSV are interpreted as minutes and
        converted to trains/hour.

    Raises
    ------
    TubePlanningError
        If the service reports that the proposal name is not recognised, if
        the response is malformed or contains invalid station
        indices/weights, or if the proposal contains no edges.

    Notes
    -----
    The expected CSV format is ``station1,station2,travel_time_minutes``
    per row. Duplicate or contradictory edges are rejected.
    """
    resp = send_query("proposals/routes", route=proposal_name)

    message = _json_error_message(resp)
    if _looks_like_not_found(message):
        raise TubePlanningError(message)

    rows = parse_edge_csv(resp.text, source=f"proposal {proposal_name!r} response")
    adjacency_matrix = adjacency_from_edges(
        rows,
        weights_are_travel_times=True,
        accumulate_duplicates=False,
    )
    return Proposal(name=proposal_name, adj_mat=adjacency_matrix)
