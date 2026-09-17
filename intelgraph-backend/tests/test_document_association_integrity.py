import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from fastapi import HTTPException

from app.main import app
from app.database import get_db
from app.document_processing.entity_extractor import EntityExtractor
from app.services.machine_resolution_service import MachineResolutionService, machine_resolution
from app.services.auth_service import auth_service, SystemRole
from app.services.asset_service import asset_service
from app.models.asset import AssetCreate
from app.ai.query_understanding import QueryUnderstandingEngine
from app.ai.llm_service import LLMService

@pytest.fixture(autouse=True)
def setup_test_assets():
    """Ensure baseline test assets exist in database."""
    db = get_db()
    if db is not None:
        db.assets.update_one(
            {"tag": "P-194"},
            {"$set": {
                "tag": "P-194",
                "name": "P-194 Hydrocarbon Process Pump",
                "plant": "Plant A - Gulf Coast",
                "area": "Unit 2 - Fluid Processing",
                "status": "Operational",
                "tenant_id": "tenant_default"
            }},
            upsert=True
        )
        db.assets.update_one(
            {"tag": "P-194B"},
            {"$set": {
                "tag": "P-194B",
                "name": "P-194B Cooling Water Process Pump",
                "plant": "Plant A - Gulf Coast",
                "area": "Unit 2 - Fluid Processing",
                "status": "Operational",
                "tenant_id": "tenant_default"
            }},
            upsert=True
        )
        db.assets.update_one(
            {"tag": "P-205"},
            {"$set": {
                "tag": "P-205",
                "name": "P-205 Secondary Feed Pump",
                "plant": "Plant A - Gulf Coast",
                "area": "Unit 2 - Fluid Processing",
                "status": "Operational",
                "tenant_id": "tenant_default"
            }},
            upsert=True
        )
        db.assets.update_one(
            {"tag": "CROSS-TENANT-99"},
            {"$set": {
                "tag": "CROSS-TENANT-99",
                "name": "Tenant B Isolated Machine",
                "plant": "Plant B - Midwest",
                "area": "Unit 9",
                "status": "Operational",
                "tenant_id": "tenant_b"
            }},
            upsert=True
        )

# =========================================================================
# TEST 1: P-194 hint + P-194B document → P-194B
# =========================================================================
def test_p194_hint_p194b_document_resolves_to_p194b():
    text = """
    INCIDENT INVESTIGATION REPORT
    Equipment Tag: P-194B
    Description: High bearing vibration detected on Cooling Water Process Pump B.
    Drive-End Bearing temperature reached 94C.
    """
    res = MachineResolutionService.resolve_machine_association(
        text=text,
        filename="Incident_Report.pdf",
        hint_tag="P-194",
        tenant_id="tenant_default"
    )
    assert res["status"] == "RESOLVED_EXISTING"
    assert res["resolved_tag"] == "P-194B"
    assert res["is_mismatch"] is True  # Mismatch with hint detected
    assert res["detected_tags"] == ["P-194B"]
    assert res["confidence"] == "High"

# =========================================================================
# TEST 2: P-194 hint + P-194A/P-194B document → Review Required
# =========================================================================
def test_multi_asset_document_triggers_review_required():
    text = """
    STANDARD OPERATING PROCEDURE
    Equipment Tag: P-194A / P-194B
    Applicable Units: Duplex Cooling Water Pumps A & B.
    Pre-start checks must be completed for both pump trains.
    """
    res = MachineResolutionService.resolve_machine_association(
        text=text,
        filename="SOP-P194-Duplex.pdf",
        hint_tag="P-194",
        tenant_id="tenant_default"
    )
    assert res["status"] == "MULTIPLE_MACHINES_DETECTED"
    assert res["requires_review"] is True
    assert "Multiple machine references detected" in res["message"]
    assert "P-194A" in res["detected_tags"]
    assert "P-194B" in res["detected_tags"]
    assert res["resolved_tag"] is None

    # Server-side validation MUST reject ingestion without explicit override
    with pytest.raises(HTTPException) as exc_info:
        machine_resolution.validate_and_resolve_for_ingestion(
            text=text,
            filename="SOP-P194-Duplex.pdf",
            target_asset_tag="P-194",
            hint_asset_tag="P-194",
            tenant_id="tenant_default",
            explicit_override=False
        )
    assert exc_info.value.status_code == 422
    assert "Multiple machine references detected" in exc_info.value.detail

