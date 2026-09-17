import pytest
from pathlib import Path
from app.database import get_db
from app.document_processing.extractor import DocumentExtractor
from app.document_processing.entity_extractor import EntityExtractor
from app.services.machine_resolution_service import MachineResolutionService
from app.rag.vector_store import vector_store
from app.rag.qdrant_store import qdrant_store
from app.services.neo4j_service import neo4j_graph

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "storage" / "uploads"


def extract_file_evidence(filename: str):
    fp = UPLOADS_DIR / filename
    assert fp.exists(), f"Source file {filename} not found in {UPLOADS_DIR}"
    ext = filename.rsplit(".", 1)[-1].lower()
    pages = DocumentExtractor.extract(fp, ext)
    combined_text = "\n".join([p.get("content", "") for p in pages if p.get("content")])
    return EntityExtractor.extract_document_equipment_evidence(combined_text, filename=filename), combined_text


# =========================================================================
# FILE 1: P-194_Process_Flowsheet.txt
# =========================================================================
def test_file_1_process_flowsheet():
    ev, _ = extract_file_evidence("P-194_Process_Flowsheet.txt")
    assert ev["document_scope"] == "SYSTEM", f"Expected SYSTEM scope, got {ev['document_scope']}"
    assert ev["primary_asset_tags"] == [], "System document must not force a single primary machine"
    assert "T-200" in ev["related_asset_tags"], "T-200 must be in related system assets"
    assert "P-194A" in ev["related_asset_tags"], "P-194A must be in related system assets"
    assert "P-194B" in ev["related_asset_tags"], "P-194B must be in related system assets"
    assert any(tag.startswith("E-") for tag in ev["related_asset_tags"]), "Heat exchangers E-201... must be in related assets"
    # Verify components like valves/strainers are recognized as components
    assert any(c.startswith("V-") or c.startswith("ST-") for c in ev["component_tags"])


# =========================================================================
# FILE 2: P-194_Shift_Handover_20260810.eml
# =========================================================================
def test_file_2_shift_handover():
    ev, _ = extract_file_evidence("P-194_Shift_Handover_20260810.eml")
    assert ev["document_scope"] == "ASSET"
    assert ev["primary_asset_tags"] == ["P-194B"]


# =========================================================================
# FILE 3: P-194_Failure_Incident_Report_20260812.pdf
# =========================================================================
def test_file_3_failure_incident_report():
    ev, _ = extract_file_evidence("P-194_Failure_Incident_Report_20260812.pdf")
    assert ev["document_scope"] == "ASSET"
    assert ev["primary_asset_tags"] == ["P-194B"]


# =========================================================================
# FILE 4: P-194_Inspection_Report_20260715.pdf
# =========================================================================
def test_file_4_inspection_report():
    ev, _ = extract_file_evidence("P-194_Inspection_Report_20260715.pdf")
    assert ev["document_scope"] == "ASSET"
    assert ev["primary_asset_tags"] == ["P-194B"]


# =========================================================================
# FILE 5: P-194_Maintenance_Report_20260802.pdf
# =========================================================================
def test_file_5_maintenance_report():
    ev, _ = extract_file_evidence("P-194_Maintenance_Report_20260802.pdf")
    assert ev["document_scope"] == "ASSET"
    assert ev["primary_asset_tags"] == ["P-194B"]


# =========================================================================
# FILE 6: P-194_Maintenance_Schedule.xlsx
# =========================================================================
def test_file_6_maintenance_schedule():
    ev, _ = extract_file_evidence("P-194_Maintenance_Schedule.xlsx")
    assert ev["document_scope"] == "MULTI_ASSET"
    assert "P-194A" in ev["primary_asset_tags"]
    assert "P-194B" in ev["primary_asset_tags"]


# =========================================================================
# FILE 7: P-194_OEM_Manual.pdf
# =========================================================================
def test_file_7_oem_manual():
    ev, _ = extract_file_evidence("P-194_OEM_Manual.pdf")
    assert ev["document_scope"] == "MULTI_ASSET"
    assert "P-194A" in ev["primary_asset_tags"]
    assert "P-194B" in ev["primary_asset_tags"]
    # Model and Doc numbers must be protected and extracted as identifiers, NOT machines
    assert ev["model_number"] == "SCP-3008-HD"
    assert ev["document_number"] == "VHP-IOM-3008-HD-R3"
    assert "VHP-3008" not in ev["primary_asset_tags"]
    assert "SCP-3008" not in ev["primary_asset_tags"]


# =========================================================================
# FILE 8: P-194_PID_Diagram.png
# =========================================================================
def test_file_8_pid_diagram():
    ev, _ = extract_file_evidence("P-194_PID_Diagram.png")
    assert ev["document_scope"] == "SYSTEM"
    assert ev["primary_asset_tags"] == [], "P&ID must not force a single primary machine"
    assert "V-194A" in ev["component_tags"], "V-194A must be classified as a component tag"
    assert "V-194A" not in ev["primary_asset_tags"], "V-194A must NEVER become a primary machine"


