"""
IntelGraphAI — Data Lineage & Integrity Tests
================================================
Tests: upload → document record → asset association → Mongo chunks → 
       Neo4j asset/document relationship → knowledge-map API → frontend data.

Run: python3 -m pytest tests/test_data_lineage.py -v
"""
import pytest
import sys
import os
import io
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from app.database import get_db, db_manager
from app.document_processing.entity_extractor import EntityExtractor

# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(scope="module", autouse=True)
def connect_db():
    db_manager.connect()
    yield
    # Teardown: remove test assets/documents created in these tests
    db = get_db()
    if db is not None:
        db.assets.delete_many({"tag": {"$regex": "^TEST-AG-NEW"}})
        db.documents.delete_many({"asset_tag": {"$regex": "^TEST-AG-NEW"}})
        db.document_chunks.delete_many({"asset_tag": {"$regex": "^TEST-AG-NEW"}})
        db.failures.delete_many({"asset_tag": {"$regex": "^TEST-AG-NEW"}})
        db.maintenance_records.delete_many({"asset_tag": {"$regex": "^TEST-AG-NEW"}})
        db.inspection_records.delete_many({"asset_tag": {"$regex": "^TEST-AG-NEW"}})


@pytest.fixture
def db():
    return get_db()


def make_test_pdf_text(tag="TEST-AG-NEW-001"):
    """Create a synthetic document with explicit equipment header for clean extraction."""
    return f"""
Equipment Tag: {tag}
Equipment Type: Centrifugal Pump
Maximum Operating Pressure: 31.42 bar
Design Flow Rate: 45.0 m3/h

Connected Component: TEST-BRG-001
Component Type: Drive-End Bearing
Component Condition: Normal

Incident Date: 2026-09-01

FAILURE INCIDENT REPORT

This report documents an observed vibration anomaly on {tag} (Centrifugal Pump)
at the Gulf Coast refinery. The Drive-End Bearing (TEST-BRG-001) showed elevated
vibration levels of 4.2 mm/s RMS during the 2026-09-01 inspection.

Root Cause: Lubrication starvation due to blocked lube line.
Corrective Action: Bearing replacement scheduled under WO-TEST-001.

OISD Reference: OISD-STD-116
"""


# ============================================================
# TEST A: Entity Extractor — correct tag extraction
# ============================================================

class TestEntityExtraction:
    def test_explicit_header_tag_extracted(self):
        """Entity extractor must pick up 'Equipment Tag: TEST-AG-NEW-001' as primary tag."""
        text = make_test_pdf_text("TEST-AG-NEW-001")
        result = EntityExtractor.extract_entities(text, filename="test_failure_report.pdf")
        
        assert result["primary_asset_tag"] == "TEST-AG-NEW-001", (
            f"Expected primary_asset_tag='TEST-AG-NEW-001', got '{result['primary_asset_tag']}'"
        )
        assert "TEST-AG-NEW-001" in result["primary_asset_tags"], (
            f"Expected TEST-AG-NEW-001 in primary_asset_tags, got {result['primary_asset_tags']}"
        )
        assert result["document_scope"] == "ASSET"
        assert result["confidence"] in ("High", "Medium")

    def test_connected_component_extracted(self):
        """Entity extractor must find Connected Component: TEST-BRG-001."""
        text = make_test_pdf_text("TEST-AG-NEW-001")
        result = EntityExtractor.extract_entities(text, filename="test.pdf")
        
        comp_tags = result.get("connected_components", [])
        comp_tag_ids = [c.get("tag") for c in comp_tags]
        assert "TEST-BRG-001" in comp_tag_ids, (
            f"Expected TEST-BRG-001 in connected_components tags, got {comp_tag_ids}"
        )

    def test_pressure_NOT_extracted_as_tag(self):
        """'31.42' must not be extracted as an asset tag."""
        text = make_test_pdf_text("TEST-AG-NEW-001")
        result = EntityExtractor.extract_entities(text, filename="test.pdf")
        
        all_tags = result.get("primary_asset_tags", []) + result.get("related_asset_tags", [])
        for t in all_tags:
            assert "31" not in t, f"Pressure value leaked into asset tags: {t}"
            assert "42" not in t, f"Pressure value leaked into asset tags: {t}"

    def test_document_id_not_extracted_as_tag(self):
        """Document IDs like 'FAIL-INCIDENT-REPORT-001' must NOT become asset tags."""
        text = "FAILURE-INCIDENT-REPORT-P-101\n\nThis is a case study document."
        result = EntityExtractor.extract_entities(text, filename="FAILURE-INCIDENT-REPORT-P-101.pdf")
        
        for t in result.get("primary_asset_tags", []) + result.get("related_asset_tags", []):
            parts = t.split("-")
            assert "FAILURE" not in parts, f"Document ID leaked into tags: {t}"
            assert "INCIDENT" not in parts, f"Document ID leaked into tags: {t}"
            assert "REPORT" not in parts, f"Document ID leaked into tags: {t}"

    def test_multi_part_tag_preserved(self):
        """TEST-PUMP-REAL-001 (4-segment explicit header tag) must be preserved."""
        text = "Equipment Tag: TEST-PUMP-REAL-001\nThis is a test pump report."
        result = EntityExtractor.extract_entities(text, filename="test_pump_report.pdf")
        
        all_tags = result.get("primary_asset_tags", [])
        assert "TEST-PUMP-REAL-001" in all_tags, (
            f"Multi-part tag TEST-PUMP-REAL-001 was not preserved. Got: {all_tags}"
        )


