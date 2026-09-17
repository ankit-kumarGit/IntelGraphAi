import pytest
import io
import os
import zipfile
import tempfile
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.document_processing.extractor import DocumentExtractor
from app.services.connectors import connectors_manager, RockwellMESConnector
from app.services.auth_service import auth_service

@pytest.mark.asyncio
async def test_email_eml_extraction():
    """Verify that native email parser extracts headers, body, and operational metadata."""
    eml_content = (
        b"From: maintenance.lead@plant-ops.local\r\n"
        b"To: reliability.team@plant-ops.local\r\n"
        b"Date: Mon, 23 Feb 2026 07:30:00 +0000\r\n"
        b"Subject: Shift Handover: P-101 Vibration Alert & LOTO Clearance\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"Night shift completed routine vibration survey on Centrifugal Pump P-101.\r\n"
        b"Drive-end bearing vibration peaked at 12.4 mm/s RMS under full load.\r\n"
        b"Unit tripped on high vibration interlock. LOTO clearance standard applied.\r\n"
    )
    with tempfile.NamedTemporaryFile(suffix=".eml", delete=False) as tf:
        tf.write(eml_content)
        tf_path = Path(tf.name)

    try:
        pages = DocumentExtractor.extract(tf_path, "eml")
        assert len(pages) == 1
        page = pages[0]
        assert page["extraction_mode"] == "email_parser"
        assert "Shift Handover" in page["section"]
        assert "P-101" in page["content"]
        assert "12.4 mm/s" in page["content"]
        assert page["email_metadata"]["sender"] == "maintenance.lead@plant-ops.local"
    finally:
        if tf_path.exists():
            os.unlink(tf_path)

@pytest.mark.asyncio
async def test_safe_zip_archive_extraction():
    """Verify that multi-file .zip archive packages are safely extracted and indexed."""
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
        zip_path = Path(tf.name)

    try:
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("shift_handover.txt", "P-101 bearing temperature was 78C at 04:00 AM.")
            zf.writestr("inspection_log.csv", "timestamp,asset,metric,value\n2026-02-22,P-101,vib,12.4\n")

        pages = DocumentExtractor.extract(zip_path, "zip")
        assert len(pages) == 2
        modes = [p["extraction_mode"] for p in pages]
        assert all(m == "archive_member_extraction" for m in modes)
        contents = " ".join(p["content"] for p in pages)
        assert "P-101" in contents
        assert "12.4" in contents
    finally:
        if zip_path.exists():
            os.unlink(zip_path)

@pytest.mark.asyncio
async def test_zip_slip_security_protection():
    """Verify that Zip Slip path traversal attempts are rejected and extraction is safely aborted."""
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
        zip_path = Path(tf.name)

    try:
        with zipfile.ZipFile(zip_path, "w") as zf:
            # Add a malicious member with path traversal characters
            zf.writestr("../../etc/malicious_payload.txt", "MALICIOUS PAYLOAD OUTSIDE SANDBOX")

        pages = DocumentExtractor.extract(zip_path, "zip")
        assert len(pages) == 1
        assert pages[0]["extraction_mode"] == "failed"
        assert "Path traversal / Zip Slip attempt detected" in pages[0]["content"]
    finally:
        if zip_path.exists():
            os.unlink(zip_path)

@pytest.mark.asyncio
async def test_zip_archive_file_quota_protection():
    """Verify that archives with excessive file counts (>25) are rejected to prevent Zip Bombs."""
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
        zip_path = Path(tf.name)

    try:
        with zipfile.ZipFile(zip_path, "w") as zf:
            for i in range(28):  # Exceeds MAX_ARCHIVE_FILES = 25
                zf.writestr(f"file_{i}.txt", f"Data chunk {i}")

        pages = DocumentExtractor.extract(zip_path, "zip")
        assert len(pages) == 1
        assert pages[0]["extraction_mode"] == "failed"
        assert "Quota Exceeded" in pages[0]["section"]
    finally:
        if zip_path.exists():
            os.unlink(zip_path)

def test_rockwell_mes_connector():
    """Verify the Rockwell FactoryTalk MES connector tests connection and syncs production logs."""
    mes = RockwellMESConnector()
    status = mes.get_status()
    assert status.system_type == "MES"
    assert "Connected (Prototype/Mock Integration)" in status.status
    assert "FTMES_PLANT_A" in mes.test_connection()["system_id"]

    sync_res = mes.sync_records("P-101")
    assert sync_res["status"] == "success"
    assert sync_res["records_imported"] == 8

