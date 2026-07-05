import pytest
from tube_planning.criteria.cost import CostCriteria


def test_normal_costs_init():
    c = CostCriteria(["infra", "vehic"], budget=100)
    assert c.costs == ["infra", "vehic"]
    assert c.budget == 100.0


def test_total_overrides_other_costs():
    c = CostCriteria(["infra", "total", "vehic"])
    assert c.costs == ["total"]


def test_costs_must_be_list():
    with pytest.raises(TypeError):
        CostCriteria("infra")  # not a list


def test_costs_must_be_strings():
    with pytest.raises(TypeError):
        CostCriteria(["infra", 123])  # 123 is not str


def test_invalid_cost_value():
    with pytest.raises(ValueError):
        CostCriteria(["unknown"])  # does not contain valid substrings


def test_budget_cast_to_float():
    c = CostCriteria(["infra"], budget="50")
    assert isinstance(c.budget, float)
    assert c.budget == 50.0