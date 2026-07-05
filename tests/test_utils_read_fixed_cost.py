import json
import pytest
from pathlib import Path
from tube_planning.utils import read_fixed_costs


def test_file_not_exist():
    """
    Test that FileNotFoundError is raised when the file does not exist.
    """
    with pytest.raises(FileNotFoundError):
        read_fixed_costs(Path("no_such_file.json"))


def test_json_missing_keys(tmp_path):
    """
    Test that KeyError is raised when required keys are missing in the JSON file.
    """
    file = tmp_path / "fixed.json"
    file.write_text(json.dumps({"new": 1, "ext": 2}), encoding="utf-8")  # 缺 hire, train

    with pytest.raises(KeyError):
        read_fixed_costs(file)


def test_json_extra_keys(tmp_path):
    """
    Test that extra keys in the JSON file are ignored.
    """
    file = tmp_path / "fixed.json"
    file.write_text(json.dumps({
        "new": 1, "ext": 2, "hire": 3, "train": 4,
        "extra": 999
    }), encoding="utf-8")

    result = read_fixed_costs(file)

    assert "extra" not in result
    assert set(result.keys()) == {"new", "ext", "hire", "train"}


def test_all_results_are_float(tmp_path):
    """
    Test that all returned values are floats, even if input types vary.
    """
    file = tmp_path / "fixed.json"
    file.write_text(json.dumps({
        "new": "1.1",
        "ext": "2",
        "hire": 3,
        "train": "4.5"
    }), encoding="utf-8")

    result = read_fixed_costs(file)

    assert all(isinstance(v, float) for v in result.values())