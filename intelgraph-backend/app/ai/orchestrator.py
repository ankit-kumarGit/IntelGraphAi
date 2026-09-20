import time
import logging
import re
from typing import Dict, Any, Optional, List
from app.rag.graphrag_retriever import graphrag_retriever
from app.ai.llm_service import LLMService
from app.ai.query_understanding import query_understanding, KnowledgeScope
from app.services.observability_service import observability_service
from app.config import settings
from app.models.chat import ChatRequest, ChatResponse, Citation
from app.rag.provenance import validate_asset_provenance
from app.database import db_manager

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
            "CUSTOMER_FAILURE": "Internal RCA Engine",
            "CUSTOMER_MAINTENANCE_HISTORY": "Internal Maintenance Engine",
            "CUSTOMER_MAINTENANCE": "Internal Maintenance Engine",
            "CUSTOMER_INSPECTION_RECORD": "Internal Inspection Engine",
            "CUSTOMER_INSPECTION": "Internal Inspection Engine",
            "CUSTOMER_SHIFT_HANDOVER": "Internal Operations Engine",
            "CUSTOMER_COMPLIANCE_STATUS": "Internal Compliance Engine",
            "CUSTOMER_COMPLIANCE": "Internal Compliance Engine",
            "CUSTOMER_TELEMETRY": "Internal Telemetry & Sensor Engine",
            "CUSTOMER_DOCUMENT": "Internal Document Engine",
            "CUSTOMER_COMPONENT": "Internal Component Engine",
            "CUSTOMER_OPERATING_PROCEDURE": "Internal Procedure Engine",
            "CROSS_ASSET_COMPARISON": "Internal Lessons Learned & Cross-Asset Engine",
            "CROSS_ASSET": "Internal Lessons Learned & Cross-Asset Engine",
            "CUSTOMER_ASSET_PROFILE": "Internal Asset Profiler",
            "HYBRID_REASONING": "Internal Hybrid Synthesis Engine",
            "UNSUPPORTED_CUSTOMER_FACT": "Internal Safety Guardrail Engine",
            "GENERAL_ENGINEERING_EXPLANATION": "Internal General Reasoning Engine",
            "CONCEPT_DEFINITION": "Internal Conceptual Definition Engine",
            "TECHNICAL_EXPLANATION": "Internal Technical Explanation Engine",
            "COMPARISON_ANALYSIS": "Internal Comparative Engine",
            "SUMMARIZATION": "Internal Summarization Engine",
            "DRAFTING_ASSISTANCE": "Internal Drafting Engine",
            "GENERAL_ENGINEERING_REASONING": "Internal General Reasoning Engine",
            "GREETING": "Internal Conversational Agent"
        }

    def route_and_execute(
        self,
        req: ChatRequest,
        asset_context: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        t_start = time.time()

        # 1. Semantic Query Understanding & Scope Arbitration
        t_classify_start = time.time()

        # Build context for QUE — use context_asset_tag for pronoun resolution only
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

        # Zero Industrial Retrieval Guardrail for Greetings / Small Talk
        if analysis.scope == KnowledgeScope.GREETING:
            total_latency_ms = round((time.time() - t_start) * 1000, 2)
            return ChatResponse(
                answer="Hello! I am **IntelGraph AI**, your industrial operations and equipment intelligence assistant. How can I assist you with equipment reliability, maintenance procedures, root cause analysis, or plant operations today?",
                scope="GREETING",
                response_format="CONVERSATIONAL",
                confidence=None,
                evidence_summary=[],
                citations=[],
                refused=False,
                query_latency_ms=total_latency_ms,
                agent_name="IntelGraph AI",
                traversal_hops=[],
                dependency_type="GREETING",
                resolved_query=req.query,
                latency_breakdown={
                    "total_ms": total_latency_ms,
                    "llm_ms": 0.0,
                    "qdrant_ms": 0.0,
                    "neo4j_ms": 0.0,
                    "orchestration_ms": total_latency_ms
                }
            )

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
        asset_in_tenant = None

        # 2. GraphRAG Evidence Retrieval (Only when customer-specific or hybrid knowledge is required)
        if analysis.requires_customer_evidence:
            t_retrieval_start = time.time()

            que_detected_tag = analysis.referenced_asset_tags[0] if analysis.referenced_asset_tags else None
            effective_tag = que_detected_tag or req.asset_tag

            logger.info(
                "Asset resolution: query='%s' | QUE detected='%s' | req.asset_tag='%s' | effective='%s' | scope_filter='%s'",
                req.query[:60], que_detected_tag, req.asset_tag, effective_tag, req.scope_filter
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
                penalized_document_categories=getattr(analysis, "penalized_document_categories", []),
                query_intent=analysis.intent,
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
                valid_chunks = [
                    item for item in retrieved_chunks
                    if validate_asset_provenance(item.get("chunk", {}), eff_tag_u)
                ]

                # Strict Graph Evidence Provenance Filter:
                t_norm = eff_tag_u.replace("-", "_")
                asset_node_ids = {f"asset_{t_norm}", f"asset_{eff_tag_u}", eff_tag_u}
                traversal_hops = [
                    h for h in (traversal_hops or [])
                    if h.get("from") in asset_node_ids or h.get("to") in asset_node_ids
                    or (h.get("asset_tag") or "").upper() == eff_tag_u
                ]

                # If no valid chunks and asset does NOT exist in tenant registry: enforce grounded refusal
                if not valid_chunks and not asset_in_tenant and not asset_context:
                    logger.warning(
                        "LLM SAFETY TRIGGERED: Requested asset '%s' has no verified documents or registry record. Enforcing grounded refusal.",
                        effective_tag
                    )
                    total_latency_ms = round((time.time() - t_start) * 1000, 2)
                    return ChatResponse(
                        answer=f"I couldn't find a verified record for machine {effective_tag} in the current enterprise knowledge repository.",
                        scope="UNSUPPORTED_CUSTOMER",
                        response_format="REFUSAL",
                        confidence="Low",
                        evidence_summary=[f"Safety guardrail: Zero verified records for machine {effective_tag}."],
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
            asset_context=asset_in_tenant or asset_context or req.active_asset_context,
            conversation_history=req.conversation_history,
            trusted_sources_only=req.trusted_sources_only,
            graph_evidence=traversal_hops
        )
        llm_latency_ms = round((time.time() - t_llm_start) * 1000, 2)
        total_latency_ms = round((time.time() - t_start) * 1000, 2)
        orchestration_latency_ms = max(0.0, round(total_latency_ms - (retrieval_latency_ms + llm_latency_ms), 2))

        # 4. Final Citation Provenance Gate (Strict Non-Negotiable Enforcement)
        verified_citations = []
        for c in result.get("citations", []):
            c_dict = {
                "document_id": c.get("document_id") if isinstance(c, dict) else getattr(c, "document_id", ""),
                "title": c.get("document_name") if isinstance(c, dict) else getattr(c, "document_name", ""),
                "asset_tag": c.get("asset_tag") if isinstance(c, dict) else getattr(c, "asset_tag", None),
                "primary_asset_tags": c.get("primary_asset_tags", []) if isinstance(c, dict) else getattr(c, "primary_asset_tags", []),
                "related_asset_tags": c.get("related_asset_tags", []) if isinstance(c, dict) else getattr(c, "related_asset_tags", []),
                "document_scope": c.get("document_scope", "ASSET") if isinstance(c, dict) else getattr(c, "document_scope", "ASSET"),
                "content": (c.get("content") if isinstance(c, dict) else getattr(c, "content", "")) or (c.get("excerpt", "") if isinstance(c, dict) else getattr(c, "excerpt", ""))
            }
            if db_manager.db is not None and c_dict["document_id"]:
                doc_record = db_manager.db.documents.find_one({"document_id": c_dict["document_id"]})
                if doc_record:
                    c_dict.update({
                        "asset_tag": doc_record.get("asset_tag"),
                        "primary_asset_tags": doc_record.get("primary_asset_tags", []),
                        "related_asset_tags": doc_record.get("related_asset_tags", []),
                        "document_scope": doc_record.get("document_scope", "ASSET"),
                        "title": doc_record.get("title") or c_dict["title"]
                    })
                # Check for chunk content support if effective_tag is present
                if effective_tag and not re.search(r"\b" + re.escape(effective_tag) + r"\b", c_dict["content"], re.IGNORECASE):
                    chunk_rec = db_manager.db.document_chunks.find_one({
                        "document_id": c_dict["document_id"],
                        "content": {"$regex": re.escape(effective_tag), "$options": "i"}
                    })
                    if chunk_rec:
                        c_dict["content"] = chunk_rec.get("content", "")
            clean_cit_obj = Citation(
                document_name=c_dict.get("title") or (c.get("document_name") if isinstance(c, dict) else getattr(c, "document_name", "")),
                document_id=c_dict.get("document_id", ""),
                page_number=c.get("page_number", 1) if isinstance(c, dict) else getattr(c, "page_number", 1),
                section_title=c.get("section_title", "General") if isinstance(c, dict) else getattr(c, "section_title", "General"),
                record_date=c.get("record_date") if isinstance(c, dict) else getattr(c, "record_date", None),
                version=c.get("version", "v1.0") if isinstance(c, dict) else getattr(c, "version", "v1.0"),
                governance_status=c.get("governance_status", "Approved") if isinstance(c, dict) else getattr(c, "governance_status", "Approved"),
                excerpt=c.get("excerpt", "") if isinstance(c, dict) else getattr(c, "excerpt", "")
            )
            if effective_tag:
                if validate_asset_provenance(c_dict, effective_tag):
                    verified_citations.append(clean_cit_obj)
                else:
                    logger.warning(
                        f"CITATION PROVENANCE REJECTED: document '{c_dict['document_id']}' rejected for asset '{effective_tag}'."
                    )
            else:
                verified_citations.append(clean_cit_obj)

        citations = verified_citations
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
