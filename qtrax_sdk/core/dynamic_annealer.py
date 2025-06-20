"""
DynamicAnnealer: Runs a multi-agent, event-driven, quantum-inspired
optimization loop on a changing graph.
"""
import random
import math
from typing import List, Dict, Callable, Any # type: ignore
from qtrax_sdk.models.problem import Problem
from qtrax_sdk.models.solution import Solution
from qtrax_sdk.models.agent import Agent
from qtrax_sdk.core.neighbor import quantum_jump_neighbor
from qtrax_sdk.core.annealer import tsp_total_cost


class DynamicAnnealer:
    def __init__(
        self,
        problem: Problem,
        agents: List[Agent],
        event_callback: Callable[[int], None] = None, # type: ignore
        max_tick: int = 100,
        mini_iter: int = 200,
        start_temp: float = 100.0,
        cooling_rate: float = 0.9,
        min_temp: float = 1e-2,
        quantum_jump_prob: float = 0.05,
        random_seed: int = 42
    ):
        """
        :param problem: Dynamic Problem (graph) instance (NetworkX DiGraph inside).
        :param agents: List of Agent objects to route simultaneously.
        :param event_callback: Optional callback(tick) to inject dynamic events each tick.
        :param max_tick: Maximum number of time steps (ticks) to simulate.
        :param mini_iter: Number of SA‐style iterations per agent per tick.
        :param start_temp: Starting temperature for the mini‐SA pass.
        :param cooling_rate: Temperature multiplication factor each mini‐iteration.
        :param min_temp: Minimum temperature threshold to break out of mini‐SA early.
        :param quantum_jump_prob: Probability of performing a "quantum jump" neighbor instead of 2‐opt.
        :param random_seed: Seed to initialize Python’s random module.
        """
        self.problem = problem
        self.agents = agents
        self.event_callback = event_callback
        self.max_tick = max_tick
        self.mini_iter = mini_iter
        self.start_temp = start_temp
        self.cooling_rate = cooling_rate
        self.min_temp = min_temp
        self.quantum_jump_prob = quantum_jump_prob
        self.random_seed = random_seed

        # Initialize the random seed for reproducibility
        random.seed(random_seed)

        # Track each agent's most recent full mini‐solution
        self.agent_solutions: Dict[str, Solution] = {agent.id: None for agent in agents} # type: ignore

    def _acceptance_probability(self, old_cost: float, new_cost: float, temperature: float) -> float:
        """
        Standard Metropolis acceptance probability.
        Accept if new_cost < old_cost, otherwise accept with exp((old - new)/T).
        """
        if new_cost < old_cost:
            return 1.0
        return math.exp((old_cost - new_cost) / (temperature + 1e-9))

    def _local_sa(self, agent: Agent) -> Solution:
        """
        Run a Mini‐Simulated Annealing pass for a single agent to decide its next step.
        We build a cyclic "mini-route" starting and ending at agent.current_node, then perform 'mini_iter'
        annealing iterations using the quantum_jump_neighbor, and finally return the best Solution found.

        :param agent: The Agent for whom we’re optimizing the next move.
        :return: A Solution object representing the best cycle found. The next node is taken from Solution.routes.
        """
        # 1) Collect all node IDs in the graph
        nodes = [n.id for n in self.problem.nodes]

        # 2) Build an initial random route that starts and ends at agent.current_node
        route = nodes.copy()
        random.shuffle(route)

        # Ensure agent.current_node is at the front of the route
        if route[0] != agent.current_node:
            try:
                idx = route.index(agent.current_node)
                route[0], route[idx] = route[idx], route[0]
            except ValueError:
                # If somehow agent.current_node not in nodes (shouldn’t happen), insert it
                route.insert(0, agent.current_node)

        # Ensure the route ends back at agent.current_node (to form a cycle)
        if route[-1] != agent.current_node:
            route.append(agent.current_node)

        # 3) Wrap in a Solution; cost will be calculated below
        best_solution = Solution(route, None) # type: ignore
        best_cost = tsp_total_cost(best_solution, self.problem)
        temperature = self.start_temp

        # 4) Mini-SA loop
        for _ in range(self.mini_iter):
            neighbor = quantum_jump_neighbor(best_solution, self.problem, jump_prob=self.quantum_jump_prob)
            neighbor_cost = tsp_total_cost(neighbor, self.problem)

            ap = self._acceptance_probability(best_cost, neighbor_cost, temperature)
            if random.random() < ap:
                best_solution = neighbor
                best_cost = neighbor_cost

            # Cool down
            temperature *= self.cooling_rate
            if temperature < self.min_temp:
                break

        return best_solution

    def _detect_collisions(self, proposed_moves: Dict[str, int]) -> List[str]:
        """
        Identify agents that propose to move to the same next_node during this tick.
        Returns a list of agent IDs that are in collision—those agents will be blocked and not moved.

        :param proposed_moves: Mapping of agent_id -> proposed next_node ID.
        :return: List of agent IDs that are colliding.
        """
        reverse_map: Dict[int, List[str]] = {}
        for aid, node in proposed_moves.items():
            reverse_map.setdefault(node, []).append(aid)

        collisions: List[str] = []
        for node, aids in reverse_map.items():
            if len(aids) > 1:
                collisions.extend(aids)
        return collisions

    def run(self) -> None:
        """
        Main simulation loop for dynamic, multi-agent routing:
        1) At each tick, fire event_callback(tick) if provided.
        2) For each active agent:
            a) If at goal, mark completed.
            b) Else run _local_sa and pick the immediate next_node from best_solution.routes.
               Store that in proposed_moves[agent.id].
        3) Detect collisions among proposed_moves; block colliding agents (they do not move this tick).
        4) Move the non-colliding agents one step (agent.step_to(next_node)).
        5) Unblock previously-blocked agents so they can try again next tick.
        6) If all agents are completed, break early; otherwise, proceed to next tick.
        """
        for tick in range(self.max_tick):
            # 1) Apply any dynamic events (e.g., edge closures) for this tick
            if self.event_callback: # type: ignore
                self.event_callback(tick)

            # 2) Each agent proposes a next move
            proposed_moves: Dict[str, int] = {}
            for agent in self.agents:
                # Skip agents not active
                if agent.status != 'active':
                    continue

                # If already at goal, mark completed
                if agent.current_node == agent.goal_node:
                    agent.status = 'completed'
                    continue

                # Run a mini-SA pass to get a full candidate cycle
                best_solution = self._local_sa(agent)

                # From that cycle, find the index of the current_node
                try:
                    current_idx = best_solution.routes.index(agent.current_node)
                except ValueError:
                    # Fallback: if current_node somehow not in routes, pick a random neighbor
                    neighbors = self.problem.get_neighbors(agent.current_node)
                    if not neighbors:
                        agent.status = 'blocked'
                        continue
                    next_node = random.choice(neighbors)
                    proposed_moves[agent.id] = next_node
                    continue

                # The next node is the one immediately after current_idx
                next_idx = (current_idx + 1) % len(best_solution.routes)
                next_node = best_solution.routes[next_idx]
                proposed_moves[agent.id] = next_node

                # Save the full mini-Solution for later inspection
                self.agent_solutions[agent.id] = best_solution

            # 3) Detect and handle collisions
            collisions = self._detect_collisions(proposed_moves)
            for aid in collisions:
                # Remove from proposed_moves so they don't move this tick
                del proposed_moves[aid]
                # Mark them blocked; next tick they can try again
                blocked_agent = next(a for a in self.agents if a.id == aid)
                blocked_agent.status = 'blocked'

            # 4) Commit moves for non-colliding agents
            for agent_id, next_node in proposed_moves.items():
                moving_agent = next(a for a in self.agents if a.id == agent_id)
                moving_agent.step_to(next_node)

            # 5) Unblock previously-blocked agents
            for agent in self.agents:
                if agent.status == 'blocked':
                    agent.status = 'active'

            # 6) Check if all agents have completed
            if all(agent.status == 'completed' for agent in self.agents):
                print(f"All agents completed by tick {tick}.")
                break

        # Final message after loop ends (either all done or max_tick reached)
        print(f"Simulation ended at tick {min(tick, self.max_tick)}.") # type: ignore