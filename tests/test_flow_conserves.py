import numpy as np
from tube_planning.flow import Flow


def make_flow(matrix, sources=None, sinks=None):
    """Helper to build Flow without checking conservation during __init__."""
    f = Flow.__new__(Flow)
    f.flow_matrix = np.array(matrix, dtype=float)
    f._sources = list(sources or [])
    f._sinks = list(sinks or [])
    return f


def test_conserves_flow_balanced_no_sources():
    """
    Balanced flow:
        Row sums = 0 → net flow = 0 → conserves
    """
    mat = np.array([[0, 5, -5], [-5, 0, 5], [5, -5, 0]])

    f = make_flow(mat)
    assert f._conserves_flow() is True


def test_conserves_flow_unbalanced_no_sources():
    """
    Unbalanced flow:
        Row 1 has net_flow != 0 → does NOT conserve
    """
    mat = np.array(
        [
            [0, 3, -3],  # net = 0
            [-2, 0, 1],  # net = -1 → violates conservation
            [2, -1, 0],  # net = 1
        ]
    )

    f = make_flow(mat)
    assert f._conserves_flow() is False


def test_conserves_flow_sources_are_skipped():
    """
    Sources are *skipped* in conservation check.
    So even if source row is unbalanced, it should NOT affect the result.
    """
    mat = np.array([[0, 10, -1], [-10, 0, 10], [1, -10, 0]])

    f = make_flow(mat, sources=[0, 2])
    assert f._conserves_flow() is True


def test_conserves_flow_sinks_are_skipped():
    """
    Sinks are also *skipped* in conservation check.
    So even if sink row is unbalanced, it should be ignored.
    """
    mat = np.array([[0, 10, -1], [-10, 0, 10], [1, -10, 0]])

    f = make_flow(mat, sinks=[0, 2])
    assert f._conserves_flow() is True


def test_conserves_flow_all_unbalanced_but_all_skipped():
    """
    Extreme case:
    Every node is either source or sink → no internal nodes to check.
    Should return True.
    """
    mat = np.array([[0, 5], [-5, 0]])

    f = make_flow(mat, sources=[0], sinks=[1])
    assert f._conserves_flow() is True


def test_conserves_flow_rejects_non_skew_symmetric_matrix():
    mat = np.array([[0, 3, 0], [-2, 0, 2], [0, -2, 0]])

    f = make_flow(mat, sources=[0], sinks=[2])
    assert f._conserves_flow() is False
