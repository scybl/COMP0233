import json
import pytest
from tube_planning.criteria.group import CriteriaGroup
from tube_planning.criteria.cost import CostCriteria
from tube_planning.criteria.performance import PerformanceCriteria


# Test: malformed JSON file
def test_malformed_json(tmp_path):
    """
    If the .cfile is not valid JSON, from_file must raise an error.
    """
    f = tmp_path / "bad_json.cfile"
    f.write_text("{bad json:::")  # intentionally broken

    with pytest.raises(Exception):
        CriteriaGroup.from_file(f)


# Helper to write JSON dict to tmp file
def write_cfile(tmp_path, data, name="temp.cfile"):
    f = tmp_path / name
    f.write_text(json.dumps(data))
    return f


# 1. BASIC LOADING TESTS
def test_load_basic_cost_and_performance(tmp_path):
    data = {
        "essential": [
            {
                "costs": ["infra"],
                "budget": 10,
                "description": "infra test",
                "weight": 2,
            }
        ],
        "desirable": [
            {
                "sources": [1],
                "sinks": [5],
                "description": "perf test",
                "weight": 3,
            }
        ],
    }

    f = write_cfile(tmp_path, data)
    cg = CriteriaGroup.from_file(f)

    # Cost criterion
    e = cg.essential[0]
    assert isinstance(e, CostCriteria)
    assert e.costs == ["infra"]
    assert e.budget == 10.0
    assert e.weight == 2
    assert e.description == "infra test"

    # Performance criterion
    d = cg.desirable[0]
    assert isinstance(d, PerformanceCriteria)
    assert d.sources == [1]
    assert d.sinks == [5]
    assert d.weight == 3
    assert d.description == "perf test"


def test_default_weight(tmp_path):
    data = {"essential": [{"costs": ["total"], "budget": 3}]}
    f = write_cfile(tmp_path, data)
    cg = CriteriaGroup.from_file(f)

    crit = cg.essential[0]
    assert crit.weight == 1.0


def test_performance_missing_supplies_demands(tmp_path):
    data = {"desirable": [{"sources": [1, 2], "sinks": [3, 4]}]}
    f = write_cfile(tmp_path, data)

    cg = CriteriaGroup.from_file(f)
    crit = cg.desirable[0]

    assert isinstance(crit, PerformanceCriteria)
    assert crit.sources == [1, 2]
    assert crit.sinks == [3, 4]
    assert crit.supplies is None
    assert crit.demands is None


# 2. ERROR CASES
def test_error_mixed_criterion_types(tmp_path):
    # both costs and sources/sinks present -> invalid
    data = {"essential": [{"costs": ["infra"], "sources": [1], "sinks": [2]}]}
    f = write_cfile(tmp_path, data)

    with pytest.raises(ValueError):
        CriteriaGroup.from_file(f)


def test_error_invalid_criterion(tmp_path):
    # neither costs nor (sources+sinks)
    data = {"essential": [{"description": "invalid"}]}
    f = write_cfile(tmp_path, data)

    with pytest.raises(ValueError):
        CriteriaGroup.from_file(f)


def test_error_weight_nonpositive(tmp_path):
    data = {"essential": [{"costs": ["infra"], "weight": 0}]}
    f = write_cfile(tmp_path, data)

    with pytest.raises(ValueError):
        CriteriaGroup.from_file(f)


# 3. OPTIONAL FIELDS & EMPTY GROUPS
def test_optional_fields_defaults(tmp_path):
    data = {"essential": [{"costs": ["vehic"]}]}
    f = write_cfile(tmp_path, data)

    cg = CriteriaGroup.from_file(f)
    crit = cg.essential[0]

    assert crit.description == ""
    assert crit.weight == 1.0
    assert crit.budget == 0


def test_missing_essential_and_desirable(tmp_path):
    data = {"other": []}
    f = write_cfile(tmp_path, data)

    cg = CriteriaGroup.from_file(f)
    assert cg.essential == []
    assert cg.desirable == []


def test_empty_groups(tmp_path):
    data = {"essential": [], "desirable": [{"sources": [1], "sinks": [2]}]}
    f = write_cfile(tmp_path, data)

    cg = CriteriaGroup.from_file(f)
    assert len(cg.essential) == 0
    assert isinstance(cg.desirable[0], PerformanceCriteria)


# 4. ROUND-TRIP (load -> save -> load)   — FOCUSED ON REAL ODD BEHAVIOURS
def test_round_trip_preserves_meaning(tmp_path):
    data = {
        "essential": [
            {"costs": ["infra"], "budget": 10, "description": "x", "weight": 2}
        ],
        "desirable": [
            {"sources": [1], "sinks": [2]}
        ],
    }

    f1 = write_cfile(tmp_path, data)
    cg1 = CriteriaGroup.from_file(f1)

    f2 = tmp_path / "saved.cfile"
    cg1.to_criteria_file(f2)

    cg2 = CriteriaGroup.from_file(f2)

    # Check semantic equivalence
    e = cg2.essential[0]
    assert isinstance(e, CostCriteria)
    assert e.costs == ["infra"]
    assert e.budget == 10
    assert e.weight == 2
    assert e.description == "x"   # your implementation preserves description

    d = cg2.desirable[0]
    assert d.sources == [1]
    assert d.sinks == [2]


def test_round_trip_adds_default_weight(tmp_path):
    data = {"essential": [{"costs": ["infra"], "budget": 10}]}
    f1 = write_cfile(tmp_path, data)

    cg1 = CriteriaGroup.from_file(f1)
    f2 = tmp_path / "saved.cfile"
    cg1.to_criteria_file(f2)

    saved = json.loads(f2.read_text())
    assert saved["essential"][0]["weight"] == 1.0


def test_round_trip_budget_becomes_float(tmp_path):
    data = {"essential": [{"costs": ["infra"], "budget": 5}]}  # int
    f1 = write_cfile(tmp_path, data)

    cg1 = CriteriaGroup.from_file(f1)
    f2 = tmp_path / "saved.cfile"
    cg1.to_criteria_file(f2)

    saved = json.loads(f2.read_text())
    assert isinstance(saved["essential"][0]["budget"], float)


def test_round_trip_key_order_changes(tmp_path):
    data = {"essential": [{"costs": ["infra"], "budget": 5, "weight": 2}]}

    f1 = write_cfile(tmp_path, data)
    original_text = f1.read_text()

    cg1 = CriteriaGroup.from_file(f1)
    f2 = tmp_path / "saved.cfile"
    cg1.to_criteria_file(f2)

    new_text = f2.read_text()

    # JSON key order is typically not preserved
    assert original_text != new_text


def test_round_trip_supplies_demands_preserved(tmp_path):
    data = {
        "desirable": [
            {"sources": [1], "sinks": [2], "supplies": [5], "demands": [3]}
        ]
    }

    f1 = write_cfile(tmp_path, data)
    cg1 = CriteriaGroup.from_file(f1)

    f2 = tmp_path / "saved.cfile"
    cg1.to_criteria_file(f2)
    saved = json.loads(f2.read_text())

    new = saved["desirable"][0]

    # supplies/demands should be preserved
    assert new["supplies"] == [5.0]
    assert new["demands"] == [3.0]