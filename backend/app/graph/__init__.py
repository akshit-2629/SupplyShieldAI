"""
Phase 5: Knowledge Graph — Module Init

Exports all key singletons and classes for easy import elsewhere.
"""

from app.graph.nodes import NodeType, EdgeType, GraphNode, GraphEdge
from app.graph.builder import SupplyChainGraphBuilder
from app.graph.algorithms import GraphAlgorithms
from app.graph.analyzer import BlastRadiusAnalyzer, DependencyAnalyzer
from app.graph.search import GraphSearch
from app.graph.serializer import ReactFlowSerializer
from app.graph.snapshot import graph_store

__all__ = [
    "NodeType",
    "EdgeType",
    "GraphNode",
    "GraphEdge",
    "SupplyChainGraphBuilder",
    "GraphAlgorithms",
    "BlastRadiusAnalyzer",
    "DependencyAnalyzer",
    "GraphSearch",
    "ReactFlowSerializer",
    "graph_store",
]
