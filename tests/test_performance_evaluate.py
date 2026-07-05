from unittest.mock import MagicMock
from tube_planning.criteria.performance import PerformanceCriteria


class FakeFlow:
    """
    Fake flow object to mimic return value of network flow methods.
    """
    def __init__(self, value):
        self.value = value


class FakeNetwork:
    def __init__(self, max_flow_value=None, sufficient_flow_value=None, feasible=True):
        """
        Initialize a fake network with specified flow values.
        """
        self.max_flow_value = max_flow_value
        self.sufficient_flow_value = sufficient_flow_value
        self.feasible = feasible

    # max-flow API used by PerformanceCriteria
    def maximum_flow(self, sources, sinks):
        return FakeFlow(self.max_flow_value)

    # sufficient-flow API used by PerformanceCriteria
    def sufficient_flow(self, sources_dict, sinks_dict):
        return (self.feasible, FakeFlow(self.sufficient_flow_value))

    def __add__(self, other):
        # combine values for testing
        return FakeNetwork(
            max_flow_value=(self.max_flow_value or 0) + (other.max_flow_value or 0),
            sufficient_flow_value=self.sufficient_flow_value,
            feasible=self.feasible and other.feasible,
        )


def test_performance_max_flow():
    """
    Test PerformanceCriteria with max-flow evaluation.
    """
    proposed = FakeNetwork(max_flow_value=15)
    current = FakeNetwork(max_flow_value=15)

    crit = PerformanceCriteria(
        sources=[1, 2],
        sinks=[5],
        supplies=None,
        demands=None,
    )

    score = crit._evaluate(proposed, current)

    assert score == 15.0

def test_performance_sufficient_flow():
    """
    Test PerformanceCriteria with sufficient-flow evaluation.
    """
    proposed = FakeNetwork(sufficient_flow_value=42)
    current = FakeNetwork(sufficient_flow_value=42)

    crit = PerformanceCriteria(
        sources=[1, 2],
        sinks=[5, 6],
        supplies=[10, 20],
        demands=[15, 15],
    )

    score = crit._evaluate(proposed, current)

    assert score == 1.0  # feasible → always 1.0 in PerformanceCriteria


def test_correct_solver_called():
    """
    Test that the correct network flow solver is called based on criteria configuration.
    """
    proposed = MagicMock()
    current = MagicMock()

    combined = MagicMock()
    current.__add__.return_value = combined

    # mock return objects
    combined.maximum_flow.return_value = MagicMock(value=100)
    combined.sufficient_flow.return_value = (True, MagicMock())

    # case 1: max-flow
    crit_max = PerformanceCriteria(
        sources=[1], sinks=[2], supplies=None, demands=None
    )
    crit_max._evaluate(proposed, current)

    combined.maximum_flow.assert_called_once()

    # case 2: sufficient-flow
    crit_suf = PerformanceCriteria(
        sources=[1], sinks=[2], supplies=[5], demands=[5]
    )
    crit_suf._evaluate(proposed, current)

    combined.sufficient_flow.assert_called_once()