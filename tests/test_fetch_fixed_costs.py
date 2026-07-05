import pytest
from unittest.mock import patch
from tube_planning._exceptions import TubePlanningError
import tube_planning.query as query


@patch("tube_planning.query.send_query")
def test_fetch_fixed_costs_success(mock_query):
    """Test that valid JSON response returns a correct dictionary."""
    mock_query.return_value.json.return_value = {
        "new": 100,
        "ext": 200,
        "hire": 30,
        "train": 80,
    }

    result = query.fetch_fixed_costs("2026-05-10")
    assert result == {"new": 100.0, "ext": 200.0, "hire": 30.0, "train": 80.0}


def test_fetch_fixed_costs_invalid_date_format():
    """Test that invalid date format raises an error."""
    with pytest.raises(TubePlanningError):
        query.fetch_fixed_costs("2026/01/01")


def test_fetch_fixed_costs_outside_2026():
    """Test that a date outside the allowed range raises error."""
    with pytest.raises(TubePlanningError):
        query.fetch_fixed_costs("2025-12-31")


@patch("tube_planning.query.send_query")
def test_fetch_fixed_costs_missing_keys(mock_query):
    """Test missing required JSON keys raises TubePlanningError."""
    mock_query.return_value.json.return_value = {
        "new": 100,
        "ext": 200,
    }

    with pytest.raises(TubePlanningError):
        query.fetch_fixed_costs("2026-05-10")
