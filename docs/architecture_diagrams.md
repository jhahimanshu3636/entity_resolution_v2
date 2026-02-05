# Entity Resolution System - Architecture Diagrams

## System Architecture Overview

```mermaid
graph TB
    subgraph Input["🔵 INPUT LAYER"]
        A[Block Input<br/>Size-bounded records]
    end
    
    subgraph Feature["🟢 FEATURE LAYER"]
        B[Feature Extraction<br/>Text, Numeric, Categorical, Embeddings]
    end
    
    subgraph Similarity["🟡 SIMILARITY LAYER"]
        C[Pairwise Similarity<br/>Multi-dimensional vectors]
    end
    
    subgraph Graph["🟠 GRAPH CONSTRUCTION"]
        D[Initial Graph<br/>Nodes=Records, Edges=Candidates]
        E[Constraint Engine<br/>Hard & Soft Constraints]
        F[Graph Pruning<br/>Top-K, Normalization]
    end
    
    subgraph Seed["🔴 SEED LAYER"]
        G[Seed Clusters<br/>High-precision anchors]
    end
    
    subgraph Embedding["🟣 EMBEDDING LAYER"]
        H[Graph Embeddings<br/>FastRP / Node2Vec]
        I[Embedding Refinement<br/>α × original + β × embedding]
    end
    
    subgraph Clustering["🟤 CLUSTERING LAYER"]
        J[Community Detection<br/>Leiden / Louvain]
        K[Cluster Validation<br/>Entropy, Conflicts, Density]
        L[Cluster Repair<br/>Split, Remove, Reassign]
    end
    
    subgraph Output["🔵 OUTPUT LAYER"]
        M[Entity Assignment<br/>Confidence + Explanations]
    end
    
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
    J --> K
    K --> L
    L --> M
    
    style A fill:#4A90E2
    style B fill:#7ED321
    style C fill:#F5A623
    style D fill:#FF6B6B
    style E fill:#FF6B6B
    style F fill:#FF6B6B
    style G fill:#D0021B
    style H fill:#9013FE
    style I fill:#9013FE
    style J fill:#8B572A
    style K fill:#8B572A
    style L fill:#8B572A
    style M fill:#4A90E2
```

---

## Module Dependency Graph

```mermaid
graph LR
    subgraph Core["Core Modules"]
        DM[data_models.py<br/>Pydantic schemas]
        CFG[config.py<br/>Configuration]
    end
    
    subgraph Stage1["Stage 1-3"]
        FE[feature_extraction.py]
        PS[pairwise_similarity.py]
        GB[graph_builder.py]
    end
    
    subgraph Stage4["Stage 4-6"]
        CE[constraint_engine.py]
        GP[graph_pruning.py]
        SC[seed_clustering.py]
    end
    
    subgraph Stage7["Stage 7-8"]
        GE[graph_embeddings.py]
        ER[embedding_refinement.py]
    end
    
    subgraph Stage9["Stage 9-11"]
        CL[clustering.py]
        CV[cluster_validation.py]
        CS[confidence_scoring.py]
        EX[explainability.py]
    end
    
    subgraph Orchestration["Orchestration"]
        PL[pipeline.py<br/>Main orchestrator]
    end
    
    DM --> FE
    DM --> PS
    DM --> GB
    DM --> CE
    DM --> GP
    DM --> SC
    DM --> GE
    DM --> ER
    DM --> CL
    DM --> CV
    DM --> CS
    DM --> EX
    
    CFG --> FE
    CFG --> PS
    CFG --> CE
    CFG --> GP
    CFG --> GE
    CFG --> ER
    CFG --> CL
    CFG --> CV
    
    FE --> PS
    PS --> GB
    GB --> CE
    CE --> GP
    GP --> SC
    SC --> GE
    GE --> ER
    ER --> CL
    CL --> CV
    CV --> CS
    CS --> EX
    
    PL --> FE
    PL --> PS
    PL --> GB
    PL --> CE
    PL --> GP
    PL --> SC
    PL --> GE
    PL --> ER
    PL --> CL
    PL --> CV
    PL --> CS
    PL --> EX
    
    style DM fill:#4A90E2
    style CFG fill:#4A90E2
    style PL fill:#D0021B,color:#fff
```

