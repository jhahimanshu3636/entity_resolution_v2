"""
Data Models for P2P Payment Entity Resolution System
=====================================================

Strict data contracts using Pydantic for type safety and validation.
All models follow the Architectural Information Document (AID) specifications.

Author: Entity Resolution System
Domain: P2P Payment Fraud Detection
"""

from typing import Dict, List, Optional, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class EntityType(str, Enum):
    """Entity types in P2P payment system"""
    USER_ACCOUNT = "user_account"
    PAYMENT_DEVICE = "payment_device"
    IP_ADDRESS = "ip_address"
    TRANSACTION_PATTERN = "transaction_pattern"


class DeviceOS(str, Enum):
    """Device operating systems"""
    IOS = "iOS"
    IPADOS = "iPadOS"
    ANDROID = "Android"
    WEB = "Web"
    UNKNOWN = "Unknown"


class TransactionStatus(str, Enum):
    """Transaction statuses"""
    COMPLETED = "completed"
    PENDING = "pending"
    FAILED = "failed"
    REVERSED = "reversed"
    DISPUTED = "disputed"


class ConstraintType(str, Enum):
    """Constraint types for edge validation"""
    HARD = "hard"
    SOFT = "soft"


class FraudPattern(str, Enum):
    """Known fraud patterns"""
    MULTI_ACCOUNTING = "multi_accounting"
    ACCOUNT_TAKEOVER = "account_takeover"
    FRAUD_RING = "fraud_ring"
    MONEY_MULE = "money_mule"
    VELOCITY_ABUSE = "velocity_abuse"
    NONE = "none"


# ============================================================================
# INPUT SCHEMAS
# ============================================================================

class RecordMetadata(BaseModel):
    """Metadata associated with each record"""
    source: str = Field(..., description="Data source identifier")
    timestamp: datetime = Field(..., description="Record creation/update timestamp")
    trust_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Source trust score (0-1)"
    )
    kyc_verified: bool = Field(default=False, description="KYC verification status")
    fraud_confirmed: bool = Field(default=False, description="Confirmed fraud flag")


class Record(BaseModel):
    """Individual record representing a user/device/transaction"""
    record_id: str = Field(..., description="Unique record identifier")
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Record attributes (flexible schema)"
    )
    metadata: RecordMetadata = Field(..., description="Record metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "record_id": "user_12345",
                "attributes": {
                    "email": "john@example.com",
                    "phone": "+1234567890",
                    "name": "John Smith",
                    "device_fingerprint": "abc123xyz"
                },
                "metadata": {
                    "source": "registration_db",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "trust_score": 0.95,
                    "kyc_verified": True,
                    "fraud_confirmed": False
                }
            }
        }


class BlockInput(BaseModel):
    """Input block of records for entity resolution"""
    block_id: str = Field(..., description="Unique block identifier")
    records: List[Record] = Field(..., min_length=1, description="List of records in block")
    
    @validator('records')
    def check_unique_record_ids(cls, records):
        """Ensure all record IDs are unique within block"""
        record_ids = [r.record_id for r in records]
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("Duplicate record IDs found in block")
        return records
    
    @property
    def size(self) -> int:
        """Number of records in block"""
        return len(self.records)


# ============================================================================
# FEATURE REPRESENTATION
# ============================================================================

class TextFeatures(BaseModel):
    """Text-based features"""
    name_tokens: List[str] = Field(default_factory=list, description="Tokenized name")
    address_tokens: List[str] = Field(default_factory=list, description="Tokenized address")
    ngrams: List[str] = Field(default_factory=list, description="Character n-grams")


class NumericFeatures(BaseModel):
    """Numeric features"""
    account_age_days: Optional[float] = None
    transaction_count: Optional[int] = None
    avg_transaction_amount: Optional[float] = None
    transaction_velocity_24h: Optional[int] = None


class CategoricalFeatures(BaseModel):
    """Categorical features"""
    device_os: Optional[DeviceOS] = None
    transaction_frequency_category: Optional[str] = None
    payment_method: Optional[str] = None


class Embeddings(BaseModel):
    """Embedding vectors"""
    text_embedding: Optional[List[float]] = Field(
        default=None,
        description="SBERT text embedding"
    )
    graph_embedding: Optional[List[float]] = Field(
        default=None,
        description="FastRP/Node2Vec graph embedding"
    )


class SourceFeatures(BaseModel):
    """Source and trust features"""
    source_trust_score: float = Field(default=1.0, ge=0.0, le=1.0)
    ip_reputation_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    vpn_detected: bool = Field(default=False)


class FeatureVector(BaseModel):
    """Complete feature representation for a record"""
    record_id: str
    text_features: TextFeatures = Field(default_factory=TextFeatures)
    numeric_features: NumericFeatures = Field(default_factory=NumericFeatures)
    categorical_features: CategoricalFeatures = Field(default_factory=CategoricalFeatures)
    embeddings: Embeddings = Field(default_factory=Embeddings)
    source_features: SourceFeatures = Field(default_factory=SourceFeatures)


# ============================================================================
# SIMILARITY REPRESENTATION
# ============================================================================

