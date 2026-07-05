import json

import numpy as np

from tube_planning.evaluation import _format_rankings, _load_base_network, rank_proposals
from tube_planning.networks.proposal import Proposal


def make_record(name, score, failed=False):
    return {
        "proposal": Proposal(name=name, adj_mat=np.zeros((2, 2))),
        "score": score,
        "failed_essential": failed,
    }


def test_rank_proposals_prefers_pass_score_then_name():
    Proposal._all_proposals.clear()
    records = [
        make_record("zeta", 10, failed=False),
        make_record("alpha", 10, failed=False),
        make_record("beta", 99, failed=True),
    ]

    ranked = rank_proposals(records)

    assert [record["proposal"].name for record in ranked] == [
        "alpha",
        "zeta",
        "beta",
    ]


def test_format_rankings_json():
    Proposal._all_proposals.clear()
    records = [make_record("alpha", 12.345, failed=False)]

    payload = json.loads(_format_rankings(records, output_format="json"))

    assert payload == [
        {
            "rank": 1,
            "proposal": "alpha",
            "score": 12.35,
            "essential_passed": True,
        }
    ]


def test_load_base_network_from_file(tmp_path):
    network_file = tmp_path / "network.csv"
    network_file.write_text("0,1,4\n1,2,5\n", encoding="utf-8")

    network = _load_base_network(str(network_file))

    assert network.adjacency_matrix.shape == (3, 3)
    assert network.adjacency_matrix[0, 1] == 15
