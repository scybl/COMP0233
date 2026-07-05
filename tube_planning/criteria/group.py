from typing import Iterable
from pathlib import Path
import json

from tube_planning.criteria.base import Criteria
from tube_planning.criteria.cost import CostCriteria
from tube_planning.criteria.performance import PerformanceCriteria


class CriteriaGroup:
    """
    Represents a set of essential and desirable criteria used to evaluate proposals.

    - Essential criteria must all achieve positive scores for a proposal to pass.
    - Desirable criteria contribute to the final score but do not affect feasibility.

    Criteria may be loaded from a JSON criteria file using ``from_file()``, and
    the group can be evaluated against networks via ``evaluate()``. The instance
    can also be serialized back into a criteria file using ``to_criteria_file()``.

    Attributes
    ----------
    essential : list[Criteria]
        Criteria that must all be satisfied for a proposal to be feasible.
    desirable : list[Criteria]
        Criteria that contribute to the final score but are not mandatory.
    """

    @classmethod
    def from_file(cls, fpath: Path) -> "CriteriaGroup":
        """
        Create a ``CriteriaGroup`` instance from a ``.cfile`` JSON specification.

        This method reads a JSON file describing two types of criteria groups:
        * ``essential`` — criteria that must be satisfied.
        * ``desirable`` — criteria that improve the proposal but are not mandatory.

        Each criterion entry in the JSON is interpreted as either a:
        - ``CostCriteria`` (if it contains a ``"costs"`` field), or
        - ``PerformanceCriteria`` (if it contains both ``"sources"`` and ``"sinks"``).

        Validation rules applied:
        - Criterion cannot include both cost fields and flow fields.
        - A performance criterion must contain both ``"sources"`` and ``"sinks"``.
        - ``weight`` must be a strictly positive number.

        Parameters
        ----------
        fpath : Path or str
            Path to a ``.cfile`` JSON file defining essential and desirable criteria.

        Returns
        -------
        CriteriaGroup
            A new instance with populated ``essential`` and ``desirable`` lists
            of criterion objects.

        Raises
        ------
        ValueError
            If a criterion entry mixes cost and flow types, lacks required fields,
            or has a non-positive weight.
        TypeError
            If ``costs`` is not a list when constructing a ``CostCriteria``.
        """

        #  ensure fpath is a Path object
        if not isinstance(fpath, Path):
            fpath = Path(fpath)

        #  read JSON data
        with fpath.open() as json_file:
            data = json.load(json_file)

        essential_list = []
        desirable_list = []

        for key, target_list in [
            ("essential", essential_list),
            ("desirable", desirable_list),
        ]:
            for obj in data.get(key, []):

                # justfye object type
                has_costs = "costs" in obj
                has_sources = "sources" in obj
                has_sinks = "sinks" in obj

                # check for data types
                if has_costs and (has_sources or has_sinks):
                    raise ValueError(
                        "Criterion object cannot contain both 'costs' and 'sources'/'sinks'."
                    )

                # if the data type is neither, raise error
                if (not has_costs) and not (has_sources and has_sinks):
                    raise ValueError(
                        "Criterion must contain 'costs' OR both 'sources' and 'sinks'."
                    )

                # must be positive weight
                weight = obj.get("weight", 1.0)
                if weight <= 0:
                    raise ValueError("weight must be a positive number.")

                #  4. create a CostCriteria
                if has_costs:
                    crit = CostCriteria(
                        costs=obj["costs"],
                        budget=obj.get("budget", 0),
                        description=obj.get("description", ""),
                        weight=weight,
                    )

                # create a PerformanceCriteria
                else:
                    crit = PerformanceCriteria(
                        sources=obj["sources"],
                        sinks=obj["sinks"],
                        supplies=obj.get("supplies"),
                        demands=obj.get("demands"),
                        description=obj.get("description", ""),
                        weight=weight,
                    )

                target_list.append(crit)

        return cls(essential=essential_list, desirable=desirable_list)


    def __init__(
        self,
        *,
        desirable: Iterable[Criteria] = (),
        essential: Iterable[Criteria] = (),
    ):
        """Create a new CriteriaGroup from a list of essential and desirable ``Criteria``.

        Args:
            desirable : Iterable[Criteria]
                Collection of ``Criteria`` objects to be considered desirable.
            essential : Iterable[Criteria]
                Collection of ``Criteria`` objects to be considered essential.

        THIS METHOD IS PROVIDED TO YOU, AND DOES NOT NEED TO BE TESTED IN YOUR TEST SUITE.
        """
        self.desirable = list(desirable)
        self.essential = list(essential)

    def evaluate(self, proposed, current, costing_information):
        """
        Evaluate all essential and desirable criteria for a proposal.

        This method computes the weighted scores of every criterion in the
        ``essential`` and ``desirable`` lists. The evaluation follows these rules:

        - Essential criteria are considered *met* only if **all** essential
          scores are strictly positive.
        - Desirable criteria do not affect feasibility, only the total score.
        - The final total score is the sum of all essential and desirable scores.

        Parameters
        ----------
        proposed : Network
            The proposed network configuration under evaluation.
        current : Network
            The current baseline network.
        costing_information : dict[str, float]
            Mapping of required cost parameters used by cost-based criteria.

        Returns
        -------
        tuple[bool, float]
            A pair ``(all_essential_met, total_score)`` where:

            - ``all_essential_met`` (bool):
                ``True`` if every essential criterion has a score > 0,
                otherwise ``False``.
            - ``total_score`` (float):
                Sum of all essential and desirable criterion scores.

        Notes
        -----
        A negative score for *any* essential criterion indicates the proposal
        fails to meet mandatory requirements, even if its desirable score is strong.
        """
        # compute essential scores
        essential_scores = [
            c.evaluate(proposed, current, costing_information) for c in self.essential
        ]

        # essential criteria are met only if all scores are > 0
        all_essential_met = all(score > 0 for score in essential_scores)

        # compute desirable scores
        desirable_scores = [
            c.evaluate(proposed, current, costing_information) for c in self.desirable
        ]

        # total score = essential + desirable
        total_score = sum(essential_scores) + sum(desirable_scores)

        # required return format
        return all_essential_met, total_score

    def to_criteria_file(self, fpath: Path) -> None:
        """
        Serialize the current instance to a JSON criteria file.

        The resulting file is a JSON object with exactly two keys:
        ``"essential"`` and ``"desirable"``. The value of each key is a list of
        JSON-serializable dictionaries produced by calling
        ``Criteria.to_json_part()`` on each corresponding ``Criteria`` object
        in the instance.

        The file is written to disk at the specified path and will overwrite
        any existing file with the same name.

        Args:
            fpath (Path):
                Destination path where the criteria JSON file will be written.

        Returns:
            None

        Raises:
            OSError:
                If the file cannot be opened or written to.

        Notes:
            THIS METHOD IS PROVIDED TO YOU – do not make functional edits to it.
            YOU WILL BE REQUIRED TO WRITE TESTS FOR THIS METHOD.
        """
        json_dict = {}
        json_dict["essential"] = [c.to_json_part() for c in self.essential]
        json_dict["desirable"] = [c.to_json_part() for c in self.desirable]

        with open(fpath, "w", encoding="utf-8") as json_file:
            json.dump(json_dict, json_file, indent=2, sort_keys=True)
            json_file.write("\n")
