Excellent — this is exactly the right move.
Below is a **clean, explicit, production-grade Architectural Information Document (AID)** written **for an LLM** whose job is to generate **correct, maintainable, explainable code** for **graph-based entity resolution inside blocks**, enhanced with **graph embeddings**.

This is **not prose**, not research notes — it is a **machine-usable design spec**.

---

# ARCHITECTURAL INFORMATION DOCUMENT

## Graph-Based Entity Resolution (Post-Blocking)

---

## 1. Purpose of This Document

This document defines the **authoritative architecture** for implementing **production-level entity resolution** using **graph-based clustering with embedding enhancement**, **within pre-computed blocks**.

The target consumer is:

* An **LLM generating production code**
* A **senior engineer implementing ER pipelines**
* A **data scientist validating ER correctness**

The design prioritizes:

* Correctness over recall
* Explainability
* Deterministic behavior
* Production safety
* Extensibility

---

## 2. Scope & Assumptions

### In Scope

* Entity resolution **within a block**
* Graph construction, refinement, clustering, validation
* Optional graph embeddings (FastRP / Node2Vec)
* Confidence scoring

### Out of Scope

* Blocking
* Cross-block entity merging
* UI / visualization
* Model training pipelines

### Assumptions

* Blocks are **size-bounded** and safe to process fully
* Blocking may contain **false positives**
* Input data may be noisy and incomplete
* Labeled data may be unavailable

---

## 3. Core Design Principles (Non-Negotiable)

1. **Edges are evidence, not decisions**
2. **Similarity ≠ identity**
3. **Transitivity must be validated**
4. **Graph embeddings enhance, never decide**
5. **All merges must be explainable**
6. **Every stage must be re-runnable and auditable**

Any implementation violating these principles is **incorrect by design**.

---

## 4. High-Level Pipeline Overview

```
BLOCK INPUT
   ↓
Feature Extraction
   ↓
Pairwise Similarity Computation
   ↓
Constraint-Aware Graph Construction
   ↓
Edge Pruning & Normalization
   ↓
High-Confidence Seed Clustering
   ↓
Graph Embedding (Optional, Controlled)
   ↓
Embedding-Aware Graph Refinement
   ↓
Graph Community Detection
   ↓
Cluster Validation & Repair
   ↓
Entity Assignment + Confidence
```

---

## 5. Data Contracts (Strict)

### 5.1 Block Input Schema

```json
{
  "block_id": "string",
  "records": [
    {
      "record_id": "string",
      "attributes": { "key": "value" },
      "metadata": {
        "source": "string",
        "timestamp": "datetime",
        "trust_score": "float"
      }
    }
  ]
}
```

---

### 5.2 Feature Representation (Per Record)

Each record must be transformed into:

```json
{
  "record_id": "string",
  "text_features": {
    "name_tokens": [...],
    "address_tokens": [...],
    "ngrams": [...]
  },
  "numeric_features": {...},
  "categorical_features": {...},
  "embeddings": {
    "text_embedding": [...]
  },
  "source_features": {...}
}
```

Feature extraction **must be deterministic**.

---

## 6. Pairwise Similarity Layer

### 6.1 Similarity Output Contract

For each candidate pair `(i, j)`:

```json
{
  "pair": ["record_i", "record_j"],
  "similarities": {
    "name_sim": float,
    "address_sim": float,
    "phone_sim": float,
    "email_sim": float,
    "embedding_sim": float,
    "source_agreement": float
  }
}
```

### Key Rule

**Do not collapse similarities into a single score at this stage.**

---

## 7. Graph Construction

### 7.1 Graph Definition

* Nodes: Records
* Edges: Candidate matches
* Edge attributes: Full similarity vector

```json
Edge {
  source: record_i
  target: record_j
  attributes: {
    similarity_vector,
    base_edge_score
  }
}
```

### 7.2 Base Edge Score

Computed via **rule-aware aggregation**, not naive averaging.

