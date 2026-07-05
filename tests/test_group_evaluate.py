from unittest.mock import Mock
from tube_planning.criteria.group import CriteriaGroup


def make_mock_criterion(score):
    """create a mock criterion that returns 'score' when evaluated"""
    mock = Mock()
    mock.evaluate.return_value = score
    return mock


def test_evaluate_all_essential_pass():
    """all essential > 0, return True"""
    essential = [make_mock_criterion(2), make_mock_criterion(1)]
    desirable = [make_mock_criterion(3)]

    cg = CriteriaGroup(essential=essential, desirable=desirable)

    passed, total = cg.evaluate(None, None, {})

    assert passed is True
    assert total == 2 + 1 + 3


def test_evaluate_one_essential_fail():
    """if any essential == 0, should return False"""
    essential = [make_mock_criterion(1), make_mock_criterion(0)]
    desirable = [make_mock_criterion(5)]

    cg = CriteriaGroup(essential=essential, desirable=desirable)

    passed, total = cg.evaluate(None, None, {})

    assert passed is False
    assert total == 1 + 0 + 5


def test_evaluate_negative_essential():
    """exist essential < 0, should return False"""
    essential = [make_mock_criterion(-2)]
    desirable = [make_mock_criterion(4)]

    cg = CriteriaGroup(essential=essential, desirable=desirable)

    passed, total = cg.evaluate(None, None, {})

    assert passed is False
    assert total == -2 + 4


def test_evaluate_no_desirable():
    """no existing desirable criteria"""
    essential = [make_mock_criterion(3), make_mock_criterion(2)]
    desirable = []

    cg = CriteriaGroup(essential=essential, desirable=desirable)

    passed, total = cg.evaluate(None, None, {})

    assert passed is True
    assert total == 3 + 2
