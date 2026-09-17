# Qdrant Vector Database Architecture

## 1. Architectural Role
IntelGraphAI designates **Qdrant** as the authoritative enterprise vector search engine for industrial documentation chunks, technical manuals, condition monitoring logs, and standard operating procedures (SOPs).

FAISS remains available purely as an in-memory cache/fallback for backward compatibility, while all semantic document retrieval flows through the unified `QdrantVectorStore` repository abstraction.

---

## 2. Collection Schema & Payloads
The primary collection is named **`industrial_kb`**.

### Distance Metric
- **Cosine Distance** (`Distance.COSINE`)
- **Vector Dimension**: 256 (standardized industrial embedding space)

### Point Payloads
Each stored vector point includes a rich metadata payload ensuring fine-grained filtering:

```json
{
  "chunk_id": "chunk_p101_oem_1",
  "document_id": "Pump_P101_OEM_Manual",
  "asset_tag": "P-101",
  "category": "OEM Manual",
  "page_number": 1,
  "section_title": "1.0 Equipment Identification & Design Specifications",
  "record_date": "2023-01-15",
  "version": "v1.0",
  "governance_status": "Approved",
  "is_obsolete": false,
  "content": "ABC PUMPS - MODEL XYZ-200 TECHNICAL MANUAL..."
}
```

---

## 3. Metadata Filtering & Governance Enforcement
Qdrant payload filters enforce strict industrial governance rules before vector scoring:
1. **Asset Isolation**: `FieldCondition(key="asset_tag", match=MatchValue(value=asset_tag))` restricts search boundaries to the requested machine.
2. **Obsolete / Draft Exclusion**: When `trusted_sources_only=True`, chunks tagged `governance_status="Obsolete"` or `"Unverified"` are excluded from similarity scoring.
3. **Role-Aware Filtering**: Only authorized document classifications are presented to specific personas.

---

## 4. Dual-Mode Deployment & Fallback Strategy
- **Cluster Deployment**: Connects via HTTP REST (`http://localhost:6333`) or gRPC (`6334`) to an enterprise Qdrant cluster.
- **Embedded Local Persistence**: When no external cluster is provisioned, `QdrantClient(path="storage/qdrant_db")` provides embedded SQLite-backed on-disk vector storage.
- **In-Memory Lock Fallback**: If a second process opens the storage folder concurrently (e.g. during standalone test execution alongside Uvicorn), `QdrantClient(":memory:")` automatically initializes without throwing lock conflicts.