---

## Data Flow with Size Changes

```mermaid
graph TD
    A["📊 INPUT<br/>Block: 1,000 records"] --> B["⚙️ Feature Extraction<br/>1,000 feature vectors"]
    B --> C["🔍 Pairwise Similarity<br/>~499,500 candidate pairs<br/>(all-pairs comparison)"]
    C --> D["📈 Graph Construction<br/>1,000 nodes<br/>~50,000 edges (threshold > 0.5)"]
    D --> E["🚫 Constraint Engine<br/>1,000 nodes<br/>~45,000 edges (10% removed)"]
    E --> F["✂️ Graph Pruning<br/>1,000 nodes<br/>~10,000 edges (top-10 per node)"]
    F --> G["🎯 Seed Clusters<br/>150 high-confidence seeds<br/>(threshold > 0.95)"]
    G --> H["🧮 Graph Embeddings<br/>1,000 node embeddings<br/>(64-dim vectors)"]
    H --> I["🔄 Embedding Refinement<br/>1,000 nodes<br/>~12,000 edges (weights adjusted)"]
    I --> J["🏘️ Community Detection<br/>85 entity clusters<br/>(initial hypothesis)"]
    J --> K["✅ Validation & Repair<br/>92 validated clusters<br/>(7 split due to conflicts)"]
    K --> L["🎖️ Final Entities<br/>92 entities with confidence<br/>+ explanations"]
    
    style A fill:#4A90E2,color:#fff
    style L fill:#7ED321,color:#000
```

---

## Constraint Engine Decision Flow

```mermaid
flowchart TD
    Start([Edge: Record A ↔ Record B]) --> HC1{Hard Constraint 1:<br/>Conflicting SSN?}
    
    HC1 -->|Yes| Remove1[❌ Remove Edge]
    HC1 -->|No| HC2{Hard Constraint 2:<br/>DOB diff > 365 days?}
    
    HC2 -->|Yes| Remove2[❌ Remove Edge]
    HC2 -->|No| HC3{Hard Constraint 3:<br/>Domain violation?}
    
    HC3 -->|Yes| Remove3[❌ Remove Edge]
    HC3 -->|No| SC1{Soft Constraint 1:<br/>Low source trust?}
    
    SC1 -->|Yes| Pen1[⚠️ Penalize: -30%]
    SC1 -->|No| SC2{Soft Constraint 2:<br/>Partial mismatch?}
    
    SC2 -->|Yes| Pen2[⚠️ Penalize: -20%]
    SC2 -->|No| Keep[✅ Keep Edge]
    
    Pen1 --> Keep
    Pen2 --> Keep
    
    Remove1 --> End([Edge Decision Made])
    Remove2 --> End
    Remove3 --> End
    Keep --> End
    
    style Remove1 fill:#D0021B,color:#fff
    style Remove2 fill:#D0021B,color:#fff
    style Remove3 fill:#D0021B,color:#fff
    style Pen1 fill:#F5A623
    style Pen2 fill:#F5A623
    style Keep fill:#7ED321
```

---

## Embedding Refinement Strategy

```mermaid
graph LR
    subgraph Input["Input"]
        OS[Original Similarity<br/>from pairwise comparison]
        ES[Embedding Similarity<br/>from graph structure]
    end
    
    subgraph Weights["Configurable Weights"]
        Alpha["α = 0.7<br/>(original weight)"]
        Beta["β = 0.3<br/>(embedding weight)"]
    end
    
    subgraph Computation["Weighted Blend"]
        Calc["final_score = α × original + β × embedding<br/><br/>Constraint: α > β"]
    end
    
    subgraph Validation["Validation"]
        Check1{Score > min_threshold?}
        Check2{Constraint safe?}
    end
    
    subgraph Output["Output"]
        RefEdge["Refined Edge<br/>with adjusted weight"]
        RemEdge["Edge Removed"]
    end
    
    OS --> Calc
    ES --> Calc
    Alpha --> Calc
    Beta --> Calc
    
    Calc --> Check1
    Check1 -->|Yes| Check2
    Check1 -->|No| RemEdge
    Check2 -->|Yes| RefEdge
    Check2 -->|No| RemEdge
    
    style OS fill:#4A90E2
    style ES fill:#9013FE
    style Alpha fill:#7ED321
    style Beta fill:#7ED321
    style Calc fill:#F5A623
    style RefEdge fill:#7ED321
    style RemEdge fill:#D0021B,color:#fff
```

