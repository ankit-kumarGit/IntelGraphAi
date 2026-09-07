import time
from typing import Optional
from app.models.chat import ChatRequest, ChatResponse, Citation
from app.rag.hybrid_search import hybrid_search
from app.ai.llm_service import LLMService

class KnowledgeAssistant:
    @staticmethod
    def answer_query(req: ChatRequest, asset_context: Optional[dict] = None) -> ChatResponse:
        start_time = time.time()
        
        # 1. Retrieve relevant chunks via hybrid search
        retrieved = hybrid_search.search(
            query=req.query,
            asset_tag=req.asset_tag,
            trusted_sources_only=req.trusted_sources_only,
            top_k=5
        )

        # 2. Synthesize answer with LLM Service
        result = LLMService.generate_grounded_answer(
            query=req.query,
            retrieved_chunks=retrieved,
            asset_context=asset_context,
            trusted_sources_only=req.trusted_sources_only
        )

        latency_ms = round((time.time() - start_time) * 1000, 2)

        citations = [Citation(**c) for c in result.get("citations", [])]

        return ChatResponse(
            answer=result["answer"],
            confidence=result.get("confidence", "High"),
            evidence_summary=result.get("evidence_summary", []),
            citations=citations,
            refused=result.get("refused", False),
            query_latency_ms=latency_ms
        )

knowledge_assistant = KnowledgeAssistant()
