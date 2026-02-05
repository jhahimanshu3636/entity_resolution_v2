"""
Test Pipeline with Embeddings Enabled
=====================================

Run the full pipeline with graph embeddings enabled
to compare accuracy improvements.
"""

import sys
sys.path.append('../src')

from pipeline import EntityResolutionPipeline
from config import load_config
from data_models import BlockInput, Record, RecordMetadata
from datetime import datetime, timedelta
import random
import time


def generate_test_block() -> BlockInput:
    """Generate test block with known fraud patterns"""
    
    records = []
    record_id = 1
    
    # Fraud Ring 1: Multi-accounting (5 accounts, shared device)
    base_device = "device_fraud_shared_001"
    base_ip = "10.0.1.100"
    
    for i in range(5):
        records.append(Record(
            record_id=f"FRAUD_RING_1_{i+1}",
            attributes={
                "name": f"Fraud User 1 Variation {i}",
                "email": f"fraud1_{i}@tempmail.com",
                "phone": f"+1555{i:07d}",
                "address": "123 Fraud St City ST",
                "device_fingerprint": base_device,  # SHARED
                "device_os": "iOS",
                "ip_address": base_ip,  # SHARED
                "avg_transaction_amount": 50.0 + i,
                "transaction_count": 10 + i,
                "account_age_days": i
            },
            metadata=RecordMetadata(
                source="registration_db",
                timestamp=datetime.utcnow() - timedelta(days=i),
                trust_score=0.7
            )
        ))
    
    # Legitimate User with 2 devices
    records.extend([
        Record(
            record_id="LEGIT_MOBILE",
            attributes={
                "name": "John Smith",
                "email": "john.smith@gmail.com",
                "phone": "+15551234567",
                "address": "456 Main St City ST",
                "device_fingerprint": "device_john_iphone",
                "device_os": "iOS",
                "ip_address": "192.168.1.10",
                "avg_transaction_amount": 100.0,
                "transaction_count": 50,
                "account_age_days": 365
            },
            metadata=RecordMetadata(
                source="mobile_app",
                timestamp=datetime.utcnow() - timedelta(days=365),
                trust_score=1.0,
                kyc_verified=True
            )
        ),
        Record(
            record_id="LEGIT_WEB",
            attributes={
                "name": "John Smith",
                "email": "john.smith@gmail.com",
                "phone": "+15551234567",
                "address": "456 Main St City ST",
                "device_fingerprint": "device_john_laptop",
                "device_os": "Web",
                "ip_address": "192.168.1.11",
                "avg_transaction_amount": 105.0,
                "transaction_count": 30,
                "account_age_days": 365
            },
            metadata=RecordMetadata(
                source="web_app",
                timestamp=datetime.utcnow() - timedelta(days=200),
                trust_score=1.0,
                kyc_verified=True
            )
        )
    ])
    
    # Clean singletons
    for i in range(10):
        records.append(Record(
            record_id=f"CLEAN_{i+1}",
            attributes={
                "name": f"Clean User {i}",
                "email": f"clean{i}@example.com",
                "phone": f"+1444{i:07d}",
                "address": f"{1000 + i * 10} Clean St City ST",
                "device_fingerprint": f"device_clean_{i}",
                "device_os": random.choice(["iOS", "Android", "Web"]),
                "ip_address": f"192.0.2.{i+1}",
                "avg_transaction_amount": random.uniform(50, 150),
                "transaction_count": random.randint(10, 50),
                "account_age_days": random.randint(100, 500)
            },
            metadata=RecordMetadata(
                source="registration_db",
                timestamp=datetime.utcnow() - timedelta(days=random.randint(100, 500)),
                trust_score=random.uniform(0.85, 1.0)
            )
        ))
    
    return BlockInput(
        block_id="embeddings_test_block",
        records=records
    )


