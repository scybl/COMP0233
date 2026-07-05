import numpy as np
from tube_planning.flow import Flow


def make_flow(matrix, sources=None, sinks=None):
    """Helper to create Flow objects for property tests."""
    mat = np.array(matrix, dtype=float)
    f = Flow(mat, sources or [], sinks or [])
    return f


def test_flow_in():
    """
    flow_in = sum of abs(negative entries in each row)
    """
    mat = np.array(
        [
            [0, 3, -3],
            [-3, 0, 3],
            [3, -3, 0],
        ]
    )

    f = make_flow(mat)

    expected = np.array([3, 3, 3])
    np.testing.assert_array_equal(f.flow_in, expected)


def test_flow_out():
    """
    flow_out = sum of positive entries in each row
    """
    mat = np.array(
        [
            [0, 3, -3],
            [-3, 0, 3],
            [3, -3, 0],
        ]
    )

    f = make_flow(mat)

    expected = np.array([3, 3, 3])
    np.testing.assert_array_equal(f.flow_out, expected)


def test_net_flow():
    """
    net_flow = flow_in - flow_out
    """
    mat = np.array(
        [
            [0, 3, -3],
            [-3, 0, 3],
            [3, -3, 0],
        ]
    )

    f = make_flow(mat)

    expected = np.array([0, 0, 0])
    np.testing.assert_array_equal(f.net_flow, expected)


def test_value_with_sources():
    """
    value = total net outflow from source nodes
    i.e. sum of entries in rows indexed by sources
    """
    mat = np.array(
        [
            [0, 5, -3],  # inflow=3, outflow=5 → net = -2 → source
            [-5, 0, 5],  # inflow=5, outflow=5 → net = 0
            [3, -5, 0],  # inflow=5, outflow=3 → net = +2 → sink
        ]
    )

    f = make_flow(mat, sources=[0], sinks=[2])

    # Value = net outflow from source 0 = flow_out[0] - flow_in[0] = 5 - 3 = 2
    assert f.value == 2.0


def test_value_multiple_sources():
    """
    Multiple sources: sum all their row sums
    """
    mat = np.array(
        [
            [0, 5, 0],  # row sum = 5
            [-5, 0, 9],  # row sum = 4
            [0, -9, 0],  # row sum = -9
        ]
    )

    f = make_flow(mat, sources=[0, 1], sinks=[2])

    # Expected = 5 + 4 = 9
    assert f.value == 9.0


def test_value_no_sources():
    """
    If no sources, value = 0
    """
    mat = np.zeros((3, 3))
    f = make_flow(mat, sources=[])

    assert f.value == 0.0
