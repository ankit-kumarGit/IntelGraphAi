import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import db_manager
from app.rag.vector_store import vector_store
from app.ai.query_understanding import QueryUnderstandingEngine, KnowledgeScope
from app.models.chat import ChatRequest, DependencyType
from app.ai.orchestrator import orchestrator

@pytest.fixture(autouse=True)
def setup_test_env():
    db_manager.connect()
    vector_store.load()

# =========================================================================
# 1. UNIT TESTS: QueryUnderstandingEngine Context & Dependency Resolution
# =========================================================================

def test_greeting_no_context_leak():
    """Greeting turns must be classified as GREETING with zero customer evidence requirement."""
    analysis = QueryUnderstandingEngine.analyze(
        query="heyy",
        conversation_history=[
            {"role": "user", "content": "What is the calibration frequency of transmitter X-99?"},
            {"role": "assistant", "content": "I don't have enough verified information about this asset to answer that (could not find sufficient information in verified records)."}
        ]
    )
    assert analysis.dependency_type == DependencyType.GREETING
    assert analysis.scope in (KnowledgeScope.GREETING, KnowledgeScope.GENERAL)
    assert analysis.requires_customer_evidence is False
    assert analysis.intent == "GREETING"
    assert "X-99" not in analysis.resolved_query
    assert "calibration" not in analysis.resolved_query

def test_standalone_engineering_query_after_refusal():
    """Asking 'what is bearing??' after an unsupported refusal must remain pure STANDALONE."""
    analysis = QueryUnderstandingEngine.analyze(
        query="what is bearing??",
        conversation_history=[
            {"role": "user", "content": "What is the calibration frequency of transmitter X-99?"},
            {"role": "assistant", "content": "I don't have enough verified information about this asset to answer that."}
        ]
    )
    assert analysis.dependency_type == DependencyType.STANDALONE
    assert analysis.scope == KnowledgeScope.GENERAL
    assert analysis.requires_customer_evidence is False
    assert "X-99" not in analysis.resolved_query

def test_typo_correction_gearing_pump():
    """Typo 'what is gearing pump??' should be mapped to gear pump."""
    analysis = QueryUnderstandingEngine.analyze(
        query="what is gearing pump??",
        conversation_history=[]
    )
    assert analysis.dependency_type == DependencyType.STANDALONE
    assert analysis.typo_correction is not None
    assert analysis.typo_correction["original"] == "gearing pump"
    assert analysis.typo_correction["corrected"] == "gear pump"

def test_context_dependent_followup_failure_modes():
    """Follow-up 'what are its common failure modes?' after gear pump must resolve to gear pump failure modes."""
    history = [
        {"role": "user", "content": "what is gearing pump??"},
        {"role": "assistant", "content": "A gear pump is a rotating positive displacement pump..."}
    ]
    analysis = QueryUnderstandingEngine.analyze(
        query="what are its common failure modes?",
        conversation_history=history
    )
    assert analysis.dependency_type == DependencyType.CONTEXT_DEPENDENT
    assert "gear pump" in analysis.resolved_query.lower()

def test_hybrid_resolution_p101_failure_modes():
    """Asking 'Which of those apply to P-101?' after failure modes discussion must resolve to HYBRID."""
    history = [
        {"role": "user", "content": "what is gearing pump??"},
        {"role": "assistant", "content": "A gear pump is a rotating positive displacement pump..."},
        {"role": "user", "content": "what are its common failure modes?"},
        {"role": "assistant", "content": "Common failure modes include gear tooth wear, casing scoring..."}
    ]
    analysis = QueryUnderstandingEngine.analyze(
        query="Which of those apply to P-101?",
        conversation_history=history
    )
    assert analysis.dependency_type == DependencyType.HYBRID
    assert analysis.scope == KnowledgeScope.HYBRID
    assert "P-101" in analysis.referenced_asset_tags
    assert analysis.requires_customer_evidence is True

def test_coreference_what_does_it_do_for_p101():
    """Asking 'What does it do?' right after 'What is machine P-101?' must resolve to P-101."""
    history = [
        {"role": "user", "content": "What is machine P-101?"},
        {"role": "assistant", "content": "P-101 is a critical Centrifugal Feed Pump..."}
    ]
    analysis = QueryUnderstandingEngine.analyze(
        query="What does it do?",
        conversation_history=history
    )
    assert analysis.dependency_type == DependencyType.CONTEXT_DEPENDENT
    assert "P-101" in analysis.referenced_asset_tags
    assert "P-101" in analysis.resolved_query

# =========================================================================
# 2. END-TO-END GOLDEN TEST SEQUENCE (5-Turn Real Orchestration)
# =========================================================================

