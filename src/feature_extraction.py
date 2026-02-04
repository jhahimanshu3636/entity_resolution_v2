"""
Feature Extraction Module
=========================

Deterministic feature extraction from records for entity resolution.
Stage 1 of the entity resolution pipeline.

Features:
- Text features (name, address tokenization, n-grams)
- Numeric features (account age, transaction metrics)
- Categorical features (device OS, payment methods)
- Text embeddings (SBERT for semantic similarity)
- Source features (trust scores, reputation)

Author: Entity Resolution System
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import sys
sys.path.append('..')

from data_models import Record, FeatureVector, TextFeatures, NumericFeatures, CategoricalFeatures, Embeddings, SourceFeatures, DeviceOS
from utils import normalize_string, tokenize, generate_ngrams, normalize_email, normalize_phone, get_logger, StageLogger
from config import EntityResolutionConfig

# Try to import sentence transformers (optional)
try:
    from sentence_transformers import SentenceTransformer
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False
    print("Warning: sentence-transformers not available. Text embeddings will be disabled.")


logger = get_logger(__name__)


class FeatureExtractor:
    """
    Deterministic feature extraction from records
    
    Ensures:
    - Same input → same output (determinism)
    - Cacheable transformations
    - Structured feature representation
    """
    
    def __init__(self, config: EntityResolutionConfig, enable_embeddings: bool = True):
        """
        Initialize feature extractor
        
        Args:
            config: Entity resolution configuration
            enable_embeddings: Whether to use text embeddings (requires sentence-transformers)
        """
        self.config = config
        self.enable_embeddings = enable_embeddings and SBERT_AVAILABLE
        
        # Initialize text embedding model if enabled
        self.embedding_model = None
        if self.enable_embeddings:
            try:
                # Use lightweight model for speed
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("feature_extractor_initialized", embedding_model="all-MiniLM-L6-v2")
            except Exception as e:
                logger.warning("failed_to_load_embedding_model", error=str(e))
                self.enable_embeddings = False
    
    def extract_features(self, records: List[Record]) -> Dict[str, FeatureVector]:
        """
        Extract features from all records in a block
        
        Args:
            records: List of input records
            
        Returns:
            Dictionary mapping record_id to FeatureVector
        """
        features = {}
        
        for record in records:
            feature_vector = self.extract_single(record)
            features[record.record_id] = feature_vector
        
        logger.info(
            "features_extracted",
            num_records=len(records),
            embeddings_enabled=self.enable_embeddings
        )
        
        return features
    
    def extract_single(self, record: Record) -> FeatureVector:
        """
        Extract features from a single record
        
        Args:
            record: Input record
            
        Returns:
            Complete feature vector
        """
        attrs = record.attributes
        metadata = record.metadata
        
        # Extract text features
        text_features = self._extract_text_features(attrs)
        
        # Extract numeric features
        numeric_features = self._extract_numeric_features(attrs)
        
        # Extract categorical features
        categorical_features = self._extract_categorical_features(attrs)
        
        # Extract embeddings
        embeddings = self._extract_embeddings(attrs, text_features)
        
        # Extract source features
        source_features = self._extract_source_features(metadata, attrs)
        
        return FeatureVector(
            record_id=record.record_id,
            text_features=text_features,
            numeric_features=numeric_features,
            categorical_features=categorical_features,
            embeddings=embeddings,
            source_features=source_features
        )
    
    def _extract_text_features(self, attrs: Dict[str, Any]) -> TextFeatures:
        """Extract text-based features"""
        
        # Name tokenization
        name = attrs.get('name', attrs.get('full_name', ''))
        name_tokens = tokenize(name) if name else []
        
        # Address tokenization
        address = attrs.get('address', '')
        address_tokens = tokenize(address) if address else []
        
        # Generate n-grams for fuzzy matching
        ngrams = []
        if name:
            ngrams.extend(list(generate_ngrams(name, n=3)))
        
        return TextFeatures(
            name_tokens=name_tokens,
            address_tokens=address_tokens,
            ngrams=ngrams
        )
    
    def _extract_numeric_features(self, attrs: Dict[str, Any]) -> NumericFeatures:
        """Extract numeric features"""
        
        # Account age calculation
        account_age_days = None
        if 'registration_timestamp' in attrs or 'account_created_at' in attrs:
            reg_timestamp = attrs.get('registration_timestamp') or attrs.get('account_created_at')
            if isinstance(reg_timestamp, str):
                try:
                    from dateutil.parser import parse
                    reg_date = parse(reg_timestamp)
                    account_age_days = (datetime.utcnow() - reg_date).days
                except Exception:
                    pass
            elif isinstance(reg_timestamp, datetime):
                account_age_days = (datetime.utcnow() - reg_timestamp).days
        
        return NumericFeatures(
            account_age_days=account_age_days,
            transaction_count=attrs.get('transaction_count'),
            avg_transaction_amount=attrs.get('avg_transaction_amount'),
            transaction_velocity_24h=attrs.get('transaction_velocity_24h')
        )
    
    def _extract_categorical_features(self, attrs: Dict[str, Any]) -> CategoricalFeatures:
        """Extract categorical features"""
        
        # Device OS mapping
        device_os = None
        device_os_str = attrs.get('device_os', attrs.get('os'))
        if device_os_str:
            device_os_str = device_os_str.lower()
            if 'ios' in device_os_str or 'iphone' in device_os_str:
                device_os = DeviceOS.IOS
            elif 'ipad' in device_os_str:
                device_os = DeviceOS.IPADOS
            elif 'android' in device_os_str:
                device_os = DeviceOS.ANDROID
            elif 'web' in device_os_str or 'browser' in device_os_str:
                device_os = DeviceOS.WEB
            else:
                device_os = DeviceOS.UNKNOWN
        
        # Transaction frequency categorization
        tx_freq = None
        if attrs.get('transaction_velocity_24h'):
            velocity = attrs['transaction_velocity_24h']
            if velocity < 1:
                tx_freq = 'low'
            elif velocity < 5:
                tx_freq = 'medium'
            else:
                tx_freq = 'high'
        
        return CategoricalFeatures(
            device_os=device_os,
            transaction_frequency_category=tx_freq,
            payment_method=attrs.get('payment_method')
        )
    
    def _extract_embeddings(self, attrs: Dict[str, Any], text_features: TextFeatures) -> Embeddings:
        """Extract embedding vectors"""
        
        text_embedding = None
        
        if self.enable_embeddings and self.embedding_model:
            # Create a combined text representation
            text_parts = []
            
            # Add name
            if 'name' in attrs or 'full_name' in attrs:
                text_parts.append(attrs.get('name', attrs.get('full_name', '')))
            
            # Add email domain (not full email for privacy)
            if 'email' in attrs:
                email = attrs['email']
                if '@' in email:
                    domain = email.split('@')[1]
                    text_parts.append(domain)
            
            # Add address
            if 'address' in attrs:
                text_parts.append(attrs['address'])
            
            if text_parts:
                combined_text = ' '.join(text_parts)
                try:
                    # Generate embedding
                    embedding_array = self.embedding_model.encode(
                        combined_text,
                        convert_to_numpy=True,
                        show_progress_bar=False
                    )
                    text_embedding = embedding_array.tolist()
                except Exception as e:
                    logger.warning("embedding_generation_failed", error=str(e))
        
        return Embeddings(text_embedding=text_embedding)
    
    def _extract_source_features(self, metadata, attrs: Dict[str, Any]) -> SourceFeatures:
        """Extract source and trust features"""
        
        return SourceFeatures(
            source_trust_score=metadata.trust_score,
            ip_reputation_score=attrs.get('ip_reputation_score'),
            vpn_detected=attrs.get('vpn_flag', attrs.get('vpn_detected', False))
        )


def extract_features_from_block(
    records: List[Record],
    config: EntityResolutionConfig,
    enable_embeddings: bool = True
) -> Dict[str, FeatureVector]:
    """
    Convenience function to extract features from a block
    
    Args:
        records: List of records
        config: Configuration
        enable_embeddings: Whether to use embeddings
        
    Returns:
        Feature vectors by record ID
    """
    extractor = FeatureExtractor(config, enable_embeddings)
    return extractor.extract_features(records)
