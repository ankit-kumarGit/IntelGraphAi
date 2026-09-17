import time
from typing import List, Dict, Any, Optional
from collections import deque
from app.database import get_db

class ObservabilityService:
    """
    Enterprise AI Observability Service:
    Tracks end-to-end telemetry across query understanding, Qdrant semantic retrieval,
    Neo4j graph traversal, internal agent orchestration, and LLM answer generation.
    Exposes transparent, separated performance metrics to Platform Administrators.
    """
    def __init__(self, max_buffer_size: int = 200):
        self._buffer: deque = deque(maxlen=max_buffer_size)

    def log_interaction(
        self,
        query: str,
        scope: str,
        intent: str,
        asset_tag: Optional[str],
        total_latency_ms: float,
        llm_latency_ms: float,
        qdrant_latency_ms: float,
        neo4j_latency_ms: float,
        orchestration_latency_ms: float,
        citations_count: int,
        refused: bool,
        user_role: str = "Maintenance Engineer",
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        entry = {
            "id": f"obs_{int(time.time() * 1000)}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "query": query[:120] + ("..." if len(query) > 120 else ""),
            "full_query": query,
            "scope": scope,
            "intent": intent,
            "asset_tag": asset_tag or "Fleet / None",
            "total_latency_ms": round(total_latency_ms, 2),
            "llm_latency_ms": round(llm_latency_ms, 2),
            "qdrant_latency_ms": round(qdrant_latency_ms, 2),
            "neo4j_latency_ms": round(neo4j_latency_ms, 2),
            "orchestration_latency_ms": round(orchestration_latency_ms, 2),
            "citations_count": citations_count,
            "refused": refused,
            "user_role": user_role,
            "error": error
        }

        self._buffer.appendleft(entry)

        # Persist to MongoDB if available
        try:
            db = get_db()
            if db is not None:
                db.ai_observability.insert_one(dict(entry))
        except Exception:
            pass

        return entry

    def get_dashboard_data(self, limit: int = 50) -> Dict[str, Any]:
        logs = list(self._buffer)
        total = len(logs)

        if total == 0:
            return {
                "aggregated": {
                    "total_queries": 0,
                    "avg_total_latency_ms": 0.0,
                    "avg_llm_latency_ms": 0.0,
                    "avg_qdrant_latency_ms": 0.0,
                    "avg_neo4j_latency_ms": 0.0,
                    "avg_orchestration_latency_ms": 0.0,
                    "evidence_coverage_pct": 100.0,
                    "refusal_rate_pct": 0.0,
                    "scope_distribution": {"GENERAL": 0, "CUSTOMER": 0, "HYBRID": 0, "CROSS_ASSET": 0}
                },
                "recent_telemetry": []
            }

        avg_total = round(sum(l["total_latency_ms"] for l in logs) / total, 2)
        avg_llm = round(sum(l["llm_latency_ms"] for l in logs) / total, 2)
        avg_qdrant = round(sum(l["qdrant_latency_ms"] for l in logs) / total, 2)
        avg_neo4j = round(sum(l["neo4j_latency_ms"] for l in logs) / total, 2)
        avg_orch = round(sum(l["orchestration_latency_ms"] for l in logs) / total, 2)

        customer_queries = [l for l in logs if l["scope"] in ("CUSTOMER", "HYBRID", "MAINTENANCE", "RCA", "COMPLIANCE")]
        evidence_cov = (
            round((sum(1 for l in customer_queries if l["citations_count"] > 0) / len(customer_queries)) * 100, 1)
            if customer_queries else 100.0
        )
        refusal_rate = round((sum(1 for l in logs if l["refused"]) / total) * 100, 1)

        scope_dist: Dict[str, int] = {}
        for l in logs:
            s = l["scope"]
            scope_dist[s] = scope_dist.get(s, 0) + 1

        return {
            "aggregated": {
                "total_queries": total,
                "avg_total_latency_ms": avg_total,
                "avg_llm_latency_ms": avg_llm,
                "avg_qdrant_latency_ms": avg_qdrant,
                "avg_neo4j_latency_ms": avg_neo4j,
                "avg_orchestration_latency_ms": avg_orch,
                "evidence_coverage_pct": evidence_cov,
                "refusal_rate_pct": refusal_rate,
                "scope_distribution": scope_dist
            },
            "recent_telemetry": logs[:limit]
        }

observability_service = ObservabilityService()
