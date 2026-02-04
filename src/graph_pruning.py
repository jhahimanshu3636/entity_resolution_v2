"""
Graph Pruning Module
====================

Stage 5 of the entity resolution pipeline.
Prunes and normalizes graph for stable clustering.

Goals:
- Prevent hub dominance
- Remove weak noise edges
- Stabilize clustering

Author: Entity Resolution System
"""

from typing import Dict, List
import networkx as nx
import sys
sys.path.append('..')

from utils import get_logger, log_graph_metrics
from config import EntityResolutionConfig, GraphPruningConfig


logger = get_logger(__name__)


class GraphPruner:
    """
    Prunes and normalizes graph structure
    
    Methods:
    - Top-K edges per node (prevent hubs)
    - Threshold-based pruning
    - Edge weight normalization
    """
    
    def __init__(self, config: EntityResolutionConfig):
        """
        Initialize graph pruner
        
        Args:
            config: Entity resolution configuration
        """
        self.config = config
        self.pruning_config = config.get_graph_pruning_config()
    
    def prune_graph(self, G: nx.Graph, block_id: str = "default") -> nx.Graph:
        """
        Prune and normalize graph
        
        Args:
            G: Input graph
            block_id: Block identifier for logging
            
        Returns:
            Pruned graph
        """
        original_edges = G.number_of_edges()
        
        # Step 1: Remove edges below minimum threshold
        G = self._threshold_pruning(G)
        
        # Step 2: Top-K edges per node
        G = self._topk_pruning(G)
        
        # Step 3: Enforce max degree
        G = self._max_degree_pruning(G)
        
        # Step 4: Normalize edge weights
        G = self._normalize_weights(G)
        
        final_edges = G.number_of_edges()
        
        log_graph_metrics(
            logger,
            block_id=block_id,
            stage="pruning",
            original_edges=original_edges,
            final_edges=final_edges,
            edges_removed=original_edges - final_edges,
            pruning_rate=(original_edges - final_edges) / original_edges if original_edges > 0 else 0
        )
        
        return G
    
    def _threshold_pruning(self, G: nx.Graph) -> nx.Graph:
        """Remove edges below minimum threshold"""
        min_threshold = self.pruning_config.min_threshold
        
        edges_to_remove = [
            (u, v) for u, v, data in G.edges(data=True)
            if data['weight'] < min_threshold
        ]
        
        G.remove_edges_from(edges_to_remove)
        
        logger.debug(
            "threshold_pruning_complete",
            min_threshold=min_threshold,
            edges_removed=len(edges_to_remove)
        )
        
        return G
    
    def _topk_pruning(self, G: nx.Graph) -> nx.Graph:
        """Keep only top-K edges per node"""
        top_k = self.pruning_config.top_k
        
        edges_to_remove = []
        
        for node in G.nodes():
            # Get all edges for this node with weights
            node_edges = []
            for neighbor in G.neighbors(node):
                weight = G[node][neighbor]['weight']
                node_edges.append((node, neighbor, weight))
            
            # Sort by weight descending
            node_edges.sort(key=lambda x: x[2], reverse=True)
            
            # Keep only top-K
            if len(node_edges) > top_k:
                to_remove = node_edges[top_k:]
                edges_to_remove.extend([(u, v) for u, v, w in to_remove])
        
        G.remove_edges_from(edges_to_remove)
        
        logger.debug(
            "topk_pruning_complete",
            top_k=top_k,
            edges_removed=len(edges_to_remove)
        )
        
        return G
    
    def _max_degree_pruning(self, G: nx.Graph) -> nx.Graph:
        """Enforce maximum node degree"""
        max_degree = self.pruning_config.max_degree
        
        edges_to_remove = []
        
        for node in G.nodes():
            degree = G.degree(node)
            
            if degree > max_degree:
                # Get all edges sorted by weight
                node_edges = []
                for neighbor in G.neighbors(node):
                    weight = G[node][neighbor]['weight']
                    node_edges.append((node, neighbor, weight))
                
                # Sort by weight descending
                node_edges.sort(key=lambda x: x[2], reverse=True)
                
                # Remove weakest edges beyond max_degree
                to_remove = node_edges[max_degree:]
                edges_to_remove.extend([(u, v) for u, v, w in to_remove])
        
        G.remove_edges_from(edges_to_remove)
        
        logger.debug(
            "max_degree_pruning_complete",
            max_degree=max_degree,
            edges_removed=len(edges_to_remove)
        )
        
        return G
    
    def _normalize_weights(self, G: nx.Graph) -> nx.Graph:
        """Normalize edge weights within block"""
        
        # Get all weights
        weights = [data['weight'] for u, v, data in G.edges(data=True)]
        
        if not weights:
            return G
        
        # Min-max normalization
        min_weight = min(weights)
        max_weight = max(weights)
        weight_range = max_weight - min_weight
        
        if weight_range == 0:
            # All weights are the same
            for u, v in G.edges():
                G[u][v]['weight'] = 1.0
        else:
            for u, v in G.edges():
                original = G[u][v]['weight']
                normalized = (original - min_weight) / weight_range
                G[u][v]['weight'] = normalized
        
        logger.debug(
            "weight_normalization_complete",
            min_weight=min_weight,
            max_weight=max_weight
        )
        
        return G


def prune_entity_graph(
    G: nx.Graph,
    config: EntityResolutionConfig,
    block_id: str = "default"
) -> nx.Graph:
    """
    Convenience function to prune graph
    
    Args:
        G: Graph
        config: Configuration
        block_id: Block identifier
        
    Returns:
        Pruned graph
    """
    pruner = GraphPruner(config)
    return pruner.prune_graph(G, block_id)
