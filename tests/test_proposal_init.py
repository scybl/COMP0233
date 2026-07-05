import pytest
import numpy as np

from tube_planning.networks.proposal import Proposal
from tube_planning._exceptions import TubePlanningError


def setup_function():
    """
    Runs before every test to reset Proposal._all_proposals.
    This ensures tests do not interfere with each other.
    """
    Proposal._all_proposals.clear()


def test_proposal_name_is_converted_to_string():
    p = Proposal(name=123, adj_mat=np.zeros((1, 1)))
    assert p.name == "123"


def test_proposal_rejects_duplicate_name():
    Proposal(name="A", adj_mat=np.zeros((1, 1)))
    with pytest.raises(TubePlanningError):
        Proposal(name="A", adj_mat=np.zeros((1, 1)))


def test_proposal_rejects_none_name():
    with pytest.raises(TubePlanningError):
        Proposal(name=None, adj_mat=np.zeros((1, 1)))


def test_proposal_is_added_to_all_proposals():
    assert Proposal._all_proposals == []

    p1 = Proposal(name="X", adj_mat=np.zeros((1, 1)))
    p2 = Proposal(name="Y", adj_mat=np.zeros((1, 1)))

    assert len(Proposal._all_proposals) == 2
    assert Proposal._all_proposals[0] is p1
    assert Proposal._all_proposals[1] is p2


def test_names_in_use_property():
    Proposal(name="P1", adj_mat=np.zeros((1, 1)))
    Proposal(name="P2", adj_mat=np.zeros((1, 1)))

    dummy = Proposal(name="TEMP", adj_mat=np.zeros((1, 1)))
    names = dummy.names_in_use

    assert set(names) == {"P1", "P2", "TEMP"}


def test_proposal_calls_network_init():
    adj = np.array([[0.0]])

    p = Proposal(name="Valid", adj_mat=adj)

    assert isinstance(p, Proposal)
    assert p.adjacency_matrix.shape == (1, 1)
    assert p.adjacency_matrix[0, 0] == 0.0
