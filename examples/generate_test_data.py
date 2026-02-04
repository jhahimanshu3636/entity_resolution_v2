"""
Example Data Generator
=====================

Generates synthetic P2P payment data for testing entity resolution.

Scenarios:
- Legitimate users with multiple devices
- Multi-accounting fraud (same person, multiple accounts)
- Account takeover scenarios
- Clean singleton entities

Author: Entity Resolution System
"""

import random
import string
from datetime import datetime, timedelta
from typing import List
import sys
sys.path.append('..')

from data_models import BlockInput, Record, RecordMetadata


class ExampleDataGenerator:
    """Generates synthetic P2P payment data"""
    
    def __init__(self, seed: int = 42):
        """
        Initialize generator
        
        Args:
            seed: Random seed for reproducibility
        """
        random.seed(seed)
        self.record_counter = 0
    
    def generate_test_block(self, scenario: str = "mixed") -> BlockInput:
        """
        Generate test block with different scenarios
        
        Args:
            scenario: One of "mixed", "multi_accounting", "legitimate", "ato"
            
        Returns:
            BlockInput with synthetic records
        """
        if scenario == "multi_accounting":
            records = self._generate_multi_accounting_scenario()
        elif scenario == "legitimate":
            records = self._generate_legitimate_users()
        elif scenario == "ato":
            records = self._generate_ato_scenario()
        else:  # mixed
            records = []
            records.extend(self._generate_multi_accounting_scenario())
            records.extend(self._generate_legitimate_users())
            records.extend(self._generate_singleton_users())
        
        return BlockInput(
            block_id="test_block_001",
            records=records
        )
    
    def _generate_multi_accounting_scenario(self) -> List[Record]:
        """Generate multi-accounting fraud scenario"""
        
        # Same person with 3 accounts (promo abuse)
        base_name = "John Smith"
        base_device = "device_ABC123"
        base_ip = "192.168.1.100"
        
        records = []
        
        # Account 1: Primary
        records.append(Record(
            record_id=self._next_id(),
            attributes={
                "name": "John A Smith",
                "email": "john.smith@gmail.com",
                "phone": "+1234567890",
                "address": "123 Main St Boston MA",
                "device_fingerprint": base_device,
                "device_os": "iOS",
                "ip_address": base_ip,
                "avg_transaction_amount": 50.0,
                "transaction_count": 10,
                "account_age_days": 30
            },
            metadata=RecordMetadata(
                source="registration_db",
                timestamp=datetime.utcnow() - timedelta(days=30),
                trust_score=0.9
            )
        ))
        
        # Account 2: Variation with same device
        records.append(Record(
            record_id=self._next_id(),
            attributes={
                "name": "J Smith",
                "email": "jsmith123@gmail.com",
                "phone": "+1234567891",
                "address": "123 Main Street Boston MA",
                "device_fingerprint": base_device,  # SAME DEVICE
                "device_os": "iOS",
                "ip_address": base_ip,  # SAME IP
                "avg_transaction_amount": 48.0,
                "transaction_count": 8,
                "account_age_days": 7
            },
            metadata=RecordMetadata(
                source="registration_db",
                timestamp=datetime.utcnow() - timedelta(days=7),
                trust_score=0.85
            )
        ))
        
        # Account 3: Another variation
        records.append(Record(
            record_id=self._next_id(),
            attributes={
                "name": "John Smith Jr",
                "email": "johnsmith.jr@gmail.com",
                "phone": "+1234567892",
                "address": "123 Main St Boston MA 02101",
                "device_fingerprint": base_device,  # SAME DEVICE
                "device_os": "iOS",
                "ip_address": base_ip,  # SAME IP
                "avg_transaction_amount": 52.0,
                "transaction_count": 9,
                "account_age_days": 3
            },
            metadata=RecordMetadata(
                source="registration_db",
                timestamp=datetime.utcnow() - timedelta(days=3),
                trust_score=0.8
            )
        ))
        
        return records
    
    def _generate_legitimate_users(self) -> List[Record]:
        """Generate legitimate user with multiple devices"""
        
        records = []
        
        # Same person, different devices (legitimate)
        # Mobile device
        records.append(Record(
            record_id=self._next_id(),
            attributes={
                "name": "Alice Johnson",
                "email": "alice.johnson@gmail.com",
                "phone": "+1987654321",
                "address": "456 Oak Ave Seattle WA",
                "device_fingerprint": "device_XYZ789",
                "device_os": "iOS",
                "ip_address": "10.0.1.50",
                "avg_transaction_amount": 120.0,
                "transaction_count": 50,
                "account_age_days": 365
            },
            metadata=RecordMetadata(
                source="mobile_app",
                timestamp=datetime.utcnow() - timedelta(days=365),
                trust_score=1.0,
                kyc_verified=True
            )
        ))
        
        # Web device (same person)
        records.append(Record(
            record_id=self._next_id(),
            attributes={
                "name": "Alice M Johnson",
                "email": "alice.johnson@gmail.com",  # SAME EMAIL
                "phone": "+1987654321",  # SAME PHONE
                "address": "456 Oak Avenue Seattle WA",
                "device_fingerprint": "device_WEB456",
                "device_os": "Web",
                "ip_address": "10.0.1.51",  # Different IP (home network)
                "avg_transaction_amount": 125.0,
                "transaction_count": 30,
                "account_age_days": 365
            },
            metadata=RecordMetadata(
                source="web_app",
                timestamp=datetime.utcnow() - timedelta(days=200),
                trust_score=1.0,
                kyc_verified=True
            )
        ))
        
        return records
    
    def _generate_ato_scenario(self) -> List[Record]:
        """Generate account takeover scenario"""
        
        records = []
        
        # Victim account (normal activity)
        records.append(Record(
            record_id=self._next_id(),
            attributes={
                "name": "Bob Williams",
                "email": "bob.williams@yahoo.com",
                "phone": "+1555123456",
                "address": "789 Pine Rd Austin TX",
                "device_fingerprint": "device_VICTIM1",
                "device_os": "Android",
                "ip_address": "172.16.0.100",
                "avg_transaction_amount": 75.0,
                "transaction_count": 100,
                "account_age_days": 500
            },
            metadata=RecordMetadata(
                source="mobile_app",
                timestamp=datetime.utcnow() - timedelta(days=10),
                trust_score=1.0,
                kyc_verified=True
            )
        ))
        
        # Attacker session (after takeover)
        records.append(Record(
            record_id=self._next_id(),
            attributes={
                "name": "Bob Williams",  # Same name (stolen account)
                "email": "bob.williams@yahoo.com",  # SAME EMAIL
                "phone": "+1555123456",  # SAME PHONE
                "address": "789 Pine Rd Austin TX",
                "device_fingerprint": "device_ATTACKER999",  # NEW DEVICE
                "device_os": "Web",  # Different platform
                "ip_address": "203.0.113.50",  # Different IP (foreign)
                "ip_reputation_score": 0.2,  # LOW REPUTATION
                "vpn_flag": True,  # VPN detected
                "avg_transaction_amount": 2000.0,  # UNUSUAL AMOUNT
                "transaction_count": 5,
                "account_age_days": 500
            },
            metadata=RecordMetadata(
                source="web_app",
                timestamp=datetime.utcnow() - timedelta(hours=2),
                trust_score=0.3,  # LOW TRUST
                fraud_confirmed=False  # Not yet confirmed
            )
        ))
        
        return records
    
    def _generate_singleton_users(self) -> List[Record]:
        """Generate clean singleton entities"""
        
        records = []
        
        for i in range(3):
            records.append(Record(
                record_id=self._next_id(),
                attributes={
                    "name": f"User {i}",
                    "email": f"user{i}@example.com",
                    "phone": f"+1{random.randint(1000000000, 9999999999)}",
                    "address": f"{random.randint(100, 999)} Street City ST",
                    "device_fingerprint": f"device_{self._random_string(8)}",
                    "device_os": random.choice(["iOS", "Android", "Web"]),
                    "ip_address": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                    "avg_transaction_amount": random.uniform(20, 200),
                    "transaction_count": random.randint(5, 50),
                    "account_age_days": random.randint(30, 1000)
                },
                metadata=RecordMetadata(
                    source="registration_db",
                    timestamp=datetime.utcnow() - timedelta(days=random.randint(30, 365)),
                    trust_score=random.uniform(0.7, 1.0)
                )
            ))
        
        return records
    
    def _next_id(self) -> str:
        """Generate next record ID"""
        self.record_counter += 1
        return f"REC_{self.record_counter:04d}"
    
    def _random_string(self, length: int) -> str:
        """Generate random string"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


# Example usage
if __name__ == "__main__":
    generator = ExampleDataGenerator()
    block = generator.generate_test_block("mixed")
    
    print(f"Generated block with {len(block.records)} records:")
    for record in block.records:
        print(f"  - {record.record_id}: {record.attributes.get('name')}")
