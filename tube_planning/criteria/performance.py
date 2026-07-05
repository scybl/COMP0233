from tube_planning.criteria.base import Criteria


class PerformanceCriteria(Criteria):
    """
    A criterion that evaluates network performance using flow-based metrics.

    A ``PerformanceCriteria`` represents either:
    - a **maximum-flow** problem (when no supplies/demands are provided), or
    - a **sufficient-flow** problem (when supplies and demands are given and must be met).

    Scoring is handled by ``_evaluate()``:
    - Maximum-flow: score is the improvement in feasible flow after applying the proposal.
    - Sufficient-flow: score is +1 if all supplies/demands can be satisfied, else −1.

    Instances can be serialized using ``to_json_part()``.

    Attributes
    ----------
    description : str
        Provide some human-readable description of the criterion.
    weight : float
        Positive weight used when computing the final score. Default is 1.0.
    """

    @property
    def is_sufficient_problem(self) -> bool:
        """Whether this criteria examines a sufficient flow problem (True)
        or a maximum flow problem (False).

        THIS PROPERTY IS PROVIDED TO YOU, AND DOES NOT NEED TO BE TESTED IN YOUR TEST SUITE.
        """
        return self.supplies is not None and self.demands is not None

    def __init__(
        self, sources, sinks, supplies=None, demands=None, *, description="", weight=1.0
    ):
        """
        Initialize a performance-based criterion.

        If ``supplies`` and ``demands`` are both omitted, the criterion represents
        a maximum-flow problem. Otherwise, it represents a sufficient-flow problem,
        where supplies and demands must be matched.

        Parameters
        ----------
        sources : Iterable
            Source node IDs. Must not contain duplicates.
        sinks : Iterable
            Sink node IDs. Must not contain duplicates.
        supplies : Iterable[float], optional
            Supplies associated with each source (required for sufficient-flow).
        demands : Iterable[float], optional
            Demands associated with each sink (required for sufficient-flow).
        description : str, optional
            Description of the criterion.
        weight : float, optional
            Weight used when scoring; must be positive.

        Raises
        ------
        ValueError
            If sources/sinks contain duplicates,
            if only one of supplies/demands is provided,
            if non-numeric values appear in supplies/demands,
            or if lengths do not match.
        """
        super().__init__(description=description, weight=weight)

        sources = list(sources)
        sinks = list(sinks)

        # Check for duplicates in sources and sinks
        if len(sources) != len(set(sources)):
            raise ValueError("Duplicate entries detected in sources.")
        if len(sinks) != len(set(sinks)):
            raise ValueError("Duplicate entries detected in sinks.")

        # if neither supplies nor demands are provided,
        # it's a max-flow problem
        if supplies is None and demands is None:
            self.supplies = None
            self.demands = None
            self.sources = sorted(sources)
            self.sinks = sorted(sinks)
            return
        # if only one of supplies or demands is provided, raise error
        elif (supplies is None) != (demands is None):
            raise ValueError(
                "Both supplies and demands must be provided to define a sufficient flow problem."
            )
        # else, both supplies and demands are provided
        else:
            self.supplies = list(supplies)
            self.demands = list(demands)

            # Validate supplies and demands are numeric
            for p in supplies:
                if not isinstance(p, (int, float)):
                    raise ValueError("Supplies must be numeric values.")
            for d in demands:
                if not isinstance(d, (int, float)):
                    raise ValueError("Demands must be numeric values.")

            self.sources = list(sources)
            self.sinks = list(sinks)

            # check lengths is correct
            if len(self.supplies) != len(self.sources):
                raise ValueError("Length of supplies must match length of sources.")
            if len(self.demands) != len(self.sinks):
                raise ValueError("Length of demands must match length of sinks.")

            # sort sources, supplies together
            src_pairs = sorted(zip(self.sources, self.supplies), key=lambda x: x[0])
            self.sources = [s for s, _ in src_pairs]
            self.supplies = [float(p) for _, p in src_pairs]  # convert to float

            # sort sinks, demands together
            sink_pairs = sorted(zip(self.sinks, self.demands), key=lambda x: x[0])
            self.sinks = [s for s, _ in sink_pairs]
            self.demands = [float(d) for _, d in sink_pairs]  # convert to float


    def _evaluate(self, proposed, current, *args, **kwargs):
        """
        Evaluate a performance-based criterion.
        """
        combined = current + proposed

        # -----------------------------
        # Case 1: Maximum Flow Criterion
        # -----------------------------
        if not self.is_sufficient_problem:
            # 1. compute current flow
            f_current = current.maximum_flow(self.sources, self.sinks)
            v_current = f_current.value

            # 2. compute combined flow
            f_combined = combined.maximum_flow(self.sources, self.sinks)
            v_combined = f_combined.value

            # 3. compute score
            return (v_combined - v_current)

        # -----------------------------
        # Case 2: Sufficient Flow Criterion
        # -----------------------------
        else:
            sources_dict = dict(zip(self.sources, self.supplies))
            sinks_dict = dict(zip(self.sinks, self.demands))

            feasible, _flow = combined.sufficient_flow(sources_dict, sinks_dict)
            return 1.0 if feasible else -1.0


    def to_json_part(self) -> dict[str, bool | float | str | list[int] | list[float]]:
        """Convert this ``Criteria`` to a dictionary.

        A dictionary can be saved to a `json` file, or used as part of an entry in
        a larger dictionary that is to be saved to a `json` file.

        The dictionary that is returned has keys that correspond to the class
        names of the class's attributes (``str``). The value of these keys is the
        value of the corresponding instance attribute at the time of calling this
        method.

        THIS METHOD IS PROVIDED TO YOU, AND DOES NOT NEED TO BE TESTED IN YOUR TEST SUITE.
        """
        all_attributes = {
            **super().to_json_part(),
            "sources": self.sources,
            "sinks": self.sinks,
        }
        if self.is_sufficient_problem:
            all_attributes["supplies"] = self.supplies
            all_attributes["demands"] = self.demands
        return all_attributes