# =========================================================================
# TEST 3: P-194 hint + no machine evidence → Needs Review
# =========================================================================
def test_no_machine_evidence_triggers_needs_review():
    text = """
    GENERAL FACILITY SAFETY BULLETIN
    All personnel must wear flame-resistant PPE in process areas.
    Ear protection is required within designated high-noise boundary zones.
    """
    res = MachineResolutionService.resolve_machine_association(
        text=text,
        filename="Safety_Notice.pdf",
        hint_tag="P-194",
        tenant_id="tenant_default"
    )
    assert res["status"] == "NEEDS_REVIEW"
    assert res["requires_review"] is True
    assert "Needs Review — Machine Association Unresolved" in res["message"]
    assert res["resolved_tag"] is None
    assert res["detected_tags"] == []

    # Server-side validation MUST reject auto-attachment to hint
    with pytest.raises(HTTPException) as exc_info:
        machine_resolution.validate_and_resolve_for_ingestion(
            text=text,
            filename="Safety_Notice.pdf",
            target_asset_tag="P-194",
            hint_asset_tag="P-194",
            tenant_id="tenant_default",
            explicit_override=False
        )
    assert exc_info.value.status_code == 422
    assert "Needs Review — Machine Association Unresolved" in exc_info.value.detail

# =========================================================================
# TEST 4: P-194 hint + unknown P-999 → New Machine Confirmation
# =========================================================================
def test_unknown_machine_triggers_new_machine_confirmation():
    db = get_db()
    if db is not None:
        db.assets.delete_many({"tag": "P-999"})

    text = """
    EQUIPMENT COMMISSIONING SHEET
    Equipment Tag: P-999
    Manufacturer: Flowserve Industrial Systems.
    Initial vibration and mechanical seal pressure test completed.
    """
    res = MachineResolutionService.resolve_machine_association(
        text=text,
        filename="Commissioning_Sheet.pdf",
        hint_tag="P-194",
        tenant_id="tenant_default"
    )
    assert res["status"] == "NEW_MACHINE_DETECTED"
    assert res["requires_review"] is True
    assert "New machine detected" in res["message"] and "Confirmation required" in res["message"]
    assert res["resolved_tag"] == "P-999"
    assert res["machine_exists"] is False

    # Server-side validation rejects without explicit create_missing_machine confirmation
    with pytest.raises(HTTPException) as exc_info:
        machine_resolution.validate_and_resolve_for_ingestion(
            text=text,
            filename="Commissioning_Sheet.pdf",
            target_asset_tag="P-999",
            hint_asset_tag="P-194",
            tenant_id="tenant_default",
            create_missing_machine=False
        )
    assert exc_info.value.status_code == 422
    assert "New machine detected" in exc_info.value.detail and "Confirmation required" in exc_info.value.detail

    # When user confirms creation, validation returns the machine tag
    resolved = machine_resolution.validate_and_resolve_for_ingestion(
        text=text,
        filename="Commissioning_Sheet.pdf",
        target_asset_tag="P-999",
        hint_asset_tag="P-194",
        tenant_id="tenant_default",
        create_missing_machine=True
    )
    assert resolved == "P-999"

