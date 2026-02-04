"""
Entity Resolution Pipeline
==========================

Main orchestration pipeline that coordinates all stages.

Stages:
1. Feature Extraction
2. Pairwise Similarity
3. Graph Construction
4. Constraint Application
5. Graph Pruning
6. Seed Clustering (high precision)
7. Graph Embeddings (optional)
8. Embedding Refinement (optional)
9. Community Detection
10. Cluster Validation (simplified)
11. Entity Assignment + Confidence

Author: Entity Resolution System
"""

import time
from typing import Dict, List, Optional
from datetime import datetime
import networkx as nx
import sys
sys.path.append('..')

from data_models import (
    BlockInput, FeatureVector, SimilarityVector, GraphEdge,
    EntityCluster, ClusterMetrics, PipelineArtifacts,
    EntityType, FraudPattern
)
from config import EntityResolutionConfig
from utils import configure_logging, get_logger, StageLogger

# Import pipeline stages
from feature_extraction import extract_features_from_block
from pairwise_similarity import compute_all_similarities
from graph_builder import build_entity_graph
from constraint_engine import apply_entity_constraints
from graph_pruning import prune_entity_graph
from clustering import perform_clustering
from confidence_scoring import compute_cluster_confidence
from explainability import generate_cluster_explanation


logger = get_logger(__name__)


