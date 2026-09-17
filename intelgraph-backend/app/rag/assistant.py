import time
from typing import Optional
from app.models.chat import ChatRequest, ChatResponse
from app.ai.orchestrator import orchestrator

class KnowledgeAssistant:
    @staticmethod
    def answer_query(req: ChatRequest, asset_context: Optional[dict] = None) -> ChatResponse:
        """
        Routes user query through AI Orchestrator with GraphRAG (Qdrant + Neo4j) evidence.
        """
        return orchestrator.route_and_execute(req, asset_context=asset_context)

knowledge_assistant = KnowledgeAssistant()
