from typing import Literal, TypeAlias
import math

import numpy as np

from tube_planning.criteria.base import Criteria


COST_NAMES = sorted(["infra", "staff", "vehic", "total"])
CostTypes: TypeAlias = Literal["infra", "staff", "total", "vehic"]


class CostCriteria(Criteria):
    """
    Criterion that evaluates a proposal based on its costs.

    costs: list[str] of cost categories to include (e.g. ["infra", "vehic"])
    budget: float or None
    """

    def __init__(self, costs, budget=0, *, description="", weight=1.0):
        """
        Initialize a CostCriteria.

        Parameters
        ----------
        costs : list[str]
            Cost categories to include (e.g. ["infra", "vehic"]). If "total" is
            present, all other categories are ignored.
        budget : float, optional
            Budget against which total selected costs are compared.
        description : str, optional
            Description of this criterion.
        weight : float, optional
            Weight applied during evaluation; must be positive.

        Raises
        ------
        TypeError
            If `costs` is not a list or contains non-string entries.
        ValueError
            If an entry does not match allowed cost substrings.
        """
        super().__init__(description=description, weight=weight)

        if not isinstance(costs, list):
            raise TypeError("costs must be a list of cost type strings.")

        self.budget = float(budget)

        invalid_costs = [cost for cost in costs if not isinstance(cost, str)]
        if invalid_costs:
            raise TypeError("costs must contain only strings.")

        unknown_costs = [cost for cost in costs if cost not in COST_NAMES]
        if unknown_costs:
            raise ValueError(f"Invalid cost type(s): {unknown_costs}")

        if "total" in costs:
            self.costs = ["total"]
        else:
            self.costs = list(dict.fromkeys(costs))

    def _evaluate(self, proposed, current, costing_information):
        """
        Compute the unweighted cost-based score for the proposal.

        The score is defined as:

            ``score = budget - sum(selected_costs)``

        The selected cost categories are determined by ``self.costs``.
        If ``"total"`` is included, all cost types (infrastructure, staff,
        vehicle) are summed.

        Cost definitions referenced from the system specification:

        - Infrastructure cost = new_stations * new_cost + new_edges * ext_cost
        - Staff cost = new_staff * hire_cost
        - Vehicle cost = new_trains * train_cost

        Parameters
        ----------
        proposed : Network
            The proposed network after modifications.
        current : Network
            The current, unmodified network.
        costing_information : dict[str, float]
            Mapping containing required unit costs:
            - ``"new"``   : cost for constructing a new station
            - ``"ext"``   : cost for adding a new edge
            - ``"hire"``  : cost for hiring one staff member
            - ``"train"`` : cost for one new train

        Returns
        -------
        float
            A numeric score representing ``budget - total_cost``.
            Lower construction cost → higher score.

        Notes
        -----
        Negative values indicate the proposal exceeds the available budget.
        """
        # read costing information
        c_new = float(costing_information["new"])
        c_ext = float(costing_information["ext"])
        c_hire = float(costing_information["hire"])
        c_train = float(costing_information["train"])

        p_mat, c_mat = self._aligned_matrices(
            proposed.adjacency_matrix,
            current.adjacency_matrix,
        )

        current_size = current.adjacency_matrix.shape[0]
        new_edge_count_per_node = np.zeros(p_mat.shape[0], dtype=int)
        num_new_edges = 0

        for i in range(p_mat.shape[0]):
            for j in range(i + 1, p_mat.shape[1]):
                if p_mat[i, j] > 0 and c_mat[i, j] == 0:
                    num_new_edges += 1
                    new_edge_count_per_node[i] += 1
                    new_edge_count_per_node[j] += 1

        new_station_count = sum(
            1
            for node in range(current_size, p_mat.shape[0])
            if new_edge_count_per_node[node] > 0
        )
        max_weight_edge = float(np.max(p_mat)) if p_mat.size else 0.0

        # create new staff and new trains
        # json maybe not contain these fields, default to 0 if not.
        staff_cost = 0.0
        for edge_count in new_edge_count_per_node:
            if edge_count > 0:
                staff_cost += c_hire ** math.sqrt(edge_count)

        # calculate costs
        infra_cost = new_station_count * c_new + num_new_edges * c_ext
        vehic_cost = max_weight_edge * c_train * 24

        # choose costs to include
        if "total" in self.costs:
            total_cost = infra_cost + staff_cost + vehic_cost
        else:
            total_cost = 0
            if "infra" in self.costs:
                total_cost += infra_cost
            if "staff" in self.costs:
                total_cost += staff_cost
            if "vehic" in self.costs:
                total_cost += vehic_cost

        # compute total score
        score = self.budget - total_cost
        return round(score, 2)

    @staticmethod
    def _aligned_matrices(
        proposed_matrix: np.ndarray, current_matrix: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Pad current/proposed matrices to a shared square shape."""
        target_size = max(proposed_matrix.shape[0], current_matrix.shape[0])
        proposed_padded = np.zeros((target_size, target_size), dtype=float)
        current_padded = np.zeros((target_size, target_size), dtype=float)
        proposed_padded[: proposed_matrix.shape[0], : proposed_matrix.shape[1]] = (
            proposed_matrix
        )
        current_padded[: current_matrix.shape[0], : current_matrix.shape[1]] = (
            current_matrix
        )
        return proposed_padded, current_padded

    def to_json_part(self) -> dict[str, bool | float | list[str] | str]:
        """Convert this ``Criteria`` to a dictionary.

        A dictionary can be saved to a `json` file, or used as part of an entry in
        a larger dictionary that is to be saved to a `json` file.

        The dictionary that is returned has keys that correspond to the class
        names of the class's attributes (``str``). The value of these keys is the
        value of the corresponding instance attribute at the time of calling this
        method.

        THIS METHOD IS PROVIDED TO YOU, AND DOES NOT NEED TO BE TESTED IN YOUR TEST SUITE.
        """
        return {**super().to_json_part(), "costs": self.costs, "budget": self.budget}