---

## Cluster Validation & Repair Flow

```mermaid
flowchart TD
    Start([Cluster from<br/>Community Detection]) --> V1{Attribute<br/>Entropy > 0.7?}
    
    V1 -->|Yes| R1[🔨 REPAIR: Split cluster<br/>into homogeneous groups]
    V1 -->|No| V2{Conflicting<br/>attributes?}
    
    V2 -->|Yes| R2[🔨 REPAIR: Remove conflicting<br/>records or split]
    V2 -->|No| V3{Edge Density<br/>< 0.3?}
    
    V3 -->|Yes| R3[🔨 REPAIR: Remove bridge nodes<br/>or split weak clusters]
    V3 -->|No| V4{Embedding Cohesion<br/>low?}
    
    V4 -->|Yes| R4[🔨 REPAIR: Reassign<br/>outlier records]
    V4 -->|No| Valid[✅ Valid Cluster]
    
    R1 --> Revalidate{Re-validate<br/>sub-clusters?}
    R2 --> Revalidate
    R3 --> Revalidate
    R4 --> Revalidate
    
    Revalidate -->|Yes| V1
    Revalidate -->|No| Valid
    
    Valid --> End([Validated Cluster])
    
    style Start fill:#4A90E2
    style Valid fill:#7ED321
    style End fill:#7ED321
    style R1 fill:#F5A623
    style R2 fill:#F5A623
    style R3 fill:#F5A623
    style R4 fill:#F5A623
```

---

## Entity Confidence Scoring Components

```mermaid
mindmap
  root((Entity<br/>Confidence))
    Internal Edge Strength
      Average edge weight
      Minimum edge weight
      Edge weight std dev
    Attribute Agreement
      Name consistency
      Address consistency
      Phone/Email matches
      Attribute entropy
    Embedding Cohesion
      Avg cosine similarity
      Centroid distance
      Outlier detection
    Source Trust
      Source consistency
      Trust score distribution
      Multi-source validation
    Cluster Metrics
      Edge density
      Cluster size
      Seed cluster presence
```

---

## Production Monitoring Dashboard Structure

```mermaid
graph TB
    subgraph Metrics["📊 Real-time Metrics"]
        M1[Processing Time<br/>per Stage]
        M2[Entity Cluster<br/>Size Distribution]
        M3[Confidence Score<br/>Distribution]
        M4[Constraint Violation<br/>Frequency]
    end
    
    subgraph Quality["✅ Quality Metrics"]
        Q1[Precision<br/>Target: > 95%]
        Q2[Recall<br/>Target: > 85%]
        Q3[F1 Score<br/>Target: > 90%]
        Q4[Determinism<br/>Target: 100%]
    end
    
    subgraph Alerts["🚨 Alerts"]
        A1[High Repair Rate<br/>threshold: > 20%]
        A2[Low Confidence<br/>threshold: < 0.6]
        A3[Processing Timeout<br/>threshold: > 60s]
        A4[Quality Degradation<br/>F1 drop: > 5%]
    end
    
    subgraph Actions["⚙️ Actions"]
        AC1[Auto-retry failed blocks]
        AC2[Flag for manual review]
        AC3[Trigger config adjustment]
        AC4[Generate incident report]
    end
    
    M1 --> Metrics
    M2 --> Metrics
    M3 --> Metrics
    M4 --> Metrics
    
    Q1 --> Quality
    Q2 --> Quality
    Q3 --> Quality
    Q4 --> Quality
    
    A1 --> Actions
    A2 --> Actions
    A3 --> Actions
    A4 --> Actions
    
    Metrics --> Alerts
    Quality --> Alerts
    
    style Metrics fill:#4A90E2
    style Quality fill:#7ED321
    style Alerts fill:#F5A623
    style Actions fill:#D0021B,color:#fff
```

