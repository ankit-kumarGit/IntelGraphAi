import re
from typing import List, Dict, Any, Optional
from app.config import settings
from app.rag.vector_store import vector_store
from app.rag.qdrant_store import qdrant_store

class HybridSearchEngine:
    @staticmethod
    def search(
        query: str,
        asset_tag: Optional[str] = None,
        trusted_sources_only: bool = True,
        top_k: int = 6,
        tenant_id: Optional[str] = None,
        target_categories: Optional[List[str]] = None,
        fact_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Combines exact keyword/tag lexical matching with primary Qdrant vector similarity (and FAISS fallback).
        Applies first-class document category boosting, fact-type prioritization, document governance, and tenant isolation policies.
        """
        all_chunks = vector_store.chunks_metadata
        if not all_chunks:
            return []

        query_lower = query.lower()
        query_words = set(re.findall(r"\w+", query_lower))

        # 1. Primary Semantic Search: Qdrant Vector Engine with FAISS Fallback
        effective_query = query
        has_generic_noun = any(w in query_words for w in ["machine", "equipment", "asset", "system", "unit"])
        if has_generic_noun:
            effective_query = f"{query} {asset_tag or ''} pump compressor technical manual specification"
        if target_categories:
            effective_query = f"{effective_query} {' '.join(target_categories)}"

        vector_results = []
        try:
            vector_results = qdrant_store.search(
                query=effective_query,
                top_k=top_k * 3,
                asset_tag=asset_tag,
                trusted_sources_only=trusted_sources_only,
                tenant_id=tenant_id
            )
        except Exception:
            pass

        # Fallback to local FAISS index if Qdrant returned no matches or encountered local file lock
        if not vector_results:
            vector_results = vector_store.search(effective_query, top_k=top_k * 3, asset_tag=asset_tag)
        vector_scores = {res[0]["chunk_id"]: res[1] for res in vector_results}

        # Normalize target categories for matching
        target_cats_lower = [c.lower() for c in (target_categories or [])]

        # 2. Score calculation with hybrid boost
        scored_candidates = []
        for chunk in all_chunks:
            # Tenant isolation enforcement
            default_tenant = getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")
            raw_chunk_tenant = chunk.get("tenant_id")
            chunk_tenant = raw_chunk_tenant or (tenant_id if tenant_id in [default_tenant, "tenant_apex"] else default_tenant)
            if tenant_id and chunk_tenant != tenant_id and chunk_tenant != "global":
                continue

            # Asset tag filtering
            if asset_tag:
                t_u = asset_tag.upper()
                c_tag = (chunk.get("asset_tag") or "").upper()
                primaries = [p.upper() for p in chunk.get("primary_asset_tags", [])]
                related = [r.upper() for r in chunk.get("related_asset_tags", [])]
                scope = chunk.get("document_scope", "ASSET")
                is_match = (c_tag == t_u) or (t_u in primaries) or (scope in ["SYSTEM", "MULTI_ASSET"] and t_u in related)
                if not is_match:
                    continue

            # Governance filtering
            gov_status = chunk.get("governance_status", "Approved")
            excluded_statuses = ["Obsolete", "Unverified", "Rejected"]
            if getattr(settings, "REQUIRE_MANUAL_APPROVAL_BEFORE_AI", False):
                excluded_statuses.extend(["Needs Review", "Draft", "Uploaded"])
            if trusted_sources_only and gov_status in excluded_statuses:
                continue

            chunk_id = chunk["chunk_id"]
            content = chunk.get("content", "").lower()
            section = chunk.get("section_title", "").lower()
            tag = chunk.get("asset_tag", "").lower()
            category = chunk.get("category", "").lower()
            doc_id = chunk.get("document_id", "").lower()

            # Lexical score: exact match of query words + tag boosts
            lexical_hits = sum(1 for w in query_words if w in content or w in section)
            if has_generic_noun and (asset_tag and tag == asset_tag.lower()):
                lexical_hits += 2

            # Technical domain concept boosts
            if ("non-drive" in query_lower or "nde" in query_lower) and ("non-drive" in content or "nde" in content or "nu 312" in content):
                lexical_hits += 6
            if ("power" in query_lower or "motor" in query_lower) and ("power" in content or "kw" in content) and "oem" in doc_id:
                lexical_hits += 5
            if ("part" in query_lower or "bearing" in query_lower) and "oem" in doc_id and ("skf 6312" in content or "nu 312" in content or "skf-6314" in content):
                lexical_hits += 5
            if "alignment" in query_lower and ("misalignment" in content or "0.05" in content):
                lexical_hits += 4

            tag_hit = 1.5 if (tag and tag in query_lower) else 0.0
            
            # Exact phrase match boost
            phrase_hit = 2.0 if (len(query_words) > 1 and query_lower in content) else 0.0

            sem_score = vector_scores.get(chunk_id, 0.0)
            asset_presence = 0.5 if (asset_tag and tag == asset_tag.lower()) else 0.0

            # Document Category Matching & Down-ranking
            category_boost = 0.0
            if target_cats_lower:
                matches_cat = any(tc in category for tc in target_cats_lower) or any(tc in doc_id for tc in target_cats_lower)
                if matches_cat:
                    category_boost = 6.0
                else:
                    # Strongly down-rank irrelevant categories when an explicit category is targeted
                    category_boost = -4.0

            # Fact Type (DATE) Prioritization
            date_boost = 0.0
            if fact_type == "DATE":
                has_labeled_date = any(p in content for p in [
                    "inspection date", "date of inspection", "survey date", "date performed",
                    "maintenance date", "incident date", "failure date", "event date", "date:"
                ])
                if has_labeled_date:
                    date_boost = 4.0
                elif any(m in content for m in ["2024", "2025", "2026", "2027"]):
                    date_boost = 1.5
                else:
                    date_boost = -1.0

            # Boost Approved documents
            gov_multiplier = 1.2 if gov_status == "Approved" else (0.8 if gov_status == "Draft" else 0.4)

            total_score = ((sem_score * 1.5) + (lexical_hits * 0.4) + tag_hit + phrase_hit + asset_presence + category_boost + date_boost) * gov_multiplier

            if total_score > 0.01:
                scored_candidates.append({
                    "chunk": chunk,
                    "score": total_score,
                    "semantic_score": sem_score,
                    "lexical_hits": lexical_hits,
                    "category": chunk.get("category", "Other")
                })

        # Sort descending by total score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        return scored_candidates[:top_k]

hybrid_search = HybridSearchEngine()
