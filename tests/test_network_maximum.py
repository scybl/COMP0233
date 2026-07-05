import numpy as np
import pytest
from typing import Iterable
from tube_planning._exceptions import TubePlanningError
from tube_planning.flow import Flow
from tube_planning.networks.network import Network


def _flow_value(flow: Flow, sources: Iterable[int]) -> float:
    """Helper: total flow leaving all sources"""
    fm = flow.flow_matrix
    return sum(fm[s, :].sum() for s in sources)


# ----------------------------------------------------------
# 1. Basic multi-source multi-sink max flow
# ----------------------------------------------------------


def test_maximum_flow_simple_diamond():
    # Graph:
    # 0 -> 1 -> 3
    # 0 -> 2 -> 3
    # Each edge has capacity 5 → max flow = 10
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
    flow = net.maximum_flow(sources=[0], sinks=[3])

    assert isinstance(flow, Flow)
    assert pytest.approx(_flow_value(flow, [0])) == 10.0
    assert net.capacity_constraint(flow) is True


# ----------------------------------------------------------
# 2. Multiple source, multiple sink
# ----------------------------------------------------------


def test_maximum_flow_multi_sources_sinks():
    # 0 and 1 are sources
    # 4 is sink
    # Should push 5+3=8 units total
    adj = np.array(
        [
            [0, 0, 5, 0, 0],
            [0, 0, 3, 0, 0],
            [5, 3, 0, 4, 0],
            [0, 0, 4, 0, 6],
            [0, 0, 0, 6, 0],
        ],
        dtype=float,
    )

    net = Network(adj_mat=adj)
    flow = net.maximum_flow([0, 1], [4])

    assert pytest.approx(_flow_value(flow, [0, 1])) == 4.0
    assert net.capacity_constraint(flow) is True


# ----------------------------------------------------------
# 3. Input validation
# ----------------------------------------------------------


def test_maximum_flow_rejects_single_int_sources():
    adj = np.zeros((3, 3))
    net = Network(adj_mat=adj)

    with pytest.raises(TubePlanningError):
        net.maximum_flow(0, [2])  # Not iterable


def test_maximum_flow_rejects_non_int_entries():
    adj = np.zeros((3, 3))
    net = Network(adj_mat=adj)

    with pytest.raises(TubePlanningError):
        net.maximum_flow(["bad"], [2])


def test_maximum_flow_rejects_overlapping_nodes():
    adj = np.zeros((3, 3))
    net = Network(adj_mat=adj)

    with pytest.raises(TubePlanningError):
        net.maximum_flow([0, 1], [1, 2])  # 1 overlaps


# ----------------------------------------------------------
# 4. maxiter forwarding
# ----------------------------------------------------------


def test_maximum_flow_maxiter_forwarded():
    adj = np.array([[0, 5], [5, 0]])
    net = Network(adj_mat=adj)

    # maxiter=0 → edmonds_karp must fail immediately
    with pytest.raises(TubePlanningError):
        net.maximum_flow([0], [1], maxiter=0)
