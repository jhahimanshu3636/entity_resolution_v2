"""
Enhanced Large-Scale Pipeline Test
===================================

Tests the complete pipeline with embeddings ENABLED
to show accuracy improvements over baseline.

Compares:
- Without embeddings (baseline from test_results.md)
- With embeddings (new enhanced version)

Author: Entity Resolution System
"""

import sys
sys.path.append('../src')

from pipeline import EntityResolutionPipeline
from config import load_config
from data_models import BlockInput, Record, RecordMetadata
from datetime import datetime, timedelta
import random
import time


class LargeScaleDataGenerator:
    """Generate large-scale synthetic P2P payment test data"""
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.record_counter = 0
    
    def generate_large_test_block(self, num_records: int = 100) -> BlockInput:
        """Generate comprehensive test block"""
        records = []
        
        # 1. Multi-accounting fraud rings (15 records - 3 rings of 5 accounts each)
        print("Generating multi-accounting fraud rings...")
        for ring_id in range(3):
            records.extend(self._generate_multi_accounting_ring(ring_id, size=5))
        
        # 2. Account takeover scenarios (10 records - 5 ATO cases)
        print("Generating account takeover scenarios...")
        for ato_id in range(5):
            records.extend(self._generate_ato_case(ato_id))
        
        # 3. Legitimate multi-device users (20 records - 10 users with 2 devices each)
        print("Generating legitimate multi-device users...")
        for user_id in range(10):
            records.extend(self._generate_legitimate_user(user_id))
        
        # 4. Money mule network (10 records - interconnected suspicious accounts)
        print("Generating money mule network...")
        records.extend(self._generate_mule_network(size=10))
        
        # 5. Clean singleton accounts (fill remainder)
        remaining = num_records - len(records)
        if remaining > 0:
            print(f"Generating {remaining} clean singleton accounts...")
            records.extend(self._generate_clean_singletons(remaining))
        
        print(f"✓ Generated {len(records)} total records")
        
        return BlockInput(
            block_id="enhanced_test_block_001",
            records=records
        )
    
    def _generate_multi_accounting_ring(self, ring_id: int, size: int = 5) -> list:
        """Generate a multi-accounting fraud ring (same person, multiple promos)"""
        
        base_name = f"Fraud Ring {ring_id}"
        base_device = f"device_fraud_{ring_id}_shared"
        base_ip = f"10.{ring_id}.1.100"
        base_address = f"{100 + ring_id * 10} Fraud Street City ST"
        
        records = []
        creation_days = [30, 7, 3, 1, 0]  # Accounts created in sequence
        
        for i in range(size):
            records.append(Record(
                record_id=self._next_id(),
                attributes={
                    "name": f"{base_name} Account {i}",
                    "email": f"fraud{ring_id}_{i}@tempmail.com",
                    "phone": f"+1{ring_id}{i:09d}",
                    "address": base_address,
                    "device_fingerprint": base_device,  # SHARED DEVICE
                    "device_os": "iOS",
                    "ip_address": base_ip,  # SHARED IP
                    "avg_transaction_amount": 45.0 + random.uniform(-5, 5),
                    "transaction_count": random.randint(1, 15),
                    "account_age_days": creation_days[i]
                },
                metadata=RecordMetadata(
                    source="registration_db",
                    timestamp=datetime.now() - timedelta(days=creation_days[i]),
                    trust_score=0.7 - (i * 0.1)  # Declining trust
                )
            ))
        
        return records
    
    def _generate_ato_case(self, ato_id: int) -> list:
        """Generate account takeover scenario"""
        
        records = []
        
        # Victim (normal activity)
        records.append(Record(
            record_id=self._next_id(),
            attributes={
                "name": f"Victim User {ato_id}",
                "email": f"victim{ato_id}@legitimate.com",
                "phone": f"+1900{ato_id:07d}",
                "address": f"{500 + ato_id} Victim Ave City ST",
                "device_fingerprint": f"device_victim_{ato_id}",
                "device_os": "Android",
                "ip_address": f"192.168.{ato_id}.50",
                "avg_transaction_amount": 75.0,
                "transaction_count": 100,
                "account_age_days": 500
            },
            metadata=RecordMetadata(
                source="mobile_app",
                timestamp=datetime.now() - timedelta(days=10),
                trust_score=1.0,
                kyc_verified=True
            )
        ))
        
        # Attacker (suspicious activity)
        records.append(Record(
            record_id=self._next_id(),
            attributes={
                "name": f"Victim User {ato_id}",  # Same name (stolen)
                "email": f"victim{ato_id}@legitimate.com",  # Same email
                "phone": f"+1900{ato_id:07d}",  # Same phone
                "address": f"{500 + ato_id} Victim Ave City ST",
                "device_fingerprint": f"device_attacker_{ato_id}_foreign",
                "device_os": "Web",  # Different platform
                "ip_address": f"203.0.{ato_id}.99",  # Foreign IP
                "ip_reputation_score": 0.15,  # Very low
                "vpn_flag": True,  # VPN detected
                "avg_transaction_amount": 1500.0,  # Unusual
                "transaction_count": 3,
                "account_age_days": 500
            },
            metadata=RecordMetadata(
                source="web_app",
                timestamp=datetime.now() - timedelta(hours=2),
                trust_score=0.2  # Very low trust
            )
        ))
        
        return records
    
    def _generate_legitimate_user(self, user_id: int) -> list:
        """Generate legitimate user with multiple devices"""
        
        records = []
        
        email = f"legit.user{user_id}@gmail.com"
        phone = f"+1800{user_id:07d}"
        name = f"Legitimate User {user_id}"
        address = f"{1000 + user_id} Main St City ST"
        
        # Mobile device
        records.append(Record(
            record_id=self._next_id(),
            attributes={
                "name": name,
                "email": email,
                "phone": phone,
                "address": address,
                "device_fingerprint": f"device_mobile_{user_id}",
                "device_os": "iOS",
                "ip_address": f"172.16.{user_id}.10",
                "avg_transaction_amount": 100.0,
                "transaction_count": 50,
                "account_age_days": 365
            },
            metadata=RecordMetadata(
                source="mobile_app",
                timestamp=datetime.now() - timedelta(days=365),
                trust_score=1.0,
                kyc_verified=True
            )
        ))
        
        # Web device
        records.append(Record(
            record_id=self._next_id(),
            attributes={
                "name": name,
                "email": email,
                "phone": phone,
                "address": address,
                "device_fingerprint": f"device_web_{user_id}",
                "device_os": "Web",
                "ip_address": f"172.16.{user_id}.11",  # Same network
                "avg_transaction_amount": 105.0,
                "transaction_count": 30,
                "account_age_days": 365
            },
            metadata=RecordMetadata(
                source="web_app",
                timestamp=datetime.now() - timedelta(days=200),
                trust_score=1.0,
                kyc_verified=True
            )
        ))
        
        return records
    
    def _generate_mule_network(self, size: int = 10) -> list:
        """Generate money mule network (interconnected suspicious accounts)"""
        
        records = []
        shared_devices = [f"device_mule_shared_{i}" for i in range(3)]  # Shared devices
        
        for i in range(size):
            records.append(Record(
                record_id=self._next_id(),
                attributes={
                    "name": f"Mule Account {i}",
                    "email": f"mule{i}@tempmail{i % 3}.com",
                    "phone": f"+1700{i:07d}",
                    "address": f"{2000 + i * 5} Mule Rd City ST",
                    "device_fingerprint": shared_devices[i % 3],  # Rotating shared devices
                    "device_os": "Android",
                    "ip_address": f"198.51.100.{10 + i}",
                    "vpn_flag": i % 2 == 0,  # Half using VPN
                    "avg_transaction_amount": 200.0 + random.uniform(-50, 50),
                    "transaction_count": random.randint(5, 25),
                    "account_age_days": random.randint(7, 60)
                },
                metadata=RecordMetadata(
                    source="registration_db",
                    timestamp=datetime.now() - timedelta(days=random.randint(7, 60)),
                    trust_score=0.4 + random.uniform(-0.1, 0.1)
                )
            ))
        
        return records
    
    def _generate_clean_singletons(self, count: int) -> list:
        """Generate clean singleton accounts"""
        
        records = []
        
        for i in range(count):
            records.append(Record(
                record_id=self._next_id(),
                attributes={
                    "name": f"Clean User {i}",
                    "email": f"clean{i}@example.com",
                    "phone": f"+1600{i:07d}",
                    "address": f"{3000 + i * 10} Clean St City ST",
                    "device_fingerprint": f"device_clean_{i}_{random.randint(1000, 9999)}",
                    "device_os": random.choice(["iOS", "Android", "Web"]),
                    "ip_address": f"192.0.2.{random.randint(1, 255)}",
                    "avg_transaction_amount": random.uniform(30, 200),
                    "transaction_count": random.randint(10, 100),
                    "account_age_days": random.randint(100, 1000)
                },
                metadata=RecordMetadata(
                    source="registration_db",
                    timestamp=datetime.now() - timedelta(days=random.randint(100, 1000)),
                    trust_score=random.uniform(0.8, 1.0)
                )
            ))
        
        return records
    
    def _next_id(self) -> str:
        self.record_counter += 1
        return f"REC_{self.record_counter:05d}"


