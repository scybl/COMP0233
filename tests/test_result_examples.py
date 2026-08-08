import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_module(module: str, *args: str) -> str:
    result = subprocess.run(
        [sys.executable, "-m", module, *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() + "\n"


def test_demo_result_files_match_cli_output():
    csv_output = run_module(
        "tube_planning.evaluation",
        "--network-file",
        "examples/baseline_network.csv",
        "--format",
        "csv",
        "examples/costs.fixed-cost",
        "examples/criteria.cfile",
        "examples/proposals/*.csv",
    )
    json_output = run_module(
        "tube_planning.evaluation",
        "--network-file",
        "examples/baseline_network.csv",
        "--format",
        "json",
        "examples/costs.fixed-cost",
        "examples/criteria.cfile",
        "examples/proposals/*.csv",
    )

    assert csv_output == (ROOT / "examples/results/demo_ranking.csv").read_text(
        encoding="utf-8"
    )
    assert json_output == (ROOT / "examples/results/demo_ranking.json").read_text(
        encoding="utf-8"
    )


def test_ucl_snapshot_result_file_matches_cli_output():
    output = run_module(
        "tube_planning.evaluation",
        "--network-file",
        "data/ucl_snapshot/baseline_network.csv",
        "--format",
        "csv",
        "data/ucl_snapshot/costs/2026-07-01.fixed-cost",
        "data/ucl_snapshot/demo_criteria.cfile",
        "data/ucl_snapshot/proposals/*.csv",
    )

    assert output == (
        ROOT / "data/ucl_snapshot/results/ranking_2026-07-01.csv"
    ).read_text(encoding="utf-8")


def test_ucl_snapshot_route_result_files_match_cli_output():
    baseline_output = run_module(
        "tube_planning.routing",
        "--source",
        "Highgate",
        "--target",
        "Waterloo",
    )
    proposal_output = run_module(
        "tube_planning.routing",
        "--source",
        "Highgate",
        "--target",
        "Waterloo",
        "--extra-edges",
        "data/ucl_snapshot/proposals/goodrum.csv",
    )

    assert baseline_output == (
        ROOT / "data/ucl_snapshot/results/route_highgate_waterloo.txt"
    ).read_text(encoding="utf-8")
    assert proposal_output == (
        ROOT / "data/ucl_snapshot/results/route_highgate_waterloo_goodrum.txt"
    ).read_text(encoding="utf-8")
