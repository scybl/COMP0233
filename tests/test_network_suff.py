import numpy as np
import pytest

from tube_planning._exceptions import TubePlanningError
from tube_planning.flow import Flow
from tube_planning.networks import Network


def test_sufficient_flow_feasible():
    # Simple chain: 0 -> 1 -> 2
    adj = np.array([[0, 5, 0], [5, 0, 5], [0, 5, 0]], dtype=float)

    net = Network(adj_mat=adj)

    sources = {0: 3}
    sinks = {2: 3}

    feasible, flow = net.sufficient_flow(sources, sinks)
    assert feasible is True
    assert isinstance(flow, Flow)
    assert np.isclose(flow.flow_matrix[0].sum(), 3.0)


def test_sufficient_flow_infeasible():
    adj = np.array([[0, 2, 0], [2, 0, 1], [0, 1, 0]], dtype=float)

    net = Network(adj_mat=adj)

    sources = {0: 5}
    sinks = {2: 5}

    feasible, flow = net.sufficient_flow(sources, sinks)

    # Only 1 unit can reach 2 (bottleneck)
    assert feasible is False
    assert np.isclose(flow.flow_matrix[0].sum(), 1.0)


def test_sufficient_flow_negative_supply_rejected():
    adj = np.zeros((3, 3))
    net = Network(adj_mat=adj)

    with pytest.raises(TubePlanningError):
        net.sufficient_flow({0: -1}, {2: 5})


def test_sufficient_flow_non_dict_rejected():
    adj = np.zeros((3, 3))
    net = Network(adj_mat=adj)

    with pytest.raises(TubePlanningError):
        net.sufficient_flow([0], {2: 5})
