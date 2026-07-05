"""Offline project showcase for Tube Planning."""

from __future__ import annotations

from pathlib import Path

from tube_planning.evaluation import evaluate_proposals, rank_proposals
from tube_planning.networks import Network, Proposal
from tube_planning.utils import adjacency_from_edges, read_edge_csv, read_fixed_costs
from tube_planning.criteria.group import CriteriaGroup


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = PROJECT_ROOT / "examples"


def _edge_count(network: Network) -> int:
    """Return the number of undirected edges in a network."""
    return int((network.adjacency_matrix > 0).sum() // 2)


def _load_example_network() -> Network:
    rows = read_edge_csv(EXAMPLES_DIR / "baseline_network.csv")
    adjacency_matrix = adjacency_from_edges(rows, weights_are_travel_times=True)
    return Network(adj_mat=adjacency_matrix)


def _load_example_proposals() -> list[Proposal]:
    proposals = []
    for path in sorted((EXAMPLES_DIR / "proposals").glob("*.csv")):
        proposals.append(Proposal.from_file(path, name=path.stem))
    return proposals


def build_showcase_rows() -> tuple[Network, list[dict]]:
    """Evaluate bundled example proposals and return ranked records."""
    network = _load_example_network()
    criteria = CriteriaGroup.from_file(EXAMPLES_DIR / "criteria.cfile")
    costs = read_fixed_costs(EXAMPLES_DIR / "costs.fixed-cost")
    proposals = _load_example_proposals()
    records = evaluate_proposals(proposals, criteria, network, costs)
    return network, rank_proposals(records)


def main() -> None:
    """Run the offline showcase and print a compact ranking table."""
    network, ranked_records = build_showcase_rows()

    print("Tube Planning Showcase")
    print("======================")
    print(
        f"Baseline network: {network.n_nodes} stations, "
        f"{_edge_count(network)} connections"
    )
    print("Scenario: rank candidate extensions by cost and flow performance")
    print()
    print(f"{'Rank':<6}{'Proposal':<22}{'Score':>10}  Essential")
    print("-" * 52)

    for rank, record in enumerate(ranked_records, start=1):
        proposal = record["proposal"]
        status = "pass" if not record["failed_essential"] else "fail"
        print(f"{rank:<6}{proposal.name:<22}{record['score']:>10.2f}  {status}")

    print()
    print("Run the same scenario through the CLI:")
    print(
        'evaluate-proposals --network-file examples/baseline_network.csv '
        '--format csv examples/costs.fixed-cost examples/criteria.cfile '
        '"examples/proposals/*.csv"'
    )


if __name__ == "__main__":
    main()
