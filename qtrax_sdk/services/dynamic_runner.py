"""
Service to orchestrate dynamic, multi-agent solves using DynamicAnnealer.
"""

from __future__ import annotations

import json
import yaml
from pathlib import Path
from typing import List, Dict, Any

from qtrax_sdk.models.agent import Agent
from qtrax_sdk.models.problem import Problem
from qtrax_sdk.models.solution import Solution
from qtrax_sdk.core.dynamic_annealer import DynamicAnnealer
from qtrax_sdk.utils.io_helpers import (
    load_problem_yaml,
    load_problem_json,
    save_solution_json,
)
from qtrax_sdk.utils.event_bus import EventBus


# ──────────────────────────────────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────────────────────────────────
def load_agents_from_config(raw: Dict[str, Any]) -> List[Agent]:
    """Translate YAML / JSON rows → Agent objects."""
    agents: List[Agent] = []
    for row in raw.get("agents", []):
        agents.append(
            Agent(
                agent_id=row["id"],
                start_node=row["start"],
                goal_node=row["goal"],
            )
        )
    return agents


def get_node_id(node):  # type: ignore
    if isinstance(node, dict):
        return node.get("id") or node.get("node_id") # type: ignore
    return getattr(node, "id", getattr(node, "node_id", None))  # type: ignore


def try_int(val):  # type: ignore
    try:
        return int(val) # type: ignore
    except Exception:
        return val # type: ignore


# ──────────────────────────────────────────────────────────────────────────
# main entry
# ──────────────────────────────────────────────────────────────────────────
def dynamic_solve(
    config_path: str | Path,
    output_path: str | Path,
    *,
    use_yaml: bool = True,
    max_tick: int = 50,
) -> Dict[str, Any]:
    """Run DynamicAnnealer on a file-based problem definition."""
    config_path, output_path = Path(config_path), Path(output_path)

    # 1. load problem graph -------------------------------------------------
    problem: Problem = (
        load_problem_yaml(config_path) if use_yaml else load_problem_json(config_path) # type: ignore
    )

    # 2. load raw config + agents ------------------------------------------
    raw_cfg: Dict[str, Any] = (
        yaml.safe_load(config_path.read_text())
        if use_yaml
        else json.loads(config_path.read_text())
    )
    agents: List[Agent] = load_agents_from_config(raw_cfg)

    # debug dump -----------------------------------------------------------
    if __debug__ and agents:
        print("Agent fields:", list(vars(agents[0]).keys()))

    # 3. sanity-check IDs ---------------------------------------------------
    node_ids = {try_int(get_node_id(n)) for n in problem.nodes} # type: ignore
    for ag in agents:
        start = try_int(ag.start_node)
        goal = try_int(ag.goal_node)
        if start not in node_ids or goal not in node_ids:
            raise ValueError(
                f"Agent {ag.id} refers to unknown node (start={start}, goal={goal})"
            )

    # 4. optional event callback -------------------------------------------
    def on_tick(tick: int) -> None:
        if tick == 10:
            print("Event: blocking edge 1→2 at tick 10")
            try:
                problem.remove_edge(1, 2)
                EventBus.publish("edge_blocked", {"source": 1, "target": 2})
            except Exception as exc:
                import logging
                logging.exception("Error in on_tick: %s", exc)

    EventBus.subscribe("edge_blocked", lambda d: print("EventBus:", d))

    # 5. run annealer -------------------------------------------------------
    DynamicAnnealer(
        problem=problem,
        agents=agents,
        event_callback=on_tick,
        max_tick=max_tick,
        mini_iter=200,
        start_temp=100.0,
        cooling_rate=0.9,
        min_temp=1e-2,
        quantum_jump_prob=0.1,
        random_seed=42,
    ).run()

    # 6. collect & persist results -----------------------------------------
    results = {ag.id: {"route": ag.route, "status": ag.status} for ag in agents} # type: ignore

    save_solution_json(
        Solution(routes=results, total_cost=0.0, meta={}),
        output_path, # type: ignore
    )
    print(f"Dynamic solution written to {output_path}")
    return results # type: ignore