class EntityResolutionPipeline:
    """
    Production-grade entity resolution pipeline
    
    Orchestrates all 11 stages with:
    - Deterministic execution
    - Intermediate artifact preservation
    - Stage-by-stage logging
    - Error handling
    """
    
    def __init__(
        self,
        config: EntityResolutionConfig,
        enable_embeddings: bool = False  # Disabled by default for speed
    ):
        """
        Initialize pipeline
        
        Args:
            config: Entity resolution configuration
            enable_embeddings: Whether to use graph embeddings (Stages 7-8)
        """
        self.config = config
        self.enable_embeddings = enable_embeddings
        
        # Configure logging
        log_config = config.logging
        configure_logging(
            level=log_config.get('level', 'INFO'),
            format_type=log_config.get('format', 'console')
        )
        
        logger.info(
            "pipeline_initialized",
            domain=config.domain,
            embeddings_enabled=enable_embeddings
        )
    
    def resolve_entities(self, block: BlockInput) -> PipelineArtifacts:
        """
        Execute end-to-end entity resolution pipeline
        
        Args:
            block: Input block of records
            
        Returns:
            Pipeline artifacts with final entities
        """
        start_time = time.time()
        
        logger.info(
            "pipeline_started",
            block_id=block.block_id,
            num_records=block.size
        )
        
        # Initialize artifacts
        artifacts = PipelineArtifacts(block_id=block.block_id)
        
        try:
            # Stage 1: Feature Extraction
            features = self._stage_feature_extraction(block, artifacts)
            
            # Stage 2: Pairwise Similarity
            similarities = self._stage_pairwise_similarity(features, artifacts)
            
            # Stage 3: Graph Construction
            G = self._stage_graph_construction(similarities, features, artifacts)
            
            # Stage 4: Constraint Application
            G = self._stage_constraint_application(G, features, artifacts)
            
            # Stage 5: Graph Pruning
            G = self._stage_graph_pruning(G, block.block_id, artifacts)
            
            # Stage 6: Seed Clustering (skipped for simplicity in v1)
            
            # Stage 7-8: Embeddings & Refinement (optional)
            if self.enable_embeddings:
                G = self._stage_embeddings(G, artifacts)
            
            # Stage 9: Community Detection
            clusters = self._stage_clustering(G, artifacts)
            
            # Stage 10: Cluster Validation (simplified - just metrics)
            cluster_metrics_map = self._stage_cluster_validation(clusters, G, features)
            
            # Stage 11: Entity Assignment + Confidence
            entities = self._stage_entity_assignment(
                clusters, G, features, cluster_metrics_map, artifacts
            )
            
            # Finalize
            artifacts.entities = entities
            artifacts.processing_time_seconds = time.time() - start_time
            
            logger.info(
                "pipeline_completed",
                block_id=block.block_id,
                num_entities=len(entities),
                processing_time=artifacts.processing_time_seconds
            )
            
        except Exception as e:
            logger.error(
                "pipeline_error",
                block_id=block.block_id,
                error=str(e),
                exc_info=True
            )
            raise
        
        return artifacts
    
    def _stage_feature_extraction(
        self,
        block: BlockInput,
        artifacts: PipelineArtifacts
    ) -> Dict[str, FeatureVector]:
        """Stage 1: Feature Extraction"""
        stage_logger = StageLogger("feature_extraction", block.block_id)
        stage_logger.start(num_records=block.size)
        
        features = extract_features_from_block(
            block.records,
            self.config,
            enable_embeddings=False  # Text embeddings done separately
        )
        
        artifacts.features = features
        stage_logger.complete(num_features=len(features))
        return features
    
    def _stage_pairwise_similarity(
        self,
        features: Dict[str, FeatureVector],
        artifacts: PipelineArtifacts
    ) -> List[SimilarityVector]:
        """Stage 2: Pairwise Similarity"""
        stage_logger = StageLogger("pairwise_similarity", artifacts.block_id)
        stage_logger.start(num_records=len(features))
        
        similarities = compute_all_similarities(
            features,
            self.config,
            min_threshold=0.3  # Initial filter
        )
        
        artifacts.similarities = similarities
        stage_logger.complete(num_pairs=len(similarities))
        return similarities
    
    def _stage_graph_construction(
        self,
        similarities: List[SimilarityVector],
        features: Dict[str, FeatureVector],
        artifacts: PipelineArtifacts
    ) -> nx.Graph:
        """Stage 3: Graph Construction"""
        stage_logger = StageLogger("graph_construction", artifacts.block_id)
        stage_logger.start()
        
        G = build_entity_graph(similarities, features, self.config)
        
        # Store edges
        artifacts.edges = [
            data['edge_data'] for u, v, data in G.edges(data=True)
        ]
        
        stage_logger.complete(num_nodes=G.number_of_nodes(), num_edges=G.number_of_edges())
        return G
    
    def _stage_constraint_application(
        self,
        G: nx.Graph,
        features: Dict[str, FeatureVector],
        artifacts: PipelineArtifacts
    ) -> nx.Graph:
        """Stage 4: Constraint Application"""
        stage_logger = StageLogger("constraint_application", artifacts.block_id)
        stage_logger.start(edges_before=G.number_of_edges())
        
        G = apply_entity_constraints(G, features, self.config)
        
        stage_logger.complete(edges_after=G.number_of_edges())
        return G
    
    def _stage_graph_pruning(
        self,
        G: nx.Graph,
        block_id: str,
        artifacts: PipelineArtifacts
    ) -> nx.Graph:
        """Stage 5: Graph Pruning"""
        stage_logger = StageLogger("graph_pruning", block_id)
        stage_logger.start(edges_before=G.number_of_edges())
        
        G = prune_entity_graph(G, self.config, block_id)
        
        stage_logger.complete(edges_after=G.number_of_edges())
        return G
    
    def _stage_embeddings(
        self,
        G: nx.Graph,
        artifacts: PipelineArtifacts
    ) -> nx.Graph:
        """Stages 7-8: Graph Embeddings & Refinement (optional)"""
        # Placeholder - would use FastRP or Node2Vec
        logger.info("embeddings_stage_skipped", reason="not_implemented_in_v1")
        return G
    
    def _stage_clustering(
        self,
        G: nx.Graph,
        artifacts: PipelineArtifacts
    ) -> Dict[str, List[str]]:
        """Stage 9: Community Detection"""
        stage_logger = StageLogger("clustering", artifacts.block_id)
        stage_logger.start()
        
        clusters = perform_clustering(G, self.config)
        
        artifacts.clusters = clusters
        stage_logger.complete(num_clusters=len(clusters))
        return clusters
    
    def _stage_cluster_validation(
        self,
        clusters: Dict[str, List[str]],
        G: nx.Graph,
        features: Dict[str, FeatureVector]
    ) -> Dict[str, ClusterMetrics]:
        """Stage 10: Cluster Validation (simplified)"""
        
        cluster_metrics_map = {}
        
        for cluster_id, members in clusters.items():
            metrics = self._compute_cluster_metrics(cluster_id, members, G)
            cluster_metrics_map[cluster_id] = metrics
        
        return cluster_metrics_map
    
    def _compute_cluster_metrics(
        self,
        cluster_id: str,
        members: List[str],
        G: nx.Graph
    ) -> ClusterMetrics:
        """Compute metrics for a cluster"""
        
        # Edge weights
        edge_weights = []
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                if G.has_edge(members[i], members[j]):
                    edge_weights.append(G[members[i]][members[j]]['weight'])
        
        # Compute metrics
        size = len(members)
        avg_edge_weight = sum(edge_weights) / len(edge_weights) if edge_weights else 0.0
        min_edge_weight = min(edge_weights) if edge_weights else None
        max_edge_weight = max(edge_weights) if edge_weights else None
        
        # Edge density
        max_possible_edges = size * (size - 1) / 2
        edge_density = len(edge_weights) / max_possible_edges if max_possible_edges > 0 else 0.0
        
        # Attribute entropy (simplified)
        attribute_entropy = 0.0  # Placeholder
        
        return ClusterMetrics(
            cluster_id=cluster_id,
            size=size,
            avg_edge_weight=avg_edge_weight,
            min_edge_weight=min_edge_weight,
            max_edge_weight=max_edge_weight,
            edge_density=edge_density,
            attribute_entropy=attribute_entropy,
            has_conflicts=False
        )
    
    def _stage_entity_assignment(
        self,
        clusters: Dict[str, List[str]],
        G: nx.Graph,
        features: Dict[str, FeatureVector],
        cluster_metrics_map: Dict[str, ClusterMetrics],
        artifacts: PipelineArtifacts
    ) -> List[EntityCluster]:
        """Stage 11: Entity Assignment + Confidence"""
        
        stage_logger = StageLogger("entity_assignment", artifacts.block_id)
        stage_logger.start(num_clusters=len(clusters))
        
        entities = []
        
        for cluster_id, members in clusters.items():
            cluster_metrics = cluster_metrics_map[cluster_id]
            
            # Compute confidence
            confidence = compute_cluster_confidence(
                members, G, features, cluster_metrics, self.config
            )
            
            # Generate explanation
            explanation = generate_cluster_explanation(
                members, G, features, cluster_metrics, self.config
            )
            
            # Create entity
            entity = EntityCluster(
                entity_id=f"E_{cluster_id}",
                entity_type=EntityType.USER_ACCOUNT,
                records=members,
                confidence=confidence,
                explanations=explanation,
                fraud_risk_score=0.0,  # Placeholder
                fraud_pattern=FraudPattern.NONE,
                requires_manual_review=confidence < self.config.confidence.min_confidence
            )
            
            entities.append(entity)
        
        stage_logger.complete(num_entities=len(entities))
        return entities


# Convenience function
def resolve_block(
    block: BlockInput,
    config: EntityResolutionConfig,
    enable_embeddings: bool = False
) -> PipelineArtifacts:
    """
    Convenience function to resolve a block
    
    Args:
        block: Input block
        config: Configuration
        enable_embeddings: Use embeddings
        
    Returns:
        Pipeline artifacts
    """
    pipeline = EntityResolutionPipeline(config, enable_embeddings)
    return pipeline.resolve_entities(block)
