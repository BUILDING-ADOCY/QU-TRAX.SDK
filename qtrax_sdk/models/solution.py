"""
Solution representation for Q-TRAX Algorithm.
Models routes, total cost, and provides serialization.
"""
from typing import Dict, List, Any # type: ignore

class Solution:
    """
    Holds a candidate solution: route(s) and associated cost.
    - For TSP: a single route (list of node ids)
    - For VRP: dict of vehicle_id -> route (list of node ids)
    """
    def __init__(
        self,
        routes: Any,  # Could be List[int] (TSP) or Dict[str, List[int]] (VRP)
        total_cost: float,
        meta: Dict[str, Any] = None, # type: ignore
    ):
        self.routes = routes
        self.total_cost = total_cost
        self.meta = meta or {}

    def __repr__(self):
        return f"Solution(routes={self.routes}, total_cost={self.total_cost:.2f}, meta={self.meta})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "routes": self.routes,
            "total_cost": self.total_cost,
            "meta": self.meta,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Solution':
        return Solution(
            routes=data["routes"],
            total_cost=data["total_cost"],
            meta=data.get("meta", {}),
        )