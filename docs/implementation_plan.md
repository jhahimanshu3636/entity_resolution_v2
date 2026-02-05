# Production-Level Entity Resolution Architecture

## Overview

This implementation plan defines a **production-grade graph-based entity resolution system** that operates within pre-computed blocks, enhanced with graph embeddings for improved accuracy while maintaining explainability and deterministic behavior.

---

## User Review Required

> [!IMPORTANT]
> **Design Philosophy**
> - **Correctness over recall**: We prioritize precision and explainability
> - **Embeddings enhance, never decide**: Graph embeddings reinforce existing evidence but never make standalone decisions
> - **Constraint-aware**: Hard and soft constraints must be validated before any clustering
> - **Fully auditable**: Every decision must be traceable and explainable

> [!WARNING]
> **Key Architectural Constraints**
> - Graph embeddings (FastRP/Node2Vec) are **optional** but recommended for enhanced accuracy
> - Embedding weight `β` must always be less than original similarity weight `α` (α > β)
> - All intermediate stages must be re-runnable and deterministic
> - No blind transitivity - all clusters must be validated

---

## Proposed Changes

### Core System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        BLOCK INPUT                              │
│                    (Size-bounded records)                       │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              Stage 1: Feature Extraction Layer                  │
│  • Text tokenization (name, address)                            │
│  • N-gram generation                                            │
│  • Numeric/categorical feature extraction                       │
│  • Text embeddings (SBERT/FastText)                            │
│  • Deterministic, cacheable transformations                    │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│         Stage 2: Pairwise Similarity Computation                │
│  • Multi-dimensional similarity vectors                         │
│  • Separate scores: name, address, phone, email, embedding     │
│  • NO aggregation at this stage                                │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│          Stage 3: Graph Construction (Initial)                  │
│  • Nodes = Records                                              │
│  • Edges = Candidate matches                                    │
│  • Edge attributes = Full similarity vector + base score        │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              Stage 4: Constraint Layer                          │
│  • Hard constraints → Edge removal                              │
│    - Conflicting immutable IDs                                  │
│    - Domain violations                                          │
│  • Soft constraints → Edge penalization                         │
│    - Partial mismatches, source distrust                        │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│          Stage 5: Graph Pruning & Normalization                 │
│  • Top-K edges per node (prevent hub dominance)                 │
│  • Adaptive threshold-based edge removal                        │
│  • Edge weight normalization                                    │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│        Stage 6: Seed Cluster Generation                         │
│  • High-precision anchor clusters                               │
│  • Very strong edges only (exact/near-exact matches)            │
│  • Zero false positives target                                  │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│         Stage 7: Graph Embedding (Optional)                     │
│  • FastRP (preferred) or Node2Vec                               │
│  • Input: Constraint-validated, pruned graph                    │
│  • Output: Node embeddings for evidence reinforcement          │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│         Stage 8: Embedding-Aware Graph Refinement               │
│  • Recompute edge weights:                                      │
│    final_score = α × original_score + β × embedding_similarity  │
│    (constraint: α > β)                                          │
│  • Re-prune edges, re-limit node degree                        │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│           Stage 9: Community Detection                          │
│  • Leiden algorithm (preferred) or Louvain                      │
│  • Weighted modularity optimization                             │
│  • Generates entity hypotheses                                  │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│        Stage 10: Cluster Validation & Repair                    │
│  • Validate: attribute entropy, conflicts, edge density         │
│  • Repair: split weak clusters, remove bridges                  │
│  • Reassign ambiguous records                                   │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│         Stage 11: Entity Assignment + Confidence                │
│  • Generate entity IDs                                          │
│  • Compute composite confidence scores                          │
│  • Build explanations (strongest edges, metrics)                │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
                     ENTITY OUTPUT
