import pytest
from unittest.mock import patch
from tube_planning._exceptions import TubePlanningError
import tube_planning.query as query


GOOD_CSV = "0,1,2\n1,2,3\n"
BAD_CSV = "0,1\n"   # Missing weight


@patch("tube_planning.query.send_query")
def test_fetch_proposed_line_success(mock_query):
    """Test normal proposal CSV parsing and adjacency creation."""
    mock_query.return_value.text = GOOD_CSV
    mock_query.return_value.json.side_effect = TubePlanningError("not JSON")

    proposal = query.fetch_proposed_line("proposalA")
    adj = proposal.adjacency_matrix

    assert adj.shape == (3, 3)
    assert adj[0, 1] == pytest.approx(60/2)
    assert adj[1, 2] == pytest.approx(60/3)


@patch("tube_planning.query.send_query")
def test_fetch_proposed_line_bad_format(mock_query):
    """Test that a malformed CSV raises TubePlanningError."""
    mock_query.return_value.text = BAD_CSV
    mock_query.return_value.json.side_effect = TubePlanningError("not JSON")

    with pytest.raises(TubePlanningError):
        query.fetch_proposed_line("proposalB")


@patch("tube_planning.query.send_query")
def test_fetch_proposed_line_json_error_message(mock_query):
    """Test JSON error message from service triggers TubePlanningError."""
    mock_query.return_value.json.return_value = {
        "message": "Error in query; Proposal not recognised."
    }
    mock_query.return_value.text = ""

    with pytest.raises(TubePlanningError):
        query.fetch_proposed_line("invalidProposal")
