import pytest
import os
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import get_db
from app.config import settings, UPLOADS_DIR
from app.models.document import DocumentChunk
from app.services.neo4j_service import neo4j_kg
from app.rag.qdrant_store import qdrant_store
from app.rag.vector_store import vector_store

TEST_TAG = "DELETE-TEST-001"

@pytest.mark.asyncio
async def test_machine_lifecycle_end_to_end():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        db = get_db()
        assert db is not None, "MongoDB connection required"

        # =====================================================================
        # STEP 0: P-194 INTEGRITY PRE-CHECK (REQUIREMENT #6)
        # =====================================================================
        p194_before_asset = db.assets.find_one({"tag": "P-194"})
        assert p194_before_asset is not None, "P-194 must exist prior to testing"
        p194_docs_count_before = db.documents.count_documents({"asset_tag": "P-194"})
        p194_chunks_count_before = db.document_chunks.count_documents({"asset_tag": "P-194"})
        p194_telemetry_before = db.telemetry.count_documents({"asset_tag": "P-194"})
        assert p194_docs_count_before == 12, f"Expected 12 documents for P-194, found {p194_docs_count_before}"
        assert p194_chunks_count_before == 14, f"Expected 14 chunks for P-194, found {p194_chunks_count_before}"

        # =====================================================================
        # STEP 1: CREATE DISPOSABLE FIXTURE DELETE-TEST-001 (REQUIREMENT #6, #11)
        # =====================================================================
        # Clean any prior test artifact
        db.assets.delete_many({"tag": TEST_TAG})
        db.documents.delete_many({"$or": [{"asset_tag": TEST_TAG}, {"document_id": {"$in": ["doc_delete_test_manual", "doc_shared_spec", "doc_shared_spec_p101_link"]}}]})
        db.document_chunks.delete_many({"asset_tag": TEST_TAG})
        db.telemetry.delete_many({"asset_tag": TEST_TAG})
        db.inspection_records.delete_many({"asset_tag": TEST_TAG})
        db.maintenance_records.delete_many({"asset_tag": TEST_TAG})
        db.failures.delete_many({"asset_tag": TEST_TAG})
        db.human_notes.delete_many({"asset_tag": TEST_TAG})
        db.findings.delete_many({"asset_tag": TEST_TAG})
        db.custom_actions.delete_many({"asset_tag": TEST_TAG})

        # 1.1 Asset document
        db.assets.insert_one({
            "tag": TEST_TAG,
            "name": "Disposable Test Hydrocarbon Pump",
            "plant": "Gulf Coast Facility",
            "area": "Unit 9 Test Train",
            "criticality": "Medium",
            "status": "Operational",
            "tenant_id": "tenant_default",
            "manufacturer": "Sulzer",
            "model": "CP-TEST-500",
            "description": "Fixture asset created strictly for machine lifecycle and cascade deletion verification."
        })

        # 1.2 Exclusive test files and documents
        exclusive_file_1 = UPLOADS_DIR / "DELETE_TEST_001_manual.txt"
        exclusive_file_1.write_text("Exclusive manual content for DELETE-TEST-001 disposable pump.")
        
        shared_file = UPLOADS_DIR / "SHARED_safety_spec.txt"
        shared_file.write_text("Shared plant-wide safety standard specification.")

        db.documents.insert_one({
            "document_id": "doc_delete_test_manual",
            "asset_tag": TEST_TAG,
            "filename": "DELETE_TEST_001_manual.txt",
            "file_path": str(exclusive_file_1),
            "sha256_hash": "hash_delete_test_exclusive_001",
            "governance_status": "Approved",
            "tenant_id": "tenant_default"
        })

        # Shared document: also referenced by dummy asset P-SHARED
        db.documents.insert_one({
            "document_id": "doc_shared_spec",
            "asset_tag": TEST_TAG,
            "filename": "SHARED_safety_spec.txt",
            "file_path": str(shared_file),
            "sha256_hash": "hash_shared_safety_spec_all",
            "governance_status": "Approved",
            "tenant_id": "tenant_default"
        })
        db.documents.insert_one({
            "document_id": "doc_shared_spec_p101_link",
            "asset_tag": "P-101",
            "filename": "SHARED_safety_spec.txt",
            "file_path": str(shared_file),
            "sha256_hash": "hash_shared_safety_spec_all",
            "governance_status": "Approved",
            "tenant_id": "tenant_default"
        })

        # 1.3 Chunks
        chunk_obj = DocumentChunk(
            chunk_id="chunk_del_01",
            document_id="doc_delete_test_manual",
            asset_tag=TEST_TAG,
            section_title="Operating Specs",
            content="Disposable pump DELETE-TEST-001 requires 50 kW motor and 2950 RPM.",
            page_number=1,
            governance_status="Approved",
            tenant_id="tenant_default"
        )
        db.document_chunks.insert_one(chunk_obj.model_dump())

        # 1.4 Telemetry, Inspection, Maintenance, Failure, Note, Finding, Action
        db.telemetry.insert_one({
            "asset_tag": TEST_TAG,
            "timestamp": "2026-09-12T12:00:00Z",
            "vibration_rms": 2.5,
            "bearing_temp_c": 68.0,
            "discharge_pressure_bar": 15.0
        })
        db.inspection_records.insert_one({
            "inspection_id": "insp_del_01",
            "asset_tag": TEST_TAG,
            "date": "2026-09-10",
            "result": "Passed"
        })
        db.maintenance_records.insert_one({
            "record_id": "wo_del_01",
            "work_order_number": "WO-DEL-9999",
            "asset_tag": TEST_TAG,
            "date": "2026-09-08",
            "status": "Completed"
        })
        db.failures.insert_one({
            "failure_id": "fail_del_01",
            "asset_tag": TEST_TAG,
            "failure_mode": "Test Seal Leak",
            "severity": "Minor"
        })
        db.human_notes.insert_one({
            "note_id": "note_del_01",
            "asset_tag": TEST_TAG,
            "author": "Tester",
            "text": "Temporary test note for lifecycle validation."
        })
        db.findings.insert_one({
            "finding_id": "find_del_01",
            "asset_tag": TEST_TAG,
            "title": "Test Finding",
            "status": "Open"
        })
        db.custom_actions.insert_one({
            "action_id": "act_del_01",
            "asset_tag": TEST_TAG,
            "title": "Test Action",
            "status": "Open"
        })

        # 1.5 Neo4j: Add test asset node, relationships, and connect to a global ontology node
        neo4j_kg.add_node(
            node_id="asset_DELETE_TEST_001",
            label="Asset",
            properties={"tag": TEST_TAG, "name": "Disposable Test Pump", "tenant_id": "tenant_default"}
        )
        neo4j_kg.add_node(
            node_id="wo_DELETE_TEST_001_9999",
            label="WorkOrder",
            properties={"asset_tag": TEST_TAG, "number": "WO-DEL-9999"}
        )
        neo4j_kg.add_node(
            node_id="concept_Centrifugal_Pump",
            label="OntologyConcept",
            properties={"name": "Centrifugal Pump", "is_global": True}
        )
        neo4j_kg.add_relationship("asset_DELETE_TEST_001", "wo_DELETE_TEST_001_9999", "HAS_WORK_ORDER")
        neo4j_kg.add_relationship("asset_DELETE_TEST_001", "concept_Centrifugal_Pump", "IS_TYPE_OF")

        # 1.6 Vector Stores
        qdrant_store.add_chunks([chunk_obj])
        vector_store.add_chunks([chunk_obj])

        # Authenticate real test sessions
        from app.services.auth_service import auth_service
        admin_session = auth_service.authenticate("admin@intelgraph.local", "AdminPassword123!")
        admin_headers = {"Authorization": f"Bearer {admin_session.token}"}

        manager_session = auth_service.authenticate("manager@plant-ops.local", "Password123!")
        manager_headers = {"Authorization": f"Bearer {manager_session.token}"}

        # =====================================================================
        # STEP 2: REVERSIBLE ARCHIVE & RESTORE CYCLE (REQUIREMENT #10)
        # =====================================================================
        # 2.1 Archive the machine (Manager role)
        res_arch = await ac.post(f"/api/machines/{TEST_TAG}/archive", headers=manager_headers)
        assert res_arch.status_code == 200
        arch_data = res_arch.json()
        assert arch_data["success"] is True
        assert arch_data["status"] == "Archived"

        # 2.2 Verify it does NOT appear in default active machines view
        res_active_list = await ac.get("/api/machines")
        assert res_active_list.status_code == 200
        active_tags = [a["tag"] for a in res_active_list.json()]
        assert TEST_TAG not in active_tags, "Archived machine must not appear in default active machine view"

        # 2.3 Verify it appears when include_archived=true
        res_all_list = await ac.get("/api/machines?include_archived=true")
        assert res_all_list.status_code == 200
        all_tags = [a["tag"] for a in res_all_list.json()]
        assert TEST_TAG in all_tags, "Archived machine must appear when include_archived=true"

        # 2.4 Verify data was NOT deleted during archival
        assert db.documents.count_documents({"asset_tag": TEST_TAG}) >= 2
        assert db.telemetry.count_documents({"asset_tag": TEST_TAG}) == 1

        # 2.5 Restore machine to Operational
        res_rest = await ac.post(f"/api/machines/{TEST_TAG}/restore", headers=manager_headers)
        assert res_rest.status_code == 200
        assert res_rest.json()["status"] == "Operational"

        # 2.6 Verify it is back in active machines list
        res_active_list_2 = await ac.get("/api/machines")
        active_tags_2 = [a["tag"] for a in res_active_list_2.json()]
        assert TEST_TAG in active_tags_2, "Restored machine must be back in active machine view"

        # =====================================================================
        # STEP 3: LIVE DELETION IMPACT PREVIEW (REQUIREMENT #2, #9)
        # =====================================================================
        res_prev = await ac.get(f"/api/machines/{TEST_TAG}/deletion-preview", headers=admin_headers)
        assert res_prev.status_code == 200
        prev_data = res_prev.json()
        assert prev_data["asset_tag"] == TEST_TAG
        assert prev_data["counts"]["documents"] == 2
        assert prev_data["counts"]["document_chunks"] == 1
        assert prev_data["counts"]["telemetry_points"] == 1
        assert prev_data["counts"]["maintenance_records"] == 1
        assert prev_data["counts"]["inspection_records"] == 1
        assert prev_data["counts"]["failure_records"] == 1
        assert prev_data["counts"]["exclusive_files"] == 1
        assert prev_data["counts"]["shared_files"] == 1

        # =====================================================================
        # STEP 4: SERVER-SIDE ROLE RESTRICTION - HTTP 403 (REQUIREMENT #1)
        # =====================================================================
        forbidden_users = [
            ("engineer@plant-ops.local", "Password123!", "Maintenance Engineer"),
            ("manager@plant-ops.local", "Password123!", "Plant Manager"),
            ("auditor@compliance.local", "Password123!", "Quality / Compliance Auditor"),
            ("technician@plant-ops.local", "Password123!", "Field Technician")
        ]
        for email, pwd, role in forbidden_users:
            sess = auth_service.authenticate(email, pwd)
            res_forbid = await ac.delete(
                f"/api/machines/{TEST_TAG}?exact_tag_confirm={TEST_TAG}",
                headers={"Authorization": f"Bearer {sess.token}"}
            )
            assert res_forbid.status_code == 403, f"Role '{role}' must receive HTTP 403 Forbidden"
            assert "strictly restricted to Platform Administrator" in res_forbid.text

        # 4.1 Client Header Spoofing Protection Check
        # Attempting X-User-Role: Platform Administrator without valid admin session
        res_spoof = await ac.delete(
            f"/api/machines/{TEST_TAG}?exact_tag_confirm={TEST_TAG}",
            headers={"X-User-Role": "Platform Administrator"}
        )
        assert res_spoof.status_code == 403

        # 4.2 Exact Tag Confirmation Check
        res_mismatch = await ac.delete(
            f"/api/machines/{TEST_TAG}?exact_tag_confirm=WRONG-TAG",
            headers=admin_headers
        )
        assert res_mismatch.status_code == 400

        # =====================================================================
        # STEP 5: PERMANENT CASCADE DELETION SAGA (REQUIREMENT #2, #4, #7)
        # =====================================================================
        res_del = await ac.delete(
            f"/api/machines/{TEST_TAG}?exact_tag_confirm={TEST_TAG}",
            headers=admin_headers
        )
        assert res_del.status_code == 200
        del_data = res_del.json()
        assert del_data["success"] is True
        assert del_data["report"]["all_layers_verified_clean"] is True

        # =====================================================================
        # STEP 6: ALL-LAYER VERIFICATION (REQUIREMENT #8)
        # =====================================================================
        # 6.1 MongoDB verification
        assert db.assets.count_documents({"tag": TEST_TAG}) == 0
        assert db.document_chunks.count_documents({"asset_tag": TEST_TAG}) == 0
        assert db.telemetry.count_documents({"asset_tag": TEST_TAG}) == 0
        assert db.inspection_records.count_documents({"asset_tag": TEST_TAG}) == 0
        assert db.maintenance_records.count_documents({"asset_tag": TEST_TAG}) == 0
        assert db.failures.count_documents({"asset_tag": TEST_TAG}) == 0
        assert db.human_notes.count_documents({"asset_tag": TEST_TAG}) == 0
        assert db.findings.count_documents({"asset_tag": TEST_TAG}) == 0
        assert db.custom_actions.count_documents({"asset_tag": TEST_TAG}) == 0

        # 6.2 Filesystem verification: Exclusive file deleted; Shared file PRESERVED
        assert not exclusive_file_1.exists(), "Exclusive file must be unlinked"
        assert shared_file.exists(), "Legitimately shared file MUST NOT be deleted (Requirement #4)"

        # 6.3 Neo4j Graph verification: Asset node deleted; Ontology concept PRESERVED
        assert "asset_DELETE_TEST_001" not in neo4j_kg.nodes
        assert "concept_Centrifugal_Pump" in neo4j_kg.nodes, "Global ontology concept MUST NOT be deleted (Requirement #4)"

        # 6.4 Qdrant vector store verification
        assert qdrant_store.count_by_asset_tag(TEST_TAG) == 0

        # 6.5 FAISS vector store verification
        assert vector_store.count_by_asset_tag(TEST_TAG) == 0

        # =====================================================================
        # STEP 7: AI RETRIEVAL REFUSAL VERIFICATION (REQUIREMENT #8)
        # =====================================================================
        res_ai = await ac.post("/api/chat", json={
            "query": f"What is the operating status of machine {TEST_TAG}?",
            "asset_tag": TEST_TAG,
            "user_role": "Maintenance Engineer"
        })
        assert res_ai.status_code == 200
        ai_data = res_ai.json()
        assert "couldn't find a verified record for machine DELETE-TEST-001" in ai_data["answer"]
        assert ai_data["refused"] is True

        # =====================================================================
        # STEP 8: IMMUTABLE AUDIT TRAIL VERIFICATION (REQUIREMENT #7)
        # =====================================================================
        arch_audit = db.audit_logs.find_one({"target_id": TEST_TAG, "action": "MACHINE_ARCHIVED"})
        rest_audit = db.audit_logs.find_one({"target_id": TEST_TAG, "action": "MACHINE_RESTORED"})
        forbid_audit = db.audit_logs.find_one({"target_id": TEST_TAG, "action": "UNAUTHORIZED_MACHINE_DELETION_ATTEMPT"})
        del_audit = db.audit_logs.find_one({"target_id": TEST_TAG, "action": "MACHINE_DELETED"})

        assert arch_audit is not None, "MACHINE_ARCHIVED audit event must exist"
        assert rest_audit is not None, "MACHINE_RESTORED audit event must exist"
        assert forbid_audit is not None, "UNAUTHORIZED_MACHINE_DELETION_ATTEMPT audit event must exist"
        assert del_audit is not None, "MACHINE_DELETED audit event must exist"
        assert del_audit["details"]["status"] == "COMPLETELY_VERIFIED"

        # =====================================================================
        # STEP 9: P-194 PROTECTION FINAL ASSERTION (REQUIREMENT #6)
        # =====================================================================
        p194_after_asset = db.assets.find_one({"tag": "P-194"})
        assert p194_after_asset is not None, "CRITICAL: P-194 was deleted!"
        p194_docs_after = db.documents.count_documents({"asset_tag": "P-194"})
        p194_chunks_after = db.document_chunks.count_documents({"asset_tag": "P-194"})
        p194_telemetry_after = db.telemetry.count_documents({"asset_tag": "P-194"})
        assert p194_docs_after == p194_docs_count_before == 12, "CRITICAL: P-194 documents were modified!"
        assert p194_chunks_after == p194_chunks_count_before == 14, "CRITICAL: P-194 chunks were modified!"
        assert p194_telemetry_after == p194_telemetry_before == 15, "CRITICAL: P-194 telemetry was modified!"

        # Cleanup test shared file
        if shared_file.exists():
            shared_file.unlink()
        db.documents.delete_many({"document_id": {"$in": ["doc_shared_spec", "doc_shared_spec_p101_link"]}})
