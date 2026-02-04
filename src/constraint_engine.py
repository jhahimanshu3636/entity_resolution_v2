"""
Constraint Engine Module
========================

Stage 4 of the entity resolution pipeline.
Applies hard and soft constraints to validate edges.

CRITICAL: Executes BEFORE embeddings or clustering.

Hard Constraints: Remove edges completely
Soft Constraints: Penalize edge weights

Author: Entity Resolution System
"""

from typing import Dict, List, Tuple, Optional
import networkx as nx
from datetime import datetime, timedelta
import sys
sys.path.append('..')

from data_models import FeatureVector, GraphEdge, DeviceOS
from utils import get_logger, log_constraint_violation, haversine_distance
from config import EntityResolutionConfig, HardConstraintConfig, SoftConstraintConfig


logger = get_logger(__name__)


class ConstraintEngine:
    """
    Validates and penalizes edges based on domain constraints
    
    Prevents invalid entity merges and reduces confidence for suspicious links.
    """
    
    def __init__(self, config: EntityResolutionConfig):
        """
        Initialize constraint engine
        
        Args:
            config: Entity resolution configuration
        """
        self.config = config
        self.hard_constraints = config.get_hard_constraints()
        self.soft_constraints = config.get_soft_constraints()
    
    def apply_constraints(
        self,
        G: nx.Graph,
        features: Dict[str, FeatureVector]
    ) -> nx.Graph:
        """
        Apply all constraints to graph
        
        Args:
            G: Input graph
            features: Feature vectors for constraint logic
            
        Returns:
            Graph with constraints applied
        """
        # Apply hard constraints (edge removal)
        G = self._apply_hard_constraints(G, features)
        
        # Apply soft constraints (edge penalization)
        G = self._apply_soft_constraints(G, features)
        
        return G
    
    def _apply_hard_constraints(
        self,
        G: nx.Graph,
        features: Dict[str, FeatureVector]
    ) -> nx.Graph:
        """Apply hard constraints - remove violating edges"""
        
        edges_to_remove = []
        
        for u, v in list(G.edges()):
            feat_a = features[u]
            feat_b = features[v]
            edge_data = G[u][v]['edge_data']
            
            # Check each hard constraint
            for constraint in self.hard_constraints:
                violated, reason = self._check_hard_constraint(
                    constraint,
                    feat_a,
                    feat_b
                )
                
                if violated:
                    edges_to_remove.append((u, v))
                    edge_data.is_valid = False
                    edge_data.constraints_applied.append(constraint.name)
                    
                    log_constraint_violation(
                        logger,
                        constraint_type="hard",
                        constraint_name=constraint.name,
                        edge=(u, v),
                        reason=reason
                    )
                    break  # One violation is enough to remove edge
        
        # Remove invalid edges
        G.remove_edges_from(edges_to_remove)
        
        logger.info(
            "hard_constraints_applied",
            edges_removed=len(edges_to_remove),
            remaining_edges=G.number_of_edges()
        )
        
        return G
    
    def _apply_soft_constraints(
        self,
        G: nx.Graph,
        features: Dict[str, FeatureVector]
    ) -> nx.Graph:
        """Apply soft constraints - penalize edge weights"""
        
        penalized_count = 0
        
        for u, v in G.edges():
            feat_a = features[u]
            feat_b = features[v]
            edge_data = G[u][v]['edge_data']
            current_weight = G[u][v]['weight']
            
            total_penalty = 0.0
            
            # Check each soft constraint
            for constraint in self.soft_constraints:
                violated, reason = self._check_soft_constraint(
                    constraint,
                    feat_a,
                    feat_b
                )
                
                if violated:
                    total_penalty += constraint.penalty
                    edge_data.constraints_applied.append(constraint.name)
                    penalized_count += 1
                    
                    log_constraint_violation(
                        logger,
                        constraint_type="soft",
                        constraint_name=constraint.name,
                        edge=(u, v),
                        reason=reason,
                        penalty=constraint.penalty
                    )
            
            # Apply penalty (multiplicative reduction)
            if total_penalty > 0:
                new_weight = current_weight * (1.0 - min(total_penalty, 0.9))  # Cap at 90% reduction
                G[u][v]['weight'] = new_weight
        
        logger.info(
            "soft_constraints_applied",
            edges_penalized=penalized_count
        )
        
        return G
    
    def _check_hard_constraint(
        self,
        constraint: HardConstraintConfig,
        feat_a: FeatureVector,
        feat_b: FeatureVector
    ) -> Tuple[bool, str]:
        """
        Check if a hard constraint is violated
        
        Returns:
            (violated, reason)
        """
        # Implement constraint logic based on constraint name
        
        if constraint.name == "conflicting_verified_identity":
            # Different verified KYC identities
            # Note: In production, these would come from record attributes
            # For now, return False (not violated)
            return False, ""
        
        elif constraint.name == "conflicting_bank_ownership":
            # Different verified bank account owners
            return False, ""
        
        elif constraint.name == "impossible_geolocation":
            #  Cannot be in two distant locations within short timeframe
            # Note: Would need geolocation and timestamp data
            return False, ""
        
        elif constraint.name == "conflicting_device_os":
            # Different OS families in short time window
            os_a = feat_a.categorical_features.device_os
            os_b = feat_b.categorical_features.device_os
            
            if os_a and os_b and os_a != os_b:
                # iOS/iPadOS vs Android conflict
                if (os_a in [DeviceOS.IOS, DeviceOS.IPADOS] and os_b == DeviceOS.ANDROID) or \
                   (os_b in [DeviceOS.IOS, DeviceOS.IPADOS] and os_a == DeviceOS.ANDROID):
                    return True, f"Conflicting OS families: {os_a} vs {os_b}"
            
            return False, ""
        
        elif constraint.name == "fraud_contamination":
            # Confirmed fraud cannot merge with legitimate user
            # Note: Would need fraud flags from metadata
            return False, ""
        
        return False, ""
    
    def _check_soft_constraint(
        self,
        constraint: SoftConstraintConfig,
        feat_a: FeatureVector,
        feat_b: FeatureVector
    ) -> Tuple[bool, str]:
        """
        Check if a soft constraint is violated
        
        Returns:
            (violated, reason)
        """
        if constraint.name == "low_source_trust":
            # Low source trust score
            trust_a = feat_a.source_features.source_trust_score
            trust_b = feat_b.source_features.source_trust_score
            
            if trust_a < 0.5 or trust_b < 0.5:
                return True, f"Low source trust: {trust_a:.2f}, {trust_b:.2f}"
            
            return False, ""
        
        elif constraint.name == "account_age_mismatch":
            # Large age difference between accounts
            age_a = feat_a.numeric_features.account_age_days
            age_b = feat_b.numeric_features.account_age_days
            
            if age_a and age_b:
                age_diff = abs(age_a - age_b)
                if age_diff > 365:
                    return True, f"Account age mismatch: {age_diff} days"
            
            return False, ""
        
        elif constraint.name == "vpn_proxy_usage":
            # VPN/Proxy detected
            vpn_a = feat_a.source_features.vpn_detected
            vpn_b = feat_b.source_features.vpn_detected
            
            if vpn_a or vpn_b:
                return True, "VPN/Proxy detected"
            
            return False, ""
        
        elif constraint.name == "behavioral_mismatch":
            # Very different transaction behaviors
            avg_amt_a = feat_a.numeric_features.avg_transaction_amount
            avg_amt_b = feat_b.numeric_features.avg_transaction_amount
            
            if avg_amt_a and avg_amt_b:
                diff = abs(avg_amt_a - avg_amt_b)
                if diff > 1000:
                    return True, f"Behavioral mismatch: ${diff:.2f} difference in avg transaction"
            
            return False, ""
        
        elif constraint.name == "low_ip_reputation":
            # Low IP reputation scores
            ip_rep_a = feat_a.source_features.ip_reputation_score
            ip_rep_b = feat_b.source_features.ip_reputation_score
            
            if ip_rep_a and ip_rep_a < 0.3:
                return True, f"Low IP reputation: {ip_rep_a:.2f}"
            if ip_rep_b and ip_rep_b < 0.3:
                return True, f"Low IP reputation: {ip_rep_b:.2f}"
            
            return False, ""
        
        return False, ""


def apply_entity_constraints(
    G: nx.Graph,
    features: Dict[str, FeatureVector],
    config: EntityResolutionConfig
) -> nx.Graph:
    """
    Convenience function to apply constraints
    
    Args:
        G: Graph
        features: Feature vectors
        config: Configuration
        
    Returns:
        Graph with constraints applied
    """
    engine = ConstraintEngine(config)
    return engine.apply_constraints(G, features)