# =========================================================================
# FILE 9: P-194_Scanned_Field_Checklist.png
# =========================================================================
def test_file_9_scanned_field_checklist():
    ev, _ = extract_file_evidence("P-194_Scanned_Field_Checklist.png")
    assert ev["document_scope"] == "ASSET"
    assert ev["primary_asset_tags"] == ["P-194B"]


# =========================================================================
# FILE 10: P-194B_Telemetry_20260810_20260812.csv
# =========================================================================
def test_file_10_telemetry():
    ev, _ = extract_file_evidence("P-194B_Telemetry_20260810_20260812.csv")
    assert ev["document_scope"] == "ASSET"
    assert ev["primary_asset_tags"] == ["P-194B"]


# =========================================================================
# FILE 11: SOP-P194-01_Startup_Shutdown.pdf
# =========================================================================
def test_file_11_sop_startup_shutdown():
    ev, _ = extract_file_evidence("SOP-P194-01_Startup_Shutdown.pdf")
    assert ev["document_scope"] == "MULTI_ASSET"
    assert "P-194A" in ev["primary_asset_tags"]
    assert "P-194B" in ev["primary_asset_tags"]
    assert ev["document_number"] == "SOP-P194-01"


# =========================================================================
# DATABASE INTEGRITY & IDENTITY VERIFICATION
# =========================================================================
def test_database_asset_identities_and_component_protection():
    db = get_db()
    assert db is not None

    # 1. T-200 must be Cooling Tower, NOT pump
    t200 = db.assets.find_one({"tag": "T-200"})
    assert t200 is not None
    assert t200["asset_type"] == "Cooling Tower"
    assert "Cooling Tower" in t200["name"]
    assert "Pump" not in t200["name"]
    # Check cooling tower components
    comp_names = [c["name"] for c in t200.get("components", [])]
    assert any("Fan" in c or "Drift" in c or "Basin" in c for c in comp_names)
    assert not any("Bearing" in c for c in comp_names), "T-200 must not have pump bearing components"

    # 2. VHP-3008 must NOT exist as a machine asset
    vhp = db.assets.find_one({"tag": "VHP-3008"})
    assert vhp is None, "VHP-3008 must not exist as an asset in MongoDB"

    # 3. V-194A must NOT exist as a machine asset
    v194 = db.assets.find_one({"tag": "V-194A"})
    assert v194 is None, "V-194A valve must not exist as a machine asset in MongoDB"

    # 4. Neo4j graph nodes check
    assert "asset_T_200" in neo4j_graph.nodes
    assert neo4j_graph.nodes["asset_T_200"]["properties"]["asset_type"] == "Cooling Tower"
    assert "asset_VHP_3008" not in neo4j_graph.nodes
    assert "asset_V_194A" not in neo4j_graph.nodes

    # V-194A must be preserved as Component in Neo4j
    assert "comp_V_194A" in neo4j_graph.nodes
    assert neo4j_graph.nodes["comp_V_194A"]["label"] == "Component"

    # 5. P-101 historical data must be intact
    p101 = db.assets.find_one({"tag": "P-101"})
    assert p101 is not None
    p101_maint = list(db.maintenance_records.find({"asset_tag": "P-101"}))
    assert len(p101_maint) > 0
    assert any("WO-1023" in str(m) for m in p101_maint)
    assert any("WO-1189" in str(m) for m in p101_maint)


# =========================================================================
# CROSS-MACHINE ISOLATION & RETRIEVAL VERIFICATION
# =========================================================================
def test_retrieval_isolation_no_cross_machine_contamination():
    # 1. Querying T-200 must NOT retrieve P-194B failure or maintenance reports
    t200_results = vector_store.search("bearing seizure high temperature vibration incident failure", top_k=10, asset_tag="T-200")
    for chunk, score in t200_results:
        # None of the chunks should be P-194B asset-specific records
        assert chunk.get("asset_tag") != "P-194B" or chunk.get("document_scope") in ("SYSTEM", "MULTI_ASSET")
        assert "FAIL-P194B" not in chunk.get("content", "")
        assert "P-194_Failure_Incident_Report" not in chunk.get("document_id", "")

    # 2. Querying P-194B CAN retrieve its authentic failure report
    p194b_results = vector_store.search("bearing excursion emergency shutdown 2026-08-12", top_k=5, asset_tag="P-194B")
    assert any("194B" in c.get("content", "") or "P-194B" in c.get("primary_asset_tags", []) for c, _ in p194b_results)

    # 3. Querying P-101 must NOT retrieve P-194B records
    p101_results = vector_store.search("vibration bearing inspection", top_k=5, asset_tag="P-101")
    for chunk, score in p101_results:
        assert chunk.get("asset_tag") == "P-101"
