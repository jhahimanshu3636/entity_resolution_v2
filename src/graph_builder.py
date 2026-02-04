"""
Graph Builder Module
===================

Stage 3 of the entity resolution pipeline.
Constructs graph from pairwise similarities.

Nodes: Records
Edges: Candidate matches with similarity vectors

Author: Entity Resolution System
"""

from typing import Dict, List, Tuple
import networkx as nx
import sys
sys.path.append('..')

from data_models import SimilarityVector, GraphEdge, FeatureVector
from utils import get_logger
from config import EntityResolutionConfig


logger = get_logger(__name__)


class GraphBuilder:
    """
    Builds entity resolution graph from similarities
    
    Graph structure:
    - Nodes: Record IDs
    - Edges: Similarity-based connections
    - Edge attributes: Full similarity vector + scores
    """
    
    def __init__(self, config: EntityResolutionConfig):
        """
        Initialize graph builder
        
        Args:
            config: Entity resolution configuration
        """
        self.config = config
    
    def build_graph(
        self,
        similarities: List[SimilarityVector],
        features: Dict[str, FeatureVector]
    ) -> nx.Graph:
        """
        Build undirected weighted graph from similarities
        
        Args:
            similarities: List of similarity vectors
            features: Feature vectors (for node attributes)
            
        Returns:
            NetworkX graph
        """
        G = nx.Graph()
        
        # Add nodes with attributes
        for record_id, feat_vector in features.items():
            G.add_node(
                record_id,
                feature_vector=feat_vector
            )
        
        # Add edges with similarity vectors
        for sim_vector in similarities:
            source, target = sim_vector.pair
            
            # Compute base edge score (weighted aggregation)
            base_score = self._compute_base_edge_score(sim_vector)
            
            # Create graph edge
            edge = GraphEdge(
                source=source,
                target=target,
                similarity_vector=sim_vector,
                base_edge_score=base_score,
                is_valid=True
            )
            
            # Add edge to graph
            G.add_edge(
                source,
                target,
                weight=base_score,
                similarity_vector=sim_vector,
                edge_data=edge
            )
        
        logger.info(
            "graph_built",
            num_nodes=G.number_of_nodes(),
            num_edges=G.number_of_edges(),
            avg_degree=sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0
        )
        
        return G
    
    def _compute_base_edge_score(self, sim_vector: SimilarityVector) -> float:
        """
        Compute weighted aggregation of similarity scores
        
        Uses configured weights from similarity config.
        NOT a simple average - respects domain-specific weights.
        
        Args:
            sim_vector: Similarity vector
            
        Returns:
            Weighted base score (0-1)
        """
        weighted_sum = 0.0
        total_weight = 0.0
        
        # Get all non-null similarities
        sims = sim_vector.to_dict()
        
        for attr_name, sim_value in sims.items():
            # Get configured weight for this attribute
            # Remove '_sim' suffix to match config keys
            config_key = attr_name.replace('_sim', '')
            sim_config = self.config.get_similarity_config(config_key)
            
            if sim_config:
                weight = sim_config.weight
                weighted_sum += sim_value * weight
                total_weight += weight
            else:
                # Default weight if not configured
                weighted_sum += sim_value
                total_weight += 1.0
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
    
    def get_edge_data(self, G: nx.Graph, source: str, target: str) -> GraphEdge:
        """Get edge data from graph"""
        edge_attrs = G[source][target]
        return edge_attrs['edge_data']
    
    def update_edge_score(self, G: nx.Graph, source: str, target: str, new_score: float):
        """Update edge weight in graph"""
        G[source][target]['weight'] = new_score
        edge_data = G[source][target]['edge_data']
        edge_data.refined_edge_score = new_score


def build_entity_graph(
    similarities: List[SimilarityVector],
    features: Dict[str, FeatureVector],
    config: EntityResolutionConfig
) -> nx.Graph:
    """
    Convenience function to build entity resolution graph
    
    Args:
        similarities: Similarity vectors
        features: Feature vectors
        config: Configuration
        
    Returns:
        NetworkX graph
    """
    builder = GraphBuilder(config)
    return builder.build_graph(similarities, features)