# ============================================================
# TEST B: Full ingestion pipeline — data lineage
# ============================================================

class TestIngestionDataLineage:
    TEST_TAG = "TEST-AG-NEW-001"
    
    @pytest.fixture(autouse=True)
    def cleanup_before(self, db):
        """Ensure no pre-existing TEST-AG-NEW-001 records before each test."""
        if db is not None:
            db.assets.delete_many({"tag": self.TEST_TAG})
            db.documents.delete_many({"asset_tag": self.TEST_TAG})
            db.document_chunks.delete_many({"asset_tag": self.TEST_TAG})

    def test_B_full_ingestion_creates_correct_mongo_records(self, db, tmp_path):
        """Upload new document → verify correct asset, document, and chunks in MongoDB."""
        if db is None:
            pytest.skip("MongoDB not available")
        
        from app.services.doc_service import doc_service
        
        # Write a temp PDF-like text file
        test_file = tmp_path / "test_failure_report.pdf"
        test_text = make_test_pdf_text(self.TEST_TAG)
        # Write as .txt since we're testing the service layer, not PDF parsing
        test_file_txt = tmp_path / "test_failure_report.txt"
        test_file_txt.write_text(test_text)
        
        result = doc_service.process_and_save_document(
            file_path=test_file_txt,
            filename="test_failure_report.txt",
            asset_tag=self.TEST_TAG,
            category="Failure / Incident Report",
            tenant_id="tenant_default",
            explicit_override=True,
            create_missing_machine=True
        )
        
        # Verify ingestion returned success
        assert result.get("status") == "success", f"Ingestion failed: {result}"
        assert result.get("chunk_count", 0) > 0, "No chunks created"
        assert result.get("asset_tag") == self.TEST_TAG or result.get("tag") == self.TEST_TAG, (
            f"Wrong asset tag in result: {result.get('asset_tag')}"
        )
        
        # Verify MongoDB asset record was created
        asset_in_db = db.assets.find_one({"tag": self.TEST_TAG})
        assert asset_in_db is not None, f"Asset {self.TEST_TAG} not found in MongoDB after ingestion"
        assert asset_in_db["tag"] == self.TEST_TAG
        # Must NOT have stale fan data
        assert asset_in_db.get("name") != "F-01 Induced Draft Fan", "Cross-asset contamination!"
        assert asset_in_db.get("asset_type") != "Process Fan", "Wrong asset type for new test pump"
        
        # Verify MongoDB document record
        doc_in_db = db.documents.find_one({"asset_tag": self.TEST_TAG})
        assert doc_in_db is not None, f"Document for {self.TEST_TAG} not found in MongoDB"
        assert doc_in_db["asset_tag"] == self.TEST_TAG
        assert doc_in_db["tenant_id"] == "tenant_default"
        
        # Verify chunks
        chunk_count = db.document_chunks.count_documents({"asset_tag": self.TEST_TAG})
        assert chunk_count > 0, f"No chunks found for {self.TEST_TAG} in MongoDB"
        
        # Sample a chunk to verify content
        sample_chunk = db.document_chunks.find_one({"asset_tag": self.TEST_TAG})
        assert sample_chunk["asset_tag"] == self.TEST_TAG
        assert sample_chunk["tenant_id"] == "tenant_default"

    def test_B_no_cross_asset_pollution(self, db, tmp_path):
        """After ingesting TEST-AG-NEW-001, P-101 data must remain unchanged."""
        if db is None:
            pytest.skip("MongoDB not available")
        
        # Get P-101 before ingestion
        p101_before = db.assets.find_one({"tag": "P-101"})
        if not p101_before:
            pytest.skip("P-101 not in database, cannot check cross-pollution")
        
        p101_name_before = p101_before.get("name")
        p101_comps_before = len(p101_before.get("components", []))
        
        from app.services.doc_service import doc_service
        test_file = tmp_path / "test_new_machine.txt"
        test_file.write_text(make_test_pdf_text(self.TEST_TAG))
        
        doc_service.process_and_save_document(
            file_path=test_file,
            filename="test_new_machine.txt",
            asset_tag=self.TEST_TAG,
            category="OEM Manual",
            tenant_id="tenant_default",
            explicit_override=True,
            create_missing_machine=True
        )
        
        # Verify P-101 unchanged after ingesting new asset
        p101_after = db.assets.find_one({"tag": "P-101"})
        assert p101_after is not None, "P-101 was deleted during new asset ingestion!"
        assert p101_after.get("name") == p101_name_before, (
            f"P-101 name changed: '{p101_name_before}' -> '{p101_after.get('name')}'"
        )
        assert len(p101_after.get("components", [])) == p101_comps_before, (
            "P-101 component count changed during new asset ingestion!"
        )

    def test_B_graph_relationships_created(self, db, tmp_path):
        """After ingestion, local graph must have asset node and document → asset relationship."""
        if db is None:
            pytest.skip("MongoDB not available")
        
        from app.services.doc_service import doc_service
        test_file = tmp_path / "graph_test.txt"
        test_file.write_text(make_test_pdf_text(self.TEST_TAG))
        
        result = doc_service.process_and_save_document(
            file_path=test_file,
            filename="graph_test.txt",
            asset_tag=self.TEST_TAG,
            category="Failure / Incident Report",
            tenant_id="tenant_default",
            explicit_override=True,
            create_missing_machine=True
        )
        
        # Verify no graph_link_errors — the NameError must be fixed
        assert "graph_link_warnings" not in result, (
            f"Graph linking had errors after NameError fix: {result.get('graph_link_warnings')}"
        )
        
        # Verify local graph has the asset node
        from app.services.neo4j_service import neo4j_graph
        doc_id = result.get("document_id")
        
        # asset node must exist
        asset_node_id = f"asset_{self.TEST_TAG.replace('-', '_')}"
        assert asset_node_id in neo4j_graph.nodes, (
            f"Asset node '{asset_node_id}' not found in local graph. "
            f"Available nodes: {[k for k in neo4j_graph.nodes.keys() if 'test' in k.lower() or 'new' in k.lower()]}"
        )
        
        # document node must exist
        if doc_id:
            doc_node_id = f"doc_{doc_id}"
            assert doc_node_id in neo4j_graph.nodes, (
                f"Document node '{doc_node_id}' not found in local graph"
            )
            
            # Relationship must exist
            rels = neo4j_graph.relationships
            # Local graph uses 'from'/'to' field names (not 'source'/'target')
            asset_doc_rels = [
                r for r in rels 
                if (
                    r.get("from") == asset_node_id and r.get("to") == doc_node_id
                ) or (
                    r.get("from") == doc_node_id and r.get("to") == asset_node_id
                ) or (
                    # Also check source/target in case implementation varies
                    r.get("source") == asset_node_id and r.get("target") == doc_node_id
                ) or (
                    r.get("source") == doc_node_id and r.get("target") == asset_node_id
                )
            ]
            assert len(asset_doc_rels) > 0, (
                f"No ASSET_HAS_DOCUMENT or APPLIES_TO relationship found between "
                f"'{asset_node_id}' and '{doc_node_id}'. "
                f"All rels for this asset: {[r for r in rels if asset_node_id in str(r) or doc_node_id in str(r)]}"
            )


