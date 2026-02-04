"""
Pairwise Similarity Computation Module
======================================

Stage 2 of the entity resolution pipeline.
Computes multi-dimensional similarity scores between record pairs.

CRITICAL: Returns full similarity vector - NO AGGREGATION at this stage.

Author: Entity Resolution System
"""

from typing import Dict, List, Tuple, Optional
import sys
sys.path.append('..')

from rapidfuzz import fuzz
from jellyfish import jaro_winkler_similarity
import numpy as np

from data_models import FeatureVector, SimilarityVector
from utils import normalize_email, normalize_phone, normalize_address, get_ip_subnet, get_logger
from config import EntityResolutionConfig, SimilarityConfig, SimilarityAlgorithm


logger = get_logger(__name__)


class SimilarityComputer:
    """
    Computes pairwise similarities between feature vectors
    
    Maintains separate scores for each dimension - no premature aggregation
    """
    
    def __init__(self, config: EntityResolutionConfig):
        """
        Initialize similarity computer
        
        Args:
            config: Entity resolution configuration
        """
        self.config = config
    
    def compute_pairwise(
        self,
        features: Dict[str, FeatureVector],
        min_threshold: float = 0.0
    ) -> List[SimilarityVector]:
        """
        Compute pairwise similarities for all record pairs
        
        Args:
            features: Feature vectors by record ID
            min_threshold: Minimum threshold to include a pair
            
        Returns:
            List of similarity vectors
        """
        similarities = []
        record_ids = list(features.keys())
        
        # All pairs comparison
        for i in range(len(record_ids)):
            for j in range(i + 1, len(record_ids)):
                record_i = record_ids[i]
                record_j = record_ids[j]
                
                sim_vector = self.compute_similarity(
                    features[record_i],
                    features[record_j]
                )
                
                # Only include if meets minimum threshold
                max_sim = max(sim_vector.to_dict().values()) if sim_vector.to_dict() else 0.0
                if max_sim >= min_threshold:
                    similarities.append(sim_vector)
        
        logger.info(
            "pairwise_similarities_computed",
            num_pairs=len(similarities),
            total_possible_pairs=len(record_ids) * (len(record_ids) - 1) // 2
        )
        
        return similarities
    
    def compute_similarity(
        self,
        feat_a: FeatureVector,
        feat_b: FeatureVector
    ) -> SimilarityVector:
        """
        Compute similarity between two feature vectors
        
        Args:
            feat_a: First feature vector
            feat_b: Second feature vector
            
        Returns:
            Multi-dimensional similarity vector
        """
        pair = (feat_a.record_id, feat_b.record_id)
        
        # Compute each similarity dimension
        name_sim = self._compute_name_similarity(feat_a, feat_b)
        address_sim = self._compute_address_similarity(feat_a, feat_b)
        phone_sim = self._compute_phone_similarity(feat_a, feat_b)
        email_sim = self._compute_email_similarity(feat_a, feat_b)
        device_fingerprint_sim = self._compute_device_similarity(feat_a, feat_b)
        ip_sim = self._compute_ip_similarity(feat_a, feat_b)
        embedding_sim = self._compute_embedding_similarity(feat_a, feat_b)
        behavioral_sim = self._compute_behavioral_similarity(feat_a, feat_b)
        source_agreement = self._compute_source_agreement(feat_a, feat_b)
        
        return SimilarityVector(
            pair=pair,
            name_sim=name_sim,
            address_sim=address_sim,
            phone_sim=phone_sim,
            email_sim=email_sim,
            device_fingerprint_sim=device_fingerprint_sim,
            ip_sim=ip_sim,
            embedding_sim=embedding_sim,
            behavioral_sim=behavioral_sim,
            source_agreement=source_agreement
        )
    
    def _compute_name_similarity(self, feat_a: FeatureVector, feat_b: FeatureVector) -> Optional[float]:
        """Compute name similarity using configured algorithm"""
        config = self.config.get_similarity_config('name')
        if not config:
            return None
        
        tokens_a = feat_a.text_features.name_tokens
        tokens_b = feat_b.text_features.name_tokens
        
        if not tokens_a or not tokens_b:
            return None
        
        name_a = ' '.join(tokens_a)
        name_b = ' '.join(tokens_b)
        
        if config.algorithm == SimilarityAlgorithm.EXACT_MATCH:
            return 1.0 if name_a == name_b else 0.0
        
        elif config.algorithm == SimilarityAlgorithm.JARO_WINKLER:
            return jaro_winkler_similarity(name_a, name_b)
        
        elif config.algorithm == SimilarityAlgorithm.TOKEN_SORT:
            return fuzz.token_sort_ratio(name_a, name_b) / 100.0
        
        return None
    
    def _compute_address_similarity(self, feat_a: FeatureVector, feat_b: FeatureVector) -> Optional[float]:
        """Compute address similarity"""
        config = self.config.get_similarity_config('address')
        if not config:
            return None
        
        tokens_a = feat_a.text_features.address_tokens
        tokens_b = feat_b.text_features.address_tokens
        
        if not tokens_a or not tokens_b:
            return None
        
        address_a = ' '.join(tokens_a)
        address_b = ' '.join(tokens_b)
        
        # Use token sort ratio for addresses (handles word order)
        return fuzz.token_sort_ratio(address_a, address_b) / 100.0
    
    def _compute_phone_similarity(self, feat_a: FeatureVector, feat_b: FeatureVector) -> Optional[float]:
        """Compute phone similarity (typically exact match)"""
        # Note: In production, you'd extract phone from attributes
        # For now, return None as phone is not in FeatureVector base class
        return None
    
    def _compute_email_similarity(self, feat_a: FeatureVector, feat_b: FeatureVector) -> Optional[float]:
        """Compute email similarity (typically exact match)"""
        # Note: In production, you'd extract email from attributes
        # For now, return None as email is not in FeatureVector base class
        return None
    
    def _compute_device_similarity(self, feat_a: FeatureVector, feat_b: FeatureVector) -> Optional[float]:
        """Compute device fingerprint similarity"""
        # Note: Device fingerprint would be in attributes
        return None
    
    def _compute_ip_similarity(self, feat_a: FeatureVector, feat_b: FeatureVector) -> Optional[float]:
        """Compute IP address similarity"""
        # Note: IP address would be in attributes
        return None
    
    def _compute_embedding_similarity(self, feat_a: FeatureVector, feat_b: FeatureVector) -> Optional[float]:
        """Compute text embedding cosine similarity"""
        emb_a = feat_a.embeddings.text_embedding
        emb_b = feat_b.embeddings.text_embedding
        
        if not emb_a or not emb_b:
            return None
        
        # Cosine similarity
        vec_a = np.array(emb_a)
        vec_b = np.array(emb_b)
        
        dot_product = np.dot(vec_a, vec_b)
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    def _compute_behavioral_similarity(self, feat_a: FeatureVector, feat_b: FeatureVector) -> Optional[float]:
        """Compute behavioral pattern similarity"""
        # Simple behavioral similarity based on transaction patterns
        num_a = feat_a.numeric_features
        num_b = feat_b.numeric_features
        
        if not num_a.avg_transaction_amount or not num_b.avg_transaction_amount:
            return None
        
        # Similarity based on transaction amount (normalized difference)
        diff = abs(num_a.avg_transaction_amount - num_b.avg_transaction_amount)
        max_val = max(num_a.avg_transaction_amount, num_b.avg_transaction_amount)
        
        if max_val == 0:
            return 1.0
        
        # Convert to similarity (0 = very different, 1 = same)
        similarity = 1.0 - min(diff / max_val, 1.0)
        return similarity
    
    def _compute_source_agreement(self, feat_a: FeatureVector, feat_b: FeatureVector) -> Optional[float]:
        """Compute source trust agreement"""
        trust_a = feat_a.source_features.source_trust_score
        trust_b = feat_b.source_features.source_trust_score
        
        # Average of the two trust scores
        return (trust_a + trust_b) / 2.0


def compute_all_similarities(
    features: Dict[str, FeatureVector],
    config: EntityResolutionConfig,
    min_threshold: float = 0.5
) -> List[SimilarityVector]:
    """
    Convenience function to compute all pairwise similarities
    
    Args:
        features: Feature vectors
        config: Configuration
        min_threshold: Minimum similarity threshold
        
    Returns:
        List of similarity vectors
    """
    computer = SimilarityComputer(config)
    return computer.compute_pairwise(features, min_threshold)