# =========================================================================
# TEST 5: filename P-194 + body P-194B → P-194B
# =========================================================================
def test_filename_p194_body_p194b_resolves_to_p194b():
    filename = "P-194_Failure_Incident_Report_20260812.pdf"
    body_text = """
    INCIDENT REPORT
    Equipment Tag: P-194B
    Date: 2026-08-12
    Subject: Drive-end bearing temperature excursion and emergency shutdown.
    """
    evidence = EntityExtractor.extract_document_equipment_evidence(body_text, filename=filename)
    assert evidence["distinct_tags"] == ["P-194B"]
    assert evidence["confidence"] == "High"
    assert evidence["detection_method"] == "explicit_content_header"

    res = MachineResolutionService.resolve_machine_association(
        text=body_text,
        filename=filename,
        hint_tag="P-194",
        tenant_id="tenant_default"
    )
    assert res["resolved_tag"] == "P-194B"
    assert res["status"] == "RESOLVED_EXISTING"

# =========================================================================
# TEST 6: mixed P-194B/P-205 batch → independent per-file resolution
# =========================================================================
def test_mixed_batch_independent_per_file_resolution():
    doc1_text = "Equipment Tag: P-194B\nCooling water circulating pump monthly inspection."
    doc2_text = "Equipment Tag: P-205\nUnit 2 secondary booster pump overhaul logs."

    res1 = MachineResolutionService.resolve_machine_association(
        text=doc1_text,
        filename="doc1.pdf",
        hint_tag="P-194",
        tenant_id="tenant_default"
    )
    res2 = MachineResolutionService.resolve_machine_association(
        text=doc2_text,
        filename="doc2.pdf",
        hint_tag="P-194",
        tenant_id="tenant_default"
    )

    assert res1["resolved_tag"] == "P-194B"
    assert res2["resolved_tag"] == "P-205"
    assert res1["resolved_tag"] != res2["resolved_tag"]

# =========================================================================
# TEST 7: cross-tenant machine with same tag → HTTP 403 / inaccessible
# =========================================================================
@pytest.mark.asyncio
async def test_cross_tenant_machine_inaccessible():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        admin_default = auth_service.authenticate("admin@intelgraph.local", "AdminPassword123!")
        
        # User in tenant_default attempts to access machine belonging to tenant_b
        res = await ac.get(
            "/api/machines/CROSS-TENANT-99",
            headers={"Authorization": f"Bearer {admin_default.token}"}
        )
        assert res.status_code == 403
        assert "belongs to another tenant" in res.json()["detail"]

# =========================================================================
# TEST 8: API attempt to force wrong machine → rejected
# =========================================================================
@pytest.mark.asyncio
async def test_api_attempt_to_force_wrong_machine_rejected(tmp_path):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        admin_default = auth_service.authenticate("admin@intelgraph.local", "AdminPassword123!")

        # Create file with P-194B content
        p194b_file = tmp_path / "test_p194b_incident.txt"
        p194b_file.write_text("Equipment Tag: P-194B\nCritical bearing trip report.")

        with open(p194b_file, "rb") as f:
            res = await ac.post(
                "/api/documents/upload",
                files={"file": ("test_p194b_incident.txt", f, "text/plain")},
                data={
                    "asset_tag": "P-194",  # Malicious/mismatched target tag
                    "hint_asset_tag": "P-194",
                    "category": "Incident",
                    "explicit_override": "false"
                },
                headers={"Authorization": f"Bearer {admin_default.token}"}
            )
        assert res.status_code == 422
        assert "Machine mismatch rejected" in res.json()["detail"]