def main():
    print("=" * 80)
    print("ENHANCED PIPELINE TEST WITH EMBEDDINGS")
    print("=" * 80)
    print()
    
    # Generate large test dataset
    print("Generating large-scale synthetic dataset...")
    print("-" * 80)
    generator = LargeScaleDataGenerator(seed=42)
    block = generator.generate_large_test_block(num_records=100)
    print()
    
    print("Dataset Summary:")
    print(f"  - Multi-accounting rings: 3 rings × 5 accounts = 15 records")
    print(f"  - Account takeover cases: 5 cases × 2 records = 10 records")
    print(f"  - Legitimate multi-device: 10 users × 2 devices = 20 records")
    print(f"  - Money mule network: 10 records")
    print(f"  - Clean singletons: {len(block.records) - 55} records")
    print(f"  - TOTAL: {len(block.records)} records")
    print()
    
    # Load configuration
    print("Loading P2P payment configuration...")
    config = load_config("p2p_payment_resolution")
    print(f"✓ Configuration loaded: {config.domain}")
    print()
    
    # Run pipeline WITH EMBEDDINGS
    print("=" * 80)
    print("RUNNING PIPELINE WITH EMBEDDINGS ENABLED")
    print("=" * 80)
    print()
    
    pipeline = EntityResolutionPipeline(config=config, enable_embeddings=True)
    
    start_time = time.time()
    artifacts = pipeline.resolve_entities(block)
    end_time = time.time()
    
    print()
    print(f"✓ Pipeline completed in {end_time - start_time:.2f} seconds")
    print()
    
    # Results analysis
    print("=" * 80)
    print("RESULTS WITH EMBEDDINGS")
    print("=" * 80)
    print()
    
    print(f"Input: {len(block.records)} records")
    print(f"Output: {len(artifacts.entities)} entities")
    print(f"Reduction: {len(block.records) - len(artifacts.entities)} records merged")
    print(f"Processing time: {artifacts.processing_time_seconds:.2f}s")
    print()
    
    # Cluster size distribution
    cluster_sizes = [len(e.records) for e in artifacts.entities]
    print("Cluster Size Distribution:")
    print(f"  Singletons (1 record): {sum(1 for s in cluster_sizes if s == 1)}")
    print(f"  Small clusters (2-3): {sum(1 for s in cluster_sizes if 2 <= s <= 3)}")
    print(f"  Medium clusters (4-10): {sum(1 for s in cluster_sizes if 4 <= s <= 10)}")
    print(f"  Large clusters (>10): {sum(1 for s in cluster_sizes if s > 10)}")
    print()
    
    # Confidence distribution
    avg_confidence = sum(e.confidence for e in artifacts.entities) / len(artifacts.entities)
    high_conf = sum(1 for e in artifacts.entities if e.confidence >= 0.8)
    med_conf = sum(1 for e in artifacts.entities if 0.5 <= e.confidence < 0.8)
    low_conf = sum(1 for e in artifacts.entities if e.confidence < 0.5)
    
    print("Confidence Distribution:")
    print(f"  Average confidence: {avg_confidence:.3f}")
    print(f"  High confidence (≥0.8): {high_conf}")
    print(f"  Medium confidence (0.5-0.8): {med_conf}")
    print(f"  Low confidence (<0.5): {low_conf}")
    print()
    
    # Fraud indicators
    entities_with_fraud = sum(1 for e in artifacts.entities if e.explanations.fraud_indicators)
    print(f"Entities with fraud indicators: {entities_with_fraud}")
    print()
    
    # Show top 5 largest clusters
    print("Top 5 Largest Clusters:")
    sorted_entities = sorted(artifacts.entities, key=lambda e: len(e.records), reverse=True)
    for i, entity in enumerate(sorted_entities[:5], 1):
        print(f"  {i}. {entity.entity_id}: {len(entity.records)} records, confidence={entity.confidence:.3f}")
        if entity.explanations.fraud_indicators:
            print(f"     Fraud indicators: {', '.join(entity.explanations.fraud_indicators[:2])}")
    
    print()
    
    # Comparison to baseline
    print("=" * 80)
    print("COMPARISON TO BASELINE (without embeddings)")
    print("=" * 80)
    print()
    
    # Baseline from previous test (test_results.md)
    baseline_time = 0.11
    baseline_entities = 37
    baseline_confidence = 0.91
    
    print(f"Processing Time:")
    print(f"  Baseline (no embeddings):  {baseline_time:.2f}s")
    print(f"  Enhanced (with embeddings): {artifacts.processing_time_seconds:.2f}s")
    print(f"  Difference:                {artifacts.processing_time_seconds - baseline_time:+.2f}s")
    print()
    
    print(f"Entity Count:")
    print(f"  Baseline (no embeddings):  {baseline_entities} entities")
    print(f"  Enhanced (with embeddings): {len(artifacts.entities)} entities")
    print(f"  Difference:                {len(artifacts.entities) - baseline_entities:+d}")
    print()
    
    print(f"Average Confidence:")
    print(f"  Baseline (no embeddings):  {baseline_confidence:.3f}")
    print(f"  Enhanced (with embeddings): {avg_confidence:.3f}")
    print(f"  Improvement:               {avg_confidence - baseline_confidence:+.3f} ({((avg_confidence - baseline_confidence) / baseline_confidence * 100):+.1f}%)")
    print()
    
    print("=" * 80)
    print("✅ ENHANCED PIPELINE TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