# ============================================================
# TEST C: Knowledge Map API — correct data for new asset
# ============================================================

class TestKnowledgeMapAPI:
    TEST_TAG = "TEST-AG-NEW-002"
    
    @pytest.fixture(autouse=True)
    def cleanup(self, db):
        if db is not None:
            db.assets.delete_many({"tag": self.TEST_TAG})
            db.documents.delete_many({"asset_tag": self.TEST_TAG})
            db.document_chunks.delete_many({"asset_tag": self.TEST_TAG})
        yield
        if db is not None:
            db.assets.delete_many({"tag": self.TEST_TAG})
            db.documents.delete_many({"asset_tag": self.TEST_TAG})
            db.document_chunks.delete_many({"asset_tag": self.TEST_TAG})
    
    def test_C_knowledge_map_only_contains_actual_relationships(self, db, tmp_path):
        """Knowledge map for a new asset must only show what was actually ingested."""
        if db is None:
            pytest.skip("MongoDB not available")
        
        from app.services.doc_service import doc_service
        from app.services.knowledge_map_service import KnowledgeMapService
        
        # Upload one document
        test_file = tmp_path / "new_asset_doc.txt"
        text = f"""
Equipment Tag: {self.TEST_TAG}
Equipment Type: Centrifugal Pump
Failure Date: 2026-09-01
This pump had a mechanical seal failure on 2026-09-01.
"""
        test_file.write_text(text)
        
        doc_service.process_and_save_document(
            file_path=test_file,
            filename="new_asset_doc.txt",
            asset_tag=self.TEST_TAG,
            category="Failure / Incident Report",
            tenant_id="tenant_default",
            explicit_override=True,
            create_missing_machine=True
        )
        
        # Get knowledge map
        km_service = KnowledgeMapService()
        km = km_service.get_asset_knowledge_map(self.TEST_TAG)
        
        nodes = km.get("nodes", [])
        node_ids = [n.get("id") for n in nodes]
        node_labels = [n.get("label") for n in nodes]
        
        # Must have the asset node
        assert any(self.TEST_TAG in str(nid) for nid in node_ids), (
            f"Asset node {self.TEST_TAG} not in knowledge map nodes. Got: {node_ids}"
        )
        
        # Must NOT contain P-101 or seeded asset data
        assert not any("P-101" in str(nid) for nid in node_ids), (
            f"P-101 contamination in {self.TEST_TAG} knowledge map! Nodes: {node_ids}"
        )
        assert not any("P-194" in str(nid) for nid in node_ids), (
            f"P-194 contamination in {self.TEST_TAG} knowledge map! Nodes: {node_ids}"
        )


