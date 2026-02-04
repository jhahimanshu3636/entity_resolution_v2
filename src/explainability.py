"""
Explainability Module
====================

Generates human-readable explanations for entity clusters.

Explanations include:
- Strongest edges with reasons
- Dominant attribute values
- Cluster quality metrics
- Fraud indicators (if any)

Author: Entity Resolution System
"""

from typing import Dict, List, Tuple
import networkx as nx
from datetime import datetime
import sys
sys.path.append('..')

from data_models import (
    FeatureVector, ClusterMetrics, EntityExplanation,
    EdgeExplanation, SimilarityVector
)
from utils import get_logger
from config import EntityResolutionConfig


logger = get_logger(__name__)


class ExplainabilityEngine:
    """
    Generates explanations for entity resolution decisions
    
    All merges must be explainable - core design principle.
    """
    
    def __init__(self, config: EntityResolutionConfig):
        """
        Initialize explainability engine
        
        Args:
            config: Entity resolution configuration
        """
        self.config = config
    
    def generate_explanation(
        self,
        cluster_members: List[str],
        G: nx.Graph,
        features: Dict[str, FeatureVector],
        cluster_metrics: ClusterMetrics
    ) -> EntityExplanation:
        """
        Generate complete explanation for entity cluster
        
        Args:
            cluster_members: Record IDs in cluster
            G: Graph
            features: Feature vectors
            cluster_metrics: Cluster quality metrics
            
        Returns:
            Entity explanation
        """
        # Get strongest edges
        strongest_edges = self._get_strongest_edges(cluster_members, G)
        
        # Get dominant attributes
        dominant_attrs = self._get_dominant_attributes(cluster_members, features)
        
        # Get fraud indicators
        fraud_indicators = self._detect_fraud_indicators(cluster_members, features)
        
        # Get timeline
        timeline = self._get_timeline(cluster_members, features)
        
        return EntityExplanation(
            strongest_edges=strongest_edges,
            dominant_attributes=dominant_attrs,
            cluster_metrics=cluster_metrics,
            fraud_indicators=fraud_indicators,
            timeline=timeline
        )
    
    def _get_strongest_edges(
        self,
        cluster_members: List[str],
        G: nx.Graph,
        top_n: int = 3
    ) -> List[EdgeExplanation]:
        """Get top N strongest edges with explanations"""
        
        edge_explanations = []
        
        # Get all internal edges with weights
        internal_edges = []
        for i in range(len(cluster_members)):
            for j in range(i + 1, len(cluster_members)):
                u, v = cluster_members[i], cluster_members[j]
                if G.has_edge(u, v):
                    weight = G[u][v]['weight']
                    sim_vector = G[u][v]['similarity_vector']
                    internal_edges.append((u, v, weight, sim_vector))
        
        # Sort by weight descending
        internal_edges.sort(key=lambda x: x[2], reverse=True)
        
        # Generate explanations for top edges
        for u, v, weight, sim_vector in internal_edges[:top_n]:
            reason = self._generate_edge_reason(sim_vector)
            key_sims = self._get_key_similarities(sim_vector)
            
            edge_explanations.append(EdgeExplanation(
                pair=(u, v),
                score=weight,
                reason=reason,
                key_similarities=key_sims
            ))
        
        return edge_explanations
    
    def _generate_edge_reason(self, sim_vector: SimilarityVector) -> str:
        """Generate human-readable reason for edge"""
        
        sims = sim_vector.to_dict()
        
        # Find strongest similarities
        high_sims = [(k, v) for k, v in sims.items() if v >= 0.9]
        medium_sims = [(k, v) for k, v in sims.items() if 0.7 <= v < 0.9]
        
        if high_sims:
            # Exact or near-exact matches
            attrs = [k.replace('_sim', '') for k, v in high_sims]
            return f"Exact/near-exact match on: {', '.join(attrs)}"
        
        elif medium_sims:
            # High similarity
            attrs = [k.replace('_sim', '') for k, v in medium_sims]
            return f"High similarity on: {', '.join(attrs)}"
        
        else:
            return "Moderate similarity across multiple dimensions"
    
    def _get_key_similarities(self, sim_vector: SimilarityVector) -> Dict[str, float]:
        """Get top similarity components"""
        
        sims = sim_vector.to_dict()
        
        # Sort by value descending
        sorted_sims = sorted(sims.items(), key=lambda x: x[1], reverse=True)
        
        # Return top 3
        return dict(sorted_sims[:3])
    
    def _get_dominant_attributes(
        self,
        cluster_members: List[str],
        features: Dict[str, FeatureVector]
    ) -> Dict[str, any]:
        """Get most common attribute values in cluster"""
        
        from collections import Counter
        
        dominant = {}
        
        # Name (most common)
        names = []
        for member in cluster_members:
            name_tokens = features[member].text_features.name_tokens
            if name_tokens:
                names.append(' '.join(name_tokens))
        
        if names:
            name_counts = Counter(names)
            dominant['name'] = name_counts.most_common(1)[0][0]
        
        # Device OS (most common)
        device_oss = []
        for member in cluster_members:
            device_os = features[member].categorical_features.device_os
            if device_os:
                device_oss.append(str(device_os))
        
        if device_oss:
            os_counts = Counter(device_oss)
            dominant['device_os'] = os_counts.most_common(1)[0][0]
        
        return dominant
    
    def _detect_fraud_indicators(
        self,
        cluster_members: List[str],
        features: Dict[str, FeatureVector]
    ) -> List[str]:
        """Detect fraud risk indicators in cluster"""
        
        indicators = []
        
        # VPN usage
        vpn_count = sum(
            1 for member in cluster_members
            if features[member].source_features.vpn_detected
        )
        if vpn_count > 0:
            indicators.append(f"VPN detected in {vpn_count}/{len(cluster_members)} records")
        
        # Low source trust
        low_trust_count = sum(
            1 for member in cluster_members
            if features[member].source_features.source_trust_score < 0.5
        )
        if low_trust_count > 0:
            indicators.append(f"Low source trust in {low_trust_count}/{len(cluster_members)} records")
        
        # Large cluster size (potential fraud ring)
        if len(cluster_members) > 20:
            indicators.append(f"Large cluster size: {len(cluster_members)} records (potential fraud ring)")
        
        return indicators
    
    def _get_timeline(
        self,
        cluster_members: List[str],
        features: Dict[str, FeatureVector]
    ) -> Dict[str, datetime]:
        """Get cluster timeline (first seen, last seen)"""
        
        # Note: In production, would extract actual timestamps
        # For now, return None
        return None


def generate_cluster_explanation(
    cluster_members: List[str],
    G: nx.Graph,
    features: Dict[str, FeatureVector],
    cluster_metrics: ClusterMetrics,
    config: EntityResolutionConfig
) -> EntityExplanation:
    """
    Convenience function to generate explanation
    
    Args:
        cluster_members: Cluster members
        G: Graph
        features: Features
        cluster_metrics: Cluster metrics
        config: Configuration
        
    Returns:
        Entity explanation
    """
    engine = ExplainabilityEngine(config)
    return engine.generate_explanation(cluster_members, G, features, cluster_metrics)