---

## Explanation Generation Architecture

```mermaid
sequenceDiagram
    participant E as Entity Cluster
    participant EX as Explainability Engine
    participant G as Graph
    participant F as Features
    participant O as Output
    
    E->>EX: Request explanation
    EX->>G: Get strongest edges
    G-->>EX: Top N edges with scores
    EX->>F: Get attribute agreement
    F-->>EX: Dominant attributes + entropy
    EX->>G: Get cluster metrics
    G-->>EX: Density, cohesion, size
    EX->>EX: Generate human-readable explanation
    EX->>O: Return structured explanation
    
    Note over EX,O: Explanation includes:<br/>1. Strongest edges + reasons<br/>2. Dominant attributes<br/>3. Cluster quality metrics<br/>4. Confidence justification
```

---

## Technology Stack Integration

```mermaid
graph TB
    subgraph Application["Application Layer"]
        PL[pipeline.py<br/>Main Orchestrator]
    end
    
    subgraph Core["Core Libraries"]
        NX[NetworkX<br/>Graph Operations]
        KC[karateclub<br/>Graph Embeddings]
        ST[sentence-transformers<br/>Text Embeddings]
        LA[leidenalg<br/>Community Detection]
    end
    
    subgraph Utilities["Utility Libraries"]
        RF[rapidfuzz<br/>String Similarity]
        JF[jellyfish<br/>Phonetic Matching]
        PD[Pydantic<br/>Data Validation]
        SL[structlog<br/>Structured Logging]
    end
    
    subgraph Config["Configuration"]
        YML[YAML Files<br/>Domain Configs]
    end
    
    subgraph Storage["Data Storage"]
        JSON[JSON<br/>Intermediate Artifacts]
        CSV[CSV/Parquet<br/>Input/Output]
    end
    
    PL --> NX
    PL --> KC
    PL --> ST
    PL --> LA
    PL --> RF
    PL --> JF
    PL --> PD
    PL --> SL
    PL --> YML
    PL --> JSON
    PL --> CSV
    
    style PL fill:#D0021B,color:#fff
    style NX fill:#4A90E2
    style KC fill:#4A90E2
    style ST fill:#4A90E2
    style LA fill:#4A90E2
```

---

## Scalability Architecture for Production

```mermaid
graph TB
    subgraph Input["Input Processing"]
        I1[Block Queue<br/>Kafka / RabbitMQ]
        I2[Block Splitter<br/>Size normalization]
    end
    
    subgraph Processing["Parallel Processing Layer"]
        W1[Worker 1<br/>Pipeline Instance]
        W2[Worker 2<br/>Pipeline Instance]
        W3[Worker N<br/>Pipeline Instance]
    end
    
    subgraph Cache["Cache Layer"]
        C1[Feature Cache<br/>Redis / File]
        C2[Similarity Cache<br/>Redis / File]
    end
    
    subgraph Storage["Output Storage"]
        DB[(PostgreSQL<br/>Entity Results)]
        S3[(S3 / Object Store<br/>Artifacts)]
    end
    
    subgraph Monitor["Monitoring"]
        PR[Prometheus<br/>Metrics]
        GR[Grafana<br/>Dashboards]
        AL[AlertManager<br/>Alerts]
    end
    
    I1 --> I2
    I2 --> W1
    I2 --> W2
    I2 --> W3
    
    W1 --> C1
    W2 --> C1
    W3 --> C1
    
    W1 --> C2
    W2 --> C2
    W3 --> C2
    
    W1 --> DB
    W2 --> DB
    W3 --> DB
    
    W1 --> S3
    W2 --> S3
    W3 --> S3
    
    W1 --> PR
    W2 --> PR
    W3 --> PR
    
    PR --> GR
    PR --> AL
    
    style I1 fill:#4A90E2
    style W1 fill:#7ED321
    style W2 fill:#7ED321
    style W3 fill:#7ED321
    style DB fill:#9013FE
    style PR fill:#F5A623
```

---

These diagrams provide a comprehensive visual representation of the entity resolution system architecture, covering data flow, module dependencies, decision logic, and production deployment considerations.
