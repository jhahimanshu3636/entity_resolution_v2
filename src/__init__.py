"""
Entity Resolution Package
========================

Production-grade graph-based entity resolution for P2P payment fraud detection.
"""

__version__ = "1.0.0"
__author__ = "Entity Resolution System"

from .data_models import (
    BlockInput,
    Record,
    RecordMetadata,
    FeatureVector,
    SimilarityVector,
    GraphEdge,
    EntityCluster,
    EntityExplanation,
    ClusterMetrics,
    PipelineArtifacts
)

from .config import (
    EntityResolutionConfig,
    ConfigLoader,
    load_config
)

__all__ = [
    # Data models
    'BlockInput',
    'Record',
    'RecordMetadata',
    'FeatureVector',
    'SimilarityVector',
    'GraphEdge',
    'EntityCluster',
    'EntityExplanation',
    'ClusterMetrics',
    'PipelineArtifacts',
    
    # Config
    'EntityResolutionConfig',
    'ConfigLoader',
    'load_config',
]
