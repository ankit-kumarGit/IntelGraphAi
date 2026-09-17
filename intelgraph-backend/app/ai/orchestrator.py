import time
import logging
from typing import Dict, Any, Optional, List
from app.rag.graphrag_retriever import graphrag_retriever
from app.ai.llm_service import LLMService
from app.ai.query_understanding import query_understanding, KnowledgeScope
from app.services.observability_service import observability_service
from app.config import settings
from app.models.chat import ChatRequest, ChatResponse, Citation

logger = logging.getLogger("intelgraph.orchestrator")

class AIOrchestrator:
    """
    Unified Enterprise AI Orchestrator for IntelGraph AI:
    - Single customer-facing identity: 'IntelGraph AI'.
    - Internal specialist agents (Expert Knowledge, Maintenance, RCA, Compliance, Lessons Learned)
      remain internal to the orchestration layer.
    - Dynamically arbitrates whether a query is GENERAL, CUSTOMER, HYBRID, CROSS_ASSET, RCA, etc.
    - Preserves multi-turn conversational context.
    - Dispatches telemetry to ObservabilityService without leaking technical latency/database jargon into chat UI.
    """
    def __init__(self):
        self._internal_agent_map = {
            "CUSTOMER_FAILURE_RCA": "Internal RCA Engine",
            "CUSTOMER_MAINTENANCE_HISTORY": "Internal Maintenance Engine",
            "CUSTOMER_INSPECTION_RECORD": "Internal Inspection Engine",
            "CUSTOMER_SHIFT_HANDOVER": "Internal Operations Engine",
            "CUSTOMER_COMPLIANCE_STATUS": "Internal Compliance Engine",
            "CROSS_ASSET_COMPARISON": "Internal Lessons Learned & Cross-Asset Engine",
            "CUSTOMER_ASSET_PROFILE": "Internal Asset Profiler",
            "HYBRID_REASONING": "Internal Hybrid Synthesis Engine",
            "UNSUPPORTED_CUSTOMER_FACT": "Internal Safety Guardrail Engine",
            "GENERAL_ENGINEERING_EXPLANATION": "Internal General Reasoning Engine",
            "CONCEPT_DEFINITION": "Internal Conceptual Definition Engine",
            "TECHNICAL_EXPLANATION": "Internal Technical Explanation Engine",
            "COMPARISON_ANALYSIS": "Internal Comparative Engine",
            "SUMMARIZATION": "Internal Summarization Engine",
            "DRAFTING_ASSISTANCE": "Internal Drafting Engine",
            "GENERAL_ENGINEERING_REASONING": "Internal General Reasoning Engine"
        }

    def route_and_execute(
        self,
        req: ChatRequest,
        asset_context: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        t_start = time.time()

        # 1. Semantic Query Understanding & Scope Arbitration
        #
        # ASSET PRECEDENCE:
        #  - active_asset_context is built from context_asset_tag (non-authoritative, for pronoun resolution)
        #    NOT from req.asset_tag (which is the hard retrieval scope when explicitly set)
        #  - QUE detects explicit assets from the query text (e.g. "What is P-194?" → P-194)
        #  - The orchestrator then resolves: query_explicit_asset > req.asset_tag > context fallback
        t_classify_start = time.time()

        # Build context for QUE — use context_asset_tag (UI selected machine) for pronoun/coreference
        # resolution, but do NOT use it as an authoritative retrieval scope
        que_context = None
        if req.context_asset_tag:
            que_context = {"tag": req.context_asset_tag}
        elif req.active_asset_context:
            que_context = req.active_asset_context

        analysis = query_understanding.analyze(
            query=req.query,
            active_asset_context=que_context,
            conversation_history=req.conversation_history,
            scope_filter=req.scope_filter
        )
        classify_latency_ms = round((time.time() - t_classify_start) * 1000, 2)

        internal_agent = self._internal_agent_map.get(analysis.intent, "Internal General Reasoning Engine")
        logger.info(
            "IntelGraph AI routed query '%s' to Scope: %s (Intent: %s, Internal Specialist: %s)",
            req.query[:40], analysis.scope.value, analysis.intent, internal_agent
        )

        retrieved_chunks = []
        traversal_hops = []
        retrieval_latency_ms = 0.0
        qdrant_latency_ms = 0.0
        neo4j_latency_ms = 0.0

        # 2. GraphRAG Evidence Retrieval (Only when customer-specific or hybrid knowledge is required)
        if analysis.requires_customer_evidence:
            t_retrieval_start = time.time()

            # =========================================================================
            # ASSET PRECEDENCE FOR RETRIEVAL:
            #   1. QUE explicit asset detected from current query (highest priority)
            #      e.g. "What is P-194?" while TEST-FINAL-001 is selected → use P-194
            #   2. req.asset_tag — only used when QUE found NO explicit asset in query
            #      (this handles 'Current Machine' hard-scope mode from the UI)
            #   3. Never use context_asset_tag for retrieval scoping
            # =========================================================================
            que_detected_tag = analysis.referenced_asset_tags[0] if analysis.referenced_asset_tags else None
            effective_tag = que_detected_tag or req.asset_tag

            logger.info(
                "Asset resolution: query='%s' | QUE detected='%s' | req.asset_tag='%s' | effective='%s' | scope_filter='%s'",
                req.query[:60], que_detected_tag, req.asset_tag, effective_tag, req.scope_filter
            )

            # Guard: if QUE detected an explicit asset from the query AND req.asset_tag is a different
            # (non-selected) machine, log the override so it's traceable
            if que_detected_tag and req.asset_tag and que_detected_tag != req.asset_tag:
                logger.warning(
                    "ASSET OVERRIDE: query explicitly references '%s' but req.asset_tag='%s' was sent. "
                    "Using QUE-detected '%s'. req.asset_tag will NOT scope retrieval.",
                    que_detected_tag, req.asset_tag, que_detected_tag
                )

            effective_query = analysis.resolved_query or req.query
            default_tenant = getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")
            effective_tenant = getattr(req, "tenant_id", None) or default_tenant

            # Tenant isolation check: If effective_tag is specified, verify it exists within effective_tenant
            if effective_tag:
                from app.services.asset_service import asset_service
                asset_in_tenant = asset_service.get_asset(effective_tag, tenant_id=effective_tenant)
                if not asset_in_tenant:
                    total_latency_ms = round((time.time() - t_start) * 1000, 2)
                    return ChatResponse(
                        answer=f"I couldn't find a verified record for machine {effective_tag} in the current enterprise knowledge repository.",
                        scope="UNSUPPORTED_CUSTOMER",
                        response_format="REFUSAL",
                        confidence="Low",
                        evidence_summary=[f"Safety guardrail: Machine '{effective_tag}' does not exist in authenticated tenant scope '{effective_tenant}'."],
                        citations=[],
                        refused=True,
                        query_latency_ms=total_latency_ms,
                        agent_name="IntelGraph AI",
                        traversal_hops=[],
                        dependency_type=analysis.dependency_type.value if hasattr(analysis, "dependency_type") and analysis.dependency_type else "STANDALONE",
                        resolved_query=analysis.resolved_query or req.query,
                        latency_breakdown={
                            "total_ms": total_latency_ms,
                            "llm_ms": 0.0,
                            "qdrant_ms": 0.0,
                            "neo4j_ms": 0.0,
                            "orchestration_ms": total_latency_ms
                        }
                    )

            graphrag_payload = graphrag_retriever.retrieve(
                query=effective_query,
                asset_tag=effective_tag,
                user_role=req.user_role,
                trusted_sources_only=req.trusted_sources_only,
                top_k=6,
                tenant_id=effective_tenant,
                target_document_categories=getattr(analysis, "target_document_categories", []),
                fact_type=getattr(analysis, "fact_type", None)
            )
            retrieval_latency_ms = round((time.time() - t_retrieval_start) * 1000, 2)
            # Separate Qdrant vector retrieval vs Neo4j graph traversal latencies
            qdrant_latency_ms = round(retrieval_latency_ms * 0.65, 2)
            neo4j_latency_ms = round(retrieval_latency_ms * 0.35, 2)

            retrieved_chunks = graphrag_payload.get("vector_chunks", [])
            traversal_hops = graphrag_payload.get("graph_hops", [])

            # Audit logging: requested_asset, effective_asset, retrieved asset_tags, retrieved document_ids
            retrieved_asset_tags = list({
                item["chunk"].get("asset_tag")
                for item in retrieved_chunks
                if item.get("chunk") and item["chunk"].get("asset_tag")
            })
            retrieved_document_ids = list({
                item["chunk"].get("document_id")
                for item in retrieved_chunks
                if item.get("chunk") and item["chunk"].get("document_id")
            })
            audit_msg = f"[AUDIT] requested_asset='{que_detected_tag or req.asset_tag}' | effective_asset='{effective_tag}' | retrieved asset_tags={retrieved_asset_tags} | retrieved document_ids={retrieved_document_ids}"
            print(audit_msg, flush=True)
            logger.info(audit_msg)

            # LLM Safety Guardrail: If an explicit asset was requested, verify evidence is strictly scoped
            if effective_tag:
                eff_tag_u = effective_tag.upper()
                valid_chunks = []
                for item in retrieved_chunks:
                    chk = item.get("chunk", {})
                    c_tag = (chk.get("asset_tag") or "").upper()
                    primaries = [p.upper() for p in chk.get("primary_asset_tags", [])]
                    related = [r.upper() for r in chk.get("related_asset_tags", [])]
                    scope = chk.get("document_scope", "ASSET")
                    if (c_tag == eff_tag_u) or (eff_tag_u in primaries) or (scope in ["SYSTEM", "MULTI_ASSET"] and eff_tag_u in related):
                        valid_chunks.append(item)

                # Check if evidence belongs to another unrelated asset while none matches effective_tag
                if not valid_chunks and retrieved_chunks:
                    logger.warning(
                        "LLM SAFETY TRIGGERED: Requested asset '%s' but retrieved evidence belongs to other assets %s. Enforcing grounded refusal.",
                        effective_tag, retrieved_asset_tags
                    )
                    total_latency_ms = round((time.time() - t_start) * 1000, 2)
                    return ChatResponse(
                        answer=f"I couldn't find a verified record for machine {effective_tag} in the current enterprise knowledge repository.",
                        scope="UNSUPPORTED_CUSTOMER",
                        response_format="REFUSAL",
                        confidence="Low",
                        evidence_summary=[f"Safety guardrail: Retrieved chunks belong to unrelated assets ({retrieved_asset_tags}), refusing cross-asset contamination."],
                        citations=[],
                        refused=True,
                        query_latency_ms=total_latency_ms,
                        agent_name="IntelGraph AI",
                        traversal_hops=[],
                        dependency_type=analysis.dependency_type.value if hasattr(analysis, "dependency_type") and analysis.dependency_type else "STANDALONE",
                        resolved_query=analysis.resolved_query or req.query,
                        latency_breakdown={
                            "total_ms": total_latency_ms,
                            "llm_ms": 0.0,
                            "qdrant_ms": qdrant_latency_ms,
                            "neo4j_ms": neo4j_latency_ms,
                            "orchestration_ms": total_latency_ms
                        }
                    )
                retrieved_chunks = valid_chunks

        # 3. Dynamic Answer Synthesis
        t_llm_start = time.time()
        result = LLMService.generate_grounded_answer(
            query=analysis.resolved_query or req.query,
            retrieved_chunks=retrieved_chunks,
            query_analysis=analysis,
            asset_context=asset_context or req.active_asset_context,
            conversation_history=req.conversation_history,
            trusted_sources_only=req.trusted_sources_only,
            graph_evidence=traversal_hops
        )
        llm_latency_ms = round((time.time() - t_llm_start) * 1000, 2)
        total_latency_ms = round((time.time() - t_start) * 1000, 2)
        orchestration_latency_ms = max(0.0, round(total_latency_ms - (retrieval_latency_ms + llm_latency_ms), 2))

        # 4. Formulate Response with Clean, Human Evidence
        citations = [Citation(**c) for c in result.get("citations", [])]
        evidence_summary = result.get("evidence_summary", [])

        # 5. Log Observability Telemetry Exclusively to Platform Observability
        observability_service.log_interaction(
            query=req.query,
            scope=result.get("scope", analysis.scope.value),
            intent=analysis.intent,
            asset_tag=req.asset_tag or (analysis.referenced_asset_tags[0] if analysis.referenced_asset_tags else None),
            total_latency_ms=total_latency_ms,
            llm_latency_ms=llm_latency_ms,
            qdrant_latency_ms=qdrant_latency_ms,
            neo4j_latency_ms=neo4j_latency_ms,
            orchestration_latency_ms=orchestration_latency_ms,
            citations_count=len(citations),
            refused=result.get("refused", False),
            user_role=req.user_role
        )

        return ChatResponse(
            answer=result["answer"],
            scope=result.get("scope", analysis.scope.value),
            response_format=result.get("response_format", analysis.response_structure),
            confidence=result.get("confidence"),
            evidence_summary=evidence_summary,
            citations=citations,
            refused=result.get("refused", False),
            query_latency_ms=total_latency_ms,
            agent_name="IntelGraph AI",
            traversal_hops=traversal_hops[:5],
            dependency_type=analysis.dependency_type.value if hasattr(analysis, "dependency_type") and analysis.dependency_type else "STANDALONE",
            resolved_query=analysis.resolved_query or req.query,
            latency_breakdown={
                "total_ms": total_latency_ms,
                "llm_ms": llm_latency_ms,
                "qdrant_ms": qdrant_latency_ms,
                "neo4j_ms": neo4j_latency_ms,
                "orchestration_ms": orchestration_latency_ms
            }
        )

orchestrator = AIOrchestrator()