---

## 8. Constraint Layer (Mandatory)

### Hard Constraints (Edge Removal)

* Conflicting immutable identifiers
* Strong negative evidence
* Domain violations

### Soft Constraints (Edge Penalization)

* Partial mismatches
* Source distrust

**Constraints must execute before embeddings or clustering.**

---

## 9. Graph Pruning & Normalization

Goals:

* Prevent hub dominance
* Remove weak noise edges
* Stabilize clustering

Actions:

* Top-K edges per node
* Adaptive thresholds
* Edge weight normalization per block

---

## 10. Seed Cluster Generation (High Precision)

### Purpose

Create **anchor entity clusters** with near-zero false positives.

### Method

* Use only very strong edges
* Use exact or near-exact matches
* Small cluster sizes

These clusters guide downstream clustering.

---

## 11. Graph Embedding Layer (Optional but Recommended)

### Allowed Embeddings

* FastRP (preferred)
* Node2Vec (acceptable)

### Graph Used for Embedding

* Nodes: Records
* Edges: Post-constraint, post-pruning edges
* Weights: Validated edge scores

### Embedding Rules

* Embeddings **must not** be used standalone
* Embeddings **may only reinforce existing evidence**

---

## 12. Embedding Usage Constraints

### Allowed Uses

1. Edge score reinforcement
2. Weak edge recovery (constraint-safe)
3. Cluster cohesion measurement
4. Cluster repair decisions

### Forbidden Uses

* Direct clustering on embeddings
* Hard decisions using cosine similarity
* Overriding constraint violations

---

## 13. Graph Refinement Post-Embedding

Actions:

* Recompute edge weights:

  ```
  final_edge_score =
    α * original_score +
    β * embedding_similarity
  ```
* Re-prune edges
* Re-limit node degree

Constraint: `α > β`

---

## 14. Clustering (Entity Hypothesis Generation)

### Recommended Algorithms

1. Leiden / Louvain (weighted modularity)
2. Correlation clustering (optional)
3. Constrained agglomerative clustering

### Explicitly Disallowed

* Pure connected components
* Naive transitive closure
* Single-threshold union-find

---

## 15. Cluster Validation & Repair

### Validation Metrics

* Attribute entropy
* Conflict detection
* Edge density
* Embedding cohesion

### Repair Actions

* Split weak clusters
* Remove bridge nodes
* Reassign ambiguous records

---

## 16. Final Entity Output Schema

```json
{
  "entity_id": "string",
  "records": ["record_id"],
  "confidence": float,
  "explanations": {
    "dominant_attributes": {...},
    "strongest_edges": [...],
    "cluster_metrics": {...}
  }
}
```

---

## 17. Confidence Scoring

Confidence is a **composite score**:

* Internal edge strength
* Attribute agreement
* Embedding cohesion
* Source trust consistency

Must be:

* Interpretable
* Stable across runs

---

## 18. Production Guarantees

The system must be:

* Deterministic
* Auditable
* Re-runnable
* Explainable
* Configurable per domain

---

## 19. Explicit Non-Goals

The system does NOT:

* Learn similarity thresholds automatically (unless extended)
* Assume transitivity blindly
* Replace domain logic with embeddings
* Sacrifice explainability for recall

---

## 20. Implementation Guidance for LLM

When generating code:

* Implement each stage as a **pure function**
* Avoid global state
* Log decisions at each step
* Preserve intermediate artifacts for debugging
* Favor readability over micro-optimizations

---

## Final Note (for the LLM)

This is an **entity resolution system**, not a clustering toy.

If a design choice:

* increases recall but hides errors → reject it
* reduces explainability → reject it
* violates constraints → reject it

---

If you want, next I can:

* Convert this into a **Neo4j-specific execution spec**
* Generate **Python module boundaries**
* Create a **reference implementation skeleton**
* Add **evaluation & monitoring architecture**

Just say the word.
