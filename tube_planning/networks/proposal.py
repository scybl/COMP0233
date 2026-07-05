from pathlib import Path

import numpy as np

from tube_planning._exceptions import TubePlanningError
from tube_planning.networks.network import Network
from tube_planning.utils import adjacency_from_edges, read_edge_csv

class Proposal(Network):
    """
    A proposed modification to the transport network.

    A ``Proposal`` represents a candidate network extension or modification
    loaded from a CSV file or specified manually. Each proposal has a unique
    name and behaves as a ``Network`` with additional semantics for proposal
    management and identification.

    Notes
    -----
    - Proposal names must be unique.
    - All created proposals are stored in the class-level registry
      ``Proposal._all_proposals``.

    Examples
    --------
    >>> from pathlib import Path
    >>> p = Proposal.from_file(Path("example.csv"), name="test")
    >>> p.name
    'test'
    """

    _all_proposals: list["Proposal"] = []

    @property
    def names_in_use(self) -> tuple[str]:
        """Return a tuple of all ``Proposal`` names currently in use."""
        return tuple(p.name for p in Proposal._all_proposals)

    @classmethod
    def from_file(
        cls,
        csv_file: Path,
        weights_are_travel_times: bool = True,
        name: str | None = None,
    ) -> "Proposal":
        """
        Construct a ``Proposal`` from a CSV edge table.

        The CSV file must contain rows of the form::

            i, j, w

        where ``i`` and ``j`` are node indices and ``w`` is the edge weight (travel
        time or capacity).

        Parameters
        ----------
        csv_file : pathlib.Path
            Path to the CSV file.
        weights_are_travel_times : bool, optional
            If True, weights are interpreted as travel times (in seconds) and
            converted to capacities using ``60 / w``.
            If False, weights are treated as capacities directly.
        name : str, optional
            Unique name for this proposal. Defaults to the filename.

        Returns
        -------
        Proposal
            Constructed proposal object.

        Raises
        ------
        TubePlanningError
            If the file does not exist, is improperly formatted, or contains
            invalid edges (negative indices, duplicates, or non-positive weights).

        Examples
        --------
        >>> from pathlib import Path
        >>> p = Proposal.from_file(Path("example.csv"), name="demo")
        >>> isinstance(p, Proposal)
        True
        """
        if csv_file is None or not isinstance(csv_file, Path):
            raise TubePlanningError("csv_file must be a valid pathlib.Path object.")
        if name is None:
            name = csv_file.stem

        rows = read_edge_csv(csv_file)
        adj_mat = adjacency_from_edges(
            rows,
            weights_are_travel_times=weights_are_travel_times,
            accumulate_duplicates=False,
        )

        return cls(name=name, adj_mat=adj_mat)

    def __init__(
        self,
        name: str,
        *,
        adj_mat: np.ndarray | None = None,
        edge_table: list | None = None,
    ):
        """
        Initialise a proposal network.

        Name must be unique among all existing proposals and must be provided.

        Parameters
        ----------
        name : str
            Unique proposal name.
        adj_mat : np.ndarray, optional
            Adjacency matrix.
        edge_table : list, optional
            Edge list.

        Raises
        ------
        TubePlanningError
            If name is not unique, invalid, or network construction fails.

        Examples
        --------
        >>> import numpy as np
        >>> p = Proposal(name="example", adj_mat=np.zeros((2,2)))
        >>> p.name
        'example'
        """
        # Name must be provided and unique
        if name is None:
            raise TubePlanningError("Proposal name must be unique and non-None.")

        # Convert name to string
        try:
            name = str(name)
        except Exception:
            raise TubePlanningError("Name must be convertible to a string.")

        if name is None or name in self.names_in_use:
            raise TubePlanningError("Proposal name must be unique and non-None.")

        self.name = name

        # Inherit from Network
        super().__init__(adj_mat=adj_mat, edge_table=edge_table)

        # Register this Proposal
        Proposal._all_proposals.append(self)

    def __str__(self):
        """Display information (e.g. via ``print``) for ``Proposal``s.

        THIS METHOD IS PROVIDED TO YOU, AND DOES NOT NEED TO BE TESTED IN YOUR TEST SUITE.
        """
        return super().__str__().replace("Network", f"Proposal ({self.name})")
