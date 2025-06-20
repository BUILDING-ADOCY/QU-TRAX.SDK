"""
Represents a single agent (e.g., delivery bot or drone) in a dynamic environment.
Tracks position, goal, and route history.
"""

from __future__ import annotations
from typing import List, Any


class Agent:
    def __init__(self, agent_id: str, start_node: int, goal_node: int) -> None:
        """
        :param agent_id: Unique identifier for this agent (e.g., "A1", "drone_02").
        :param start_node: The node ID where this agent begins.
        :param goal_node: The node ID where this agent must end.
        """
        # identifiers ------------------------------------------------------
        self.id: str = agent_id          # used by downstream code
        self.agent_id: str = agent_id    # alias (makes mypy/PyCharm happy)

        # positional state --------------------------------------------------
        self.start_node: int = start_node
        self.current_node: int = start_node
        self.goal_node: int = goal_node

        # runtime-tracking --------------------------------------------------
        self.route: List[int] = [start_node]   # history of nodes visited
        self.status: str = "active"            # 'active', 'completed', or 'blocked'

    # ---------------------------------------------------------------------
    # public helpers
    # ---------------------------------------------------------------------
    def step_to(self, next_node: int) -> None:
        """
        Move the agent from its current_node to next_node.
        Append next_node to the route and mark 'completed' if goal reached.
        """
        self.current_node = next_node
        self.route.append(next_node)
        if self.current_node == self.goal_node:
            self.status = "completed"

    def reset(self, new_start: int, new_goal: int) -> None:
        """
        Reinitialize the agent with a new start and goal (for reruns or new scenarios).
        """
        self.start_node = new_start
        self.current_node = new_start
        self.goal_node = new_goal
        self.route = [new_start]
        self.status = "active"

    # ---------------------------------------------------------------------
    # utilities
    # ---------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict (useful for logging or JSON dumps)."""
        return {
            "id": self.id,
            "start": self.start_node,
            "goal": self.goal_node,
            "current": self.current_node,
            "route": self.route,
            "status": self.status,
        }

    def __repr__(self) -> str:
        return (
            f"Agent(id={self.id}, current={self.current_node}, "
            f"goal={self.goal_node}, status={self.status})"
        )