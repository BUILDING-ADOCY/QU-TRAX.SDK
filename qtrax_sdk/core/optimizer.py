# qtrax_sdk/core/optimizer.py

from typing import Dict, Any # type: ignore
import yaml
import json

from qtrax_sdk.services.dynamic_runner import dynamic_solve, load_agents_from_config
from qtrax_sdk.services.postprocessor import format_solution
from qtrax_sdk.utils.io_helpers import load_problem_yaml, load_problem_json
from qtrax_sdk.models.solution import Solution
from qtrax_sdk.models.problem import Problem
from qtrax_sdk.models.agent import Agent


def optimize_routes(
    config_path: str,
    output_path: str,
    use_yaml: bool = True,
    max_tick: int = 50
) -> Solution:
    """
    1) Run your working dynamic_solve() (which loads problem, agents, mutates them, and writes output)
    2) Reload the same Problem & Agent objects
    3) Call format_solution() to assemble a Solution model
    """
    # --- 1) Solve with your existing file-based runner ---
    results_dict = dynamic_solve( # type: ignore
        config_path=config_path,
        output_path=output_path,
        use_yaml=use_yaml,
        max_tick=max_tick
    )

    # --- 2) Reload Problem + Agents so format_solution can inspect them ---
    problem: Problem = (
        load_problem_yaml(config_path)
        if use_yaml
        else load_problem_json(config_path)
    )
    with open(config_path, "r") as f:
        raw_cfg = yaml.safe_load(f) if use_yaml else json.load(f)
    agents: list[Agent] = load_agents_from_config(raw_cfg)

    # --- 3) Format into your Solution object ---
    # format_solution ignores results_dict because it reads state from agents
    solution: Solution = format_solution(agents, problem, raw_cfg)
    return solution