class SimilarityVector(BaseModel):
    """Multi-dimensional similarity scores between two records"""
    pair: tuple[str, str] = Field(..., description="Record ID pair (record_i, record_j)")
    similarities: Dict[str, float] = Field(
        default_factory=dict,
        description="Similarity scores by dimension"
    )
    
    # Individual similarity components
    name_sim: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    address_sim: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    phone_sim: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    email_sim: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    device_fingerprint_sim: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    ip_sim: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    embedding_sim: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    behavioral_sim: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    source_agreement: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary of non-null similarities"""
        return {
            k: v for k, v in {
                'name_sim': self.name_sim,
                'address_sim': self.address_sim,
                'phone_sim': self.phone_sim,
                'email_sim': self.email_sim,
                'device_fingerprint_sim': self.device_fingerprint_sim,
                'ip_sim': self.ip_sim,
                'embedding_sim': self.embedding_sim,
                'behavioral_sim': self.behavioral_sim,
                'source_agreement': self.source_agreement
            }.items() if v is not None
        }


# ============================================================================
# GRAPH REPRESENTATION
# ============================================================================

class GraphEdge(BaseModel):
    """Edge in the entity resolution graph"""
    source: str = Field(..., description="Source record ID")
    target: str = Field(..., description="Target record ID")
    similarity_vector: SimilarityVector = Field(..., description="Multi-dimensional similarity")
    base_edge_score: float = Field(..., ge=0.0, le=1.0, description="Aggregated base score")
    refined_edge_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Score after embedding refinement")
    embedding_similarity: Optional[float] = Field(default=None, description="Cosine similarity from embeddings")
    constraints_applied: List[str] = Field(default_factory=list, description="List of constraint names applied")
    is_valid: bool = Field(default=True, description="Edge validity after constraints")


# ============================================================================
# CLUSTERING & VALIDATION
# ============================================================================

class ClusterMetrics(BaseModel):
    """Metrics for cluster quality assessment"""
    cluster_id: str
    size: int = Field(..., ge=1, description="Number of records in cluster")
    avg_edge_weight: float = Field(..., ge=0.0, le=1.0)
    min_edge_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    max_edge_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    edge_density: float = Field(..., ge=0.0, le=1.0, description="Cluster cohesion")
    attribute_entropy: float = Field(..., ge=0.0, description="Attribute homogeneity")
    embedding_cohesion: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Average cosine similarity of embeddings"
    )
    has_conflicts: bool = Field(default=False, description="Conflicting attributes detected")
    
    @property
    def is_valid(self) -> bool:
        """Check if cluster meets validation criteria"""
        # Will be validated against config thresholds
        return not self.has_conflicts


class EdgeExplanation(BaseModel):
    """Explanation for a single edge"""
    pair: tuple[str, str]
    score: float = Field(..., ge=0.0, le=1.0)
    reason: str = Field(..., description="Human-readable explanation")
    key_similarities: Dict[str, float] = Field(
        default_factory=dict,
        description="Top similarity components"
    )


class EntityExplanation(BaseModel):
    """Explanation for entity cluster"""
    strongest_edges: List[EdgeExplanation] = Field(
        default_factory=list,
        description="Top N strongest edges"
    )
    dominant_attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Most common attribute values"
    )
    cluster_metrics: Optional[ClusterMetrics] = None
    fraud_indicators: List[str] = Field(
        default_factory=list,
        description="Fraud risk signals"
    )
    timeline: Optional[Dict[str, datetime]] = Field(
        default=None,
        description="First seen, last seen timestamps"
    )


# ============================================================================
# OUTPUT SCHEMA
# ============================================================================

class EntityCluster(BaseModel):
    """Final entity output with confidence and explanations"""
    entity_id: str = Field(..., description="Unique entity identifier")
    entity_type: EntityType = Field(default=EntityType.USER_ACCOUNT)
    records: List[str] = Field(..., min_length=1, description="List of record IDs")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Composite confidence score")
    explanations: EntityExplanation = Field(..., description="Explainability data")
    fraud_risk_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Fraud risk assessment"
    )
    fraud_pattern: FraudPattern = Field(
        default=FraudPattern.NONE,
        description="Detected fraud pattern"
    )
    requires_manual_review: bool = Field(
        default=False,
        description="Flag for manual review"
    )
    created_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Entity creation timestamp"
    )
    
    @validator('confidence')
    def check_confidence_matches_review_flag(cls, confidence, values):
        """Low confidence entities should be flagged for review"""
        if confidence < 0.6 and not values.get('requires_manual_review', False):
            values['requires_manual_review'] = True
        return confidence
    
    class Config:
        json_schema_extra = {
            "example": {
                "entity_id": "E_12345",
                "entity_type": "user_account",
                "records": ["user_001", "user_002", "user_003"],
                "confidence": 0.92,
                "explanations": {
                    "strongest_edges": [
                        {
                            "pair": ["user_001", "user_002"],
                            "score": 0.98,
                            "reason": "Exact email + phone match",
                            "key_similarities": {
                                "email_sim": 1.0,
                                "phone_sim": 1.0
                            }
                        }
                    ],
                    "dominant_attributes": {
                        "email": "john@example.com",
                        "phone": "+1234567890"
                    },
                    "fraud_indicators": []
                },
                "fraud_risk_score": 0.1,
                "fraud_pattern": "none",
                "requires_manual_review": False,
                "created_timestamp": "2024-01-15T10:30:00Z"
            }
        }


# ============================================================================
# PIPELINE ARTIFACTS
# ============================================================================

class PipelineArtifacts(BaseModel):
    """Intermediate artifacts for debugging and auditing"""
    block_id: str
    features: Dict[str, FeatureVector] = Field(
        default_factory=dict,
        description="Feature vectors by record ID"
    )
    similarities: List[SimilarityVector] = Field(
        default_factory=list,
        description="Pairwise similarities"
    )
    edges: List[GraphEdge] = Field(
        default_factory=list,
        description="Graph edges"
    )
    clusters: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Cluster assignments (cluster_id -> record_ids)"
    )
    entities: List[EntityCluster] = Field(
        default_factory=list,
        description="Final entity outputs"
    )
    processing_time_seconds: Optional[float] = None
    
    class Config:
        arbitrary_types_allowed = True
