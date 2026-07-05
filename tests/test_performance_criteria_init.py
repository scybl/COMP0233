import pytest
from tube_planning.criteria.performance import PerformanceCriteria


def test_max_flow_mode():
    pc = PerformanceCriteria(sources=["a", "c"], sinks=["b", "d"])
    assert pc.supplies is None
    assert pc.demands is None
    assert pc.sources == ["a", "c"]
    assert pc.sinks == ["b", "d"]


def test_supply_without_demand_error():
    with pytest.raises(ValueError):
        PerformanceCriteria(sources=["s1"], sinks=["t1"], supplies=[10])


def test_demand_without_supply_error():
    with pytest.raises(ValueError):
        PerformanceCriteria(sources=["s1"], sinks=["t1"], demands=[10])


def test_sufficient_flow_sorted_and_matched():
    pc = PerformanceCriteria(
        sources=["c", "a"],
        sinks=["y", "x"],
        supplies=[30, 10],
        demands=[50, 40]
    )

    assert pc.sources == ["a", "c"]
    assert pc.supplies == [10.0, 30.0]

    assert pc.sinks == ["x", "y"]
    assert pc.demands == [40.0, 50.0]


def test_length_mismatch_supplies():
    with pytest.raises(ValueError):
        PerformanceCriteria(
            sources=["s1", "s2"],
            sinks=["t1"],
            supplies=[10],
            demands=[20]
        )


def test_length_mismatch_demands():
    with pytest.raises(ValueError):
        PerformanceCriteria(
            sources=["s1"],
            sinks=["t1", "t2"],
            supplies=[10],
            demands=[20]
        )


def test_duplicate_sources_error():
    with pytest.raises(ValueError):
        PerformanceCriteria(sources=["s1", "s1"], sinks=["t1"])


def test_duplicate_sinks_error():
    with pytest.raises(ValueError):
        PerformanceCriteria(sources=["s1"], sinks=["t1", "t1"])


def test_invalid_demands_type():
    with pytest.raises(ValueError):
        PerformanceCriteria(
            sources=["s1"],
            sinks=["t1"],
            supplies=[10],
            demands=[None]
        )