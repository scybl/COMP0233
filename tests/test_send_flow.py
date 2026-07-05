import numpy as np
import pytest
from tube_planning.flow import Flow
from tube_planning._exceptions import TubePlanningError


def make_flow(n, sources=None, sinks=None):
    """
    Helper: Create a Flow object WITHOUT running __init__,
    so we can test send_flow_along in isolation.
    """
    f = Flow.__new__(Flow)
    f.flow_matrix = np.zeros((n, n), dtype=float)
    f._sources = list(sources or [])
    f._sinks = list(sinks or [])
    return f


def test_send_flow_path_too_short():
    f = make_flow(4, sources=[0], sinks=[3])

    with pytest.raises(TubePlanningError):
        f.send_flow_along([], 5)
    with pytest.raises(TubePlanningError):
        f.send_flow_along([1], 5)

    assert np.all(f.flow_matrix == 0)


def test_send_flow_not_source_start():
    f = make_flow(4, sources=[1], sinks=[3])
    with pytest.raises(TubePlanningError):
        f.send_flow_along([0, 3], 5)


def test_send_flow_not_sink_end():
    f = make_flow(4, sources=[0], sinks=[3])
    with pytest.raises(TubePlanningError):
        f.send_flow_along([0, 2], 5)


def test_send_flow_cycle_path_ok():
    f = make_flow(4, sources=[0], sinks=[3])

    # This cycle path must be more than 2 nodes to reach circular condition
    f.send_flow_along([1, 2, 3, 1], 4)

    assert f.flow_matrix[1, 2] == 4
    assert f.flow_matrix[2, 3] == 4
    assert f.flow_matrix[3, 1] == 4

    assert f.flow_matrix[2, 1] == -4
    assert f.flow_matrix[3, 2] == -4
    assert f.flow_matrix[1, 3] == -4


def test_send_flow_adjacent_duplicate_nodes():
    f = make_flow(5, sources=[0], sinks=[4])
    with pytest.raises(TubePlanningError):
        f.send_flow_along([0, 0, 4], 3)


def test_send_flow_out_of_bounds():
    f = make_flow(4, sources=[0], sinks=[3])
    with pytest.raises(TubePlanningError):
        f.send_flow_along([0, 99], 2)


def test_send_flow_normal_update():
    f = make_flow(5, sources=[0], sinks=[4])

    f.send_flow_along([0, 2, 4], 3)

    # edges: 0->2, 2->4
    assert f.flow_matrix[0, 2] == 3
    assert f.flow_matrix[2, 0] == -3

    assert f.flow_matrix[2, 4] == 3
    assert f.flow_matrix[4, 2] == -3


def test_send_flow_zero_amount():
    f = make_flow(4, sources=[0], sinks=[3])

    f.send_flow_along([0, 1, 3], 0)

    assert np.all(f.flow_matrix == 0)


def test_send_flow_multiple_edges():
    f = make_flow(6, sources=[1], sinks=[5])

    f.send_flow_along([1, 2, 3, 4, 5], 7)

    for u, v in [(1, 2), (2, 3), (3, 4), (4, 5)]:
        assert f.flow_matrix[u, v] == 7
        assert f.flow_matrix[v, u] == -7


def test_send_flow_invalid_path_type():
    f = make_flow(4, sources=[0], sinks=[3])
    with pytest.raises(TypeError):
        f.send_flow_along(123, 5)  # not iterable
