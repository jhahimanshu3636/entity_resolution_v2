"""
Graph Embeddings Module
=======================

Stages 7-8 of the entity resolution pipeline.
Generates graph embeddings to capture structural similarity.

Algorithms:
- FastRP (Fast Random Projection) - Preferred for speed and determinism
- Node2Vec - Alternative for richer embeddings

Author: Entity Resolution System
"""

from typing import Dict, List, Optional
import networkx as nx
import numpy as np
import sys
sys.path.append('..')

from utils import get_logger
from config import EntityResolutionConfig

# Try to import embedding libraries
try:
    from sklearn.decomposition import TruncatedSVD
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available for FastRP")

try:
    from node2vec import Node2Vec as N2V
    NODE2VEC_AVAILABLE = True
except ImportError:
    NODE2VEC_AVAILABLE = False
    print("Warning: node2vec not available")


logger = get_logger(__name__)


class GraphEmbedder:
    """
    Generate graph embeddings to capture structural similarity
    
    Embeddings enhance edge weights by considering:
    - Network structure (who you're connected to)
    - Community membership (implicit clustering)
    - Path-based similarity (random walks)
    """
    
    def __init__(self, config: EntityResolutionConfig):
        """
        Initialize graph embedder
        
        Args:
            config: Entity resolution configuration
        """
        self.config = config
        self.embedding_config = config.embeddings
    
    def generate_embeddings(self, G: nx.Graph) -> Dict[str, np.ndarray]:
        """
        Generate embeddings for all nodes in graph
        
        Args:
            G: Input graph
            
        Returns:
            Dictionary mapping node_id to embedding vector
        """
        if not self.embedding_config.enabled:
            logger.info("embeddings_disabled")
            return {}
        
        algorithm = self.embedding_config.algorithm
        
        if algorithm == "fastrp" and SKLEARN_AVAILABLE:
            embeddings = self._fastrp_embeddings(G)
        elif algorithm == "node2vec" and NODE2VEC_AVAILABLE:
            embeddings = self._node2vec_embeddings(G)
        else:
            logger.warning("embedding_algorithm_unavailable", algorithm=str(algorithm))
            embeddings = self._random_projection_fallback(G)
        
        logger.info(
            "embeddings_generated",
            algorithm=str(algorithm),
            num_nodes=len(embeddings),
            dimensions=embeddings[list(embeddings.keys())[0]].shape[0] if embeddings else 0
        )
        
        return embeddings
    
    def _fastrp_embeddings(self, G: nx.Graph) -> Dict[str, np.ndarray]:
        """
        Fast Random Projection embeddings
        
        FastRP is:
        - Fast (O(|E| * d) where d = dimensions)
        - Deterministic (with fixed seed)
        - Effective for fraud detection
        """
        dimensions = self.embedding_config.dimensions
        iterations = self.embedding_config.fastrp_params.get('iterations', 5)
        seed = self.embedding_config.fastrp_params.get('random_seed', 42)
        
        np.random.seed(seed)
        
        # Get adjacency matrix
        nodes = list(G.nodes())
        n = len(nodes)
        node_to_idx = {node: idx for idx, node in enumerate(nodes)}
        
        # Initialize with random projections
        embeddings = np.random.randn(n, dimensions)
        
        # Normalize
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        embeddings = embeddings / norms
        
        # Iterative propagation
        for iteration in range(iterations):
            new_embeddings = np.zeros_like(embeddings)
            
            for i, node in enumerate(nodes):
                neighbors = list(G.neighbors(node))
                if neighbors:
                    # Aggregate neighbor embeddings (weighted by edge weight)
                    neighbor_sum = np.zeros(dimensions)
                    total_weight = 0.0
                    
                    for neighbor in neighbors:
                        j = node_to_idx[neighbor]
                        weight = G[node][neighbor]['weight']
                        neighbor_sum += embeddings[j] * weight
                        total_weight += weight
                    
                    if total_weight > 0:
                        new_embeddings[i] = neighbor_sum / total_weight
                    else:
                        new_embeddings[i] = embeddings[i]
                else:
                    new_embeddings[i] = embeddings[i]
            
            # Normalize
            norms = np.linalg.norm(new_embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1
            embeddings = new_embeddings / norms
        
        # Convert to dictionary
        result = {node: embeddings[i] for i, node in enumerate(nodes)}
        
        return result
    
    def _node2vec_embeddings(self, G: nx.Graph) -> Dict[str, np.ndarray]:
        """
        Node2Vec embeddings using random walks
        
        Node2Vec:
        - Captures both homophily and structural equivalence
        - Richer representation but slower
        - Non-deterministic without proper seeding
        """
        dimensions = self.embedding_config.dimensions
        params = self.embedding_config.node2vec_params
        
        # Create Node2Vec model
        node2vec = N2V(
            G,
            dimensions=dimensions,
            walk_length=params.get('walk_length', 80),
            num_walks=params.get('num_walks', 10),
            p=params.get('p', 1.0),
            q=params.get('q', 1.0),
            workers=1,  # Single worker for determinism
            seed=params.get('random_seed', 42)
        )
        
        # Fit model
        model = node2vec.fit(
            window=10,
            min_count=1,
            batch_words=4
        )
        
        # Extract embeddings
        embeddings = {}
        for node in G.nodes():
            embeddings[node] = model.wv[str(node)]
        
        return embeddings
    
    def _random_projection_fallback(self, G: nx.Graph) -> Dict[str, np.ndarray]:
        """Simple random projection fallback if libraries unavailable"""
        
        dimensions = self.embedding_config.dimensions
        nodes = list(G.nodes())
        n = len(nodes)
        
        np.random.seed(42)
        
        # Simple random embeddings (better than nothing)
        embeddings_matrix = np.random.randn(n, dimensions)
        
        # Normalize
        norms = np.linalg.norm(embeddings_matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1
        embeddings_matrix = embeddings_matrix / norms
        
        result = {node: embeddings_matrix[i] for i, node in enumerate(nodes)}
        
        return result


class EmbeddingRefiner:
    """
    Refine edge weights using embedding similarity
    
    Combines:
    - Original similarity (α weight)
    - Embedding similarity (β weight)
    
    Constraint: α > β (embeddings enhance, never override)
    """
    
    def __init__(self, config: EntityResolutionConfig):
        """
        Initialize embedding refiner
        
        Args:
            config: Entity resolution configuration
        """
        self.config = config
        self.embedding_config = config.embeddings
    
    def refine_graph(
        self,
        G: nx.Graph,
        embeddings: Dict[str, np.ndarray]
    ) -> nx.Graph:
        """
        Refine edge weights using embedding similarity
        
        Args:
            G: Input graph with base edge weights
            embeddings: Node embeddings
            
        Returns:
            Graph with refined edge weights
        """
        if not embeddings:
            logger.info("no_embeddings_skipping_refinement")
            return G
        
        alpha = self.embedding_config.alpha  # Original similarity weight
        beta = self.embedding_config.beta    # Embedding similarity weight
        
        # Validate constraint: α > β
        if alpha <= beta:
            logger.warning(
                "invalid_embedding_weights",
                alpha=alpha,
                beta=beta,
                message="alpha must be > beta"
            )
            alpha = 0.7
            beta = 0.3
        
        refined_count = 0
        
        for u, v in G.edges():
            # Get original weight
            original_weight = G[u][v]['weight']
            
            # Compute embedding similarity (cosine)
            emb_u = embeddings.get(u)
            emb_v = embeddings.get(v)
            
            if emb_u is not None and emb_v is not None:
                # Cosine similarity
                dot_product = np.dot(emb_u, emb_v)
                norm_u = np.linalg.norm(emb_u)
                norm_v = np.linalg.norm(emb_v)
                
                if norm_u > 0 and norm_v > 0:
                    embedding_sim = dot_product / (norm_u * norm_v)
                    
                    # Refined weight = α * original + β * embedding
                    refined_weight = alpha * original_weight + beta * embedding_sim
                    
                    # Update graph
                    G[u][v]['weight'] = refined_weight
                    
                    # Update edge data
                    edge_data = G[u][v]['edge_data']
                    edge_data.refined_edge_score = refined_weight
                    edge_data.embedding_similarity = float(embedding_sim)
                    
                    refined_count += 1
        
        logger.info(
            "embedding_refinement_complete",
            edges_refined=refined_count,
            total_edges=G.number_of_edges(),
            alpha=alpha,
            beta=beta
        )
        
        return G


def generate_graph_embeddings(
    G: nx.Graph,
    config: EntityResolutionConfig
) -> Dict[str, np.ndarray]:
    """
    Convenience function to generate embeddings
    
    Args:
        G: Graph
        config: Configuration
        
    Returns:
        Node embeddings
    """
    embedder = GraphEmbedder(config)
    return embedder.generate_embeddings(G)


def refine_with_embeddings(
    G: nx.Graph,
    embeddings: Dict[str, np.ndarray],
    config: EntityResolutionConfig
) -> nx.Graph:
    """
    Convenience function to refine graph with embeddings
    
    Args:
        G: Graph
        embeddings: Node embeddings
        config: Configuration
        
    Returns:
        Refined graph
    """
    refiner = EmbeddingRefiner(config)
    return refiner.refine_graph(G, embeddings)
