import json

import pytest

from tube_planning._exceptions import TubePlanningError
from tube_planning.routing import (
    RouteResult,
    StationLookup,
    expand_edge_patterns,
    find_shortest_route,
    format_route,
    load_station_lookup,
    resolve_station,
    travel_time_network_from_files,
)


def write_stations(tmp_path):
    path = tmp_path / "stations.csv"
    path.write_text(
        "\n".join(
            [
                "station index,station name,terminal",
                "0,Alpha,false",
                "1,Beta,false",
                "2,Gamma,false",
            ]
        ),
        encoding="utf-8",
    )
    return path


def write_edges(tmp_path, name, rows):
    path = tmp_path / name
    path.write_text("\n".join(rows), encoding="utf-8")
    return path


def test_station_lookup_resolves_names_and_indices(tmp_path):
    stations = write_stations(tmp_path)
    lookup = load_station_lookup(stations)

    assert resolve_station(" alpha ", lookup) == 0
    assert resolve_station("BETA", lookup) == 1
    assert resolve_station("2", lookup) == 2
    assert resolve_station(2, lookup) == 2

    with pytest.raises(TubePlanningError):
        resolve_station("Missing", lookup)


def test_travel_time_network_keeps_fastest_duplicate_edge(tmp_path):
    line_a = write_edges(tmp_path, "line_a.csv", ["0,1,4", "0,2,9"])
    line_b = write_edges(tmp_path, "line_b.csv", ["0,2,3", "1,2,4"])

    network = travel_time_network_from_files([line_a, line_b], n_nodes=3)

    assert network.adjacency_matrix[0, 2] == pytest.approx(3.0)
    assert network.adjacency_matrix[2, 0] == pytest.approx(3.0)


def test_find_shortest_route_can_use_extra_proposal_edges(tmp_path):
    stations = write_stations(tmp_path)
    baseline = write_edges(tmp_path, "baseline.csv", ["0,1,8", "1,2,8"])
    proposal = write_edges(tmp_path, "proposal.csv", ["0,2,3"])

    result, lookup = find_shortest_route(
        "Alpha",
        "Gamma",
        edge_files=[baseline, proposal],
        stations_file=stations,
    )

    assert result.total_minutes == pytest.approx(3.0)
    assert result.path == [0, 2]
    assert lookup.names_by_id[result.target] == "Gamma"


def test_format_route_supports_text_csv_and_json():
    lookup = StationLookup(
        names_by_id={0: "Alpha", 2: "Gamma"},
        ids_by_name={"alpha": 0, "gamma": 2},
    )
    result = RouteResult(source=0, target=2, total_minutes=3.5, path=[0, 2])

    text_output = format_route(result, lookup)
    csv_output = format_route(result, lookup, output_format="csv")
    json_output = json.loads(format_route(result, lookup, output_format="json"))

    assert "Estimated travel time: 3.50 minutes" in text_output
    assert "Alpha -> Gamma" in text_output
    assert "source,target,total_minutes,station_indices,stations" in csv_output
    assert "Alpha,Gamma,3.50,0 > 2,Alpha > Gamma" in csv_output
    assert json_output["total_minutes"] == 3.5
    assert json_output["path"] == ["Alpha", "Gamma"]


def test_expand_edge_patterns_requires_matches(tmp_path):
    existing = write_edges(tmp_path, "line.csv", ["0,1,4"])

    assert expand_edge_patterns([existing]) == [existing]

    with pytest.raises(TubePlanningError):
        expand_edge_patterns([tmp_path / "missing.csv"])