# =========================================================================
# TEST 9: AI Query Disambiguation: P-194 vs P-194B
# =========================================================================
def test_ai_query_differentiation_p194_vs_p194b():
    # 1. Query explicitly naming P-194B while active context is P-194
    analysis_b = QueryUnderstandingEngine.analyze(
        query="What happened to P-194B?",
        active_asset_context={"tag": "P-194"}
    )
    assert "P-194B" in analysis_b.referenced_asset_tags
    assert "P-194" not in analysis_b.referenced_asset_tags

    resp_b = LLMService.generate_grounded_answer(
        query="What happened to P-194B?",
        retrieved_chunks=[],
        query_analysis=analysis_b,
        asset_context={"tag": "P-194"}  # Active context is P-194
    )
    assert "P-194B" in resp_b["answer"]
    assert "2026-08-12" in resp_b["answer"]

    # 2. Query explicitly naming P-194
    analysis_194 = QueryUnderstandingEngine.analyze(
        query="What is P-194?",
        active_asset_context={"tag": "P-194"}
    )
    assert "P-194" in analysis_194.referenced_asset_tags
    assert "P-194B" not in analysis_194.referenced_asset_tags

    resp_194 = LLMService.generate_grounded_answer(
        query="What is P-194?",
        retrieved_chunks=[],
        query_analysis=analysis_194,
        asset_context={"tag": "P-194"}
    )
    assert "P-194" in resp_194["answer"]
    assert "Model CP-194" in resp_194["answer"]

# =========================================================================
# TEST 10: Associate with T-990 (upload hint P-101, detected T-990)
# =========================================================================
@pytest.mark.asyncio
async def test_associate_with_detected_t990_flow(tmp_path):
    """
    Verifies that when a document has upload hint P-101 but detected machine T-990,
    and user chooses 'Associate with T-990':
    - Document is ingested and resolved to T-990
    - MongoDB stores asset_tag == T-990
    - Neo4j links document to T-990
    - Document appears when querying T-990
    - Document does NOT appear when querying P-101
    - Audit log records 'Machine Association Confirmed'
    """
    from app.services.audit_service import audit_service
    from app.services.neo4j_service import neo4j_graph

    db = get_db()
    if db is not None:
        db.assets.delete_many({"tag": "T-990"})
        db.documents.delete_many({"filename": "test_turbine_t990_sop.txt"})

    doc_content = (
        "STANDARD OPERATING PROCEDURE\n"
        "Machine Reference: T-990\n"
        "Equipment: T-990 High Pressure Steam Turbine\n"
        "Operating Speed: 3600 RPM. Bearing lubrication schedule and vibration limits."
    )
    test_file = tmp_path / "test_turbine_t990_sop.txt"
    test_file.write_text(doc_content)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        admin_user = auth_service.authenticate("admin@intelgraph.local", "AdminPassword123!")

        with open(test_file, "rb") as f:
            res = await ac.post(
                "/api/documents/upload",
                files={"file": ("test_turbine_t990_sop.txt", f, "text/plain")},
                data={
                    "asset_tag": "T-990",
                    "hint_asset_tag": "P-101",
                    "category": "Standard Operating Procedure",
                    "explicit_override": "false",
                    "create_missing_machine": "true",
                    "uploaded_by": "Maintenance Engineer"
                },
                headers={"Authorization": f"Bearer {admin_user.token}"}
            )

        assert res.status_code == 200, res.text
        doc_data = res.json()
        assert doc_data["asset_tag"] == "T-990"
        assert doc_data["status"] == "success"

        # Verify MongoDB storage
        if db is not None:
            saved_doc = db.documents.find_one({"filename": "test_turbine_t990_sop.txt"})
            assert saved_doc is not None
            assert saved_doc["asset_tag"] == "T-990"

        # Verify Neo4j relationship
        assert f"asset_T_990" in neo4j_graph.nodes
        rel_found = any(
            r.get("from") == "asset_T_990" and "test_turbine_t990_sop" in r.get("to", "")
            for r in neo4j_graph.relationships
        )
        assert rel_found, "Neo4j relationship ASSET_HAS_DOCUMENT not found for T-990"

        # Verify document appears for T-990
        res_t990 = await ac.get(
            "/api/documents?asset_tag=T-990",
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )
        assert res_t990.status_code == 200
        t990_docs = res_t990.json()
        assert any(d["filename"] == "test_turbine_t990_sop.txt" for d in t990_docs)

        # Verify document does NOT appear for P-101
        res_p101 = await ac.get(
            "/api/documents?asset_tag=P-101",
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )
        assert res_p101.status_code == 200
        p101_docs = res_p101.json()
        assert not any(d["filename"] == "test_turbine_t990_sop.txt" for d in p101_docs)

        # Verify Audit Log event created
        audit_logs = audit_service.get_audit_logs(limit=20)
        found_audit = any(
            log.get("action") == "Machine Association Confirmed" and "T-990" in log.get("details", "")
            for log in audit_logs
        )
        assert found_audit, "Audit event 'Machine Association Confirmed' was not recorded."

