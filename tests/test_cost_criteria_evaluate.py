import numpy as np
import uuid

from tube_planning.criteria import CostCriteria
from tube_planning.networks.proposal import Proposal


BASE_COSTING = {
    "new": 10,
    "ext": 5,
    "hire": 3,
    "train": 20,
}


def make_proposal(name, adj):
    unique = f"{name}_{uuid.uuid4().hex}"
    return Proposal(unique, adj_mat=np.array(adj))

def test_infra_single_new_edge():
    current = make_proposal(
        "current",
        [[0, 0],
         [0, 0]]
    )

    proposed = make_proposal(
        "proposed",
        [[0, 1],
         [1, 0]]
    )

    criterion = CostCriteria(costs=["infra"], budget=100)
    score = criterion._evaluate(proposed, current, BASE_COSTING)

    assert score == 95

def test_infra_two_new_edges():
    current = make_proposal(
        "current",
        [[0, 0, 0],
         [0, 0, 0],
         [0, 0, 0]]
    )

    proposed = make_proposal(
        "proposed",
        [[0, 1, 1],
         [1, 0, 0],
         [1, 0, 0]]
    )

    criterion = CostCriteria(costs=["infra"], budget=100)
    score = criterion._evaluate(proposed, current, BASE_COSTING)

    assert score == 90

def test_more_edges_costs_more():
    current = make_proposal(
        "current",
        [[0, 0, 0],
         [0, 0, 0],
         [0, 0, 0]]
    )

    one_edge = make_proposal(
        "one",
        [[0, 1, 0],
         [1, 0, 0],
         [0, 0, 0]]
    )

    two_edges = make_proposal(
        "two",
        [[0, 1, 1],
         [1, 0, 0],
         [1, 0, 0]]
    )

    criterion = CostCriteria(costs=["infra"], budget=100)

    score_one = criterion._evaluate(one_edge, current, BASE_COSTING)
    score_two = criterion._evaluate(two_edges, current, BASE_COSTING)

    assert score_two < score_one

def test_vehicle_cost_simple():
    current = make_proposal(
        "current",
        [[0, 0],
         [0, 0]]
    )

    proposed = make_proposal(
        "proposed",
        [[0, 3],
         [3, 0]]
    )

    criterion = CostCriteria(costs=["vehic"], budget=100)
    score = criterion._evaluate(proposed, current, BASE_COSTING)

    assert score == -1340

def test_over_budget_gives_negative_score():
    current = make_proposal(
        "current",
        [[0, 0],
         [0, 0]]
    )

    proposed = make_proposal(
        "proposed",
        [[0, 5],
         [5, 0]]
    )

    criterion = CostCriteria(costs=["total"], budget=10)
    score = criterion._evaluate(proposed, current, BASE_COSTING)

    assert score < 0


def test_padding_zeros_do_not_create_edges():
    current = make_proposal(
        "current",
        [[0]]
    )

    proposed = make_proposal(
        "proposed",
        [[0, 0],
         [0, 0]]
    )

    criterion = CostCriteria(costs=["infra"], budget=20)
    score = criterion._evaluate(proposed, current, BASE_COSTING)

    assert score == 20

def test_multiple_new_edges_on_new_node():
    current = make_proposal(
        "current",
        [[0, 0],
         [0, 0]]
    )

    proposed = make_proposal(
        "proposed",
        [[0, 1, 1],
         [1, 0, 0],
         [1, 0, 0]]
    )

    criterion = CostCriteria(costs=["infra"], budget=100)
    score = criterion._evaluate(proposed, current, BASE_COSTING)

    # new edge = 2 -> cost = 20 -> score = 80
    assert score == 80

def test_identical_networks_after_padding_have_no_cost():
    current = make_proposal(
        "current",
        [[0, 1],
         [1, 0]]
    )

    proposed = make_proposal(
        "proposed",
        [[0, 1],
         [1, 0]]
    )

    criterion = CostCriteria(costs=["total"], budget=40)
    score = criterion._evaluate(proposed, current, BASE_COSTING)

    assert score <= 40
