import numpy as np
import pytest

from tube_planning.networks.network import Network
from tube_planning._exceptions import TubePlanningError


# ---------------------------------------------------
# BFS TESTS
# ---------------------------------------------------


def test_bfs_simple_network():
    # 0 -- 1 -- 2
    adj = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
    net = Network(adj_mat=adj)

    trace = net.bfs(root=0)

    # root should point to itself
    assert trace[0] == 0
    assert trace[1] == 0
    assert trace[2] == 1


def test_bfs_unreachable_nodes():
    # 0 -- 1     2 (isolated)
    adj = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]])
    net = Network(adj_mat=adj)

    trace = net.bfs(root=0)

    assert trace[0] == 0
    assert trace[1] == 0
    assert trace[2] == -1  # unreachable


def test_bfs_invalid_root_negative():
    adj = np.zeros((3, 3))
    net = Network(adj_mat=adj)

    with pytest.raises(TubePlanningError):
        net.bfs(root=-1)


def test_bfs_invalid_root_too_large():
    adj = np.zeros((3, 3))
    net = Network(adj_mat=adj)

    with pytest.raises(TubePlanningError):
        net.bfs(root=3)


# ---------------------------------------------------
# path_from_bfs TESTS
# ---------------------------------------------------


def test_path_from_bfs_normal_path():
    # trace produced by BFS from root=0 on: 0-1-2-3
    trace = [0, 0, 1, 2]

    path = Network.path_from_bfs(trace, dest=3)
    assert path == [0, 1, 2, 3]


def test_path_from_bfs_root_equals_dest():
    trace = [0, -1, -1]
    path = Network.path_from_bfs(trace, dest=0)
    assert path == [0]


def test_path_from_bfs_unreachable_dest():
    # dest = 2 unreachable
    trace = [0, 0, -1]

    with pytest.raises(TubePlanningError):
        Network.path_from_bfs(trace, dest=2)


def test_path_from_bfs_invalid_dest():
    trace = [0, 0, 1]

    with pytest.raises(TubePlanningError):
        Network.path_from_bfs(trace, dest=-1)

    with pytest.raises(TubePlanningError):
        Network.path_from_bfs(trace, dest=5)


def test_path_from_bfs_no_root_detected():
    # no node satisfies trace[i] == i
    trace = [-1, 0, 1]

    with pytest.raises(TubePlanningError):
        Network.path_from_bfs(trace, dest=2)


def test_path_from_bfs_multiple_roots():
    # nodes 0 and 2 both root (invalid)
    trace = [0, -1, 2]

    with pytest.raises(TubePlanningError):
        Network.path_from_bfs(trace, dest=2)
