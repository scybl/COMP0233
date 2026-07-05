from typing import Iterable
import numpy as np
from tube_planning._exceptions import TubePlanningError


class Flow:
    """
    Representation of a flow on a directed network.

    This class models a flow on a network using a skew-symmetric
    adjacency matrix representation, where ``flow_matrix[u, v]``
    denotes the flow sent from node ``u`` to node ``v`` and
    ``flow_matrix[v, u] = -flow_matrix[u, v]`` holds.

    The class supports:
    - querying incoming, outgoing, and net flow at each node,
    - specifying source and sink nodes,
    - enforcing flow conservation at all intermediate nodes,
    - incrementally augmenting flow along valid source-to-sink paths.

    Attributes
    ----------
    flow_matrix : np.ndarray
        Square matrix of shape ``(n, n)`` representing the flow values.
    sources : list[int]
        Indices of source nodes.
    sinks : list[int]
        Indices of sink nodes.

    Notes
    -----
    - The class enforces flow conservation at all intermediate nodes
      on initialization.
    - Skew-symmetry is automatically preserved when using `send_flow_along`;
      external modification of `flow_matrix` may violate this invariant.
    - All attributes are read-only except for the internal flow matrix,
      which should only be modified through ``send_flow_along``.

    Examples
    --------
    Construct a simple flow on two nodes:

    >>> import numpy as np
    >>> from tube_planning.flow import Flow
    >>> f = Flow(np.array([[0, 3], [-3, 0]]), sources=(0,), sinks=(1,))
    >>> f.value
    3.0

    Create a zero flow and send flow along a path:

    >>> f = Flow.zero_flow(3, sources=(0,), sinks=(2,))
    >>> f.send_flow_along([0, 1, 2], 4)
    >>> f.flow_matrix
    array([[ 0.,  4.,  0.],
           [-4.,  0.,  4.],
           [ 0., -4.,  0.]])
    """

    @property
    def flow_in(self):
        """
        Compute the total incoming flow for each node.

        Incoming flow is defined as the sum of absolute values of all
        negative entries in each row of the flow matrix.

        Returns
        -------
        np.ndarray
            A 1D array where element ``i`` is the total incoming flow at node ``i``.
        """
        # Keep only negative values and set others to zero
        neg = np.minimum(self.flow_matrix, 0.0)

        # Sum along rows and take absolute value to get incoming flow
        result = np.absolute(neg).sum(axis=1)

        return result

    @property
    def flow_out(self):
        """
        Compute the total outgoing flow for each node.

        Outgoing flow is defined as the sum of all positive entries
        in each row of the flow matrix.

        Returns
        -------
        np.ndarray
            A 1D array where element ``i`` is the total outgoing flow from node ``i``.
        """
        # Keep only positive values and set others to zero
        pos = np.maximum(self.flow_matrix, 0.0)

        # Sum along rows to get outgoing flow
        result = pos.sum(axis=1)

        return result

    @property
    def net_flow(self):
        """
        Compute the net flow for each node.

        Net flow is defined as ``flow_in - flow_out``.

        Returns
        -------
        np.ndarray
            A 1D array giving the net flow at each node.
            Negative values indicate net outflow;
            positive values indicate net inflow.
        """
        return self.flow_in - self.flow_out

    @property
    def value(self):
        """
        Compute the total flow value from the source nodes.

        The flow value is defined as the total net outflow
        from all source nodes.

        Returns
        -------
        float
            Total flow value. Returns ``0.0`` if no source nodes are defined.
        """
        # If there are no sources, the flow value is 0
        if not self.sources:
            return 0.0

        result = float(self.flow_matrix[self.sources, :].sum())

        return result

    # Source and sink should not be modified after initialization
    @property
    def sources(self):
        """
        Get the list of source nodes.

        Returns
        -------
        list[int]
            A sorted list of unique source node indices.
        """
        return list(self._sources)

    @property
    def sinks(self):
        """
        Get the list of sink nodes.

        Returns
        -------
        list[int]
            A sorted list of unique sink node indices.
        """
        return list(self._sinks)

    @classmethod
    def zero_flow(
        cls, n_nodes: int, sources: Iterable[int] = (), sinks: Iterable[int] = ()
    ):
        """Creates the zero flow of a given size, with the corresponding sources and sinks.

        The zero flow can be created by calling this classmethod.

        Create the zero flow for a network of 6 nodes, with no sources or sinks:

        >>> from tube_planning.flow import Flow
        >>> zero_flow = Flow.zero_flow(6)

        Create the zero flow for a network of 6 nodes, flagging nodes 0 and 4 as the sources
        and node 3 as the sink:

        >>> from tube_planning.flow import Flow
        >>> zero_flow = Flow.zero_flow(6, sources=(0, 4), sinks=(3,))

        Args:
            n_nodes : int
                The size of the flow matrix, or equivalently the number of nodes in the
                network that this `Flow` will be used in conjunction with.
            sources : Iterable[int], default = ()
                Indexes of source nodes.
            sinks : Iterable[int], default = ()
                Indexes of sink nodes.

        Returns:
            f : Flow
                Zero flow of the requested size, with appropriate sources and sinks.

        THIS METHOD IS PROVIDED TO YOU, AND DOES NOT NEED TO BE TESTED IN YOUR TEST SUITE.
        """
        return cls(np.zeros((n_nodes, n_nodes), dtype=float), sources, sinks)

    def __init__(
        self,
        flow_matrix: np.ndarray,
        sources: Iterable[int] | None = None,
        sinks: Iterable[int] | None = None,
    ):
        """
        Initialize a Flow object.

        Parameters
        ----------
        flow_matrix : np.ndarray
            A square ``n × n`` matrix representing the flow between nodes.
            ``flow_matrix[u, v]`` denotes the flow from node ``u`` to node ``v``.
            Positive entries represent outgoing flow; negative entries represent
            incoming flow.

            The matrix is interpreted as representing a skew-symmetric flow
            (i.e. ``f(u, v) = -f(v, u)``). Skew-symmetry is not explicitly enforced
            and must be respected by the caller.

        sources : Iterable[int], optional
            Indices of source nodes. These nodes may have positive net outflow
            (i.e. ``flow_out > flow_in``). Defaults to empty if ``None``.

        sinks : Iterable[int], optional
            Indices of sink nodes. These nodes may have positive net inflow
            (i.e. ``flow_in > flow_out``). Defaults to empty if ``None``.

        Notes
        -----
        - Sources and sinks are stored internally as sorted, unique lists
          and are exposed as read-only properties.
        - All intermediate nodes (non-source and non-sink nodes) must
          satisfy flow conservation:
          ``flow_in(i) == flow_out(i)``.

        Raises
        ------
        TubePlanningError
            If ``flow_matrix`` is not convertible to float,
            if the matrix is not square,
            if source/sink indices are out of bounds,
            or if flow conservation is violated at intermediate nodes.
        """
        # Check that flow_matrix can be converted to a numpy array of floats
        try:
            flow_matrix = np.array(flow_matrix, dtype=float)
        except Exception:
            raise TubePlanningError(
                "Flow matrix must be convertible to a numpy array of floats."
            )

        # Check that flow_matrix is square
        if flow_matrix.ndim != 2 or flow_matrix.shape[0] != flow_matrix.shape[1]:
            raise TubePlanningError("flow_matrix must be a square 2D array.")

        self.flow_matrix = flow_matrix
        n = flow_matrix.shape[0]

        # Handle None defaults
        if sources is None:
            sources = ()
        if sinks is None:
            sinks = ()

        # Store sorted & unique
        self._sources = sorted(set(sources))
        self._sinks = sorted(set(sinks))

        # Bounds check
        for node in self.sources + self.sinks:
            if node < 0 or node >= n:
                raise TubePlanningError(
                    f"Source/sink node {node} is out of bounds for flow matrix of size {n}."
                )

        # Check that flow conserves at intermediate nodes
        if not self._conserves_flow():
            raise TubePlanningError(
                "Flow does not conserve flow at all intermediate nodes."
            )

    def _conserves_flow(self) -> bool:
        """
        Check that the matrix represents a valid conserved flow.

        A valid flow matrix is skew-symmetric with a zero diagonal. Every
        non-source and non-sink node must also conserve flow, i.e.
        ``flow_in(i) == flow_out(i)``.

        Returns
        -------
        bool
            True if the flow representation is valid and all intermediate
            nodes conserve flow, False otherwise.
        """
        n = self.flow_matrix.shape[0]
        if self.flow_matrix.ndim != 2 or self.flow_matrix.shape[1] != n:
            return False
        if not np.allclose(np.diag(self.flow_matrix), 0.0):
            return False
        if not np.allclose(self.flow_matrix, -self.flow_matrix.T):
            return False

        for node in range(n):
            if node in self.sources or node in self.sinks:
                continue
            if not np.isclose(self.net_flow[node], 0.0):
                return False
        return True

    def send_flow_along(self, path: Iterable[int], amount: float) -> None:
        """
        Send flow along a path.

        This method updates the flow matrix according to skew-symmetry:
        ``f(u, v) += amount`` and ``f(v, u) -= amount``.

        Parameters
        ----------
        path : Iterable[int]
            Sequence of node indices defining a valid path.
        amount : float
            Non-negative amount of flow to send along the path.

        Examples
        --------
        >>> import numpy as np
        >>> from tube_planning.flow import Flow
        >>> f = Flow.zero_flow(3, sources=(0,), sinks=(2,))
        >>> f.send_flow_along([0, 1, 2], 5.0)
        >>> f.flow_matrix
        array([[ 0.,  5.,  0.],
            [-5.,  0.,  5.],
            [ 0., -5.,  0.]])

        Raises
        ------
        TubePlanningError
            If the amount is negative,
            if any node index is out of bounds,
            if the path does not start at a source or end at a sink,
            or if the path contains invalid adjacent duplicates.
        """
        try:
            path = list(path)
        except TypeError as exc:
            raise TypeError("path must be an iterable of node indices.") from exc

        if len(path) < 2:
            raise TubePlanningError("Path must contain at least two nodes.")

        # Check that amount is non-negative
        if amount < 0:
            raise TubePlanningError("Flow amount must be non-negative.")

        # Check that all nodes in path are valid
        n = self.flow_matrix.shape[0]
        for node in path:
            if node < 0 or node >= n:
                raise TubePlanningError(f"Node {node} out of bounds.")

        start, end = path[0], path[-1]

        # If start != end, must begin at source and end at sink
        if start != end:
            if start not in self.sources:
                raise TubePlanningError("Path must start at a source.")
            if end not in self.sinks:
                raise TubePlanningError("Path must end at a sink.")

        # Apply skew-symmetric updates
        for u, v in zip(path, path[1:]):
            if u == v:
                raise TubePlanningError("Path contains duplicate adjacent nodes.")
            self.flow_matrix[u, v] += amount
            self.flow_matrix[v, u] -= amount
