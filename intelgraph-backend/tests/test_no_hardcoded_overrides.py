import pytest
from app.ai.llm_service import LLMService
from app.ai.query_understanding import QueryUnderstandingEngine, KnowledgeScope
from app.models.chat import ChatRequest
from app.ai.orchestrator import orchestrator
from app.database import db_manager
from app.rag.vector_store import vector_store

@pytest.fixture(autouse=True)
def setup_env():
    db_manager.connect()
    vector_store.load()

# =========================================================================
# PROOF 1: P-101 question no longer returns the old hardcoded P-101 answer
# =========================================================================
def test_p101_no_hardcoded_answer():
    old_p101_hardcoded_markers = [
        "abc pumps model xyz-200",
        "18.5 hours of unplanned downtime",
        "line 101-a connects the p-101 discharge",
        "work order #1189",
        "work order #1023",
        "condition monitoring survey #insp-492",
        "oem technical manual (xyz-200)"
    ]

    analysis = QueryUnderstandingEngine.analyze("What is the motor power and downtime of P-101?", conversation_history=[])

    # Case A: Without retrieved chunks -> Must refuse, never return hardcoded answer
    res_no_chunks = LLMService.generate_grounded_answer(
        query="What is the motor power and downtime of P-101?",
        retrieved_chunks=[],
        query_analysis=analysis
    )
    assert res_no_chunks["refused"] is True
    assert res_no_chunks["response_format"] == "REFUSAL"
    for marker in old_p101_hardcoded_markers:
        assert marker not in res_no_chunks["answer"].lower(), f"Found old hardcoded marker '{marker}' in refusal answer!"

    # Case B: With specific retrieved chunk -> Answers using ONLY provided chunk, not hardcoded text
    custom_chunk = [{
        "chunk": {
            "document_id": "P101_Custom_Inspection_2026",
            "page_number": 1,
            "section_title": "Electrical Audit",
            "content": "P-101 operates with a 45 kW motor and experienced 1.5 hours of downtime during scheduled sensor recalibration.",
            "record_date": "2026-09-01",
            "version": "v1.0",
            "governance_status": "Approved"
        },
        "score": 0.95
    }]
    res_with_chunk = LLMService.generate_grounded_answer(
        query="What is the motor power and downtime of P-101?",
        retrieved_chunks=custom_chunk,
        query_analysis=analysis
    )
    assert res_with_chunk["refused"] is False
    assert "45 kw" in res_with_chunk["answer"].lower()
    assert "1.5 hours" in res_with_chunk["answer"].lower()
    for marker in old_p101_hardcoded_markers:
        assert marker not in res_with_chunk["answer"].lower(), f"Found old hardcoded marker '{marker}' in grounded answer!"


# =========================================================================
# PROOF 2: P-194 and P-194B questions no longer return hardcoded responses
# =========================================================================
def test_p194_p194b_no_hardcoded_answer():
    old_p194_markers = [
        "heavy-duty hydrocarbon process pump (model cp-194)",
        "primary hydrocarbon delivery and transfer pump maintaining continuous 140 m³/h",
        "cooling water process pump b",
        "bearing thermal distress & high vibration trip",
        "wo-9412",
        "satisfactory survey on 2026-07-15",
        "4.2 hours of unplanned downtime"
    ]

    # Test P-194
    analysis_p194 = QueryUnderstandingEngine.analyze("What happened to P-194?", conversation_history=[])
    res_p194 = LLMService.generate_grounded_answer(
        query="What happened to P-194?",
        retrieved_chunks=[],
        query_analysis=analysis_p194
    )
    assert res_p194["refused"] is True
    for marker in old_p194_markers:
        assert marker not in res_p194["answer"].lower(), f"Found old hardcoded marker '{marker}' in P-194 answer!"

    # Test P-194B
    analysis_p194b = QueryUnderstandingEngine.analyze("What happened to P-194B?", conversation_history=[])
    res_p194b = LLMService.generate_grounded_answer(
        query="What happened to P-194B?",
        retrieved_chunks=[],
        query_analysis=analysis_p194b
    )
    assert res_p194b["refused"] is True
    for marker in old_p194_markers:
        assert marker not in res_p194b["answer"].lower(), f"Found old hardcoded marker '{marker}' in P-194B answer!"


# =========================================================================
# PROOF 3: Citations cannot be invented when document was not retrieved
# =========================================================================
def test_citations_not_invented_when_not_retrieved():
    synthetic_doc_ids = [
        "OEM_Manual_Centrifugal_Pump_XYZ200",
        "SOP-101_Centrifugal_Pump_Operation",
        "Unit2_Process_PID_Flowsheet",
        "P101_Failure_Report_Feb_2026",
        "P-194_Failure_Incident_Report_20260812",
        "P-194B_Telemetry_20260810_20260812",
        "P-194_Inspection_Report_20260715",
        "P-194_Maintenance_Report_20260802",
        "USER-TEST-001_USER_TEST_001_OEM_Manual",
        "USER-TEST-001_USER_TEST_001_Maintenance_Report"
    ]

    # Query about P-101 with ZERO retrieved chunks
    analysis = QueryUnderstandingEngine.analyze("Tell me about P-101 and its OEM manual", conversation_history=[])
    res = LLMService.generate_grounded_answer(
        query="Tell me about P-101 and its OEM manual",
        retrieved_chunks=[],
        query_analysis=analysis
    )
    assert len(res["citations"]) == 0

    # Query with only ONE specific document retrieved
    single_chunk = [{
        "chunk": {
            "document_id": "Genuine_Retrieved_Doc_001",
            "asset_tag": "P-101",
            "page_number": 3,
            "section_title": "Field Notes",
            "content": "Vibration levels on pump shaft were measured at 1.8 mm/s RMS.",
            "record_date": "2026-05-10",
            "version": "v1.0",
            "governance_status": "Approved"
        },
        "score": 0.88
    }]
    res_single = LLMService.generate_grounded_answer(
        query="What is the vibration of P-101?",
        retrieved_chunks=single_chunk,
        query_analysis=analysis
    )
    # The citations must contain ONLY the retrieved doc
    assert len(res_single["citations"]) == 1
    assert res_single["citations"][0]["document_id"] == "Genuine_Retrieved_Doc_001"

    # None of the old synthetic doc IDs can ever be fabricated
    cited_ids = [c["document_id"] for c in res_single["citations"]]
    for syn_id in synthetic_doc_ids:
        assert syn_id not in cited_ids, f"Synthetic citation '{syn_id}' was fabricated!"


# =========================================================================
# PROOF 4: Customer-specific question with no evidence produces refusal
# =========================================================================
def test_customer_query_with_no_evidence_produces_refusal():
    queries = [
        "What is the power of pump P-101?",
        "When was P-194 last inspected?",
        "What happened to P-194B recently?",
        "What is connected to cooling tower T-200?",
        "Describe machine USER-TEST-001"
    ]

    for q in queries:
        analysis = QueryUnderstandingEngine.analyze(q, conversation_history=[])
        res = LLMService.generate_grounded_answer(
            query=q,
            retrieved_chunks=[],
            query_analysis=analysis
        )
        assert res["refused"] is True, f"Expected refusal for query '{q}' with no chunks"
        assert res["response_format"] == "REFUSAL"
        assert res["scope"] == "UNSUPPORTED_CUSTOMER"
        assert len(res["citations"]) == 0
        assert (
            "couldn't find a verified record" in res["answer"].lower() or
            "could not find sufficient information" in res["answer"].lower()
        )
