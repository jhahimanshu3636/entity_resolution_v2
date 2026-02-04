"""
Confidence Scoring Module
=========================

Computes composite confidence scores for entity clusters.

Components:
- Internal edge strength
- Attribute agreement
- Embedding cohesion (if available)
- Source trust consistency
- Fraud indicators (absence of risk signals)

Author: Entity Resolution System
"""

from typing import Dict, List
import networkx as nx
import numpy as np
import sys
sys.path.append('..')

from data_models import FeatureVector, ClusterMetrics
from utils import get_logger
from config import EntityResolutionConfig


logger = get_logger(__name__)


class ConfidenceScorer:
    """
    Computes composite confidence scores for entity clusters
    
    Confidence must be:
    - Interpretable
    - Stable across runs
    - Composite of multiple signals
    """
    
    def __init__(self, config: EntityResolutionConfig):
        """
        Initialize confidence scorer
        
        Args:
            config: Entity resolution configuration
        """
        self.config = config
        self.confidence_config = config.confidence
    
    def compute_confidence(
        self,
        cluster_members: List[str],
        G: nx.Graph,
        features: Dict[str, FeatureVector],
        cluster_metrics: ClusterMetrics
    ) -> float:
        """
        Compute composite confidence score
        
        Args:
            cluster_members: List of record IDs in cluster
            G: Graph
            features: Feature vectors
            cluster_metrics: Precomputed cluster metrics
            
        Returns:
            Confidence score (0-1)
        """
        components = {}
        
        # Edge strength component
        components['edge_strength'] = self._compute_edge_strength_score(
            cluster_members, G
        )
        
        # Attribute agreement component
        components['attribute_agreement'] = self._compute_attribute_agreement(
            cluster_members, features
        )
        
        # Embedding cohesion component (if available)
        if cluster_metrics.embedding_cohesion is not None:
            components['embedding_cohesion'] = cluster_metrics.embedding_cohesion
        else:
            components['embedding_cohesion'] = 1.0  # Neutral if not available
        
        # Source trust component
        components['source_trust'] = self._compute_source_trust(
            cluster_members, features
        )
        
        # Fraud indicators component (absence of risk signals)
        components['fraud_indicators'] = 1.0  # Placeholder - would check for fraud signals
        
        # Weighted composite
        weights = self.confidence_config.components
        confidence = 0.0
        
        for component_name, component_value in components.items():
            weight = weights.get(component_name, 0.0)
            confidence += weight * component_value
        
        # Clamp to [0, 1]
        confidence = max(0.0, min(1.0, confidence))
        
        return confidence
    
    def _compute_edge_strength_score(
        self,
        cluster_members: List[str],
        G: nx.Graph
    ) -> float:
        """Compute score based on internal edge strengths"""
        
        if len(cluster_members) == 1:
            return 1.0  # Singleton cluster - full confidence
        
        # Get all internal edges
        internal_edges = []
        for i in range(len(cluster_members)):
            for j in range(i + 1, len(cluster_members)):
                u, v = cluster_members[i], cluster_members[j]
                if G.has_edge(u, v):
                    internal_edges.append(G[u][v]['weight'])
        
        if not internal_edges:
            return 0.0  # No internal edges - disconnected cluster
        
        # Use average edge weight as score
        return np.mean(internal_edges)
    
    def _compute_attribute_agreement(
        self,
        cluster_members: List[str],
        features: Dict[str, FeatureVector]
    ) -> float:
        """Compute score based on attribute consistency"""
        
        if len(cluster_members) == 1:
            return 1.0
        
        # Check device OS consistency
        device_oss = []
        for member in cluster_members:
            device_os = features[member].categorical_features.device_os
            if device_os:
                device_oss.append(device_os)
        
        if device_oss:
            # Agreement = most common OS frequency
            from collections import Counter
            counts = Counter(device_oss)
            most_common_count = counts.most_common(1)[0][1]
            os_agreement = most_common_count / len(device_oss)
        else:
            os_agreement = 1.0
        
        # For now, just use OS agreement
        # In production, would check name consistency, etc.
        return os_agreement
    
    def _compute_source_trust(
        self,
        cluster_members: List[str],
        features: Dict[str, FeatureVector]
    ) -> float:
        """Compute average source trust score"""
        
        trust_scores = []
        for member in cluster_members:
            trust = features[member].source_features.source_trust_score
            trust_scores.append(trust)
        
        return np.mean(trust_scores) if trust_scores else 0.5


def compute_cluster_confidence(
    cluster_members: List[str],
    G: nx.Graph,
    features: Dict[str, FeatureVector],
    cluster_metrics: ClusterMetrics,
    config: EntityResolutionConfig
) -> float:
    """
    Convenience function to compute confidence
    
    Args:
        cluster_members: Cluster members
        G: Graph
        features: Features
        cluster_metrics: Cluster metrics
        config: Configuration
        
    Returns:
        Confidence score
    """
    scorer = ConfidenceScorer(config)
    return scorer.compute_confidence(cluster_members, G, features, cluster_metrics)
