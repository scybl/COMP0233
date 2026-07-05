import pytest

from tube_planning.networks.proposal import Proposal
from tube_planning._exceptions import TubePlanningError


def setup_function():
    """Reset global state before each test."""
    Proposal._all_proposals.clear()


# ---------------------------
# File validation tests
# ---------------------------


def test_from_file_rejects_non_path(tmp_path):
    with pytest.raises(TubePlanningError):
        Proposal.from_file("not_a_path.csv")


def test_from_file_rejects_missing_file(tmp_path):
    missing = tmp_path / "missing.csv"
    with pytest.raises(TubePlanningError):
        Proposal.from_file(missing)


# ---------------------------
# Basic CSV parsing tests
# ---------------------------


def test_from_file_rejects_empty_file(tmp_path):
    f = tmp_path / "empty.csv"
    f.write_text("")
    with pytest.raises(TubePlanningError):
        Proposal.from_file(f)


def test_from_file_rejects_invalid_format(tmp_path):
    f = tmp_path / "bad.csv"
    f.write_text("0,1\n")  # missing weight
    with pytest.raises(TubePlanningError):
        Proposal.from_file(f)


# ---------------------------
# Travel-time conversion tests
# ---------------------------


def test_travel_time_conversion(tmp_path):
    # travel time = 5 min → trains/hour = 60/5 = 12
    f = tmp_path / "test.csv"
    f.write_text("0,1,5\n")

    p = Proposal.from_file(f, weights_are_travel_times=True)

    assert p.adjacency_matrix[0, 1] == pytest.approx(12.0)
    assert p.adjacency_matrix[1, 0] == pytest.approx(12.0)


def test_travel_time_must_be_positive(tmp_path):
    f = tmp_path / "test.csv"
    f.write_text("0,1,0\n")  # invalid travel time zero

    with pytest.raises(TubePlanningError):
        Proposal.from_file(f)


# ---------------------------
# trains/hour (weights_are_travel_times=False)
# ---------------------------


def test_trains_per_hour_used_as_is(tmp_path):
    f = tmp_path / "tph.csv"
    f.write_text("0,1,8\n")  # trains/hour 8

    p = Proposal.from_file(f, weights_are_travel_times=False)

    assert p.adjacency_matrix[0, 1] == pytest.approx(8.0)


def test_negative_trains_per_hour_rejected(tmp_path):
    f = tmp_path / "neg.csv"
    f.write_text("0,1,-3\n")

    with pytest.raises(TubePlanningError):
        Proposal.from_file(f, weights_are_travel_times=False)


# ---------------------------
# Duplicate / contradictory edges
# ---------------------------


def test_duplicate_edge_rejected(tmp_path):
    f = tmp_path / "dup.csv"
    f.write_text("0,1,5\n0,1,6\n")

    with pytest.raises(TubePlanningError):
        Proposal.from_file(f)


def test_contradictory_edge_rejected(tmp_path):
    f = tmp_path / "contradictory.csv"
    f.write_text("0,1,5\n1,0,5\n")

    with pytest.raises(TubePlanningError):
        Proposal.from_file(f)


# ---------------------------
# Node indexing
# ---------------------------


def test_negative_station_index_rejected(tmp_path):
    f = tmp_path / "neg_station.csv"
    f.write_text("-1,2,5\n")

    with pytest.raises(TubePlanningError):
        Proposal.from_file(f)


def test_adjacency_matrix_size_inferred_correctly(tmp_path):
    f = tmp_path / "nodes.csv"
    f.write_text("0,3,10\n")  # highest index = 3 → 4 nodes

    p = Proposal.from_file(f, weights_are_travel_times=False)

    assert p.adjacency_matrix.shape == (4, 4)


# ---------------------------
# Name handling tests
# ---------------------------


def test_name_defaults_to_filename(tmp_path):
    f = tmp_path / "abc.csv"
    f.write_text("0,1,10\n")

    p = Proposal.from_file(f)

    assert p.name == "abc"


def test_name_override_works(tmp_path):
    f = tmp_path / "aaa.csv"
    f.write_text("0,1,10\n")

    p = Proposal.from_file(f, name="CustomName")

    assert p.name == "CustomName"


# ---------------------------
# Check returned object is Proposal
# ---------------------------


def test_from_file_returns_proposal_instance(tmp_path):
    f = tmp_path / "obj.csv"
    f.write_text("0,1,5\n")

    p = Proposal.from_file(f)

    assert isinstance(p, Proposal)
