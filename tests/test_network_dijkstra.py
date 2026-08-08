import numpy as np
import pytest

from tube_planning._exceptions import TubePlanningError
from tube_planning.networks.network import Network


def test_dijkstra_prefers_lowest_total_weight():
    adj = np.array(
        [
            [0, 2, 10],
            [2, 0, 2],
            [10, 2, 0],
        ],
        dtype=float,
    )
    net = Network(adj_mat=adj)

    distances, predecessors = net.dijkstra(source=0)
    total_minutes, path = net.shortest_path(source=0, target=2)

    assert distances[2] == pytest.approx(4.0)
    assert predecessors == [0, 0, 1]
    assert total_minutes == pytest.approx(4.0)
    assert path == [0, 1, 2]


def test_shortest_path_returns_source_when_source_is_target():
    adj = np.array(
        [
            [0, 3],
            [3, 0],
        ],
        dtype=float,
    )
    net = Network(adj_mat=adj)

    total_minutes, path = net.shortest_path(source=1, target=1)

    assert total_minutes == pytest.approx(0.0)
    assert path == [1]


def test_shortest_path_raises_for_unreachable_target():
    adj = np.array(
        [
            [0, 1, 0],
            [1, 0, 0],
            [0, 0, 0],
        ],
        dtype=float,
    )
    net = Network(adj_mat=adj)

    with pytest.raises(TubePlanningError):
        net.shortest_path(source=0, target=2)


def test_dijkstra_validates_source_and_target():
    adj = np.zeros((3, 3), dtype=float)
    net = Network(adj_mat=adj)

    with pytest.raises(TubePlanningError):
        net.dijkstra(source=-1)

    with pytest.raises(TubePlanningError):
        net.dijkstra(source=3)

    with pytest.raises(TubePlanningError):
        net.shortest_path(source=0, target=-1)

    with pytest.raises(TubePlanningError):
        net.shortest_path(source=0, target=3)
