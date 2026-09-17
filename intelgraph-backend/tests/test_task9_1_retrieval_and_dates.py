import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.chat import ChatRequest
from app.ai.query_understanding import QueryUnderstandingEngine
from app.ai.orchestrator import orchestrator
from app.document_processing.entity_extractor import EntityExtractor
from app.services.machine_resolution_service import MachineResolutionService
from app.rag.hybrid_search import hybrid_search


# =========================================================================
# 1. Inspection date query
# =========================================================================
def test_inspection_date_query_understanding_and_retrieval():
    engine = QueryUnderstandingEngine()
    analysis = engine.analyze("What was the Inspection Date of P-194B?")
    
    assert analysis.fact_type == "DATE"
    assert any("Inspection" in c or "Condition" in c for c in analysis.target_document_categories)
    
    # Hybrid search retrieves Inspection document as top result, not Shift Handover
    chunks = hybrid_search.search(
        query="What was the Inspection Date of P-194B?",
        asset_tag="P-194B",
        target_categories=analysis.target_document_categories,
        fact_type="DATE"
    )
    assert len(chunks) > 0
    top_result = chunks[0]
    top_chunk = top_result["chunk"]
    top_category = top_result["category"]
    assert top_category in ["Condition Monitoring / NDT", "Inspection Report", "Inspection"]
    assert "P-194B" in top_chunk.get("asset_tag", "") or "P-194B" in top_chunk.get("primary_asset_tags", [])


# =========================================================================
# 2. Maintenance date query
# =========================================================================
def test_maintenance_date_query_understanding_and_retrieval():
    engine = QueryUnderstandingEngine()
    analysis = engine.analyze("What was the maintenance date of P-194B?")
    
    assert analysis.fact_type == "DATE"
    assert any("Maintenance" in c for c in analysis.target_document_categories)
    
    chunks = hybrid_search.search(
        query="What was the maintenance date of P-194B?",
        asset_tag="P-194B",
        target_categories=analysis.target_document_categories,
        fact_type="DATE"
    )
    assert len(chunks) > 0
    top_result = chunks[0]
    assert "Maintenance" in top_result["category"]


# =========================================================================
# 3. Incident date query
# =========================================================================
def test_incident_date_query_understanding_and_retrieval():
    engine = QueryUnderstandingEngine()
    analysis = engine.analyze("What was the failure incident date of P-194?")
    
    assert analysis.fact_type == "DATE"
    assert any("Incident" in c or "Failure" in c for c in analysis.target_document_categories)
    
    chunks = hybrid_search.search(
        query="What was the failure incident date of P-194?",
        asset_tag="P-194",
        target_categories=analysis.target_document_categories,
        fact_type="DATE"
    )
    assert len(chunks) > 0
    assert any("Incident" in c["category"] or "Failure" in c["category"] for c in chunks[:2])


# =========================================================================
# 4. Shift handover query
# =========================================================================
def test_shift_handover_query_understanding_and_retrieval():
    engine = QueryUnderstandingEngine()
    analysis = engine.analyze("What happened during the shift handover for P-194B?")
    
    assert any("Shift" in c or "Operations" in c for c in analysis.target_document_categories)
    
    chunks = hybrid_search.search(
        query="What happened during the shift handover for P-194B?",
        asset_tag="P-194B",
        target_categories=analysis.target_document_categories
    )
    assert len(chunks) > 0
    assert chunks[0]["category"] in ["Operations & Shift Logs", "Shift Handover"]


# =========================================================================
# 5. Missing inspection date refusal
# =========================================================================
def test_missing_inspection_date_refusal():
    req = ChatRequest(
        query="What was the inspection date of TEST-PUMP-001?",
        asset_tag="TEST-PUMP-001",
        tenant_id="tenant_default"
    )
    res = orchestrator.route_and_execute(req)
    
    # Must refuse or state date could not be found, without fabricating a fake date
    lower_ans = res.answer.lower()
    assert res.refused or "couldn't find" in lower_ans or "not found" in lower_ans or "unrecorded" in lower_ans or "no verified" in lower_ans or "does not contain" in lower_ans


# =========================================================================
# 6. Existing asset detection with tenant scoping
# =========================================================================
def test_existing_asset_detection_tenant_apex():
    res = MachineResolutionService.resolve_machine_association(
        text="Equipment Tag: P-101\nCentrifugal Pump Operational Survey.",
        filename="P101_Inspection.pdf",
        tenant_id="tenant_apex"
    )
    assert res["resolved_tag"] == "P-101"
    assert res["machine_exists"] is True
    assert res["status"] == "RESOLVED_EXISTING"


