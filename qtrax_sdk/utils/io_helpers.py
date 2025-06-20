
"""
Helpers for reading/writing problem definitions and solutions (YAML / JSON).
"""
import yaml  # type: ignore
import json
from typing import Any, Dict  # type: ignore

# Use relative imports so that Python finds the package correctly
from qtrax_sdk.models.problem import Problem, Node, Edge # type: ignore
from qtrax_sdk.models.solution import Solution # type: ignore



def load_problem_yaml(path: str) -> Problem: # type: ignore
    """
    Load a YAML file describing nodes, edges, and constraints,
    and construct a `Problem` object.
    """
    with open(path, "r") as f:
        data = yaml.safe_load(f)

    # Expecting data to have keys: nodes (list), edges (list), constraints (optional)
    nodes_data = data.get("nodes", [])
    edges_data = data.get("edges", [])
    constraints = data.get("constraints", {})

    nodes = [Node(item["id"], item.get("attributes")) for item in nodes_data] # type: ignore
    edges = [ # type: ignore
        Edge(item["source"], item["target"], item["weight"], item.get("attributes"))
        for item in edges_data
    ]

    return Problem(nodes=nodes, edges=edges, constraints=constraints) # type: ignore


def save_solution_json(solution: Solution, path: str) -> None: # type: ignore
    """
    Serialize the Solution to JSON and write to `path`.
    """
    with open(path, "w") as f:
        json.dump(solution.to_dict(), f, indent=2) # type: ignore


def load_problem_json(path: str) -> Problem: # type: ignore
    """
    Load a JSON file describing a problem and return a `Problem` object.
    (Structure is the same as YAML.)
    """
    with open(path, "r") as f:
        data = json.load(f)

    nodes_data = data.get("nodes", [])
    edges_data = data.get("edges", [])
    constraints = data.get("constraints", {})

    nodes = [Node(item["id"], item.get("attributes")) for item in nodes_data] # type: ignore
    edges = [ # type: ignore
        Edge(item["source"], item["target"], item["weight"], item.get("attributes"))
        for item in edges_data
    ]

    return Problem(nodes=nodes, edges=edges, constraints=constraints) # type: ignore