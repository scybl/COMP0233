import numpy as np
from tube_planning.networks import Network


class DummyFlow:
    """Minimal Flow-like object for testing."""

    def __init__(self, mat):
        self.flow_matrix = mat


# -------------------------------------------------------
# TESTS FOR capacity_constraint
# -------------------------------------------------------
def test_capacity_constraint_all_within_capacity():
    adj = np.array([[0, 5], [5, 0]])
    net = Network(adj_mat=adj)

    flow_mat = np.array([[0, 3], [3, 0]])
    flow = DummyFlow(flow_mat)

    assert net.capacity_constraint(flow) is True


def test_capacity_constraint_exceeds_capacity():
    adj = np.array([[0, 5], [5, 0]])
    net = Network(adj_mat=adj)

    # exceeds capacity (3 > 2)
    flow_mat = np.array([[0, 6], [6, 0]])
    flow = DummyFlow(flow_mat)

    assert net.capacity_constraint(flow) is False


def test_capacity_constraint_shape_mismatch():
    adj = np.zeros((3, 3))
    net = Network(adj_mat=adj)

    # 2x2 flow matrix -> shape mismatch
    flow_mat = np.zeros((2, 2))
    flow = DummyFlow(flow_mat)

    assert net.capacity_constraint(flow) is False


def test_capacity_constraint_zero_flow_always_valid():
    adj = np.array([[0, 10], [10, 0]])
    net = Network(adj_mat=adj)

    flow_mat = np.zeros((2, 2))
    flow = DummyFlow(flow_mat)

    assert net.capacity_constraint(flow) is True


def test_capacity_constraint_equal_to_capacity_is_valid():
    adj = np.array([[0, 4], [4, 0]])
    net = Network(adj_mat=adj)

    flow_mat = np.array([[0, 4], [4, 0]])
    flow = DummyFlow(flow_mat)

    assert net.capacity_constraint(flow) is True