def test_cmms_export_adapters():
    """Verify clean adapter interface dispatches action items to SAP PM, Maximo, and MES."""
    # 1. SAP PM
    res_sap = connectors_manager.export_action_to_cmms(
        action_id="ACT-P101-01",
        action_title="Drive-End Bearing Replacement",
        asset_tag="P-101",
        target_system="SAP_PM",
        operator="Lead Reliability Engineer"
    )
    assert res_sap["status"] == "success"
    assert res_sap["is_mock_integration"] is True
    assert res_sap["target_system"] == "SAP S/4HANA Plant Maintenance"
    assert res_sap["external_reference_id"].startswith("SAP-NOTIF-")

    # 2. IBM Maximo
    res_max = connectors_manager.export_action_to_cmms(
        action_id="ACT-P101-02",
        action_title="Lube Oil Flushing",
        asset_tag="P-101",
        target_system="IBM_MAXIMO",
        operator="Lead Reliability Engineer"
    )
    assert res_max["status"] == "success"
    assert res_max["target_system"] == "IBM Maximo CMMS"
    assert res_max["external_reference_id"].startswith("MAX-WO-")

    # 3. Rockwell MES
    res_mes = connectors_manager.export_action_to_cmms(
        action_id="ACT-P101-03",
        action_title="Production Maintenance Hold",
        asset_tag="P-101",
        target_system="ROCKWELL_MES",
        operator="Lead Reliability Engineer"
    )
    assert res_mes["status"] == "success"
    assert res_mes["target_system"] == "Rockwell FactoryTalk MES"
    assert res_mes["external_reference_id"].startswith("MES-HOLD-")

@pytest.mark.asyncio
async def test_api_export_cmms_endpoint():
    """Verify the REST endpoint POST /api/actions/{action_id}/export-cmms dispatches work orders."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/actions/ACT-TEST-01/export-cmms?target_system=SAP_PM&user_name=EngineerTest")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["target_system"] == "SAP S/4HANA Plant Maintenance"
        assert data["external_reference_id"].startswith("SAP-NOTIF-")

@pytest.mark.asyncio
async def test_api_upload_archive_endpoint():
    """Verify the REST endpoint POST /api/documents/upload-archive accepts and processes zip packages."""
    # Create in-memory zip
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("handover_log.txt", "P-101 pump run hours: 4120 hrs. Vibration: 12.4 mm/s.")
    zip_buffer.seek(0)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("unit2_package.zip", zip_buffer.getvalue(), "application/zip")}
        res = await ac.post("/api/documents/upload-archive", files=files, data={"asset_tag": "P-101"})
        assert res.status_code == 200
        data = res.json()
        assert data["filename"] == "unit2_package.zip"
        assert data["file_type"] == "zip"
        assert data["asset_tag"] == "P-101"

def test_generic_enterprise_auth():
    """Verify authentic authentication with generic enterprise credentials and backwards compatible aliases."""
    # 1. New generic email
    res_gen = auth_service.authenticate("engineer@plant-ops.local", "Password123!")
    assert res_gen is not None
    assert res_gen.user.email == "engineer@plant-ops.local"
    assert res_gen.user.role.value == "Maintenance Engineer"

    # 2. Backwards compatible alias
    res_alias = auth_service.authenticate("engineer@plant.apex-energy.com", "Password123!")
    assert res_alias is not None
    assert res_alias.user.email == "engineer@plant-ops.local"

@pytest.mark.asyncio
async def test_oisd_peso_factories_act_compliance_rules():
    """Verify that OISD, PESO, and The Factories Act 1948 active rules evaluate under the 3-state taxonomy."""
    from app.services.compliance_service import compliance_service

    items = compliance_service.audit_asset_compliance("P-101")
    assert len(items) >= 7

    req_ids = [i["requirement_id"] for i in items]
    assert "OISD-STD-119" in req_ids
    assert "PESO-SMPV-2016" in req_ids
    assert "FACTORIES-ACT-SEC21" in req_ids

    # Check status values match the 3-state compliance taxonomy
    oisd_item = next(i for i in items if i["requirement_id"] == "OISD-STD-119")
    peso_item = next(i for i in items if i["requirement_id"] == "PESO-SMPV-2016")
    factories_item = next(i for i in items if i["requirement_id"] == "FACTORIES-ACT-SEC21")

    assert "Satisfied" in oisd_item["status"]
    assert "Gap Identified" in peso_item["status"] or "Overdue" in peso_item["status"]
    assert "Under Review" in factories_item["status"]

    # Verify audit evidence package aggregation
    pkg = compliance_service.generate_audit_evidence_package("P-101")
    summary = pkg["compliance_summary"]
    assert summary["total_requirements"] >= 7
    assert summary["compliant_count"] >= 4
    assert summary["under_review_count"] >= 1
    assert summary["gaps_count"] >= 2

def test_pid_pipeline_capabilities_transparency():
    """Verify explicit separation of 7 P&ID stages: 5 available vs 2 unavailable limitations."""
    from app.document_processing.pid_extractor import PIDTagExtractor

    breakdown = PIDTagExtractor.get_pipeline_capability_breakdown()
    assert len(breakdown) == 7

    # Available stages
    assert breakdown["pixel_ocr"]["status"] == "AVAILABLE"
    assert breakdown["tag_detection"]["status"] == "AVAILABLE"
    assert breakdown["bounding_box_extraction"]["status"] == "AVAILABLE"
    assert breakdown["equipment_classification"]["status"] == "AVAILABLE"
    assert breakdown["spatial_association"]["status"] == "AVAILABLE"

    # Explicit limitations (unavailable)
    assert breakdown["graphical_symbol_recognition"]["status"] == "UNAVAILABLE"
    assert "NOT IMPLEMENTED" in breakdown["graphical_symbol_recognition"]["implementation"]
    assert breakdown["pipe_topology_inference"]["status"] == "UNAVAILABLE"
    assert "NOT IMPLEMENTED" in breakdown["pipe_topology_inference"]["implementation"]
