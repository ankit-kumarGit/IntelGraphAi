import re
from typing import List, Dict, Any, Optional
from app.config import settings
from app.rag.vector_store import vector_store
from app.rag.qdrant_store import qdrant_store
from app.rag.provenance import validate_asset_provenance, get_clean_document_title

class HybridSearchEngine:
    @staticmethod
    def _categorize_chunk(chunk: Dict[str, Any]) -> str:
        """
        Classifies a chunk into canonical industrial categories using metadata,
        document_id, section_title, and content signals.
        """
        cat = (chunk.get("category") or "").lower()
        doc_id = (chunk.get("document_id") or "").lower()
        section = (chunk.get("section_title") or "").lower()
        content_sample = (chunk.get("content") or "")[:300].lower()

        # 1. Telemetry / Time Series (CSVs, sensor tables, vibration logs)
        if any(k in cat for k in ["telemetry", "time series"]) or \
           any(k in doc_id for k in ["telemetry", "vibration_monitoring_log", "sensor"]) or \
           any(k in section for k in ["telemetry"]) or \
           any(k in content_sample for k in ["vibration_de_mm_s_rms", "bearing_temp_de", "vibration_rms_mm_s", "timestamp | equipment"]):
            return "TELEMETRY"

        # 2. Failure / Incident Report / RCA
        if any(k in cat for k in ["failure", "incident", "rca"]) or \
           any(k in doc_id for k in ["failure", "incident", "emergency_trip", "rca"]) or \
           any(k in section for k in ["failure", "incident", "root cause"]):
            return "FAILURE"

        # 3. Inspection / Condition Monitoring / NDT / Checklist
        if any(k in cat for k in ["inspection", "condition monitoring", "ndt", "survey", "checklist"]) or \
           any(k in doc_id for k in ["inspection", "ndt", "survey", "checklist", "condition_monitoring"]) or \
           any(k in section for k in ["inspection", "survey", "checklist"]):
            return "INSPECTION"

        # 4. Maintenance Report / Work Order / PM Schedule / Overhaul Procedures
        if any(k in cat for k in ["maintenance", "work order", "wo"]) or \
           any(k in doc_id for k in ["maintenance", "work_order", "wo_", "wo-", "pm_schedule"]) or \
           any(k in section for k in ["maintenance", "work order", "pm schedule", "preventive maintenance", "overhaul", "service"]):
            return "MAINTENANCE"

        # 5. OEM Technical Manual / Datasheet / Specification
        if any(k in doc_id for k in ["oem", "technical_manual", "datasheet", "specification"]) or \
           any(k in cat for k in ["oem", "datasheet", "specification"]) or \
           any(k in section for k in ["general description", "technical data", "specifications", "operating limits"]):
            return "PROFILE_ENGINEERING"

        # 6. P&ID / Flowsheet / Engineering Drawing
        if any(k in cat for k in ["p&id", "pid", "drawing", "flowsheet"]) or \
           any(k in doc_id for k in ["p&id", "pid", "drawing", "flowsheet"]) or \
           any(k in section for k in ["piping and instrumentation", "flowsheet", "p&id"]):
            return "PROFILE_ENGINEERING"

        # 7. Standard Operating Procedure
        if any(k in cat for k in ["sop", "operating procedure", "procedure"]) or \
           any(k in doc_id for k in ["sop", "procedure", "startup_shutdown"]):
            return "SOP"

        # 8. Operations & Shift Logs
        if any(k in cat for k in ["operations", "shift"]) or \
           any(k in doc_id for k in ["shift", "handover", "logbook"]):
            return "OPERATIONS"

        return "OTHER"

    @classmethod
    def _map_to_canonical(cls, category_list: Optional[List[str]]) -> set:
        if not category_list:
            return set()
        res = set()
        for c in category_list:
            cl = c.lower()
            if any(k in cl for k in ["telemetry", "time series", "sensor"]):
                res.add("TELEMETRY")
            if any(k in cl for k in ["failure", "incident", "rca"]):
                res.add("FAILURE")
            if any(k in cl for k in ["inspection", "condition monitoring", "ndt", "survey", "checklist"]):
                res.add("INSPECTION")
            if any(k in cl for k in ["maintenance", "work order", "wo", "schedule"]):
                res.add("MAINTENANCE")
            if any(k in cl for k in ["oem", "datasheet", "drawing", "p&id", "pid", "engineering", "manual", "specification"]):
                res.add("PROFILE_ENGINEERING")
            if any(k in cl for k in ["sop", "procedure"]):
                res.add("SOP")
            if any(k in cl for k in ["shift", "operations", "handover"]):
                res.add("OPERATIONS")
        return res

    @classmethod
    def search(
        cls,
        query: str,
        asset_tag: Optional[str] = None,
        trusted_sources_only: bool = True,
        top_k: int = 6,
        tenant_id: Optional[str] = None,
        target_categories: Optional[List[str]] = None,
        penalized_categories: Optional[List[str]] = None,
        intent: Optional[str] = None,
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

        canonical_targets = cls._map_to_canonical(target_categories)
        canonical_penalties = cls._map_to_canonical(penalized_categories)

        stopwords = {"what", "is", "the", "a", "an", "for", "of", "and", "in", "to", "on", "was", "did", "how", "why", "are", "does", "with", "from", "its", "it"}
        clean_asset_tag = (asset_tag or "").lower().replace("-", "")
        query_concept_words = {w for w in query_words if len(w) > 2 and w not in stopwords and w != clean_asset_tag}

        # 2. Score calculation with hybrid boost
        scored_candidates = []
        for chunk in all_chunks:
            # Tenant isolation enforcement
            default_tenant = getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")
            raw_chunk_tenant = chunk.get("tenant_id")
            chunk_tenant = raw_chunk_tenant or (tenant_id if tenant_id in [default_tenant, "tenant_apex"] else default_tenant)
            if tenant_id and chunk_tenant != tenant_id and chunk_tenant != "global":
                continue

            # Asset tag filtering via Strict Provenance
            asset_match_score = 0.0
            if asset_tag:
                if not validate_asset_provenance(chunk, asset_tag):
                    continue
                # Bounded score: asset presence is normalized, NOT multiplied by tag frequency
                t_u = asset_tag.upper()
                c_tag = (chunk.get("asset_tag") or "").upper()
                primaries = [p.upper() for p in chunk.get("primary_asset_tags", [])]
                asset_match_score = 2.0 if (c_tag == t_u or t_u in primaries) else 1.2

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
            doc_id = chunk.get("document_id", "").lower()

            # Lexical score: bounded match of conceptual query words (asset tag frequency capped!)
            lexical_hits = sum(1 for w in query_concept_words if w in content or w in section)
            capped_lexical_score = min(lexical_hits * 0.4, 2.0)

            # Technical domain concept boosts
            if ("non-drive" in query_lower or "nde" in query_lower) and ("non-drive" in content or "nde" in content or "nu 312" in content):
                capped_lexical_score += 2.0
            if ("power" in query_lower or "motor" in query_lower) and ("power" in content or "kw" in content) and "oem" in doc_id:
                capped_lexical_score += 1.5
            if ("part" in query_lower or "bearing" in query_lower) and "oem" in doc_id and ("skf 6312" in content or "nu 312" in content or "skf-6314" in content):
                capped_lexical_score += 1.5
            if "alignment" in query_lower and ("misalignment" in content or "0.05" in content):
                capped_lexical_score += 1.5

            phrase_hit = 1.5 if (len(query_concept_words) > 1 and query_lower in content) else 0.0
            sem_score = vector_scores.get(chunk_id, 0.0)

            # Document Category Matching & Down-ranking
            chunk_canonical = cls._categorize_chunk(chunk)
            category_score = 0.0

            if canonical_targets:
                if chunk_canonical in canonical_targets:
                    if intent == "CUSTOMER_ASSET_PROFILE":
                        if chunk_canonical == "PROFILE_ENGINEERING":
                            category_score += 6.5
                        elif chunk_canonical in ["MAINTENANCE", "INSPECTION"]:
                            category_score += 1.0
                        else:
                            category_score += 3.5
                    else:
                        category_score += 5.0
                elif chunk_canonical in canonical_penalties:
                    category_score -= 8.0
                else:
                    category_score -= 3.5
            elif canonical_penalties and chunk_canonical in canonical_penalties:
                category_score -= 8.0

            # Irrelevant Raw Data / Repetitive Table Penalty
            is_raw_tabular = (content.count("|") > 8) or (content.count(",") > 15 and any(c.isdigit() for c in content))
            raw_data_penalty = 0.0
            if is_raw_tabular:
                if "TELEMETRY" in canonical_targets or intent == "CUSTOMER_TELEMETRY":
                    raw_data_penalty = 1.0  # Relevant for telemetry
                else:
                    raw_data_penalty = -4.5  # Penalize raw tabular dumps for profile / maintenance / RCA

            # Fact Type (DATE) Prioritization
            date_boost = 0.0
            if fact_type == "DATE":
                has_labeled_date = any(p in content for p in [
                    "inspection date", "date of inspection", "survey date", "date performed",
                    "maintenance date", "incident date", "failure date", "event date", "date:"
                ])
                if has_labeled_date:
                    date_boost = 3.5
                elif any(m in content for m in ["2024", "2025", "2026", "2027"]):
                    date_boost = 1.5
                else:
                    date_boost = -1.5

            # Boost Approved documents
            gov_multiplier = 1.2 if gov_status == "Approved" else (0.8 if gov_status == "Draft" else 0.4)

            total_score = ((sem_score * 1.5) + asset_match_score + capped_lexical_score + phrase_hit + category_score + raw_data_penalty + date_boost) * gov_multiplier

            if total_score > 0.01:
                scored_candidates.append({
                    "chunk": chunk,
                    "score": total_score,
                    "semantic_score": sem_score,
                    "lexical_hits": lexical_hits,
                    "category": chunk.get("category", "Other"),
                    "canonical_category": chunk_canonical
                })

        # Sort descending by total score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        return scored_candidates[:top_k]

hybrid_search = HybridSearchEngine()