```

---

### Module Structure

#### Core Pipeline Modules

##### [NEW] [config.py](file:///Users/himanshujha/Desktop/VS_Code/entity_resolution_v2/src/config.py)

Configuration management with domain-specific parameters:
- Similarity thresholds per attribute type
- Graph pruning parameters (top-K, min threshold)
- Embedding configuration (algorithm, dimensions, α/β weights)
- Clustering algorithm selection
- Validation metrics and thresholds

##### [NEW] [data_models.py](file:///Users/himanshujha/Desktop/VS_Code/entity_resolution_v2/src/data_models.py)

Strict data contracts using Pydantic:
- `BlockInput`: Input schema with records and metadata
- `FeatureVector`: Multi-modal feature representation
- `SimilarityVector`: Multi-dimensional similarity scores
- `GraphEdge`: Edge with attributes and scores
- `EntityCluster`: Final entity output with confidence and explanations

##### [NEW] [feature_extraction.py](file:///Users/himanshujha/Desktop/VS_Code/entity_resolution_v2/src/feature_extraction.py)

Deterministic feature transformation:
- Text tokenization and n-gram generation
- Numeric/categorical feature extraction
- Text embeddings (SBERT for semantic similarity)
- Source trust score computation
- **Must be fully deterministic and cacheable**

---

##### [NEW] [pairwise_similarity.py](file:///Users/himanshujha/Desktop/VS_Code/entity_resolution_v2/src/pairwise_similarity.py)

Multi-dimensional similarity computation:
- Name similarity (Jaro-Winkler, Token sort ratio)
- Address similarity (fuzzy matching with abbreviations)
- Phone/Email similarity (normalized exact/fuzzy)
- Text embedding cosine similarity
- Source agreement scoring
- **Returns full similarity vector, NO aggregation**

---

##### [NEW] [graph_builder.py](file:///Users/himanshujha/Desktop/VS_Code/entity_resolution_v2/src/graph_builder.py)

Graph construction and management:
- Build initial graph from similarity pairs
- Manage edge attributes (similarity vectors, scores)
- NetworkX-based implementation for flexibility
- Support for constraint application

---

##### [NEW] [constraint_engine.py](file:///Users/himanshujha/Desktop/VS_Code/entity_resolution_v2/src/constraint_engine.py)

Constraint validation layer:
- Hard constraints: Remove edges completely
  - Conflicting immutable identifiers (SSN, exact DOB conflicts)
  - Strong negative evidence
- Soft constraints: Penalize edge weights
  - Partial mismatches
  - Low source trust scores
- **Executes BEFORE embeddings or clustering**

---

##### [NEW] [graph_pruning.py](file:///Users/himanshujha/Desktop/VS_Code/entity_resolution_v2/src/graph_pruning.py)

Graph refinement for clustering stability:
- Top-K edges per node (prevent hub dominance)
- Adaptive threshold-based pruning
- Edge weight normalization per block
- Degree-based outlier detection

---

##### [NEW] [seed_clustering.py](file:///Users/himanshujha/Desktop/VS_Code/entity_resolution_v2/src/seed_clustering.py)

High-precision seed cluster generation:
- Use only very strong edges (threshold > 0.95)
- Create small, high-confidence anchor clusters
- Near-zero false positive target
- Guides downstream clustering decisions

---

##### [NEW] [graph_embeddings.py](file:///Users/himanshujha/Desktop/VS_Code/entity_resolution_v2/src/graph_embeddings.py)

Graph embedding layer (optional):
- FastRP implementation (preferred - faster, deterministic)
- Node2Vec implementation (alternative)
- Input: Constraint-validated, pruned graph
- Output: Node embeddings for evidence reinforcement
- **Configurable via config**

---

##### [NEW] [embedding_refinement.py](file:///Users/himanshujha/Desktop/VS_Code/entity_resolution_v2/src/embedding_refinement.py)

Embedding-aware graph refinement:
- Compute embedding-based edge scores
- Blend with original scores: `final = α × original + β × embedding` (α > β)
- Re-prune refined graph
- Validate constraint compliance after refinement

---

##### [NEW] [clustering.py](file:///Users/himanshujha/Desktop/VS_Code/entity_resolution_v2/src/clustering.py)

Community detection algorithms:
- Leiden algorithm (preferred - better quality)
- Louvain algorithm (alternative)
- Weighted modularity optimization
- Deterministic seed for reproducibility
- **NOT allowed: pure connected components, naive transitive closure**

---

##### [NEW] [cluster_validation.py](file:///Users/himanshujha/Desktop/VS_Code/entity_resolution_v2/src/cluster_validation.py)

Cluster quality validation and repair:
- **Validation metrics:**
  - Attribute entropy (detect mixed entities)
  - Conflict detection (incompatible attributes)
  - Edge density (cluster cohesion)
  - Embedding cohesion (if embeddings used)
- **Repair actions:**
  - Split clusters with high entropy
  - Remove bridge nodes connecting disparate groups
  - Reassign ambiguous records

---

##### [NEW] [confidence_scoring.py](file:///Users/himanshujha/Desktop/VS_Code/entity_resolution_v2/src/confidence_scoring.py)

Composite confidence computation:
- Internal edge strength statistics
- Attribute agreement within cluster
- Embedding cohesion (if used)
- Source trust consistency
- **Must be interpretable and stable**

---

##### [NEW] [explainability.py](file:///Users/himanshujha/Desktop/VS_Code/entity_resolution_v2/src/explainability.py)

Explanation generation:
- Identify strongest edges in cluster
- Extract dominant attribute values
- Compute cluster quality metrics
- Generate human-readable explanations
- Support audit trails

---

##### [NEW] [pipeline.py](file:///Users/himanshujha/Desktop/VS_Code/entity_resolution_v2/src/pipeline.py)

Main orchestration pipeline:
- Coordinate all stages sequentially
- Maintain intermediate artifacts for debugging
- Support stage-by-stage execution
- Logging at each decision point
- **Pure functions, no global state**

---

### Supporting Infrastructure

##### [NEW] [utils/](file:///Users/himanshujha/Desktop/VS_Code/entity_resolution_v2/src/utils/)

Utility functions:
- String comparison utilities
- Graph visualization helpers
- Logging configuration
- Performance profiling

##### [NEW] [tests/](file:///Users/himanshujha/Desktop/VS_Code/entity_resolution_v2/tests/)

Comprehensive test suite:
- Unit tests for each module
- Integration tests for pipeline stages
- Determinism tests (same input → same output)
- Correctness tests with labeled data
- Performance benchmarks

---

### Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Graph Library** | NetworkX | Flexible, well-documented, supports weighted graphs |
| **Graph Embeddings** | karateclub (FastRP, Node2Vec) | Production-ready implementations |
| **Text Embeddings** | sentence-transformers (SBERT) | State-of-the-art semantic similarity |
| **Clustering** | python-louvain / leidenalg | Battle-tested community detection |
| **String Similarity** | rapidfuzz, jellyfish | Fast, accurate fuzzy matching |
| **Data Validation** | Pydantic | Strict schema enforcement |
| **Configuration** | YAML + Pydantic | Human-readable, validated configs |
| **Logging** | structlog | Structured, audit-friendly logging |

---

### Data Flow Example

```python
# Input: Block with 100 records
block = {
    "block_id": "email_domain_example_com",
    "records": [...]
}

