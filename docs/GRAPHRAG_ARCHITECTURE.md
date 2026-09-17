# Dynamic GraphRAG Architecture

## 1. Overview
IntelGraphAI implements true **GraphRAG**, fusing dense vector similarity retrieval from **Qdrant** with dynamic multi-hop traversal in the **Neo4j Industrial Knowledge Graph**.

Unlike naive RAG systems that rely solely on top-k text chunk similarity, GraphRAG understands the physical relationships between assets, components, failure modes, historical work orders, and governing regulations.

```text
User Query
   ↓
Query Intent Understanding (Asset, Problem, Standard, Scope)
   ↓
Vector Retrieval via Qdrant (Targeted chunks with payload filter)
   ↓
Entity Resolution (Extract machinery tags, component part numbers)
   ↓
Dynamic Neo4j Multi-Hop Traversal (Intent-driven paths)
   ↓
Evidence Ranking & Fusion
   ↓
Multi-Agent LLM Synthesis
   ↓
Answer + Citations + Confidence + Grounding Trail
```

---

## 2. Dynamic Traversal Paths
Graph traversal is never hard-coded; it adapts dynamically to the query category:

### Failure & RCA Traversal Path
```cypher
MATCH (a:Asset {tag: $asset_tag})-[:HAS_FAILURE]->(f:Failure)
MATCH (f)-[:ASSOCIATED_WITH]->(c:Component)
OPTIONAL MATCH (f)-[:DOCUMENTS_FAILURE]->(wo:WorkOrder)
OPTIONAL MATCH (a)-[:HAS_INSPECTION]->(i:Inspection)
RETURN a, f, c, wo, i
```

### Regulatory Compliance Traversal Path
```cypher
MATCH (a:Asset {tag: $asset_tag})-[:GOVERNED_BY]->(r:ComplianceRequirement)
OPTIONAL MATCH (r)-[:REQUIRES]->(p:Procedure)
OPTIONAL MATCH (a)-[:HAS_FINDING]->(fd:Finding)
RETURN a, r, p, fd
```

### Component & Procedure Traversal Path
```cypher
MATCH (a:Asset {tag: $asset_tag})-[:ASSET_HAS_COMPONENT]->(c:Component)
OPTIONAL MATCH (a)-[:ASSET_HAS_DOCUMENT]->(d:Document)-[:DOCUMENT_HAS_CHUNK]->(chk:DocumentChunk)
RETURN a, c, d, chk
```

---

## 3. Evidence Fusion & Grounding Guardrails
1. **Factual Grounding**: Every assertion made by the AI Orchestrator must be backed by a verified document excerpt or graph relationship.
2. **Refusal Protection**: Queries on unrecorded machinery, speculative failure modes, or non-existent equipment (e.g. "X-99", "P-999") return strict refusal:
   > *"I could not find sufficient information in the available industrial records."*
3. **Citation Precision**: All responses provide exact document IDs, page numbers, section headers, and governance status (Approved vs Obsolete).
