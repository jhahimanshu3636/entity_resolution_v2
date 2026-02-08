"""
Large-Scale Pipeline Test: 10,000 Records
=========================================

Comprehensive test with 10k synthetic P2P payment records.
Tests scalability, performance, and fraud detection at scale.

Generates data, runs pipeline, saves results for analysis.

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
import json
import pickle


class MassiveDataGenerator:
    """Generate large-scale synthetic P2P payment test data"""
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.record_counter = 0
    
    def generate_massive_block(self, num_records: int = 10000) -> BlockInput:
        """
        Generate massive test block
        
        Distribution:
        - 5% multi-accounting fraud rings (500 records = 100 rings of 5)
        - 5% account takeover (500 records = 250 ATO cases)
        - 10% legitimate multi-device (1000 records = 500 users × 2)
        - 5% money mule networks (500 records = 50 networks of 10)
        - 75% clean singletons (7500 records)
        """
        records = []
        
        # 1. Multi-accounting fraud rings (5% = 500 records)
        num_rings = 100
        print(f"Generating {num_rings} multi-accounting fraud rings (500 records)...")
        for ring_id in range(num_rings):
            records.extend(self._generate_multi_accounting_ring(ring_id, size=5))
        
        # 2. Account takeover (5% = 500 records)
        num_ato = 250
        print(f"Generating {num_ato} ATO scenarios (500 records)...")
        for ato_id in range(num_ato):
            records.extend(self._generate_ato_case(ato_id))
        
        # 3. Legitimate multi-device (10% = 1000 records)
        num_legit = 500
        print(f"Generating {num_legit} legitimate multi-device users (1000 records)...")
        for user_id in range(num_legit):
            records.extend(self._generate_legitimate_user(user_id))
        
        # 4. Money mule networks (5% = 500 records)
        num_networks = 50
        print(f"Generating {num_networks} money mule networks (500 records)...")
        for net_id in range(num_networks):
            records.extend(self._generate_mule_network(net_id, size=10))
        
        # 5. Clean singletons (75% = remaining)
        remaining = num_records - len(records)
        print(f"Generating {remaining} clean singleton accounts...")
        records.extend(self._generate_clean_singletons(remaining))
        
        print(f"\n✓ Generated {len(records)} total records")
        
        return BlockInput(
            block_id="massive_test_10k",
            records=records
        )
    
    def _generate_multi_accounting_ring(self, ring_id: int, size: int = 5) -> list:
        """Multi-accounting fraud ring"""
        base_device = f"device_fraud_ring_{ring_id}"
        base_ip = f"10.{ring_id % 256}.{(ring_id // 256) % 256}.{100 + ring_id % 50}"
        
        records = []
        for i in range(size):
            records.append(Record(
                record_id=self._next_id(),
                attributes={
                    "name": f"Fraud Ring {ring_id} Account {i}",
                    "email": f"fraud{ring_id}_{i}@temp{ring_id % 10}.com",
                    "phone": f"+1{ring_id:04d}{i:06d}",
                    "address": f"{100 + ring_id} Fraud St City ST",
                    "device_fingerprint": base_device,
                    "device_os": "iOS",
                    "ip_address": base_ip,
                    "avg_transaction_amount": 45.0 + random.uniform(-5, 5),
                    "transaction_count": random.randint(1, 15),
                    "account_age_days": i
                },
                metadata=RecordMetadata(
                    source="registration_db",
                    timestamp=datetime.now() - timedelta(days=i),
                    trust_score=0.6 + random.uniform(-0.1, 0.1)
                )
            ))
        return records
    
    def _generate_ato_case(self, ato_id: int) -> list:
        """Account takeover scenario"""
        records = []
        
        # Victim
        records.append(Record(
            record_id=self._next_id(),
            attributes={
                "name": f"Victim {ato_id}",
                "email": f"victim{ato_id}@legit.com",
                "phone": f"+1900{ato_id:07d}",
                "address": f"{5000 + ato_id} Victim Ave City ST",
                "device_fingerprint": f"device_victim_{ato_id}",
                "device_os": "Android",
                "ip_address": f"192.168.{ato_id % 256}.{50 + ato_id % 50}",
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
        
        # Attacker
        records.append(Record(
            record_id=self._next_id(),
            attributes={
                "name": f"Victim {ato_id}",
                "email": f"victim{ato_id}@legit.com",
                "phone": f"+1900{ato_id:07d}",
                "address": f"{5000 + ato_id} Victim Ave City ST",
                "device_fingerprint": f"device_attacker_{ato_id}",
                "device_os": "Web",
                "ip_address": f"203.0.{ato_id % 256}.{ato_id % 256}",
                "vpn_flag": True,
                "avg_transaction_amount": 1500.0,
                "transaction_count": 3,
                "account_age_days": 500
            },
            metadata=RecordMetadata(
                source="web_app",
                timestamp=datetime.now() - timedelta(hours=2),
                trust_score=0.2
            )
        ))
        
        return records
    
    def _generate_legitimate_user(self, user_id: int) -> list:
        """Legitimate multi-device user"""
        email = f"user{user_id}@gmail.com"
        phone = f"+1800{user_id:07d}"
        name = f"User {user_id}"
        
        # Mobile + Web
        return [
            Record(
                record_id=self._next_id(),
                attributes={
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "address": f"{10000 + user_id} Main St City ST",
                    "device_fingerprint": f"device_mobile_{user_id}",
                    "device_os": "iOS",
                    "ip_address": f"172.16.{user_id % 256}.{10 + user_id % 50}",
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
            ),
            Record(
                record_id=self._next_id(),
                attributes={
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "address": f"{10000 + user_id} Main St City ST",
                    "device_fingerprint": f"device_web_{user_id}",
                    "device_os": "Web",
                    "ip_address": f"172.16.{user_id % 256}.{11 + user_id % 50}",
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
            )
        ]
    
    def _generate_mule_network(self, net_id: int, size: int = 10) -> list:
        """Money mule network"""
        shared_devices = [f"device_mule_{net_id}_{i}" for i in range(3)]
        
        records = []
        for i in range(size):
            records.append(Record(
                record_id=self._next_id(),
                attributes={
                    "name": f"Mule {net_id}_{i}",
                    "email": f"mule{net_id}_{i}@temp.com",
                    "phone": f"+1700{net_id:04d}{i:03d}",
                    "address": f"{20000 + net_id * 10 + i} Mule Rd City ST",
                    "device_fingerprint": shared_devices[i % 3],
                    "device_os": "Android",
                    "ip_address": f"198.51.100.{(net_id * 10 + i) % 256}",
                    "vpn_flag": i % 2 == 0,
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
        """Clean singleton accounts"""
        records = []
        for i in range(count):
            records.append(Record(
                record_id=self._next_id(),
                attributes={
                    "name": f"Clean User {i}",
                    "email": f"clean{i}@example.com",
                    "phone": f"+1600{i:07d}",
                    "address": f"{30000 + i * 10} Clean St City ST",
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
        return f"REC_{self.record_counter:06d}"


def save_block(block: BlockInput, filepath: str):
    """Save block to pickle file"""
    with open(filepath, 'wb') as f:
        pickle.dump(block, f)
    print(f"✓ Saved block to {filepath}")


def load_block(filepath: str) -> BlockInput:
    """Load block from pickle file"""
    with open(filepath, 'rb') as f:
        return pickle.load(f)


def main():
    print("=" * 80)
    print("LARGE-SCALE PIPELINE TEST: 10,000 RECORDS")
    print("=" * 80)
    print()
    
    # Generate or load data
    data_file = "../data/synthetic_10k.pkl"
    
    print("Generating 10,000 synthetic records...")
    print("-" * 80)
    generator = MassiveDataGenerator(seed=42)
    block = generator.generate_massive_block(num_records=10000)
    
    # Save data
    import os
    os.makedirs("../data", exist_ok=True)
    save_block(block, data_file)
    
    print()
    print("Dataset Summary:")
    print(f"  - Multi-accounting rings: 100 × 5 = 500 records (5%)")
    print(f"  - Account takeover: 250 × 2 = 500 records (5%)")
    print(f"  - Legitimate multi-device: 500 × 2 = 1000 records (10%)")
    print(f"  - Money mule networks: 50 × 10 = 500 records (5%)")
    print(f"  - Clean singletons: 7500 records (75%)")
    print(f"  - TOTAL: {len(block.records)} records")
    print()
    
    # Load config
    print("Loading configuration...")
    config = load_config("p2p_payment_resolution")
    print(f"✓ Configuration: {config.domain}")
    print()
    
    # Test WITHOUT embeddings
    print("=" * 80)
    print("TEST 1: WITHOUT EMBEDDINGS (Baseline)")
    print("=" * 80)
    print()
    
    pipeline1 = EntityResolutionPipeline(config=config, enable_embeddings=False)
    
    start = time.time()
    artifacts1 = pipeline1.resolve_entities(block)
    time1 = time.time() - start
    
    print(f"\n✓ Completed in {time1:.2f}s")
    print(f"  - Throughput: {len(block.records) / time1:.0f} records/sec")
    print(f"  - Entities: {len(artifacts1.entities)}")
    print(f"  - Avg confidence: {sum(e.confidence for e in artifacts1.entities) / len(artifacts1.entities):.4f}")
    print()
    
    # Test WITH embeddings
    print("=" * 80)
    print("TEST 2: WITH EMBEDDINGS (Enhanced)")
    print("=" * 80)
    print()
    
    pipeline2 = EntityResolutionPipeline(config=config, enable_embeddings=True)
    
    start = time.time()
    artifacts2 = pipeline2.resolve_entities(block)
    time2 = time.time() - start
    
    print(f"\n✓ Completed in {time2:.2f}s")
    print(f"  - Throughput: {len(block.records) / time2:.0f} records/sec")
    print(f"  - Entities: {len(artifacts2.entities)}")
    print(f"  - Avg confidence: {sum(e.confidence for e in artifacts2.entities) / len(artifacts2.entities):.4f}")
    print()
    
    # Save results
    results = {
        "test_date": datetime.now().isoformat(),
        "num_records": len(block.records),
        "baseline": {
            "time_seconds": time1,
            "throughput": len(block.records) / time1,
            "num_entities": len(artifacts1.entities),
            "avg_confidence": sum(e.confidence for e in artifacts1.entities) / len(artifacts1.entities),
            "fraud_detected": sum(1 for e in artifacts1.entities if e.explanations.fraud_indicators)
        },
        "enhanced": {
            "time_seconds": time2,
            "throughput": len(block.records) / time2,
            "num_entities": len(artifacts2.entities),
            "avg_confidence": sum(e.confidence for e in artifacts2.entities) / len(artifacts2.entities),
            "fraud_detected": sum(1 for e in artifacts2.entities if e.explanations.fraud_indicators)
        }
    }
    
    with open("../data/results_10k.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print("✓ Results saved to data/results_10k.json")
    print()
    
    # Comparison
    print("=" * 80)
    print("COMPARISON")
    print("=" * 80)
    print()
    
    print(f"Processing Time:")
    print(f"  Baseline:  {time1:.2f}s ({len(block.records) / time1:.0f} rec/sec)")
    print(f"  Enhanced:  {time2:.2f}s ({len(block.records) / time2:.0f} rec/sec)")
    print(f"  Overhead:  {time2 - time1:+.2f}s ({((time2 - time1) / time1 * 100):+.1f}%)")
    print()
    
    print(f"Entity Count:")
    print(f"  Baseline:  {len(artifacts1.entities)}")
    print(f"  Enhanced:  {len(artifacts2.entities)}")
    print(f"  Difference: {len(artifacts2.entities) - len(artifacts1.entities):+d}")
    print()
    
    conf1 = results["baseline"]["avg_confidence"]
    conf2 = results["enhanced"]["avg_confidence"]
    print(f"Average Confidence:")
    print(f"  Baseline:  {conf1:.4f}")
    print(f"  Enhanced:  {conf2:.4f}")
    print(f"  Improvement: {conf2 - conf1:+.4f} ({((conf2 - conf1) / conf1 * 100):+.2f}%)")
    print()
    
    fraud1 = results["baseline"]["fraud_detected"]
    fraud2 = results["enhanced"]["fraud_detected"]
    print(f"Fraud Detection:")
    print(f"  Baseline:  {fraud1}/{len(artifacts1.entities)} ({fraud1/len(artifacts1.entities)*100:.1f}%)")
    print(f"  Enhanced:  {fraud2}/{len(artifacts2.entities)} ({fraud2/len(artifacts2.entities)*100:.1f}%)")
    print()
    
    print("=" * 80)
    print("✅ 10K TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
