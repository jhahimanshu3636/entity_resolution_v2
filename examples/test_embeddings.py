"""
Test Graph Embeddings Module
============================

Validate FastRP embeddings implementation.
"""

import sys
sys.path.append('../src')

import networkx as nx
import numpy as np
from graph_embeddings import GraphEmbedder, EmbeddingRefiner
from config import EntityResolutionConfig
from data_models import GraphEdge, SimilarityVector


def test_fastrp_embeddings():
    """Test FastRP embedding generation"""
    
    print("=" * 80)
    print("Testing FastRP Embeddings")
    print("=" * 80)
    print()
    
    # Create simple test graph
    G = nx.Graph()
    
    # Add nodes
    nodes = ['A', 'B', 'C', 'D', 'E']
    for node in nodes:
        G.add_node(node)
    
    # Add edges (create two communities)
    # Community 1: A-B-C
    G.add_edge('A', 'B', weight=0.9)
    G.add_edge('B', 'C', weight=0.85)
    G.add_edge('A', 'C', weight=0.8)
    
    # Community 2: D-E
    G.add_edge('D', 'E', weight=0.95)
    
    # Weak link between communities
    G.add_edge('C', 'D', weight=0.3)
    
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print()
    
    # Load config
    from config import load_config
    config = load_config("p2p_payment_resolution")
    
    # Generate embeddings
    embedder = GraphEmbedder(config)
    embeddings = embedder._fastrp_embeddings(G)
    
    print(f"✓ Generated {len(embeddings)} embeddings")
    print(f"Embedding dimensions: {len(embeddings['A'])}")
    print()
    
    # Check embedding properties
    print("Embedding Similarities (Cosine):")
    print("-" * 80)
    
    # Within Community 1 (should be high)
    sim_AB = np.dot(embeddings['A'], embeddings['B'])
    sim_BC = np.dot(embeddings['B'], embeddings['C'])
    sim_AC = np.dot(embeddings['A'], embeddings['C'])
    
    print(f"A-B (same community): {sim_AB:.4f}")
    print(f"B-C (same community): {sim_BC:.4f}")
    print(f"A-C (same community): {sim_AC:.4f}")
    print()
    
    # Within Community 2 (should be high)
    sim_DE = np.dot(embeddings['D'], embeddings['E'])
    print(f"D-E (same community): {sim_DE:.4f}")
    print()
    
    # Across communities (should be lower)
    sim_AD = np.dot(embeddings['A'], embeddings['D'])
    sim_CD = np.dot(embeddings['C'], embeddings['D'])
    
    print(f"A-D (different communities): {sim_AD:.4f}")
    print(f"C-D (bridge nodes): {sim_CD:.4f}")
    print()
    
    # Validate
    avg_within_community1 = (sim_AB + sim_BC + sim_AC) / 3
    avg_cross_community = (sim_AD + sim_CD) / 2
    
    if avg_within_community1 > avg_cross_community:
        print("✓ PASS: Within-community similarity > cross-community similarity")
    else:
        print("✗ FAIL: Embeddings not capturing community structure")
    
    print()
    print("=" * 80)
    print()


def test_embedding_refinement():
    """Test embedding-based edge refinement"""
    
    print("=" * 80)
    print("Testing Embedding Refinement")
    print("=" * 80)
    print()
    
    # Create test graph
    G = nx.Graph()
    
    nodes = ['X', 'Y', 'Z']
    for node in nodes:
        G.add_node(node)
    
    # Add edges with base weights
    G.add_edge('X', 'Y', weight=0.7, edge_data=GraphEdge(
        source='X',
        target='Y',
        similarity_vector=SimilarityVector(pair=('X', 'Y')),
        base_edge_score=0.7,
        is_valid=True
    ))
    
    G.add_edge('Y', 'Z', weight=0.6, edge_data=GraphEdge(
        source='Y',
        target='Z',
        similarity_vector=SimilarityVector(pair=('Y', 'Z')),
        base_edge_score=0.6,
        is_valid=True
    ))
    
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print()
    
    print("Original edge weights:")
    for u, v in G.edges():
        print(f"  {u}-{v}: {G[u][v]['weight']:.4f}")
    print()
    
    # Create mock embeddings
    embeddings = {
        'X': np.array([0.8, 0.6]),
        'Y': np.array([0.7, 0.7]),
        'Z': np.array([0.6, 0.8])
    }
    
    # Normalize
    for node in embeddings:
        embeddings[node] = embeddings[node] / np.linalg.norm(embeddings[node])
    
    # Load config
    from config import load_config
    config = load_config("p2p_payment_resolution")
    
    # Refine graph
    refiner = EmbeddingRefiner(config)
    G_refined = refiner.refine_graph(G, embeddings)
    
    print("Refined edge weights:")
    for u, v in G_refined.edges():
        original = 0.7 if u == 'X' else 0.6
        refined = G_refined[u][v]['weight']
        change = refined - original
        print(f"  {u}-{v}: {refined:.4f} (change: {change:+.4f})")
    
    print()
    print("✓ Refinement complete")
    print()
    print("=" * 80)
    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "GRAPH EMBEDDINGS VALIDATION" + " " * 31 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")
    
    test_fastrp_embeddings()
    test_embedding_refinement()
    
    print("✅ All embedding tests completed!")
    print()
