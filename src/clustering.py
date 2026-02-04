"""
Clustering Module
=================

Stage 9 of the entity resolution pipeline.
Performs community detection on the validated graph.

Algorithms:
- Leiden (preferred - better quality)
- Louvain (alternative)

Author: Entity Resolution System
"""

from typing import Dict, List, Set
import networkx as nx
import sys
sys.path.append('..')

from utils import get_logger
from config import EntityResolutionConfig, ClusteringAlgorithm

# Try to import clustering libraries
try:
    import leidenalg
    import igraph as ig
    LEIDEN_AVAILABLE = True
except ImportError:
    LEIDEN_AVAILABLE = False
    print("Warning: leidenalg not available")

try:
    import community as community_louvain
    LOUVAIN_AVAILABLE = True
except ImportError:
    LOUVAIN_AVAILABLE = False
    print("Warning: python-louvain not available")


logger = get_logger(__name__)


class ClusteringEngine:
    """
    Community detection for entity hypothesis generation
    
    Generates candidate entity clusters from graph structure.
    """
    
    def __init__(self, config: EntityResolutionConfig):
        """
        Initialize clustering engine
        
        Args:
            config: Entity resolution configuration
        """
        self.config = config
        self.clustering_config = config.clustering
    
    def detect_communities(self, G: nx.Graph) -> Dict[str, List[str]]:
        """
        Detect communities in graph
        
        Args:
            G: Input graph
            
        Returns:
            Dictionary mapping cluster_id to list of record_ids
        """
        algorithm = self.clustering_config.algorithm
        
        if algorithm == ClusteringAlgorithm.LEIDEN and LEIDEN_AVAILABLE:
            clusters = self._leiden_clustering(G)
        elif algorithm == ClusteringAlgorithm.LOUVAIN and LOUVAIN_AVAILABLE:
            clusters = self._louvain_clustering(G)
        else:
            # Fallback: connected components
            logger.warning("advanced_clustering_unavailable_using_connected_components")
            clusters = self._connected_components(G)
        
        logger.info(
            "clustering_complete",
            algorithm=str(algorithm),
            num_clusters=len(clusters),
            avg_cluster_size=sum(len(members) for members in clusters.values()) / len(clusters) if clusters else 0
        )
        
        return clusters
    
    def _leiden_clustering(self, G: nx.Graph) -> Dict[str, List[str]]:
        """Leiden algorithm clustering"""
        
        # Convert NetworkX to igraph
        ig_graph = self._networkx_to_igraph(G)
        
        # Get edge weights
        weights = [G[u][v]['weight'] for u, v in G.edges()]
        
        # Run Leiden algorithm
        partition = leidenalg.find_partition(
            ig_graph,
            leidenalg.ModularityVertexPartition,
            weights=weights,
            n_iterations=-1,  # Run until convergence
            seed=self.clustering_config.seed
        )
        
        # Convert to our format
        clusters = {}
        node_list = list(G.nodes())
        
        for cluster_id, members in enumerate(partition):
            cluster_key = f"C_{cluster_id}"
            clusters[cluster_key] = [node_list[i] for i in members]
        
        return clusters
    
    def _louvain_clustering(self, G: nx.Graph) -> Dict[str, List[str]]:
        """Louvain algorithm clustering"""
        
        # Run Louvain
        partition = community_louvain.best_partition(
            G,
            weight='weight',
            resolution=self.clustering_config.resolution,
            random_state=self.clustering_config.seed
        )
        
        # Convert to our format
        clusters = {}
        for node, cluster_id in partition.items():
            cluster_key = f"C_{cluster_id}"
            if cluster_key not in clusters:
                clusters[cluster_key] = []
            clusters[cluster_key].append(node)
        
        return clusters
    
    def _connected_components(self, G: nx.Graph) -> Dict[str, List[str]]:
        """Fallback: simple connected components"""
        
        clusters = {}
        for cluster_id, component in enumerate(nx.connected_components(G)):
            cluster_key = f"C_{cluster_id}"
            clusters[cluster_key] = list(component)
        
        return clusters
    
    def _networkx_to_igraph(self, G: nx.Graph):
        """Convert NetworkX graph to igraph"""
        
        # Create vertex mapping
        nodes = list(G.nodes())
        node_to_idx = {node: idx for idx, node in enumerate(nodes)}
        
        # Create edge list with indices
        edges = [(node_to_idx[u], node_to_idx[v]) for u, v in G.edges()]
        
        # Create igraph
        ig_graph = ig.Graph(n=len(nodes), edges=edges, directed=False)
        
        return ig_graph


def perform_clustering(
    G: nx.Graph,
    config: EntityResolutionConfig
) -> Dict[str, List[str]]:
    """
    Convenience function for clustering
    
    Args:
        G: Graph
        config: Configuration
        
    Returns:
        Clusters dictionary
    """
    engine = ClusteringEngine(config)
    return engine.detect_communities(G)
