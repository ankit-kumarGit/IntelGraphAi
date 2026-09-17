import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.chat import ChatRequest
from app.rag.graphrag_retriever import graphrag_retriever
from app.rag.hybrid_search import hybrid_search
from app.services.neo4j_service import neo4j_graph
from app.services.doc_service import doc_service
from app.ai.orchestrator import orchestrator

from app.config import settings

@pytest.mark.asyncio
async def test_tenant_isolation_api_documents():
    """Verify that document API queries scoped to Tenant B cannot retrieve Tenant A documents."""
    primary_tenant = getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Tenant Primary (valid tenant)
        res_apex = await ac.get(f"/api/documents?tenant_id={primary_tenant}")
        assert res_apex.status_code == 200

        # Tenant B (isolated foreign tenant)
        res_tenant_b = await ac.get("/api/documents?tenant_id=tenant_b")
        assert res_tenant_b.status_code == 200
        docs_b = res_tenant_b.json()
        assert len(docs_b) == 0, "Tenant B must NOT retrieve Tenant Apex documents"

def test_tenant_isolation_doc_service():
    """Verify that DocumentService strictly enforces tenant isolation."""
    # Direct get with tenant_apex vs tenant_b
    doc_apex = doc_service.get_document("Pump_P101_OEM_Manual", tenant_id="tenant_apex")
    if doc_apex:
        assert doc_apex.get("tenant_id", "tenant_apex") == "tenant_apex"

    doc_b = doc_service.get_document("Pump_P101_OEM_Manual", tenant_id="tenant_b")
    assert doc_b is None, "Document lookup for Tenant B must return None for Tenant Apex documents"

def test_tenant_isolation_vector_hybrid_search():
    """Verify that HybridSearchEngine filters out chunks belonging to other tenants."""
    candidates_b = hybrid_search.search(
        query="operating temperature limit P-101",
        asset_tag="P-101",
        tenant_id="tenant_b"
    )
    assert len(candidates_b) == 0, "Hybrid search for Tenant B must not retrieve Tenant Apex chunks"

def test_tenant_isolation_neo4j_subgraph():
    """Verify that Neo4jKnowledgeGraph traversal refuses cross-tenant retrieval."""
    subgraph_b = neo4j_graph.get_subgraph("P-101", tenant_id="tenant_b")
    assert len(subgraph_b["nodes"]) == 0, "Neo4j subgraph for Tenant B must not return Tenant Apex nodes"
    assert len(subgraph_b["edges"]) == 0, "Neo4j subgraph for Tenant B must not return Tenant Apex edges"

def test_tenant_isolation_ai_orchestrator_chat():
    """Verify that an AI query from Tenant B about Tenant A asset P-101 is safely refused."""
    req_b = ChatRequest(
        query="What is the rated motor power of pump P-101?",
        asset_tag="P-101",
        tenant_id="tenant_b"
    )
    res_b = orchestrator.route_and_execute(req_b)
    assert res_b.refused is True, "AI must refuse to disclose Tenant Apex asset details to Tenant B"
    assert res_b.scope == "UNSUPPORTED_CUSTOMER"
    assert len(res_b.citations) == 0

    # Primary Tenant request succeeds with citations
    primary_tenant = getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")
    req_apex = ChatRequest(
        query="What is the rated motor power of pump P-101?",
        asset_tag="P-101",
        tenant_id=primary_tenant
    )
    res_apex = orchestrator.route_and_execute(req_apex)
    assert res_apex.refused is False
    assert len(res_apex.citations) > 0
    assert "p-101" in res_apex.answer.lower()

