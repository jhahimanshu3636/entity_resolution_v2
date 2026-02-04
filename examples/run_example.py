"""
Example Usage: Run Entity Resolution Pipeline
=============================================

Demonstrates end-to-end entity resolution on synthetic P2P payment data.

Author: Entity Resolution System
"""

import sys
sys.path.append('../src')

from pipeline import EntityResolutionPipeline
from config import load_config
from generate_test_data import ExampleDataGenerator
import json


def main():
    print("=" * 80)
    print("P2P Payment Entity Resolution - Example Run")
    print("=" * 80)
    print()
    
    # Load configuration
    print("Loading configuration...")
    config = load_config("p2p_payment_resolution")
    print(f"✓ Loaded configuration for domain: {config.domain}")
    print()
    
    # Generate test data
    print("Generating synthetic test data...")
    generator = ExampleDataGenerator(seed=42)
    block = generator.generate_test_block("mixed")
    print(f"✓ Generated block with {len(block.records)} records")
    print()
    
    print("Test data includes:")
    print("  - 3 multi-accounting fraud accounts (same person)")
    print("  - 2 legitimate user accounts (same person, different devices)")
    print("  - 2 account takeover scenario (victim + attacker)")
    print("  - 3 singleton clean users")
    print()
    
    # Run pipeline
    print("Running entity resolution pipeline...")
    print("-" * 80)
    
    pipeline = EntityResolutionPipeline(
        config=config,
        enable_embeddings=False  # Disabled for speed
    )
    
    artifacts = pipeline.resolve_entities(block)
    
    print("-" * 80)
    print()
    
    # Display results
    print("RESULTS")
    print("=" * 80)
    print()
    
    print(f"Processing time: {artifacts.processing_time_seconds:.2f} seconds")
    print(f"Total entities identified: {len(artifacts.entities)}")
    print()
    
    print("Entities:")
    print("-" * 80)
    
    for entity in artifacts.entities:
        print(f"\n{entity.entity_id}")
        print(f"  Records: {', '.join(entity.records)}")
        print(f"  Confidence: {entity.confidence:.2f}")
        print(f"  Cluster size: {len(entity.records)}")
        print(f"  Requires review: {entity.requires_manual_review}")
        
        # Show strongest edge
        if entity.explanations.strongest_edges:
            top_edge = entity.explanations.strongest_edges[0]
            print(f"  Strongest edge: {top_edge.pair} (score: {top_edge.score:.2f})")
            print(f"    Reason: {top_edge.reason}")
        
        # Show dominant attributes
        if entity.explanations.dominant_attributes:
            print(f"  Dominant attributes:")
            for attr, value in entity.explanations.dominant_attributes.items():
                print(f"    - {attr}: {value}")
        
        # Show fraud indicators
        if entity.explanations.fraud_indicators:
            print(f"  ⚠️  Fraud indicators:")
            for indicator in entity.explanations.fraud_indicators:
                print(f"    - {indicator}")
    
    print()
    print("=" * 80)
    
    # Summary statistics
    print("\nSUMMARY STATISTICS")
    print("-" * 80)
    
    cluster_sizes = [len(e.records) for e in artifacts.entities]
    avg_confidence = sum(e.confidence for e in artifacts.entities) / len(artifacts.entities)
    
    print(f"Average cluster size: {sum(cluster_sizes) / len(cluster_sizes):.2f}")
    print(f"Average confidence: {avg_confidence:.2f}")
    print(f"Entities requiring review: {sum(1 for e in artifacts.entities if e.requires_manual_review)}")
    print(f"Singleton entities: {sum(1 for size in cluster_sizes if size == 1)}")
    print(f"Multi-record entities: {sum(1 for size in cluster_sizes if size > 1)}")
    
    print()
    print("✓ Pipeline execution complete!")


if __name__ == "__main__":
    main()