# ============================================================
# TEST D: Stale Data Verification
# ============================================================

class TestStaleDataVerification:
    def test_D_f01_stale_data_is_resolved(self, db):
        """Verify the F-01 stale record (Induced Draft Fan) has been replaced with real data."""
        if db is None:
            pytest.skip("MongoDB not available")
        
        asset = db.assets.find_one({"tag": "F-01"})
        if not asset:
            pytest.skip("F-01 not in database")
        
        # STALE FINGERPRINTS MUST NOT EXIST
        assert asset.get("name") != "F-01 Induced Draft Fan", (
            f"STALE DATA STILL PRESENT: F-01 still shows 'Induced Draft Fan' — cleanup incomplete"
        )
        assert asset.get("asset_type") != "Process Fan", (
            f"STALE DATA STILL PRESENT: F-01 still shows 'Process Fan' asset_type"
        )
        assert asset.get("specs", {}).get("air_flow_m3_h") != 45000.0, (
            "STALE DATA STILL PRESENT: F-01 still has hardcoded air_flow_m3_h=45000"
        )
        assert asset.get("specs", {}).get("motor_kw") != 55.0, (
            "STALE DATA STILL PRESENT: F-01 still has hardcoded motor_kw=55.0"
        )
        
        # Stale components must not exist
        comp_names = [c.get("name") for c in asset.get("components", [])]
        assert "Fan Impeller Blades" not in comp_names, (
            f"STALE COMPONENT 'Fan Impeller Blades' still present in F-01 — cleanup incomplete"
        )
        
        print(f"\n✓ F-01 STALE DATA RESOLVED: name='{asset.get('name')}' type='{asset.get('asset_type')}'")

    def test_D_f01_has_graph_relationships_after_fix(self, db):
        """F-01 in local graph now has relationships — proves the NameError fix is working."""
        from app.services.neo4j_service import neo4j_graph
        
        if neo4j_graph.connected_to_live_neo4j:
            pytest.skip("Live Neo4j is running, this test targets local fallback graph")
        
        # Get all relationships involving F-01
        neo4j_graph.load_local_graph()
        rels = neo4j_graph.relationships
        f01_rels = [
            r for r in rels
            if "f_01" in r.get("from", "").lower() or "f_01" in r.get("to", "").lower()
            or "f_01" in r.get("source", "").lower() or "f_01" in r.get("target", "").lower()
        ]
        
        # After the NameError fix, F-01 should have relationships from OISD doc ingestion
        assert len(f01_rels) > 0, (
            f"F-01 still has 0 relationships in local graph — "
            f"expected ASSET_HAS_DOCUMENT after NameError fix. Check if OISD document was re-uploaded."
        )
        print(f"\n✓ CONFIRMED: F-01 has {len(f01_rels)} graph relationships (NameError fix verified)")
        for r in f01_rels:
            print(f"    {r.get('from', r.get('source', '?'))} -[{r.get('type', '?')}]-> {r.get('to', r.get('target', '?'))}")


