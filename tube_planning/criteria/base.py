import dataclasses

from tube_planning._exceptions import TubePlanningError
from tube_planning.networks import Network


@dataclasses.dataclass(kw_only=True)
class Criteria:
    """A single criterion that a proposal may include.

    A ``Criteria`` knows how to obtain its score (or metric) once it is
    told the proposed changes, current network, and (optionally) the
    respective costs.

    ``Criteria`` can be converted into ``dicts`` (which in turn can be saved
    to ``json`` files) using their ``to_json_part`` method.

    THIS CLASS IS PROVIDED TO YOU, AND DOES NOT NEED TO BE TESTED IN YOUR TEST SUITE.
    """

    description: str = ""
    weight: float = 1.0

    def __eq__(self, other: "Criteria") -> bool:
        """Equality operation for Criteria.

        Criteria are considered equal if they are the same type,
        and the values of the keys defining the Criteria match.
        """
        return type(self) is type(other) and self.to_json_part() == other.to_json_part()

    def __post_init__(self) -> None:
        """Validate attributes that were provided.

        Validations performed:

        - description: will be cast to string.
        - weight: will be cast to float.
        - weight: must be a positive value.
        """
        self.description = str(self.description)
        self.weight = float(self.weight)

        if self.weight <= 0.0:
            raise TubePlanningError("Criteria.weight must be positive.")

    def _evaluate(
        self,
        proposed: Network,
        current: Network,
        costing_information: dict[str, float] | None = None,
    ) -> float:
        raise NotImplementedError("Must be implemented by subclass.")

    def evaluate(
        self,
        proposed: Network,
        current: Network,
        costing_information: dict[str, float],
    ):
        """Evaluate this ``Criteria``, returning its score.

        Negative scores indicate that criteria were not met.
        """
        return self.weight * self._evaluate(
            proposed, current, costing_information=costing_information
        )

    def to_json_part(self) -> dict[str, bool | float | str]:
        """Convert this ``Criteria`` to a dictionary.

        A dictionary can be saved to a `json` file, or used as part of an entry in
        a larger dictionary that is to be saved to a `json` file.

        The dictionary that is returned has keys that correspond to the class
        names of the class's attributes (``str``). The value of these keys is the
        value of the corresponding instance attribute at the time of calling this
        method.
        """
        return dataclasses.asdict(self)