# =========================================================================
# 7. New asset detection
# =========================================================================
def test_new_asset_detection():
    res = MachineResolutionService.resolve_machine_association(
        text="Equipment Tag: P-999\nBrand new unseeded unit.",
        filename="P999_Commissioning.pdf",
        tenant_id="tenant_default"
    )
    assert res["resolved_tag"] == "P-999"
    assert res["machine_exists"] is False
    assert res["status"] == "NEW_MACHINE_DETECTED"
    assert "New machine detected" in res["message"]


# =========================================================================
# 8. Timeline date normalization
# =========================================================================
def test_timeline_date_normalization():
    # Valid date normalization
    assert EntityExtractor.normalize_date("2026-08-20") == "2026-08-20"
    assert EntityExtractor.normalize_date("20-Aug-2026") == "2026-08-20"
    assert EntityExtractor.normalize_date("20 Aug 2026") == "2026-08-20"
    assert EntityExtractor.normalize_date("22 /08 / 2026") == "2026-08-22"
    
    # Invalid or missing -> None, NEVER "Unknown"
    assert EntityExtractor.normalize_date("Unknown") is None
    assert EntityExtractor.normalize_date(None) is None
    assert EntityExtractor.normalize_date("") is None


# =========================================================================
# 9. Cross-asset isolation
# =========================================================================
def test_cross_asset_retrieval_isolation():
    p101_chunks = hybrid_search.search(
        query="inspection date",
        asset_tag="P-101"
    )
    for c in p101_chunks:
        chk = c["chunk"]
        assert chk.get("asset_tag") == "P-101" or "P-101" in chk.get("primary_asset_tags", [])
        assert "P-194" not in chk.get("primary_asset_tags", [])

    p194b_chunks = hybrid_search.search(
        query="inspection date",
        asset_tag="P-194B"
    )
    for c in p194b_chunks:
        chk = c["chunk"]
        assert "P-101" not in chk.get("primary_asset_tags", [])


# =========================================================================
# 10. Explicit document tag overrides upload hint
# =========================================================================
def test_explicit_document_tag_overrides_upload_hint():
    text = """
    EQUIPMENT INSPECTION SURVEY
    Equipment Tag: P-194B
    Date: 15-Jul-2026
    Vibration and condition monitoring completed.
    """
    res = MachineResolutionService.resolve_machine_association(
        text=text,
        filename="Checklist.pdf",
        hint_tag="P-101",
        tenant_id="tenant_default"
    )
    assert res["resolved_tag"] == "P-194B"
    assert res["resolved_tag"] != "P-101"


# =========================================================================
# 11. Multiple real industrial date formats
# =========================================================================
def test_multiple_industrial_date_formats():
    dates_to_test = [
        ("15-Jul-2026", "2026-07-15"),
        ("20-Aug-2026", "2026-08-20"),
        ("10 Aug 2026", "2026-08-10"),
        ("02-Aug-2026", "2026-08-02"),
        ("22 /08 / 2026", "2026-08-22"),
        ("22/08/2026", "2026-08-22"),
        ("2026-08-22", "2026-08-22"),
        ("08/22/2026", "2026-08-22"),
        ("Mon, 10 Aug 2026 22:20:00", "2026-08-10")
    ]
    for raw, expected in dates_to_test:
        norm = EntityExtractor.normalize_date(raw)
        assert norm == expected, f"Failed for {raw}: got {norm}, expected {expected}"


# =========================================================================
# 12. Date label and context selection
# =========================================================================
def test_date_label_and_context_selection():
    text = """
    Document Header
    Issue Date: 2026-01-01
    Approval Date: 2026-01-05
    
    1. Inspection Overview
    Inspection Date: 15-Jul-2026
    Effective Date: 2026-07-20
    """
    entities = EntityExtractor.extract_entities(text, filename="P-194B_Inspection_Report.pdf")
    # Must pick the labeled Inspection Date (2026-07-15) as primary date, not the earlier Issue Date (2026-01-01)
    assert entities.get("primary_date") == "2026-07-15"
    assert entities.get("labeled_dates", {}).get("inspection_date") == "2026-07-15"
