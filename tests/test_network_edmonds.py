import numpy as np
import pytest

from tube_planning.networks import Network
from tube_planning.flow import Flow
from tube_planning._exceptions import TubePlanningError


def _max_flow_value(flow: Flow, source: int) -> float:
    """Helper: total flow leaving `source`."""
    return flow.flow_matrix[source, :].sum()


def test_edmonds_karp_diamond_network():
    adj = np.array(
        [
            [0, 5, 5, 0],
            [5, 0, 0, 5],
            [5, 0, 0, 5],
            [0, 5, 5, 0],
        ],
        dtype=float,
    )
    net = Network(adj_mat=adj)
    flow = net.edmonds_karp(source=0, sink=3, maxiter=100)
    value = _max_flow_value(flow, source=0)

    assert pytest.approx(value) == 10.0
    assert net.capacity_constraint(flow) is True


def test_edmonds_karp_linear_bottleneck():
    adj = np.array(
        [
            [0, 5, 0, 0],
            [5, 0, 3, 0],
            [0, 3, 0, 4],
            [0, 0, 4, 0],
        ],
        dtype=float,
    )
    net = Network(adj_mat=adj)

    flow = net.edmonds_karp(source=0, sink=3, maxiter=100)
    value = _max_flow_value(flow, source=0)

    assert pytest.approx(value) == 3.0
    assert net.capacity_constraint(flow) is True


def test_edmonds_karp_raises_if_not_converged():
    adj = np.array(
        [
            [0, 5, 5, 0],
            [5, 0, 0, 5],
            [5, 0, 0, 5],
            [0, 5, 5, 0],
        ],
        dtype=float,
    )
    net = Network(adj_mat=adj)

    with pytest.raises(TubePlanningError):
        net.edmonds_karp(source=0, sink=3, maxiter=0)


def test_edmonds_karp_invalid_source_or_sink():
    adj = np.zeros((3, 3), dtype=float)
    net = Network(adj_mat=adj)

    with pytest.raises(TubePlanningError):
        net.edmonds_karp(source=-1, sink=2)

    with pytest.raises(TubePlanningError):
        net.edmonds_karp(source=0, sink=3)
