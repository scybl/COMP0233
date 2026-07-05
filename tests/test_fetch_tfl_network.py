import pytest
from unittest.mock import patch, MagicMock
import tube_planning.query as query
from tube_planning._exceptions import TubePlanningError


# Mock CSV responses for line 0 and line 1
LINE0 = "0,1,2\n1,2,3\n"
LINE1 = "0,2,4\n"


def mock_send_query(service, **params):
    """Mock send_query such that line 0 and line 1 exist.

    Line >=2 raises error.
    """
    idx = params.get("line_identifier")

    # Return CSV response for line 0
    if idx == 0:
        m = MagicMock()
        m.text = LINE0
        m.json.side_effect = TubePlanningError("not JSON")
        return m

    # Return CSV response for line 1
    if idx == 1:
        m = MagicMock()
        m.text = LINE1
        m.json.side_effect = TubePlanningError("not JSON")
        return m

    # Stop iteration for line >= 2
    raise TubePlanningError("No more lines")


@patch("tube_planning.query.send_query", side_effect=mock_send_query)
def test_fetch_tfl_network(mock_query):
    """Test adjacency matrix assembly for multiple lines."""
    net = query.fetch_tfl_network()
    adj = net.adjacency_matrix

    # Should have 3 stations (0,1,2)
    assert adj.shape == (3, 3)

    # Check weights: weight = 60 / time
    assert adj[0, 1] == pytest.approx(60/2)
    assert adj[1, 2] == pytest.approx(60/3)
    assert adj[0, 2] == pytest.approx(60/4)
