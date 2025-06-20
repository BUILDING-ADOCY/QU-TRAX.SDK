import random
from typing import Optional # type: ignore

from qtrax_sdk.models.solution import Solution
from qtrax_sdk.models.problem import Problem


def tsp_2opt_neighbor(current_solution: Solution, problem: Problem) -> Solution:
    """
    Perform a standard 2-opt swap on a TSP route.

    1) Copy the current route.
    2) Pick two distinct indices i < j in [1, len(route)-2].
    3) Reverse the sub-segment between i and j.
    4) Return a new Solution with cost=None (annealer will recompute).
    """
    route = current_solution.routes.copy()
    n = len(route)

    # If fewer than 4 points (including repeat of start at end), no 2-opt possible
    if n < 4:
        return Solution(route, current_solution.total_cost, current_solution.meta)

    # Choose two indices i < j so that 1 <= i < j <= n-2 (keep endpoints intact)
    i, j = sorted(random.sample(range(1, n - 1), 2))
    # Reverse the sub-segment between i and j
    route[i:j] = reversed(route[i:j])

    return Solution(route, None, current_solution.meta) # type: ignore


def quantum_jump_neighbor(
    current_solution: Solution,
    problem: Problem,
    jump_prob: float = 0.05
) -> Solution:
    """
    Quantum-inspired “jump” neighbor for TSP routes.

    - With probability jump_prob:
        * Perform a large shuffle of a random contiguous sub-segment of the route.
        * (“Quantum tunneling” to escape deep local minima.)
    - Otherwise:
        * Fall back to a standard 2-opt swap.

    Returns a new Solution with cost=None.
    """
    route = current_solution.routes.copy()
    n = len(route)

    # If the route is too small or random() >= jump_prob, do a 2-opt instead
    if n < 4 or random.random() >= jump_prob:
        return tsp_2opt_neighbor(current_solution, problem)

    # Otherwise, perform a “quantum jump”:
    # 1) Pick two points i < j in [1, n-2]
    i, j = sorted(random.sample(range(1, n - 1), 2))

    # 2) Extract the sub-segment and shuffle it completely
    segment = route[i:j]
    random.shuffle(segment)
    route[i:j] = segment

    return Solution(route, None, current_solution.meta) # type: ignore