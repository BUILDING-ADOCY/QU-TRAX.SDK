from typing import List, Dict, Any
from qtrax_sdk.models.agent import Agent
from qtrax_sdk.models.problem import Problem
from qtrax_sdk.models.solution import Solution


def format_solution(
    agents: List[Agent],
    problem: Problem,
    config: Dict[str, Any]
) -> Solution:
    """
    Format agent results into a clean Solution object.
    """
    result_data = { # type: ignore
        agent.id: {
            "route": agent.route,
            "status": agent.status
        } for agent in agents
    }

    # Meta info (optional)
    meta = { # type: ignore
        "num_agents": len(agents),
        "num_nodes": len(problem.nodes),
        "mode": config.get("mode", "dynamic"),
    }

    # Cost placeholder (to be computed later)
    total_cost = 0.0

    return Solution(
        routes=result_data,
        total_cost=total_cost,
        meta=meta # type: ignore
    )
