import os
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from app.models.document import DocumentChunk

logger = logging.getLogger("intelgraph.qdrant")

class VectorStoreBase:
    def fit_and_index(self, chunks: List[DocumentChunk]):
        raise NotImplementedError

    def add_chunks(self, new_chunks: List[DocumentChunk]):
        raise NotImplementedError

    def search(
        self,
        query: str,
        top_k: int = 5,
        asset_tag: Optional[str] = None,
        trusted_sources_only: bool = True
    ) -> List[Tuple[Dict[str, Any], float]]:
        raise NotImplementedError

class QdrantVectorStore(VectorStoreBase):
    """
    Qdrant Industrial Vector Database Repository.
    Operates against a Qdrant cluster (http://localhost:6333) or embedded local disk store.
    """
    COLLECTION_NAME = "industrial_kb"

    def __init__(self, dimension: int = 256):
        self.dimension = dimension
        self.vectorizer = TfidfVectorizer(max_features=self.dimension, stop_words="english")
        self.is_fitted = False
        
        # Local Qdrant persistent storage path
        self.local_qdrant_dir = Path(__file__).resolve().parent.parent.parent / "storage" / "qdrant_db"
        self.local_qdrant_dir.mkdir(parents=True, exist_ok=True)
        
        self.qdrant_url = os.getenv("QDRANT_URL", "")
        self.client = None
        self.initialize_client()
        self.ensure_collection()

    def initialize_client(self):
        if self.qdrant_url:
            try:
                self.client = QdrantClient(url=self.qdrant_url, timeout=5)
                self.client.get_collections()
                logger.info("Connected to remote Qdrant cluster at %s", self.qdrant_url)
                return
            except Exception as e:
                logger.info("Remote Qdrant unavailable (%s), falling back to local storage.", e)

        try:
            self.client = QdrantClient(path=str(self.local_qdrant_dir))
            logger.info("Initialized local persistent Qdrant store at %s", self.local_qdrant_dir)
        except Exception as e:
            logger.warning("Local directory lock encountered, initializing in-memory Qdrant: %s", e)
            self.client = QdrantClient(":memory:")

    def ensure_collection(self):
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.COLLECTION_NAME for c in collections)
            if not exists:
                self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=qmodels.VectorParams(
                        size=self.dimension,
                        distance=qmodels.Distance.COSINE
                    )
                )
                logger.info("Created Qdrant collection: %s", self.COLLECTION_NAME)
        except Exception as e:
            logger.error("Error creating Qdrant collection: %s", e)

    def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        if not self.is_fitted:
            tfidf = self.vectorizer.fit_transform(texts).toarray().astype(np.float32)
            self.is_fitted = True
        else:
            try:
                tfidf = self.vectorizer.transform(texts).toarray().astype(np.float32)
            except Exception:
                tfidf = self.vectorizer.fit_transform(texts).toarray().astype(np.float32)

        actual_features = tfidf.shape[1]
        if actual_features < self.dimension:
            pad = np.zeros((tfidf.shape[0], self.dimension - actual_features), dtype=np.float32)
            embeddings = np.hstack([tfidf, pad])
        else:
            embeddings = tfidf[:, :self.dimension]

        # Normalize L2 for Cosine
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return embeddings / norms

    def fit_and_index(self, chunks: List[DocumentChunk]):
        if not chunks:
            return

        texts = [f"{c.section_title} {c.asset_tag} {c.category} {c.content}" for c in chunks]
        embeddings = self._generate_embeddings(texts)

        points = []
        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            payload = chunk.model_dump()
            points.append(
                qmodels.PointStruct(
                    id=idx + 1,
                    vector=emb.tolist(),
                    payload=payload
                )
            )

        # Upsert in batches of 100
        for i in range(0, len(points), 100):
            batch = points[i:i + 100]
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=batch
            )
        logger.info("Successfully indexed %d chunks into Qdrant collection '%s'", len(chunks), self.COLLECTION_NAME)

    def add_chunks(self, new_chunks: List[DocumentChunk]):
        if not new_chunks:
            return
        texts = [f"{c.section_title} {c.asset_tag} {c.category} {c.content}" for c in new_chunks]
        embeddings = self._generate_embeddings(texts)

        points = []
        for idx, (chunk, emb) in enumerate(zip(new_chunks, embeddings)):
            payload = chunk.model_dump()
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id))
            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=emb.tolist(),
                    payload=payload
                )
            )

        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=points
        )
        logger.info("Appended %d chunks to Qdrant with UUID keys", len(new_chunks))

    def search(
        self,
        query: str,
        top_k: int = 5,
        asset_tag: Optional[str] = None,
        trusted_sources_only: bool = True,
        tenant_id: Optional[str] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        if not self.is_fitted:
            return []

        try:
            q_emb = self._generate_embeddings([query])[0].tolist()

            conditions = []
            if tenant_id:
                conditions.append(
                    qmodels.FieldCondition(
                        key="tenant_id",
                        match=qmodels.MatchValue(value=tenant_id)
                    )
                )
            if trusted_sources_only:
                # Exclude Obsolete documents
                conditions.append(
                    qmodels.FieldCondition(
                        key="governance_status",
                        match=qmodels.MatchValue(value="Approved")
                    )
                )

            q_filter = qmodels.Filter(must=conditions) if conditions else None
            fetch_limit = top_k * 4 if asset_tag else top_k

            if hasattr(self.client, "query_points"):
                search_result = self.client.query_points(
                    collection_name=self.COLLECTION_NAME,
                    query=q_emb,
                    query_filter=q_filter,
                    limit=fetch_limit
                ).points
            else:
                search_result = self.client.search(
                    collection_name=self.COLLECTION_NAME,
                    query_vector=q_emb,
                    query_filter=q_filter,
                    limit=fetch_limit
                )

            results = []
            for res in search_result:
                payload = res.payload or {}
                if asset_tag:
                    t_u = asset_tag.upper()
                    chunk_asset = (payload.get("asset_tag") or "").upper()
                    primaries = [p.upper() for p in payload.get("primary_asset_tags", [])]
                    related = [r.upper() for r in payload.get("related_asset_tags", [])]
                    scope = payload.get("document_scope", "ASSET")

                    is_match = (chunk_asset == t_u) or (t_u in primaries) or (scope in ["SYSTEM", "MULTI_ASSET"] and t_u in related)
                    if not is_match:
                        continue
                results.append((payload, float(res.score)))
                if len(results) >= top_k:
                    break
            return results
        except Exception as e:
            logger.error("Qdrant search error: %s", e)
            return []

    def count_by_asset_tag(self, asset_tag: str, tenant_id: Optional[str] = None) -> int:
        try:
            conditions = [
                qmodels.FieldCondition(
                    key="asset_tag",
                    match=qmodels.MatchValue(value=asset_tag.upper())
                )
            ]
            if tenant_id:
                conditions.append(
                    qmodels.FieldCondition(
                        key="tenant_id",
                        match=qmodels.MatchValue(value=tenant_id)
                    )
                )
            q_filter = qmodels.Filter(must=conditions)
            count_res = self.client.count(
                collection_name=self.COLLECTION_NAME,
                count_filter=q_filter,
                exact=True
            )
            return count_res.count
        except Exception as e:
            logger.warning("Qdrant count_by_asset_tag error: %s", e)
            return 0

    def delete_by_asset_tag(self, asset_tag: str, tenant_id: Optional[str] = None) -> int:
        before_count = self.count_by_asset_tag(asset_tag, tenant_id)
        if before_count == 0:
            return 0
        try:
            conditions = [
                qmodels.FieldCondition(
                    key="asset_tag",
                    match=qmodels.MatchValue(value=asset_tag.upper())
                )
            ]
            if tenant_id:
                conditions.append(
                    qmodels.FieldCondition(
                        key="tenant_id",
                        match=qmodels.MatchValue(value=tenant_id)
                    )
                )
            q_filter = qmodels.Filter(must=conditions)
            self.client.delete(
                collection_name=self.COLLECTION_NAME,
                points_selector=qmodels.FilterSelector(filter=q_filter)
            )
            logger.info("Deleted %d points for asset '%s' from Qdrant", before_count, asset_tag)
            return before_count
        except Exception as e:
            logger.error("Qdrant delete_by_asset_tag error: %s", e)
            raise e

qdrant_store = QdrantVectorStore()