@pytest.mark.asyncio
async def test_golden_conversational_intelligence_sequence():
    """
    Executes the exact 5-step Golden Sequence from the prompt:
    Step 1: 'What is the calibration frequency of transmitter X-99?' -> Safe Refusal (UNSUPPORTED_CUSTOMER)
    Step 2: 'heyy' -> Conversational greeting, zero X-99 contamination, zero citations (GREETING)
    Step 3: 'what is a bearing?' -> Deep general engineering, zero X-99 contamination, zero citations (GENERAL)
    Step 4: 'what are its common failure modes?' -> Resolves follow-up 'its' to bearing failure modes (GENERAL)
    Step 5: 'which of those apply to P-101?' -> Resolves 'those' to bearing failure modes + P-101 -> HYBRID reasoning
    """
    history = []

    # --- Turn 1: X-99 Calibration Question ---
    t1_req = ChatRequest(query="What is the calibration frequency of transmitter X-99?", conversation_history=history)
    t1_res = orchestrator.route_and_execute(t1_req)
    assert t1_res.refused is True
    assert t1_res.scope in ("UNSUPPORTED_CUSTOMER", "UNSUPPORTED")
    assert "could not find sufficient information" in t1_res.answer.lower()
    history.append({"role": "user", "content": t1_req.query})
    history.append({"role": "assistant", "content": t1_res.answer})

    # --- Turn 2: 'heyy' ---
    t2_req = ChatRequest(query="heyy", conversation_history=history)
    t2_res = orchestrator.route_and_execute(t2_req)
    assert t2_res.refused is False
    assert t2_res.scope in ("GREETING", "GENERAL")
    assert t2_res.dependency_type == "GREETING"
    assert len(t2_res.citations) == 0
    # Crucial assertion: ZERO contamination from Turn 1!
    assert "x-99" not in t2_res.answer.lower()
    assert "calibration" not in t2_res.answer.lower()
    assert "transmitter" not in t2_res.answer.lower()
    assert "in context of our ongoing discussion" not in t2_res.answer.lower()
    assert "intelgraph" in t2_res.answer.lower() or "hello" in t2_res.answer.lower()
    history.append({"role": "user", "content": t2_req.query})
    history.append({"role": "assistant", "content": t2_res.answer})

    # --- Turn 3: 'what is a bearing?' ---
    t3_req = ChatRequest(query="what is a bearing?", conversation_history=history)
    t3_res = orchestrator.route_and_execute(t3_req)
    assert t3_res.refused is False
    assert t3_res.scope == "GENERAL"
    assert t3_res.dependency_type == "STANDALONE"
    assert len(t3_res.citations) == 0
    assert "x-99" not in t3_res.answer.lower()
    assert "in context of our ongoing discussion" not in t3_res.answer.lower()
    assert "bearing" in t3_res.answer.lower()
    assert "rolling element" in t3_res.answer.lower()
    history.append({"role": "user", "content": t3_req.query})
    history.append({"role": "assistant", "content": t3_res.answer})

    # --- Turn 4: 'what are its common failure modes?' ---
    t4_req = ChatRequest(query="what are its common failure modes?", conversation_history=history)
    t4_res = orchestrator.route_and_execute(t4_req)
    assert t4_res.refused is False
    assert t4_res.scope == "GENERAL"
    assert t4_res.dependency_type == "CONTEXT_DEPENDENT"
    assert "x-99" not in t4_res.answer.lower()
    assert "bearing" in t4_res.answer.lower()
    assert ("fatigue" in t4_res.answer.lower() or "seizure" in t4_res.answer.lower() or "iso 15243" in t4_res.answer.lower())
    history.append({"role": "user", "content": t4_req.query})
    history.append({"role": "assistant", "content": t4_res.answer})

    # --- Turn 5: 'which of those apply to P-101?' ---
    t5_req = ChatRequest(query="which of those apply to P-101?", conversation_history=history)
    t5_res = orchestrator.route_and_execute(t5_req)
    assert t5_res.refused is False
    assert t5_res.scope == "HYBRID"
    assert t5_res.dependency_type == "HYBRID"
    assert len(t5_res.citations) >= 1
    assert "x-99" not in t5_res.answer.lower()
    assert "p-101" in t5_res.answer.lower()
    assert "wo-1189" not in t5_res.answer.lower()
    assert "verified customer evidence" in t5_res.answer.lower()

# =========================================================================
# 3. FASTAPI ROUTE MULTI-TURN VERIFICATION
# =========================================================================

@pytest.mark.asyncio
async def test_api_chat_heyy_no_x99_leak():
    """Verify through the HTTP /api/chat endpoint that greeting returns no X-99 leak."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/chat", json={
            "query": "heyy",
            "conversation_history": [
                {"role": "user", "content": "What is the calibration frequency of transmitter X-99?"},
                {"role": "assistant", "content": "I don't have enough verified information about this asset to answer that."}
            ]
        })
    assert res.status_code == 200
    data = res.json()
    assert data["refused"] is False
    assert data["scope"] in ("GREETING", "GENERAL")
    assert "x-99" not in data["answer"].lower()
    assert "in context of our ongoing discussion" not in data["answer"].lower()
    assert len(data["citations"]) == 0
