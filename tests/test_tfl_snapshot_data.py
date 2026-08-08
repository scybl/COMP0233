import csv
import json
from pathlib import Path

from tube_planning.evaluation import _load_base_network, _load_proposals_from_patterns
from tube_planning.networks.proposal import Proposal
from tube_planning.utils import read_fixed_costs


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "tfl_snapshot"


def test_tfl_snapshot_manifest_matches_cached_files():
    manifest = json.loads((SNAPSHOT / "manifest.json").read_text(encoding="utf-8"))
    contents = manifest["snapshot_contents"]

    assert manifest["source"] == "TfL-derived local planning snapshot"
    assert len(list((SNAPSHOT / "lines").glob("*.csv"))) == contents["lines"] == 21
    assert len(list((SNAPSHOT / "proposals").glob("*.csv"))) == contents["proposals"] == 7

    with (SNAPSHOT / "stations.csv").open(encoding="utf-8", newline="") as file:
        stations = list(csv.DictReader(file))
    assert len(stations) == contents["stations"] == 446

    with (SNAPSHOT / "costs" / "costs_2026.csv").open(encoding="utf-8", newline="") as file:
        costs = list(csv.DictReader(file))
    assert len(costs) == contents["cost_dates"] == 365
    assert costs[0]["construction-date"] == "2026-01-01"
    assert costs[-1]["construction-date"] == "2026-12-31"


def test_tfl_snapshot_demo_inputs_are_loadable():
    Proposal._all_proposals.clear()

    network = _load_base_network(str(SNAPSHOT / "baseline_network.csv"))
    costs = read_fixed_costs(SNAPSHOT / "costs" / "2026-07-01.fixed-cost")
    proposals = _load_proposals_from_patterns([str(SNAPSHOT / "proposals" / "*.csv")])

    assert network.n_nodes == 446
    assert set(costs) == {"new", "ext", "hire", "train"}
    assert len(proposals) == 7
    assert {proposal.name for proposal in proposals} >= {"thameslink", "goodrum"}
