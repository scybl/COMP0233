import pytest
from unittest.mock import patch, MagicMock
import requests
from tube_planning._exceptions import TubePlanningError
import tube_planning.query as query


def test_send_query_invalid_service():
    """Test that an invalid service name raises TubePlanningError."""
    with pytest.raises(TubePlanningError):
        query.send_query("wrong/service")


@patch("tube_planning.query.requests.get")
def test_send_query_http_error(mock_get):
    """Test that HTTP error status code raises TubePlanningError."""
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_get.return_value = mock_resp

    with pytest.raises(TubePlanningError):
        query.send_query("line/query", line_identifier=3)


@patch("tube_planning.query.requests.get")
def test_send_query_success(mock_get):
    """Test that a valid request returns a response object."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "ok"
    mock_get.return_value = mock_resp

    resp = query.send_query("line/query", line_identifier=1)

    assert resp is mock_resp
    mock_get.assert_called_once_with(
        "https://transport-planning-service.example/tube-planning/line/query",
        params={"line_identifier": 1},
        timeout=query.DEFAULT_TIMEOUT,
    )


@patch("tube_planning.query.requests.get")
def test_send_query_request_exception(mock_get):
    mock_get.side_effect = requests.Timeout("slow")

    with pytest.raises(TubePlanningError, match="failed"):
        query.send_query("line/query", line_identifier=1)