# =========================================================================
# TEST 11: Keep P-101 Override (upload hint P-101, detected T-200)
# =========================================================================
@pytest.mark.asyncio
async def test_keep_hint_p101_override_flow(tmp_path):
    """
    Verifies that when a document has upload hint P-101 and detected machine T-200,
    and user chooses 'Keep P-101':
    - Document is ingested with explicit_override=True
    - Document resolves to P-101
    - MongoDB stores asset_tag == P-101
    - Detected T-200 reference is preserved in extracted_entities evidence
    - Neo4j links document to P-101
    - Audit log records 'Machine Association Override'
    """
    from app.services.audit_service import audit_service
    from app.services.neo4j_service import neo4j_graph

    db = get_db()
    if db is not None:
        db.documents.delete_many({"filename": "test_override_p101_doc.txt"})

    doc_content = (
        "MAINTENANCE LOG ENTRY\n"
        "Reference Machine: T-200 (Cross-train unit reference)\n"
        "Coupling realignment inspection procedure performed on auxiliary skid."
    )
    test_file = tmp_path / "test_override_p101_doc.txt"
    test_file.write_text(doc_content)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        admin_user = auth_service.authenticate("admin@intelgraph.local", "AdminPassword123!")

        with open(test_file, "rb") as f:
            res = await ac.post(
                "/api/documents/upload",
                files={"file": ("test_override_p101_doc.txt", f, "text/plain")},
                data={
                    "asset_tag": "P-101",
                    "hint_asset_tag": "P-101",
                    "category": "Maintenance",
                    "explicit_override": "true",
                    "create_missing_machine": "false",
                    "uploaded_by": "Maintenance Engineer"
                },
                headers={"Authorization": f"Bearer {admin_user.token}"}
            )

        assert res.status_code == 200, res.text
        doc_data = res.json()
        assert doc_data["asset_tag"] == "P-101"
        assert doc_data["status"] == "success"

        # Verify MongoDB storage
        if db is not None:
            saved_doc = db.documents.find_one({"filename": "test_override_p101_doc.txt"})
            assert saved_doc is not None
            assert saved_doc["asset_tag"] == "P-101"
            # Detected equipment T-200 preserved in extracted entities
            extracted = saved_doc.get("extracted_entities", {})
            machines_found = extracted.get("machines", [])
            assert "T-200" in machines_found, f"T-200 not preserved in machines: {machines_found}"

        # Verify Neo4j links to P-101
        assert f"asset_P_101" in neo4j_graph.nodes or "P-101" in [n.get("tag") for n in neo4j_graph.nodes.values()]
        rel_found = any(
            "P_101" in r.get("from", "") and "test_override_p101_doc" in r.get("to", "")
            for r in neo4j_graph.relationships
        )
        assert rel_found, "Neo4j relationship to P-101 not found"

        # Verify Audit Log event created
        audit_logs = audit_service.get_audit_logs(limit=20)
        found_override_audit = any(
            log.get("action") == "Machine Association Override" and "P-101" in log.get("details", "")
            for log in audit_logs
        )
        assert found_override_audit, "Audit event 'Machine Association Override' was not recorded."

