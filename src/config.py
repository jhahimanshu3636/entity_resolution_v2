"""
Configuration Management for Entity Resolution System
====================================================

Loads and validates configuration from YAML files.
Supports domain-specific configurations for different use cases.

Author: Entity Resolution System
Domain: P2P Payment Fraud Detection
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


# ============================================================================
# CONFIGURATION MODELS
# ============================================================================

class SimilarityAlgorithm(str, Enum):
    """Supported similarity algorithms"""
    EXACT_MATCH = "exact_match"
    NORMALIZED_EXACT = "normalized_exact"
    JARO_WINKLER = "jaro_winkler"
    LEVENSHTEIN = "levenshtein"
    TOKEN_SORT = "token_sort"
    COSINE_SIMILARITY = "cosine_similarity"
    SUBNET_MATCH = "subnet_match"


class GraphAlgorithm(str, Enum):
    """Graph embedding algorithms"""
    FASTRP = "fastrp"
    NODE2VEC = "node2vec"


class ClusteringAlgorithm(str, Enum):
    """Clustering algorithms"""
    LEIDEN = "leiden"
    LOUVAIN = "louvain"


class SimilarityConfig(BaseModel):
    """Configuration for a single similarity dimension"""
    algorithm: SimilarityAlgorithm
    threshold: float = Field(..., ge=0.0, le=1.0)
    weight: float = Field(..., ge=0.0, le=1.0)
    case_sensitive: bool = False
    normalization: Optional[str] = None
    features: Optional[List[str]] = None


class HardConstraintConfig(BaseModel):
    """Hard constraint configuration"""
    name: str
    type: str = "hard"
    enabled: bool = True
    description: str
    logic: str = Field(..., description="Constraint logic description")


class SoftConstraintConfig(BaseModel):
    """Soft constraint configuration"""
    name: str
    type: str = "soft"
    enabled: bool = True
    penalty: float = Field(..., ge=0.0, le=1.0, description="Edge weight penalty (0-1)")
    description: str
    logic: str = Field(..., description="Constraint logic description")


class GraphPruningConfig(BaseModel):
    """Graph pruning configuration"""
    top_k: int = Field(..., ge=1, description="Max edges per node")
    min_threshold: float = Field(..., ge=0.0, le=1.0)
    hub_penalty: bool = True
    max_degree: int = Field(..., ge=1)


class EmbeddingConfig(BaseModel):
    """Graph embedding configuration"""
    enabled: bool = True
    algorithm: GraphAlgorithm = GraphAlgorithm.FASTRP
    dimensions: int = Field(..., ge=16, le=512)
    alpha: float = Field(..., ge=0.0, le=1.0, description="Original score weight")
    beta: float = Field(..., ge=0.0, le=1.0, description="Embedding score weight")
    
    # Algorithm-specific parameters
    fastrp_params: Dict[str, Any] = Field(default_factory=dict)
    node2vec_params: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('beta')
    def validate_alpha_beta_constraint(cls, beta, values):
        """Ensure α > β (original similarity dominates)"""
        alpha = values.get('alpha')
        if alpha is not None and beta >= alpha:
            raise ValueError(f"Beta ({beta}) must be less than alpha ({alpha}). Constraint: α > β")
        return beta


class ClusteringConfig(BaseModel):
    """Clustering configuration"""
    algorithm: ClusteringAlgorithm = ClusteringAlgorithm.LEIDEN
    resolution: float = Field(default=1.0, ge=0.1, le=5.0)
    seed: int = 42
    min_cluster_size: int = Field(default=1, ge=1)
    max_cluster_size: int = Field(default=50, ge=1)
    louvain_params: Dict[str, Any] = Field(default_factory=dict)


class ValidationConfig(BaseModel):
    """Cluster validation configuration"""
    entropy_threshold: float = Field(..., ge=0.0, le=1.0)
    min_edge_density: float = Field(..., ge=0.0, le=1.0)
    min_embedding_cohesion: float = Field(default=0.7, ge=0.0, le=1.0)
    conflict_checks: Dict[str, bool] = Field(default_factory=dict)
    fraud_validation: Dict[str, Any] = Field(default_factory=dict)


class ConfidenceConfig(BaseModel):
    """Confidence scoring configuration"""
    components: Dict[str, float] = Field(
        ...,
        description="Component weights for composite confidence"
    )
    min_confidence: float = Field(..., ge=0.0, le=1.0)
    high_confidence: float = Field(..., ge=0.0, le=1.0)
    
    @validator('components')
    def validate_weights_sum_to_one(cls, components):
        """Ensure component weights sum to ~1.0"""
        total = sum(components.values())
        if not (0.95 <= total <= 1.05):  # Allow small floating point error
            raise ValueError(f"Component weights must sum to 1.0, got {total}")
        return components


class FraudDetectionConfig(BaseModel):
    """Fraud detection configuration"""
    risk_signals: List[str] = Field(default_factory=list)
    fraud_patterns: List[str] = Field(default_factory=list)
    thresholds: Dict[str, Any] = Field(default_factory=dict)


class PerformanceConfig(BaseModel):
    """Performance and scalability configuration"""
    cache_features: bool = True
    cache_similarities: bool = True
    cache_embeddings: bool = True
    parallel_similarity_computation: bool = True
    num_workers: int = Field(default=4, ge=1, le=32)
    batch_size: int = Field(default=1000, ge=10)
    max_block_size: int = Field(default=5000, ge=100)
    max_processing_time_seconds: int = Field(default=300, ge=10)


# ============================================================================
# MAIN CONFIGURATION
# ============================================================================

class EntityResolutionConfig(BaseModel):
    """Main configuration for entity resolution system"""
    
    # Domain metadata
    domain: str
    description: Optional[str] = None
    entity_types: List[str] = Field(default_factory=list)
    
    # Features
    features: Dict[str, List[str]] = Field(default_factory=dict)
    
    # Similarity configuration
    similarity: Dict[str, SimilarityConfig]
    
    # Constraints
    constraints: Dict[str, List[Any]] = Field(
        default_factory=lambda: {"hard": [], "soft": []}
    )
    
    # Graph configuration
    graph: Dict[str, Any] = Field(default_factory=dict)
    
    # Embeddings
    embeddings: EmbeddingConfig
    
    # Clustering
    clustering: ClusteringConfig
    
    # Validation
    validation: ValidationConfig
    
    # Confidence
    confidence: ConfidenceConfig
    
    # Fraud detection
    fraud_detection: Optional[FraudDetectionConfig] = None
    
    # Logging
    logging: Dict[str, Any] = Field(default_factory=dict)
    
    # Performance
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    
    # Output
    output: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def from_yaml(cls, config_path: str) -> "EntityResolutionConfig":
        """Load configuration from YAML file"""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(path, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        # Parse nested configurations
        if 'embeddings' in config_dict:
            config_dict['embeddings'] = EmbeddingConfig(**config_dict['embeddings'])
        
        if 'clustering' in config_dict:
            config_dict['clustering'] = ClusteringConfig(**config_dict['clustering'])
        
        if 'validation' in config_dict:
            config_dict['validation'] = ValidationConfig(**config_dict['validation'])
        
        if 'confidence' in config_dict:
            config_dict['confidence'] = ConfidenceConfig(**config_dict['confidence'])
        
        if 'fraud_detection' in config_dict:
            config_dict['fraud_detection'] = FraudDetectionConfig(**config_dict['fraud_detection'])
        
        if 'performance' in config_dict:
            config_dict['performance'] = PerformanceConfig(**config_dict['performance'])
        
        # Parse similarity configurations
        if 'similarity' in config_dict:
            similarity_configs = {}
            for key, value in config_dict['similarity'].items():
                similarity_configs[key] = SimilarityConfig(**value)
            config_dict['similarity'] = similarity_configs
        
        return cls(**config_dict)
    
    def to_yaml(self, output_path: str) -> None:
        """Save configuration to YAML file"""
        config_dict = self.dict()
        
        with open(output_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
    
    def get_similarity_config(self, attribute: str) -> Optional[SimilarityConfig]:
        """Get similarity configuration for a specific attribute"""
        return self.similarity.get(attribute)
    
    def get_hard_constraints(self) -> List[HardConstraintConfig]:
        """Get all enabled hard constraints"""
        hard_constraints = self.constraints.get('hard', [])
        return [
            HardConstraintConfig(**c) for c in hard_constraints 
            if c.get('enabled', True)
        ]
    
    def get_soft_constraints(self) -> List[SoftConstraintConfig]:
        """Get all enabled soft constraints"""
        soft_constraints = self.constraints.get('soft', [])
        return [
            SoftConstraintConfig(**c) for c in soft_constraints 
            if c.get('enabled', True)
        ]
    
    def get_graph_pruning_config(self) -> GraphPruningConfig:
        """Get graph pruning configuration"""
        pruning = self.graph.get('pruning', {})
        return GraphPruningConfig(**pruning)
    
    @property
    def seed_cluster_threshold(self) -> float:
        """Get seed cluster threshold from graph config"""
        return self.graph.get('seed_cluster_threshold', 0.95)
    
    @property
    def alpha(self) -> float:
        """Original similarity weight"""
        return self.embeddings.alpha
    
    @property
    def beta(self) -> float:
        """Embedding similarity weight"""
        return self.embeddings.beta


# ============================================================================
# CONFIGURATION LOADER
# ============================================================================

class ConfigLoader:
    """Configuration loader with caching"""
    
    _cache: Dict[str, EntityResolutionConfig] = {}
    
    @classmethod
    def load(cls, config_path: str, use_cache: bool = True) -> EntityResolutionConfig:
        """Load configuration with optional caching"""
        if use_cache and config_path in cls._cache:
            return cls._cache[config_path]
        
        config = EntityResolutionConfig.from_yaml(config_path)
        
        if use_cache:
            cls._cache[config_path] = config
        
        return config
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear configuration cache"""
        cls._cache.clear()


# ============================================================================
# DEFAULT CONFIGURATION PATH
# ============================================================================

def get_default_config_path(domain: str = "p2p_payment_resolution") -> str:
    """Get default configuration path for a domain"""
    base_dir = Path(__file__).parent.parent
    config_path = base_dir / "config" / f"{domain}.yaml"
    return str(config_path)


def load_config(domain: str = "p2p_payment_resolution") -> EntityResolutionConfig:
    """Convenience function to load domain configuration"""
    config_path = get_default_config_path(domain)
    return ConfigLoader.load(config_path)