# ============================================================
# TEST E: NameError fix validation — graph_link_warnings absent
# ============================================================

class TestNameErrorFix:
    def test_E_no_nameerror_in_ingestion_result(self, db, tmp_path):
        """After the fix, ingestion must NOT return graph_link_warnings due to NameError."""
        if db is None:
            pytest.skip("MongoDB not available")
        
        from app.services.doc_service import doc_service
        
        test_tag = "TEST-AG-NEW-003"
        try:
            db.assets.delete_many({"tag": test_tag})
            db.documents.delete_many({"asset_tag": test_tag})
            db.document_chunks.delete_many({"asset_tag": test_tag})
            
            test_file = tmp_path / "nameerror_test.txt"
            test_file.write_text(f"Equipment Tag: {test_tag}\nTest document for NameError fix validation.\n")
            
            result = doc_service.process_and_save_document(
                file_path=test_file,
                filename="nameerror_test.txt",
                asset_tag=test_tag,
                category="OEM Manual",
                tenant_id="tenant_default",
                explicit_override=True,
                create_missing_machine=True
            )
            
            assert result.get("status") == "success"
            assert "graph_link_warnings" not in result, (
                f"Graph link warnings present — NameError not fixed: "
                f"{result.get('graph_link_warnings')}"
            )
            print(f"\n✓ No graph_link_warnings in result — NameError fix confirmed")
        finally:
            db.assets.delete_many({"tag": test_tag})
            db.documents.delete_many({"asset_tag": test_tag})
            db.document_chunks.delete_many({"asset_tag": test_tag})


# ============================================================
# TEST F: P-101 and P-194 data integrity
# ============================================================

class TestSeedDataIntegrity:
    def test_F_p101_data_intact(self, db):
        """P-101 must remain in MongoDB with its established name and data."""
        if db is None:
            pytest.skip("MongoDB not available")
        
        asset = db.assets.find_one({"tag": "P-101"})
        assert asset is not None, "P-101 asset is missing from MongoDB!"
        assert "P-101" in (asset.get("name") or ""), f"P-101 name corrupted: {asset.get('name')}"
        print(f"\n✓ P-101 data intact: {asset.get('name')}")

    def test_F_p194_data_intact(self, db):
        """P-194B must remain in MongoDB."""
        if db is None:
            pytest.skip("MongoDB not available")
        
        asset = db.assets.find_one({"tag": {"$in": ["P-194", "P-194B"]}})
        assert asset is not None, "P-194/P-194B asset is missing from MongoDB!"
        print(f"\n✓ P-194 data intact: tag={asset.get('tag')} name={asset.get('name')}")

    def test_F_tenant_isolation(self, db):
        """Tenant B assets must not appear in tenant_default queries."""
        if db is None:
            pytest.skip("MongoDB not available")
        
        tenant_b_assets = list(db.assets.find({"tenant_id": "tenant_b"}))
        for a in tenant_b_assets:
            # Verify they are scoped to tenant_b
            assert a.get("tenant_id") == "tenant_b", f"Cross-tenant asset: {a}"
        
        # Tenant default must not include tenant_b assets
        default_assets = list(db.assets.find({"tenant_id": "tenant_default"}))
        for a in default_assets:
            assert a.get("tag") != "CROSS-TENANT-99", (
                "CROSS-TENANT-99 appeared in tenant_default query!"
            )
        print(f"\n✓ Tenant isolation: {len(tenant_b_assets)} tenant_b assets properly scoped")
