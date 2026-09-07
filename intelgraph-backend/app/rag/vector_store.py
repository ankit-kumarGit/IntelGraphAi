import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple
import faiss
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from app.config import settings, FAISS_DIR
from app.models.document import DocumentChunk

class FaissVectorStore:
    def __init__(self, dimension: int = 256):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(self.dimension)  # Cosine similarity via normalized inner product
        self.vectorizer = TfidfVectorizer(max_features=self.dimension, stop_words="english")
        self.chunks_metadata: List[Dict[str, Any]] = []
        self.is_fitted = False
        self.index_file = FAISS_DIR / "industrial_kb.index"
        self.meta_file = FAISS_DIR / "industrial_kb.meta.pkl"
        if self.index_file.exists() and self.meta_file.exists():
            self.load()

    def fit_and_index(self, chunks: List[DocumentChunk]):
        if not chunks:
            return

        texts = [f"{c.section_title} {c.asset_tag} {c.category} {c.content}" for c in chunks]
        
        # Fit vectorizer
        tfidf_matrix = self.vectorizer.fit_transform(texts).toarray().astype(np.float32)
        
        # Pad or truncate to exact dimension if vocabulary is smaller
        actual_features = tfidf_matrix.shape[1]
        if actual_features < self.dimension:
            padding = np.zeros((tfidf_matrix.shape[0], self.dimension - actual_features), dtype=np.float32)
            embeddings = np.hstack([tfidf_matrix, padding])
        else:
            embeddings = tfidf_matrix[:, :self.dimension]

        # Normalize L2 for cosine similarity
        faiss.normalize_L2(embeddings)

        # Reset index
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(embeddings)
        self.is_fitted = True

        self.chunks_metadata = [c.model_dump() for c in chunks]
        self.save()

    def add_chunks(self, new_chunks: List[DocumentChunk]):
        # If not fitted yet or adding dynamically, re-index all chunks
        all_metadata = list(self.chunks_metadata)
        for c in new_chunks:
            all_metadata.append(c.model_dump())
        
        # Re-create chunks list and index
        reconstructed = [DocumentChunk(**m) for m in all_metadata]
        self.fit_and_index(reconstructed)

    def search(self, query: str, top_k: int = 5, asset_tag: str = None) -> List[Tuple[Dict[str, Any], float]]:
        if not self.is_fitted or self.index.ntotal == 0:
            return []

        try:
            q_vec = self.vectorizer.transform([query]).toarray().astype(np.float32)
            actual_features = q_vec.shape[1]
            if actual_features < self.dimension:
                padding = np.zeros((1, self.dimension - actual_features), dtype=np.float32)
                q_emb = np.hstack([q_vec, padding])
            else:
                q_emb = q_vec[:, :self.dimension]

            faiss.normalize_L2(q_emb)
            scores, indices = self.index.search(q_emb, min(top_k * 3, self.index.ntotal))

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx >= len(self.chunks_metadata):
                    continue
                meta = self.chunks_metadata[idx]
                if asset_tag and meta.get("asset_tag") and meta.get("asset_tag") != asset_tag:
                    continue
                results.append((meta, float(score)))
                if len(results) >= top_k:
                    break
            return results
        except Exception as e:
            return []

    def save(self):
        try:
            faiss.write_index(self.index, str(self.index_file))
            with open(self.meta_file, "wb") as f:
                pickle.dump({
                    "vectorizer": self.vectorizer,
                    "metadata": self.chunks_metadata,
                    "is_fitted": self.is_fitted
                }, f)
        except Exception:
            pass

    def load(self) -> bool:
        try:
            if self.index_file.exists() and self.meta_file.exists():
                self.index = faiss.read_index(str(self.index_file))
                with open(self.meta_file, "rb") as f:
                    data = pickle.load(f)
                    self.vectorizer = data.get("vectorizer", self.vectorizer)
                    self.chunks_metadata = data.get("metadata", [])
                    self.is_fitted = data.get("is_fitted", False)
                return True
        except Exception:
            pass
        return False

vector_store = FaissVectorStore()
