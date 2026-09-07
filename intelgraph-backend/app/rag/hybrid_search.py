import re
from typing import List, Dict, Any, Optional
from app.rag.vector_store import vector_store

class HybridSearchEngine:
    @staticmethod
    def search(
        query: str,
        asset_tag: Optional[str] = None,
        trusted_sources_only: bool = True,
        top_k: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Combines exact keyword/tag lexical matching with FAISS vector similarity.
        Applies document governance policies.
        """
        all_chunks = vector_store.chunks_metadata
        if not all_chunks:
            return []

        query_lower = query.lower()
        query_words = set(re.findall(r"\w+", query_lower))

        # 1. FAISS Semantic Search with Query Expansion for generic equipment terms
        effective_query = query
        has_generic_noun = any(w in query_words for w in ["machine", "equipment", "asset", "system", "unit"])
        if has_generic_noun:
            effective_query = f"{query} {asset_tag or ''} pump compressor technical manual specification"

        vector_results = vector_store.search(effective_query, top_k=top_k * 2, asset_tag=asset_tag)
        vector_scores = {res[0]["chunk_id"]: res[1] for res in vector_results}

        # 2. Score calculation with hybrid boost
        scored_candidates = []
        for chunk in all_chunks:
            # Asset tag filtering
            if asset_tag and chunk.get("asset_tag") != asset_tag:
                continue

            # Governance filtering
            gov_status = chunk.get("governance_status", "Approved")
            if trusted_sources_only and gov_status in ["Obsolete", "Unverified"]:
                continue

            chunk_id = chunk["chunk_id"]
            content = chunk.get("content", "").lower()
            section = chunk.get("section_title", "").lower()
            tag = chunk.get("asset_tag", "").lower()

            # Lexical score: exact match of query words + tag boosts
            lexical_hits = sum(1 for w in query_words if w in content or w in section)
            if has_generic_noun and (asset_tag and tag == asset_tag.lower()):
                lexical_hits += 2

            tag_hit = 1.5 if (tag and tag in query_lower) else 0.0
            
            # Exact phrase match boost
            phrase_hit = 2.0 if (len(query_words) > 1 and query_lower in content) else 0.0

            sem_score = vector_scores.get(chunk_id, 0.0)
            asset_presence = 0.5 if (asset_tag and tag == asset_tag.lower()) else 0.0

            # Boost Approved documents
            gov_multiplier = 1.2 if gov_status == "Approved" else (0.8 if gov_status == "Draft" else 0.4)

            total_score = ((sem_score * 1.5) + (lexical_hits * 0.4) + tag_hit + phrase_hit + asset_presence) * gov_multiplier

            if total_score > 0.05:
                scored_candidates.append({
                    "chunk": chunk,
                    "score": total_score,
                    "semantic_score": sem_score,
                    "lexical_hits": lexical_hits
                })

        # Sort descending by total score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        return scored_candidates[:top_k]

hybrid_search = HybridSearchEngine()
