import glob
import json
import sys
from pathlib import Path

from tube_planning._exceptions import TubePlanningError
from tube_planning.criteria.group import CriteriaGroup
from tube_planning.networks.network import Network
from tube_planning.networks.proposal import Proposal
from tube_planning.query import (
    fetch_fixed_costs,
    fetch_proposed_line,
    fetch_tfl_network,
)
from tube_planning.utils import CLIParser, adjacency_from_edges, read_edge_csv, read_fixed_costs


def build_parser():
    """
    Build and configure the argument parser for the ``evaluate-proposals``
    command-line program.

    This parser defines all command-line options required to evaluate and
    rank TFL network extension proposals, including sourcing fixed-cost coefficients,
    selecting route proposals, specifying evaluation criteria, and providing proposal
    input files.

    Parameters
    ----------
    None

    Returns
    -------
    CLIParser
        A configured command-line argument parser for evaluating and ranking proposals.

    Notes
    -----
    The parser supports the following arguments:

    Live costing option
        ``--live-costings`` :
            When specified, the ``costing_information`` argument is interpreted as a
            date in ``YYYY-MM-DD`` format and is used to query the web service for
            fixed-cost coefficients for that day.

    Output option
        ``--output-file`` :
            If provided, ranking results are written to the specified file instead of
            being printed to standard output.

    Route selection option
        ``--routes`` :
            One or more route names to fetch from the web service via
            ``fetch_proposed_line`` and include in the ranking process.

    Positional arguments
        ``costing_information`` :
            Either a path to a ``.fixed-cost`` file, or a date in ``YYYY-MM-DD`` format
            when ``--live-costings`` is specified.

        ``criteria_file`` :
            Path to a ``.cfile`` file defining the evaluation criteria. This argument
            must always be provided.

        ``proposals`` :
            Zero or more shell patterns (e.g., ``*.csv`` or ``proposal_*.csv``).
            Each matched file is read as a proposal using ``Proposal.from_file``.
    """

    parser = CLIParser(
        prog="evaluate-proposals",
        description=(
            "Evaluate and rank TfL network extension proposals according "
            "to criteria and fixed-cost information."
        ),
    )

    parser.add_argument(
        "-l",
        "--live-costings",
        action="store_true",
        help=(
            "Interpret COSTING_INFORMATION as a YYYY-MM-DD date and "
            "query the web service for fixed-cost coefficients on that date."
        ),
    )

    parser.add_argument(
        "-o",
        "--output-file",
        type=str,
        help=(
            "Write ranking output to this file instead of printing "
            "to standard output."
        ),
    )

    parser.add_argument(
        "--format",
        choices=("text", "csv", "json"),
        default="text",
        help=(
            "Output format. 'text' preserves the compact ranking format; "
            "'csv' and 'json' include explicit pass/fail fields."
        ),
    )

    parser.add_argument(
        "--network-file",
        type=str,
        help=(
            "Optional local baseline network CSV. When omitted, the current "
            "TfL network is fetched from the web service."
        ),
    )

    parser.add_argument(
        "-r",
        "--routes",
        nargs="+",
        help=(
            "One or more route names to fetch from the web service via "
            "fetch_proposed_line, to be added to the list of proposals."
        ),
    )

    # positional arguments after '--' when routes are used)
    parser.add_argument(
        "costing_information",
        type=str,
        help=(
            "Path to a .fixed-cost file, or a YYYY-MM-DD date when "
            "--live-costings is specified."
        ),
    )

    parser.add_argument(
        "criteria_file",
        type=str,
        help="Path to a .cfile file defining the evaluation criteria (required).",
    )

    parser.add_argument(
        "proposals",
        nargs="*",
        help=(
            "Zero or more shell patterns (e.g. *.csv, proposal_*.csv). "
            "Each matched file is parsed as a proposal via Proposal.from_file."
        ),
    )

    return parser


"""Helper Functions"""


def _load_costing_information(costing_information: str, live: bool) -> dict[str, float]:
    """
    Load fixed-cost coefficients.

    If `live` is True, interpret `costing_information` as a date (YYYY-MM-DD)
    and fetch costs from the web service. Otherwise treat it as a path to a
    .fixed-cost file (JSON with keys: "new", "ext", "hire", "train").
    """
    if live:
        # costing_information is a date string
        try:
            return fetch_fixed_costs(costing_information)
        except TubePlanningError as exc:
            sys.stderr.write(f"ERROR: {exc}\n")
            sys.exit(2)

    # costing_information is a file path
    path = Path(costing_information)
    if not path.exists():
        sys.stderr.write(f"ERROR: Costing file not found: {path}\n")
        sys.exit(2)

    return read_fixed_costs(path)


def _load_proposals_from_patterns(patterns: list[str]) -> list[Proposal]:
    """
    Use shell patterns to construct Proposal objects from CSV files.
    Patterns that match no files are allowed.
    """
    proposals: list[Proposal] = []

    for pattern in patterns:
        for filename in sorted(glob.glob(pattern)):
            path = Path(filename)
            p = Proposal.from_file(path, name=path.stem)
            proposals.append(p)

    return proposals


