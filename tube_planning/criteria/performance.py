from tube_planning.criteria.base import Criteria


class PerformanceCriteria(Criteria):
    """
    Evaluate a proposal with maximum-flow or sufficient-flow criteria.

    If supplies and demands are omitted, the criterion scores the increase in
    maximum flow after applying the proposal. If supplies and demands are
    provided, the criterion checks whether the combined network can satisfy all
    requested demand.
    """

    @property
    def is_sufficient_problem(self) -> bool:
        """Whether this criterion represents a sufficient-flow problem."""
        return self.supplies is not None and self.demands is not None

    def __init__(
        self, sources, sinks, supplies=None, demands=None, *, description="", weight=1.0
    ):
        super().__init__(description=description, weight=weight)

        sources = list(sources)
        sinks = list(sinks)
        if len(sources) != len(set(sources)):
            raise ValueError("Duplicate entries detected in sources.")
        if len(sinks) != len(set(sinks)):
            raise ValueError("Duplicate entries detected in sinks.")

        if supplies is None and demands is None:
            self.sources = sorted(sources)
            self.sinks = sorted(sinks)
            self.supplies = None
            self.demands = None
            return

        if (supplies is None) != (demands is None):
            raise ValueError(
                "Both supplies and demands must be provided to define a sufficient flow problem."
            )

        supplies = list(supplies)
        demands = list(demands)
        if len(supplies) != len(sources):
            raise ValueError("Length of supplies must match length of sources.")
        if len(demands) != len(sinks):
            raise ValueError("Length of demands must match length of sinks.")
        if any(not isinstance(value, (int, float)) for value in supplies):
            raise ValueError("Supplies must be numeric values.")
        if any(not isinstance(value, (int, float)) for value in demands):
            raise ValueError("Demands must be numeric values.")

        source_pairs = sorted(zip(sources, supplies, strict=True))
        sink_pairs = sorted(zip(sinks, demands, strict=True))
        self.sources = [node for node, _ in source_pairs]
        self.supplies = [float(value) for _, value in source_pairs]
        self.sinks = [node for node, _ in sink_pairs]
        self.demands = [float(value) for _, value in sink_pairs]

    def _evaluate(self, proposed, current, *args, **kwargs):
        combined = current + proposed

        if not self.is_sufficient_problem:
            current_value = current.maximum_flow(self.sources, self.sinks).value
            combined_value = combined.maximum_flow(self.sources, self.sinks).value
            return combined_value - current_value

        source_supplies = dict(zip(self.sources, self.supplies, strict=True))
        sink_demands = dict(zip(self.sinks, self.demands, strict=True))
        feasible, _flow = combined.sufficient_flow(source_supplies, sink_demands)
        return 1.0 if feasible else -1.0

    def to_json_part(self) -> dict[str, bool | float | str | list[int] | list[float]]:
        all_attributes = {
            **super().to_json_part(),
            "sources": self.sources,
            "sinks": self.sinks,
        }
        if self.is_sufficient_problem:
            all_attributes["supplies"] = self.supplies
            all_attributes["demands"] = self.demands
        return all_attributes
