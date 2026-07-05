from collections import deque
from typing import Iterable

import numpy as np

from tube_planning._exceptions import TubePlanningError
from tube_planning.flow import Flow


class Network:
    """
    Undirected weighted network represented by an adjacency matrix.

    This class models a network of nodes connected by weighted,
    undirected edges. It supports:

    - construction from adjacency matrices or edge tables,
    - breadth-first search (BFS),
    - reconstruction of paths from BFS traces,
    - maximum flow computation via the Edmonds–Karp algorithm,
    - multi-source and multi-sink flow problems via graph augmentation.

    Attributes
    ----------
    adjacency_matrix : np.ndarray
        Square matrix storing non-negative edge weights.

    Notes
    -----
    - All edges are assumed to be undirected and non-negative.
    - Flow-related algorithms use this adjacency matrix as a capacity matrix.
    - Internally generated networks (e.g. residual graphs) also use this format.

    Examples
    --------
    >>> import numpy as np
    >>> from tube_planning.network import Network
    >>> adj = np.array([[0, 1], [1, 0]])
    >>> net = Network(adj_mat=adj)
    >>> net.n_nodes
    2
    """

    @property
    def n_nodes(self) -> int:
        """
        Number of nodes in the network.

        Returns
        -------
        int
            Total number of nodes.
        """
        return self.adjacency_matrix.shape[0]

    @staticmethod
    def path_from_bfs(path_trace: list[int], dest: int) -> list[int]:
        """
        Reconstruct the path from the root to a destination node
        using a BFS path trace.

        The root node is identified as the unique index ``i`` for which
        ``path_trace[i] == i``. If no such node exists, or more than one
        such node is found, a ``TubePlanningError`` is raised.
        If the destination node is unreachable (i.e., ``path_trace[dest] == -1``)
        or the destination index is invalid, an error is also raised.

        If the root and destination are the same, the method returns a list
        containing only the root.

        Parameters
        ----------
        path_trace : list of int
            The BFS trace returned by ``Network.bfs``. ``path_trace[i]`` gives the
            predecessor of node ``i`` in the BFS tree; ``-1`` indicates an unreachable node.
        dest : int
            Destination node for which the path is to be reconstructed.

        Returns
        -------
        list of int
            The path from the root node to ``dest``, in order.

        Raises
        ------
        TubePlanningError
            If the destination index is invalid, if the destination is unreachable,
            or if a unique root cannot be determined from ``path_trace``.

        Examples
        --------
        >>> trace = [0, 0, 1, 2]
        >>> Network.path_from_bfs(trace, dest=3)
        [0, 1, 2, 3]
        """

        n = len(path_trace)

        # Check dest validity.
        if dest < 0 or dest >= n:
            raise TubePlanningError("Invalid destination node.")

        roots = [i for i in range(n) if path_trace[i] == i]

        # If no roots or multiple roots, error.
        if len(roots) == 0:
            raise TubePlanningError("Root node cannot be determined from path_trace.")
        if len(roots) > 1:
            raise TubePlanningError("Multiple root nodes detected in path_trace.")

        root = roots[0]

        # If destination unreachable, error.
        if path_trace[dest] == -1:
            raise TubePlanningError("Destination cannot be reached from root.")

        # If destination is root, return [root].
        if dest == root:
            return [root]

        path = []
        current = dest

        while True:
            path.append(current)
            parent = path_trace[current]
            if parent == current:  # reached root
                break
            current = parent

        path.reverse()

        return path

    def __add__(self, other: "Network") -> "Network":
        """Combine two ``Network``s into one.

        ``Network``s are combined by element-wise addition of their adjacency matrix.
        This results in:

        - Any edge that is in exactly one of the two ``Networks``s is preserved in the resulting ``Network``.
        - Any edge that appears in both ``Network``s appears as a single edge in the resulting ``Network``,
          however the weight of the single edge is set to the SUM of the weights of the two individual
          edges that came from ``self`` and ``other``.

        If the two ``Networks`` have different numbers of nodes, we expand the adjacency matrix of the
        ``Network`` with fewer nodes to the same size of the ``Network`` with the most nodes, and fill in the
        new rows and columns with zeros. (Effectively, we treat the smaller ``Network`` as having no edges
        between the nodes that only exist in the larger ``Network``).

        Attempting to add a ``Network`` to a non-``Network`` object will throw a ``TypeError``.

        THIS METHOD IS PROVIDED TO YOU, AND DOES NOT NEED TO BE TESTED IN YOUR TEST SUITE.
        """
        if not isinstance(other, Network):
            raise TypeError(
                f"Cannot non-Network instance ({type(other).__name__}) to a Network"
            )

        # Determine which Network has the most nodes, and thus which adjacency matrix needs to be "expanded".
        if other.n_nodes < self.n_nodes:
            larger = self
            smaller = other
        else:
            larger = other
            smaller = self

        # Expand the smaller adjacency matrix to match the size of the larger one.
        # Extra rows and columns that are added, contain only zeros.
        smaller_expanded_matrix = np.zeros(larger.adjacency_matrix.shape)
        smaller_expanded_matrix[: smaller.n_nodes, : smaller.n_nodes] = (
            smaller.adjacency_matrix
        )

        return Network(adj_mat=larger.adjacency_matrix + smaller_expanded_matrix)

    def __eq__(self, other: "Network") -> bool:
        """Compare two ``Networks`` for equality.

        ``Network``s are equal if and only if their adjacency matrices are
        identical.

        - Comparing a non-``Network`` object to a ``Network`` object
        returns ``False``.
        - Any potential subclassing of ``Network`` by ``self`` or ``other`` is
          ignored for the purposes of determining equality.

        THIS METHOD IS PROVIDED TO YOU, AND DOES NOT NEED TO BE TESTED IN YOUR TEST SUITE.
        """
        return hasattr(other, "adjacency_matrix") and np.allclose(
            self.adjacency_matrix, other.adjacency_matrix
        )

    def __init__(
        self, *, adj_mat: np.ndarray | None = None, edge_table: list | None = None
    ) -> None:
        """
        Create a ``Network`` from either an adjacency matrix or an edge table.

        Exactly one of ``adj_mat`` or ``edge_table`` must be provided.

        Parameters
        ----------
        adj_mat : np.ndarray, optional
            Square adjacency matrix with non-negative weights.
        edge_table : list of tuples, optional
            List of triples (i, j, w).

        Raises
        ------
        TubePlanningError
            If inputs are invalid or mutually exclusive rules are violated.

        Examples
        --------
        >>> adj = np.array([[0, 1], [1, 0]])
        >>> Network(adj_mat=adj)

        >>> edges = [(0, 1, 2)]
        >>> Network(edge_table=edges)
        """

        # Exactly one of adj_mat and edge_table needs to be provided.
        if (adj_mat is None) == (edge_table is None):
            raise TubePlanningError(
                "Exactly one of adj_mat or edge_table should be provided."
            )

        # Adjacency matrix provided.
        if adj_mat is not None:
            # Check adjacency matrix format.
            if not isinstance(adj_mat, np.ndarray):
                raise TubePlanningError("Adjacency matrix must be a numpy array.")

            # If not square or not 2D, error.
            if adj_mat.ndim != 2 or adj_mat.shape[0] != adj_mat.shape[1]:
                raise TubePlanningError("Adjacency matrix must be square (2D).")

            # If any weight is negative, error.
            if np.any(adj_mat < 0):
                raise TubePlanningError(
                    "Adjacency matrix cannot contain negative weights."
                )

            self.adjacency_matrix = adj_mat.astype(float, copy=True)
            return

        # Edge table provided.
        if edge_table is not None:
            # Check edge_table format.
            if not isinstance(edge_table, list):
                raise TubePlanningError("edge_table must be a list of (i, j, w).")

            n_nodes = 0
            edges = set()
            edge_pairs = set()

            for item in edge_table:
                # Each entry must be a triple (i, j, w).
                if not (isinstance(item, (tuple, list)) and len(item) == 3):
                    raise TubePlanningError(
                        "Each edge_table entry must be a triple (i, j, w)."
                    )

                i, j, w = item
                if not isinstance(i, int) or not isinstance(j, int):
                    raise TubePlanningError("Edge node indices must be integers.")
                if i < 0 or j < 0:
                    raise TubePlanningError("Edge node indices must be non-negative.")
                if i == j:
                    raise TubePlanningError("Self-loop edges are not supported.")

                n_nodes = max(n_nodes, i + 1, j + 1)

                # If any weight is negative, error.
                if w < 0:
                    raise TubePlanningError("Edge weights cannot be negative.")

                # If weight is zero, ignore this edge.
                if w == 0:
                    continue

                # Check for duplicate or contradictory edges.
                if (i, j) in edge_pairs or (j, i) in edge_pairs:
                    raise TubePlanningError(
                        "Duplicate or contradictory edges detected."
                    )

                edges.add((i, j, w))
                edge_pairs.add((i, j))

            if n_nodes == 0:
                raise TubePlanningError("edge_table must contain at least one edge.")

            adj_mat = np.zeros((n_nodes, n_nodes), dtype=float)

            for i, j, w in edges:
                adj_mat[i, j] = w
                adj_mat[j, i] = w

            self.adjacency_matrix = adj_mat

            return

    def __repr__(self):
        """Display information (e.g. via ``print``) for ``Network``s.

        THIS METHOD IS PROVIDED TO YOU, AND DOES NOT NEED TO BE TESTED IN YOUR TEST SUITE.
        """
        return self.__str__()

    def __str__(self) -> str:
        """Display information (e.g. via ``print``) for ``Network``s.

        THIS METHOD IS PROVIDED TO YOU, AND DOES NOT NEED TO BE TESTED IN YOUR TEST SUITE.
        """
        # Number of edges = number of non-zero entries in adjacency matrix / 2 (for symmetry).
        # Self-connecting edges are not allowed so we can't ever get 0.5 of an edge.
        n_edges = np.floor(np.sum(self.adjacency_matrix > 0) / 2.0).astype(int)
        return f"Network of {self.n_nodes} nodes and {n_edges} edges"

    def bfs(self, root: int) -> list[int]:
        """
        Perform a breadth-first search (BFS) starting from the specified root node.

        The BFS explores all nodes reachable from the root using the edges defined by
        the adjacency matrix. The method returns a *path trace*, where entry ``i`` stores
        the predecessor of node ``i`` in the BFS tree. The root node is defined by the
        convention ``path_trace[root] = root``. Any node which cannot be reached from
        the root will have a trace value of ``-1``.

        Parameters
        ----------
        root : int
            Index of the root node from which the BFS begins. Must be a valid node
            index; otherwise a ``TubePlanningError`` is raised.

        Returns
        -------
        list of int
            A list representing the BFS path trace. ``path_trace[i]`` gives the parent
            of node ``i``; unreachable nodes have value ``-1``.

        Raises
        ------
        TubePlanningError
            If root index is invalid.

        Examples
        --------
        Given the network 0-1-2-3, performing BFS from root=0:
        >>> adj = np.array([[0, 1, 0, 0],
        ...                 [1, 0, 1, 0],
        ...                 [0, 1, 0, 1],
        ...                 [0, 0, 1, 0]])
        >>> net = Network(adj_mat=adj)
        >>> trace = net.bfs(root=0)
        >>> trace
        [0, 0, 1, 2]
        """

        adj_mat = self.adjacency_matrix
        n = self.n_nodes

        # Check root validity.
        if root < 0 or root >= n:
            raise TubePlanningError("Invalid root node index.")

        # Define queue for BFS and path trace list.
        node_queue = deque([root])
        path_trace = [-1] * n
        path_trace[root] = root

        while node_queue:
            i = node_queue.popleft()
            for j in range(n):
                # If edge exists and node j not yet visited.
                if adj_mat[i, j] > 0 and path_trace[j] == -1:
                    path_trace[j] = i
                    node_queue.append(j)

        return path_trace

    def capacity_constraint(self, flow: Flow) -> bool:
        """
        Check whether a flow respects the capacity constraints of the network.

        Parameters
        ----------
        flow : Flow
            Flow object to be validated.

        Returns
        -------
        bool
            True if flow does not exceed any edge capacity, False otherwise.
        """
        flow_matrix = flow.flow_matrix
        adj_mat = self.adjacency_matrix

        return flow_matrix.shape == adj_mat.shape and bool(np.all(flow_matrix <= adj_mat))

    def edmonds_karp(self, source: int, sink: int, maxiter: int = 1000) -> Flow:
        """
        Compute maximum flow using the Edmonds-Karp algorithm.

        The algorithm repeatedly constructs the residual graph and uses BFS to
        find the shortest (in terms of number of edges) augmenting path from
        the source to the sink. If such a path exists, we augment the flow along
        this path by the maximum possible amount (the bottleneck capacity). The
        residual graph is updated and the process repeats until no augmenting
        path remains or the maximum number of iterations is reached.

        Parameters
        ----------
        source : int
            Index of the source node.
        sink : int
            Index of the sink node.
        maxiter : int
            Max number of iterations to perform.

        Returns
        -------
        Flow
            Maximum flow.

        Raises
        ------
        TubePlanningError
            If invalid node indices are supplied, or if the algorithm fails
            to terminate within the specified iteration limit.
        """
        n_nodes = self.n_nodes
        capacity_matrix = self.adjacency_matrix

        if source == sink:
            raise TubePlanningError("Source and sink must be different nodes.")
        if maxiter < 0:
            raise TubePlanningError("maxiter must be non-negative.")
        if not (0 <= source < n_nodes) or not (0 <= sink < n_nodes):
            raise TubePlanningError("Invalid source or sink index.")

        flow = Flow.zero_flow(n_nodes, (source,), (sink,))
        terminated = False

        for _ in range(maxiter):
            residual_capacity = capacity_matrix - flow.flow_matrix
            residual_capacity[residual_capacity < 0] = 0.0
            residual_graph = Network(adj_mat=residual_capacity)

            path_trace = residual_graph.bfs(source)
            if path_trace[sink] < 0:
                terminated = True
                break

            path = Network.path_from_bfs(path_trace, sink)
            path_edges = zip(path[:-1], path[1:], strict=True)
            bottleneck = min(residual_capacity[i, j] for i, j in path_edges)
            flow.send_flow_along(path, bottleneck)

        if not terminated:
            raise TubePlanningError("Algorithm did not terminate within maxiter.")

        return flow

    def maximum_flow(
        self, sources: Iterable[int], sinks: Iterable[int], maxiter: int | None = None
    ) -> Flow:
        """
        Solve the maximum flow problem with multiple sources and sinks.

        This method introduces a super-source and super-sink, connects them
        to the specified nodes, and computes the maximum feasible flow.

        Parameters
        ----------
        sources : Iterable[int]
            Source node indices.
        sinks : Iterable[int]
            Sink node indices.
        maxiter : int, optional
            Maximum number of iterations.

        Returns
        -------
        Flow
            The maximum flow satisfying all constraints.

        Raises
        ------
        TubePlanningError
            If input is invalid or algorithm fails to terminate.
        """
        if isinstance(sources, int) or isinstance(sinks, int):
            raise TubePlanningError("sources and sinks must be iterables of ints.")

        source_nodes = list(sources)
        sink_nodes = list(sinks)
        self._validate_terminal_nodes(source_nodes, sink_nodes)

        n_nodes = self.n_nodes
        max_possible_flow = float(self.adjacency_matrix.sum()) + 1.0
        source_edges = {s: max_possible_flow for s in source_nodes}
        sink_edges = {t: max_possible_flow for t in sink_nodes}

        flow_ext = self._compute_augmented_flow(source_edges, sink_edges, maxiter)

        final_flow_mat = flow_ext.flow_matrix[:n_nodes, :n_nodes]
        final_flow = Flow(final_flow_mat, sources=source_nodes, sinks=sink_nodes)

        return final_flow

    def sufficient_flow(
        self, sources: dict, sinks: dict, maxiter: int | None = None
    ) -> tuple[bool, Flow]:
        """
        Solve the flow problem with multiple sources and sinks,
        checking if all demands can be satisfied.

        Parameters
        ----------
        sources : dict
            Mapping of source nodes to supply values.
        sinks : dict
            Mapping of sink nodes to demand values.
        maxiter : int, optional
            Maximum number of iterations.

        Returns
        -------
        (bool, Flow)
            A pair where the first element indicates feasibility and the
            second gives the computed flow.

        Raises
        ------
        TubePlanningError
            If inputs are invalid.
        """
        if not isinstance(sources, dict) or not isinstance(sinks, dict):
            raise TubePlanningError("sources and sinks must be dicts.")

        n_nodes = self.n_nodes
        super_sink = n_nodes + 1
        source_edges = self._validate_terminal_capacities(sources, label="source")
        sink_edges = self._validate_terminal_capacities(sinks, label="sink")
        self._validate_terminal_nodes(source_edges.keys(), sink_edges.keys())

        flow_ext = self._compute_augmented_flow(source_edges, sink_edges, maxiter)

        achieved = sum(flow_ext.flow_matrix[t, super_sink] for t in sink_edges)
        total_demand = sum(sink_edges.values())
        feasible = np.isclose(achieved, total_demand)

        final_flow_mat = flow_ext.flow_matrix[:n_nodes, :n_nodes]
        final_flow = Flow(
            final_flow_mat,
            sources=list(source_edges.keys()),
            sinks=list(sink_edges.keys()),
        )

        return bool(feasible), final_flow

    def _validate_terminal_nodes(
        self, sources: Iterable[int], sinks: Iterable[int]
    ) -> None:
        """Validate source and sink collections used by flow problems."""
        source_nodes = list(sources)
        sink_nodes = list(sinks)
        all_nodes = source_nodes + sink_nodes

        if not source_nodes or not sink_nodes:
            raise TubePlanningError("At least one source and one sink are required.")
        if any(not isinstance(node, int) for node in all_nodes):
            raise TubePlanningError("Source and sink nodes must be integers.")
        if len(set(source_nodes)) != len(source_nodes):
            raise TubePlanningError("Source nodes must be unique.")
        if len(set(sink_nodes)) != len(sink_nodes):
            raise TubePlanningError("Sink nodes must be unique.")
        if set(source_nodes) & set(sink_nodes):
            raise TubePlanningError("A node cannot be both a source and a sink.")
        if any(node < 0 or node >= self.n_nodes for node in all_nodes):
            raise TubePlanningError("Source or sink node index is out of bounds.")

    def _validate_terminal_capacities(
        self, terminal_capacities: dict, *, label: str
    ) -> dict[int, float]:
        """Validate terminal capacity mappings for sufficient-flow problems."""
        validated: dict[int, float] = {}
        for node, capacity in terminal_capacities.items():
            if not isinstance(node, int):
                raise TubePlanningError(
                    f"{label.title()} node indices must be integers."
                )
            if node < 0 or node >= self.n_nodes:
                raise TubePlanningError(f"Invalid {label} node index.")
            try:
                value = float(capacity)
            except (TypeError, ValueError) as exc:
                raise TubePlanningError(
                    f"{label.title()} capacity must be numeric."
                ) from exc
            if value < 0:
                raise TubePlanningError(f"{label.title()} capacity cannot be negative.")
            validated[node] = value
        return validated

    def _compute_augmented_flow(self, source_edges: dict, sink_edges: dict, maxiter):
        """
        Compute flow on an augmented network using Edmonds-Karp.

        This method constructs an augmented network by adding a super-source
        and a super-sink to the original graph. Edges are inserted from the
        super-source to each source node with the specified capacities, and
        from each sink node to the super-sink with the specified capacities.
        The Edmonds–Karp algorithm is then executed on the resulting network.

        Parameters
        ----------
        source_edges : dict
            Mapping of source node indices to capacities from the super-source
            (i.e. edges of the form super_source → node).
        sink_edges : dict
            Mapping of sink node indices to capacities to the super-sink
            (i.e. edges of the form node → super_sink).
        maxiter : int or None
            Maximum number of iterations for the Edmonds–Karp algorithm.
            If ``None``, the default iteration limit is used.

        Returns
        -------
        Flow
            The flow computed on the augmented network, including the
            super-source and super-sink nodes.

        Raises
        ------
        TubePlanningError
            If the underlying Edmonds-Karp algorithm fails to terminate.

        Notes
        -----
        - The returned ``Flow`` object contains a flow matrix of shape
          ``(n + 2, n + 2)``, where the extra two nodes correspond to the
          super-source and super-sink.
        - Downstream methods typically discard these extra nodes when
          constructing the final flow on the original network.
        """
        n = self.n_nodes
        adj = self.adjacency_matrix
        super_source = n
        super_sink = n + 1

        new_adj = np.zeros((n + 2, n + 2), dtype=float)
        new_adj[:n, :n] = adj

        for source, capacity in source_edges.items():
            new_adj[super_source, source] = capacity
        for sink, capacity in sink_edges.items():
            new_adj[sink, super_sink] = capacity

        augmented_network = Network(adj_mat=new_adj)
        if maxiter is None:
            return augmented_network.edmonds_karp(super_source, super_sink)

        return augmented_network.edmonds_karp(super_source, super_sink, maxiter)