def _load_base_network(network_file: str | None) -> Network:
    """
    Load the baseline network from a local CSV file or the live service.
    """
    if network_file is None:
        return fetch_tfl_network()

    path = Path(network_file)
    if not path.exists():
        sys.stderr.write(f"ERROR: Network file not found: {path}\n")
        sys.exit(2)

    rows = read_edge_csv(path)
    adjacency_matrix = adjacency_from_edges(rows, weights_are_travel_times=True)
    return Network(adj_mat=adjacency_matrix)


def _load_proposals_from_routes(route_names: list[str] | None) -> list[Proposal]:
    """
    Fetch proposals from the web service using route names.
    """
    if not route_names:
        return []

    proposals: list[Proposal] = []
    for name in route_names:
        try:
            proposals.append(fetch_proposed_line(name))
        except TubePlanningError as exc:
            sys.stderr.write(f"ERROR: {exc}\n")
            sys.exit(2)
    return proposals


def evaluate_proposals(
    proposals: list[Proposal],
    criteria: CriteriaGroup,
    network,
    costing_info: dict[str, float],
) -> list[dict]:
    """
    Evaluate a collection of proposals against a criteria group.

    Each proposal is scored using the same criteria, baseline network
    and costing information. For every proposal we record its total score
    and whether it failed at least one essential criterion.

    Parameters
    ----------
    proposals : list[Proposal]
        Proposals to be evaluated.
    criteria : CriteriaGroup
        Criteria used to score proposals and determine essential failures.
    network
        Baseline (current) network passed as ``current`` into
        ``criteria.evaluate``.
    costing_info : dict[str, float]
        Fixed-cost coefficients passed as ``costing_information`` into
        ``criteria.evaluate``.

    Returns
    -------
    list[dict]
        One record per proposal. Each record contains ``"proposal"``,
        ``"score"``, and ``"failed_essential"`` keys.
    """
    records = []  # proposal, score, failed_essential
    for p in proposals:
        all_essential_met, total_score = criteria.evaluate(
            proposed=p,
            current=network,
            costing_information=costing_info,
        )
        failed_essential = not all_essential_met
        records.append(
            {
                "proposal": p,
                "score": float(total_score),
                "failed_essential": failed_essential,
            }
        )
    return records


_evaluate_proposals = evaluate_proposals


def ranking_key(record: dict) -> tuple[bool, float, str]:
    """
    Key function for ranking proposals.

    Proposals that pass all essential criteria rank higher. Among proposals
    with the same essential status, higher score ranks higher. Ties are
    broken by proposal name alphabetically.
    """
    return (
        record["failed_essential"],
        -record["score"],
        record["proposal"].name,
    )


def rank_proposals(records: list[dict]) -> list[dict]:
    """Return proposal evaluation records in display order."""
    return sorted(records, key=ranking_key)


def _format_rankings(records: list[dict], output_format: str = "text") -> str:
    """
    Format ranked proposal records.
    """
    if output_format == "json":
        payload = [
            {
                "rank": rank,
                "proposal": rec["proposal"].name,
                "score": round(rec["score"], 2),
                "essential_passed": not rec["failed_essential"],
            }
            for rank, rec in enumerate(records, start=1)
        ]
        return json.dumps(payload, indent=2)

    if output_format == "csv":
        lines = ["rank,proposal,score,essential_passed"]
        for rank, rec in enumerate(records, start=1):
            lines.append(
                f"{rank},{rec['proposal'].name},{rec['score']:.2f},"
                f"{not rec['failed_essential']}"
            )
        return "\n".join(lines)

    lines: list[str] = []
    for i, rec in enumerate(records, start=1):
        name = rec["proposal"].name
        score = rec["score"]
        lines.append(f"{i}, {name}, {score:.2f},")
    return "\n".join(lines)


"""Main Entry Point"""


def main(argv: list[str] | None = None) -> None:
    """
    Entry point for the `evaluate-proposals` command.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # 1) Collect proposals from web-service routes and from file patterns
    proposals: list[Proposal] = []
    proposals.extend(_load_proposals_from_routes(args.routes))
    proposals.extend(_load_proposals_from_patterns(args.proposals))

    if not proposals:
        # Spec: error if no proposals to evaluate
        sys.stderr.write("ERROR: No proposals found to evaluate.\n")
        sys.exit(2)

    # 2) Load costing information
    costing_info = _load_costing_information(
        args.costing_information,
        live=args.live_costings,
    )

    # 3) Load criteria
    path = Path(args.criteria_file)
    if not path.exists():
        sys.stderr.write(f"ERROR: Criteria file not found: {path}\n")
        sys.exit(2)

    criteria = CriteriaGroup.from_file(path)

    # 4) Load current TfL network
    base_network = _load_base_network(args.network_file)

    # 5) Evaluate each proposal
    records = _evaluate_proposals(
        proposals=proposals,
        criteria=criteria,
        network=base_network,
        costing_info=costing_info,
    )

    # 6) Rank proposals
    ranked = rank_proposals(records)

    # 7) Format rankings
    text = _format_rankings(ranked, output_format=args.format)

    # 8) Output: to file or stdout
    if args.output_file:
        out_path = Path(args.output_file)
        out_path.write_text(text, encoding="utf-8")
    else:
        print(text)

    sys.exit(0)


if __name__ == "__main__":
    main()