# Stage 1: Feature Extraction
features = extract_features(block.records)
# Output: 100 feature vectors

# Stage 2: Pairwise Similarity
similarities = compute_pairwise_similarity(features)
# Output: ~4,950 candidate pairs with similarity vectors

# Stage 3: Graph Construction
graph = build_graph(similarities, threshold=0.5)
# Output: Graph with 100 nodes, ~500 edges

# Stage 4: Constraints
graph = apply_constraints(graph, constraints)
# Output: Graph with ~450 edges (50 removed by hard constraints)

# Stage 5: Pruning
graph = prune_graph(graph, top_k=10, min_threshold=0.6)
# Output: Graph with ~300 edges (better quality)

# Stage 6: Seed Clusters
seeds = generate_seed_clusters(graph, threshold=0.95)
# Output: 15 high-confidence seed clusters

# Stage 7: Graph Embeddings (optional)
embeddings = compute_graph_embeddings(graph, algorithm="fastrp")
# Output: 100 node embeddings (64-dim)

# Stage 8: Embedding Refinement
graph = refine_with_embeddings(graph, embeddings, alpha=0.7, beta=0.3)
# Output: Refined graph with adjusted edge weights

# Stage 9: Clustering
clusters = detect_communities(graph, algorithm="leiden")
# Output: 25 entity clusters

# Stage 10: Validation & Repair
clusters = validate_and_repair(clusters, graph, features)
# Output: 27 validated clusters (2 split due to conflicts)

# Stage 11: Confidence & Explanation
entities = assign_entities_with_confidence(clusters, graph, features)
# Output: 27 entity records with confidence scores and explanations
```

---

## Verification Plan

### Automated Tests

1. **Determinism Tests**
   ```bash
   pytest tests/test_determinism.py -v
   # Run same block 10 times, verify identical output
   ```

2. **Correctness Tests**
   ```bash
   pytest tests/test_correctness.py -v
   # Use labeled benchmark datasets (e.g., FEBRL)
   # Measure precision, recall, F1
   ```

3. **Constraint Validation Tests**
   ```bash
   pytest tests/test_constraints.py -v
   # Verify hard constraints always enforced
   # Verify α > β always maintained
   ```

4. **Integration Tests**
   ```bash
   pytest tests/test_pipeline.py -v
   # End-to-end pipeline tests
   # Verify intermediate artifacts are correct
   ```

### Manual Verification

1. **Explainability Review**
   - Generate explanations for sample entities
   - Verify strongest edges make sense
   - Check attribute dominance logic

2. **Performance Benchmarking**
   - Test on blocks of varying sizes (10, 100, 1000, 10000 records)
   - Measure time per stage
   - Identify bottlenecks

3. **Quality Assessment**
   - Use real-world sample data
   - Compare with existing ER system (if available)
   - Manual review of edge cases

### Metrics to Track

| Metric | Target | Purpose |
|--------|--------|---------|
| **Precision** | > 95% | Minimize false positives |
| **Recall** | > 85% | Balance with precision |
| **F1 Score** | > 90% | Overall quality |
| **Determinism** | 100% | Same input → same output |
| **Processing Time** | < 5s per 1000 records | Production viability |
| **Explainability Coverage** | 100% | All entities must be explainable |

---

## Configuration Strategy

### Domain-Specific Configs

Create separate config files for different domains:

```
config/
  ├── customer_resolution.yaml
  ├── vendor_resolution.yaml
  ├── fraud_detection.yaml
  └── default.yaml
