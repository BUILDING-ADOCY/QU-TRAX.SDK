"""
Simulated Annealing / Quantum-Inspired Annealer for Q-TRAX.
This class manages the optimization loop, temperature schedule, and acceptance logic.
"""
import math
import random
from typing import Any, Callable # type: ignore
from qtrax_sdk.models.problem import Problem
from qtrax_sdk.models.solution import Solution

class Annealer:
    pass
    def __init__(
        self,
        problem: Problem,
        initial_solution_fn: Callable[[Problem], Solution],
        neighbor_fn: Callable[[Solution, Problem], Solution],
        cost_fn: Callable[[Solution, Problem], float],
        max_iter: int = 10000,
        start_temp: float = 1000.0,
        cooling_rate: float = 0.995,
        min_temp: float = 1e-3,
        random_seed: int = 42,
    ):
        self.problem = problem
        self.initial_solution_fn = initial_solution_fn
        self.neighbor_fn = neighbor_fn
        self.cost_fn = cost_fn
        self.max_iter = max_iter
        self.start_temp = start_temp
        self.cooling_rate = cooling_rate
        self.min_temp = min_temp
        self.random_seed = random_seed
        random.seed(random_seed)

    def acceptance_probability(self, old_cost: float, new_cost: float, temperature: float) -> float:
        if new_cost < old_cost:
            return 1.0
        return math.exp((old_cost - new_cost) / (temperature + 1e-9))

    def run(self) -> Solution:
        current = self.initial_solution_fn(self.problem)
        best = current
        current_cost = self.cost_fn(current, self.problem)
        best_cost = current_cost
        temperature = self.start_temp

        for iteration in range(self.max_iter): # type: ignore
            neighbor = self.neighbor_fn(current, self.problem)
            neighbor_cost = self.cost_fn(neighbor, self.problem)

            ap = self.acceptance_probability(current_cost, neighbor_cost, temperature)
            if random.random() < ap:
                current = neighbor
                current_cost = neighbor_cost
                if current_cost < best_cost:
                    best = current
                    best_cost = current_cost

            temperature *= self.cooling_rate
            if temperature < self.min_temp:
                break

        return best


# --- Utility functions for TSP problems ---

def tsp_total_cost(sol: Solution, problem: Problem) -> float:
    total = 0.0
    route = sol.routes
    for i in range(len(route) - 1):
        try:
            total += problem.distance(route[i], route[i + 1])
        except ValueError:
            # Edge disappeared – treat as prohibitive so SA will reject the neighbour
            total += 1e9
    sol.total_cost = total
    return total


def tsp_initial_solution(problem: Problem) -> Solution:
    """
    Generates a random initial TSP solution (random route, closes the cycle).
    """
    import random
    nodes = [node.id for node in problem.nodes]
    route = nodes.copy()
    random.shuffle(route)
    # Ensure the route is a cycle
    if route[0] != route[-1]:
        route.append(route[0])
    return Solution(route, tsp_total_cost(Solution(route, 0.0), problem))