import numpy as np
import pytest
from tube_planning.flow import Flow
from tube_planning._exceptions import TubePlanningError

# ---------- Success Cases ----------


def test_init_valid_input():
    """Valid flow matrix with valid sources and sinks initializes correctly."""
    mat = np.array([[0, 5], [-5, 0]], dtype=float)
    flow = Flow(mat, sources=[0], sinks=[1])

    assert np.array_equal(flow.flow_matrix, mat)
    assert flow.sources == [0]
    assert flow.sinks == [1]


def test_init_defaults_empty_sources_sinks():
    """sources and sinks should default to empty when None."""
    mat = np.zeros((3, 3))
    flow = Flow(mat)

    assert flow.sources == []
    assert flow.sinks == []


def test_init_sources_sinks_unordered_and_with_duplicates():
    """sources/sinks should be sorted and deduplicated."""
    mat = np.zeros((3, 3))
    flow = Flow(mat, sources=[2, 1, 1], sinks=[2, 0, 2])

    assert flow.sources == [1, 2]
    assert flow.sinks == [0, 2]


def test_sources_and_sinks_return_copies_not_internal_list():
    """Flow.sources and Flow.sinks should return a copy so user cannot mutate internal state."""
    f = Flow(np.zeros((3, 3)), sources=[0, 2], sinks=[1])

    s1 = f.sources
    s1.append(99)

    assert f.sources == [0, 2]  # internal state unchanged

    k1 = f.sinks
    k1.append(99)

    assert f.sinks == [1]  # internal state unchanged


# ---------- Failure Cases ----------


def test_init_non_square_matrix():
    """flow_matrix must be square."""
    mat = np.zeros((2, 3))
    with pytest.raises(TubePlanningError):
        Flow(mat)


def test_init_unconvertible_flow_matrix():
    """flow_matrix must be convertible to numeric numpy array."""
    with pytest.raises(TubePlanningError):
        Flow(flow_matrix="abc")  # cannot convert to float


def test_init_source_out_of_bounds():
    """sources must be within [0, n-1]."""
    mat = np.zeros((3, 3))
    with pytest.raises(TubePlanningError):
        Flow(mat, sources=[3])  # out of bounds


def test_init_sink_out_of_bounds():
    """sinks must be within [0, n-1]."""
    mat = np.zeros((3, 3))
    with pytest.raises(TubePlanningError):
        Flow(mat, sinks=[-1])  # invalid node


def test_sources_and_sinks_are_read_only():
    """sources and sinks should be read-only properties (no external mutation)."""
    f = Flow(np.zeros((4, 4)), sources=[1], sinks=[2])

    # attempting to write should fail
    with pytest.raises(AttributeError):
        f.sources = [9]

    with pytest.raises(AttributeError):
        f.sinks = [9]


def test_init_non_conserving_flow():
    """Flow that fails conservation check must raise."""
    mat = np.array(
        [
            [0, 5, 0],
            [-5, 0, 1],  # imbalance → violates conservation
            [0, -1, 0],
        ]
    )

    with pytest.raises(TubePlanningError):
        Flow(mat)
