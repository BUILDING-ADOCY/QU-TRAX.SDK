
"""
Problem definition for Q-TRAX Algorithm.
Models nodes, edges, and constraints for logistics optimization.
"""
from typing import Dict, Any, List, Optional
import networkx as nx  # type: ignore

class Node:
    """
    Represents a location (depot, warehouse, delivery point, etc.).
    """
    def __init__(self, node_id: int, attributes: Optional[Dict[str, Any]] = None):
        self.id = node_id
        self.attributes = attributes or {}

    def __repr__(self):
        return f"Node(id={self.id}, attributes={self.attributes})"


class Edge:
    """
    Represents a weighted edge between two nodes (distance, cost, time, etc.).
    """
    def __init__(
        self,
        source: int,
        target: int,
        weight: float,
        attributes: Optional[Dict[str, Any]] = None
    ):
        self.source = source
        self.target = target
        self.weight = weight
        self.attributes = attributes or {}

    def __repr__(self):
        return (
            f"Edge({self.source} -> {self.target}, "
            f"weight={self.weight}, attributes={self.attributes})"
        )


class Problem:
    """
    Full logistics problem definition: graph + constraints.
    Uses a NetworkX DiGraph under the hood.
    Supports dynamic updates: add, remove, or change edges at runtime.
    """
    def __init__(
        self,
        nodes: List[Node],
        edges: List[Edge],
        constraints: Optional[Dict[str, Any]] = None,
    ):
        self.nodes = nodes
        self.edges = edges
        self.constraints = constraints or {}
        self.graph = self._build_graph()

    def _build_graph(self) -> nx.DiGraph:
        G = nx.DiGraph()
        for node in self.nodes:
            G.add_node(node.id, **node.attributes)  # type: ignore
        for edge in self.edges:
            G.add_edge( # type: ignore
                edge.source,
                edge.target,
                weight=edge.weight,
                **edge.attributes  # type: ignore
            )
        return G

    def get_neighbors(self, node_id: int) -> List[int]:
        return list(self.graph.successors(node_id))  # type: ignore

    def distance(self, source: int, target: int) -> float:
        if not self.graph.has_edge(source, target):  # type: ignore
            raise ValueError(f"No edge from {source} to {target}")
        return self.graph.edges[source, target]['weight']  # type: ignore

    def update_edge_weight(self, source: int, target: int, new_weight: float) -> None:
        if not self.graph.has_edge(source, target):  # type: ignore
            raise KeyError(f"No edge from {source} to {target} to update.")
        self.graph[source][target]['weight'] = new_weight

    def remove_edge(self, source: int, target: int) -> None:
        """
        Dynamically remove an edge from the graph.
        If it doesn't exist, do nothing.
        """
        if self.graph.has_edge(source, target):  # type: ignore
            self.graph.remove_edge(source, target)  # type: ignore

    def add_edge(
        self,
        source: int,
        target: int,
        weight: float,
        attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        attrs = attributes or {}
        self.graph.add_edge(source, target, weight=weight, **attrs)  # type: ignore

    def __repr__(self):
        return (
            f"Problem(nodes={len(self.nodes)}, "
            f"edges={self.graph.number_of_edges()}, " # type: ignore
            f"constraints={self.constraints})"
        )

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Problem':
        nodes = [Node(n['id'], n.get('attributes')) for n in data.get('nodes', [])]
        edges = [
            Edge(e['source'], e['target'], e['weight'], e.get('attributes'))
            for e in data.get('edges', [])
        ]
        constraints = data.get('constraints', {})
        return Problem(nodes, edges, constraints)
    



    