```

Each config specifies:
- Similarity thresholds per attribute
- Constraint rules
- Embedding parameters (α, β, dimensions)
- Clustering algorithm and parameters
- Validation thresholds

### Example Config Structure

```yaml
# config/customer_resolution.yaml
domain: customer_resolution

similarity:
  name:
    algorithm: jaro_winkler
    threshold: 0.85
    weight: 0.4
  address:
    algorithm: token_sort
    threshold: 0.75
    weight: 0.3
  phone:
    exact_match: true
    weight: 0.2
  email:
    exact_match: true
    weight: 0.1

constraints:
  hard:
    - type: conflicting_ssn
      enabled: true
    - type: incompatible_dob
      threshold: 365  # days
  soft:
    - type: source_distrust
      penalty: 0.3

graph:
  pruning:
    top_k: 10
    min_threshold: 0.6
  normalization: minmax

embeddings:
  enabled: true
  algorithm: fastrp  # or node2vec
  dimensions: 64
  alpha: 0.7  # original score weight
  beta: 0.3   # embedding score weight

clustering:
  algorithm: leiden  # or louvain
  resolution: 1.0
  seed: 42

validation:
  entropy_threshold: 0.7
  min_edge_density: 0.3
```

---

## Production Safety Guarantees

### Determinism

✅ **All random processes are seeded**
- Graph embedding algorithms
- Clustering algorithms
- Sampling operations

✅ **All operations are order-independent**
- Set operations use sorted keys
- Dictionary iterations use sorted keys

### Auditability

✅ **All stages preserve intermediate artifacts**
```python
artifacts = {
    "features": features,
    "similarities": similarities,
    "initial_graph": graph_v1,
    "constrained_graph": graph_v2,
    "pruned_graph": graph_v3,
    "embeddings": embeddings,
    "refined_graph": graph_v4,
    "clusters": clusters,
    "validated_clusters": final_clusters,
    "entities": entities
}
```

✅ **All decisions are logged**
```python
logger.info("constraint_applied", 
            constraint_type="conflicting_ssn",
            edge_removed=(record_1, record_2),
            reason="SSN mismatch: 123-45-6789 vs 987-65-4321")
```

### Explainability

✅ **Every entity includes explanation**
```json
{
  "entity_id": "E_12345",
  "records": ["R1", "R2", "R3"],
  "confidence": 0.92,
  "explanations": {
    "strongest_edges": [
      {"pair": ["R1", "R2"], "score": 0.98, "reason": "Exact name + phone match"},
      {"pair": ["R2", "R3"], "score": 0.95, "reason": "Exact email + high name similarity"}
    ],
    "dominant_attributes": {
      "name": "John A. Smith",
      "address": "123 Main St, Boston MA"
    },
    "cluster_metrics": {
      "avg_edge_weight": 0.91,
      "edge_density": 0.86,
      "attribute_entropy": 0.15
    }
  }
}
```

### Re-runnability

✅ **Pipeline is idempotent**
- Same input block always produces same entities
- Can re-run any stage with saved artifacts
- No side effects or external state dependencies

---

## Next Steps

Once this plan is approved, I will:

1. **Create project structure** with all module files
2. **Implement data models** with Pydantic validation
3. **Build each pipeline stage** as pure functions
4. **Implement configuration management**
5. **Create comprehensive test suite**
6. **Set up logging and monitoring**
7. **Run end-to-end validation** on sample data
8. **Generate performance benchmarks**
9. **Create detailed walkthrough documentation**

---

## Additional Considerations

### Scalability

For production at scale:
- Implement **caching** for feature extraction (Redis/file-based)
- Use **parallel processing** for independent blocks (multiprocessing/Ray)
- Consider **distributed graph processing** (GraphFrames/GraphX) for very large blocks
- Implement **incremental updates** to avoid re-processing unchanged data

### Monitoring

Production monitoring should track:
- Processing time per stage
- Entity cluster size distribution
- Confidence score distribution
- Constraint violation frequency
- Cluster repair frequency
- Precision/recall on labeled samples

### Extensions

Future enhancements:
- **Active learning** for threshold tuning
- **Cross-block entity linking** with controlled transitivity
- **Temporal entity evolution** tracking
- **Multi-language support** for international data
- **Privacy-preserving** techniques (differential privacy for embeddings)

---

**Ready for implementation upon approval.**
