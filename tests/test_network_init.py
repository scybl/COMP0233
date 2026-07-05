import numpy as np
import pytest
from tube_planning.networks.network import Network
from tube_planning._exceptions import TubePlanningError


# -----------------------------
# Tests for adj_mat constructor
# -----------------------------
def test_init_with_valid_adj_mat():
    adj = np.array([[0, 3], [3, 0]])

    net = Network(adj_mat=adj)

    assert isinstance(net.adjacency_matrix, np.ndarray)
    assert net.n_nodes == 2
    assert np.array_equal(net.adjacency_matrix, adj)


def test_init_adj_mat_not_numpy():
    with pytest.raises(TubePlanningError):
        Network(adj_mat=[[0, 1], [1, 0]])  # not numpy array


def test_init_adj_mat_not_square():
    adj = np.array([[0, 1, 2]])
    with pytest.raises(TubePlanningError):
        Network(adj_mat=adj)


def test_init_adj_mat_negative_weights():
    adj = np.array([[0, -1], [1, 0]])
    with pytest.raises(TubePlanningError):
        Network(adj_mat=adj)


# -----------------------------------
# Tests for edge_table constructor
# -----------------------------------
def test_init_with_valid_edge_table():
    edge_table = [(0, 1, 5), (1, 2, 7)]

    net = Network(edge_table=edge_table)

    adj = net.adjacency_matrix

    assert net.n_nodes == 3
    assert adj[0, 1] == 5 and adj[1, 0] == 5
    assert adj[1, 2] == 7 and adj[2, 1] == 7
    assert adj[0, 2] == 0


def test_init_edge_table_not_list():
    with pytest.raises(TubePlanningError):
        Network(edge_table="not-a-list")


def test_init_edge_table_invalid_triple():
    edge_table = [
        (0, 1, 5),
        (1, 2),  # invalid
    ]
    with pytest.raises(TubePlanningError):
        Network(edge_table=edge_table)


def test_init_edge_table_negative_weight():
    edge_table = [(0, 1, -3)]
    with pytest.raises(TubePlanningError):
        Network(edge_table=edge_table)


def test_init_edge_table_zero_weight_ignored():
    edge_table = [(0, 1, 3), (1, 2, 0)]  # should be ignored

    net = Network(edge_table=edge_table)
    adj = net.adjacency_matrix

    assert adj[0, 1] == 3
    assert adj[1, 0] == 3
    assert adj[1, 2] == 0
    assert adj[2, 1] == 0


def test_init_edge_table_duplicate_or_contradictory():
    edge_table = [(0, 1, 3), (1, 0, 3)]  # duplicate in reverse direction
    with pytest.raises(TubePlanningError):
        Network(edge_table=edge_table)


# -----------------------------------
# Tests for mutual exclusivity
# -----------------------------------
def test_init_both_inputs_provided():
    adj = np.zeros((2, 2))
    edge_table = [(0, 1, 3)]
    with pytest.raises(TubePlanningError):
        Network(adj_mat=adj, edge_table=edge_table)


def test_init_no_inputs_provided():
    with pytest.raises(TubePlanningError):
        Network()


# -----------------------------
# n_nodes property
# -----------------------------
def test_n_nodes_property():
    adj = np.zeros((4, 4))
    net = Network(adj_mat=adj)
    assert net.n_nodes == 4