def main():
    print("=" * 80)
    print("PIPELINE COMPARISON: WITHOUT vs WITH EMBEDDINGS")
    print("=" * 80)
    print()
    
    # Generate test data
    block = generate_test_block()
    print(f"Test data: {len(block.records)} records")
    print()
    
    # Load config
    config = load_config("p2p_payment_resolution")
    
    # Test 1: WITHOUT embeddings
    print("-" * 80)
    print("TEST 1: Pipeline WITHOUT Embeddings")
    print("-" * 80)
    print()
    
    pipeline1 = EntityResolutionPipeline(config=config, enable_embeddings=False)
    start = time.time()
    artifacts1 = pipeline1.resolve_entities(block)
    time1 = time.time() - start
    
    print(f"✓ Completed in {time1:.3f}s")
    print(f"  - Input: {len(block.records)} records")
    print(f"  - Output: {len(artifacts1.entities)} entities")
    print(f"  - Reduction: {len(block.records) - len(artifacts1.entities)} records merged")
    print(f"  - Avg confidence: {sum(e.confidence for e in artifacts1.entities) / len(artifacts1.entities):.3f}")
    print()
    
    # Test 2: WITH embeddings
    print("-" * 80)
    print("TEST 2: Pipeline WITH Embeddings (FastRP)")
    print("-" * 80)
    print()
    
    pipeline2 = EntityResolutionPipeline(config=config, enable_embeddings=True)
    start = time.time()
    artifacts2 = pipeline2.resolve_entities(block)
    time2 = time.time() - start
    
    print(f"✓ Completed in {time2:.3f}s")
    print(f"  - Input: {len(block.records)} records")
    print(f"  - Output: {len(artifacts2.entities)} entities")
    print(f"  - Reduction: {len(block.records) - len(artifacts2.entities)} records merged")
    print(f"  - Avg confidence: {sum(e.confidence for e in artifacts2.entities) / len(artifacts2.entities):.3f}")
    print()
    
    # Comparison
    print("=" * 80)
    print("COMPARISON")
    print("=" * 80)
    print()
    
    print(f"Processing time:")
    print(f"  - Without embeddings: {time1:.3f}s")
    print(f"  - With embeddings:    {time2:.3f}s")
    print(f"  - Overhead:           {time2 - time1:.3f}s ({((time2-time1)/time1*100):.1f}%)")
    print()
    
    print(f"Entity count:")
    print(f"  - Without embeddings: {len(artifacts1.entities)} entities")
    print(f"  - With embeddings:    {len(artifacts2.entities)} entities")
    print(f"  - Difference:         {len(artifacts1.entities) - len(artifacts2.entities)}")
    print()
    
    avg_conf1 = sum(e.confidence for e in artifacts1.entities) / len(artifacts1.entities)
    avg_conf2 = sum(e.confidence for e in artifacts2.entities) / len(artifacts2.entities)
    
    print(f"Average confidence:")
    print(f"  - Without embeddings: {avg_conf1:.4f}")
    print(f"  - With embeddings:    {avg_conf2:.4f}")
    print(f"  - Improvement:        {avg_conf2 - avg_conf1:+.4f}")
    print()
    
    # Check fraud ring detection
    fraud_ring_entities_1 = [e for e in artifacts1.entities if any('FRAUD_RING' in r for r in e.records)]
    fraud_ring_entities_2 = [e for e in artifacts2.entities if any('FRAUD_RING' in r for r in e.records)]
    
    print(f"Fraud ring detection:")
    print(f"  - Without embeddings: {len(fraud_ring_entities_1)} entities (expected: 1)")
    print(f"  - With embeddings:    {len(fraud_ring_entities_2)} entities (expected: 1)")
    
    if fraud_ring_entities_1:
        print(f"    └─ Size: {len(fraud_ring_entities_1[0].records)} records, conf: {fraud_ring_entities_1[0].confidence:.3f}")
    
    if fraud_ring_entities_2:
        print(f"    └─ Size: {len(fraud_ring_entities_2[0].records)} records, conf: {fraud_ring_entities_2[0].confidence:.3f}")
    
    print()
    print("=" * 80)
    print("✅ EMBEDDINGS TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
