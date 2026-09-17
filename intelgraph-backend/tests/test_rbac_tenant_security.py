import pytest
import os
import shutil
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import get_db
from app.models.auth import SystemRole
from app.models.document import DocumentChunk
from app.services.auth_service import auth_service
from app.services.neo4j_service import neo4j_kg
from app.rag.qdrant_store import qdrant_store
from app.rag.vector_store import vector_store

@pytest.mark.asyncio
async def test_rbac_and_tenant_security_matrix():
    """
    Dedicated Comprehensive RBAC & Multi-Tenant Security Verification Suite:
    1. Operational Roles Rejection: 403 on DELETE for all operational roles.
    2. Platform Administrator same-tenant Deletion: 200 and full saga cleanup.
    3. Cross-Tenant Isolation: Tenant A Admin -> Tenant B asset -> 403; Tenant B Admin -> Tenant A asset -> 403.
    4. Client Header Spoofing Protection: X-User-Role / X-Tenant-ID header spoofing rejected.
    5. Negative Operational Test: Failed operational delete leaves 100% of records intact across all layers.
    6. Deletion Preview Isolation: Cross-tenant preview denied with 403.
    7. Archive / Restore Authorization: Operational denied (403); Admin/Manager allowed (200).
    8. Protected Asset P-194 Integrity: Asserts P-194 is completely unaffected.
    """
    db = get_db()
    assert db is not None, "MongoDB must be available"

    # =========================================================================
    # BASELINE: Verify P-194 Protected Asset Integrity
    # =========================================================================
    p194_docs_before = db.documents.count_documents({"asset_tag": "P-194"})
    assert p194_docs_before == 12, f"P-194 must have 12 documents before test, found {p194_docs_before}"

    # Setup test file fixtures
    temp_dir = Path("./data/test_rbac_fixtures")
    temp_dir.mkdir(parents=True, exist_ok=True)
    rbac_file_1 = temp_dir / "rbac_exclusive_01.pdf"
    rbac_file_2 = temp_dir / "rbac_exclusive_02.pdf"
    rbac_file_b = temp_dir / "rbac_tenant_b_doc.pdf"
    rbac_file_1.write_text("RBAC Test exclusive document content 1")
    rbac_file_2.write_text("RBAC Test exclusive document content 2")
    rbac_file_b.write_text("Tenant B confidential manual")

    TAG_A1 = "DELETE-TEST-RBAC-001"  # For admin successful deletion
    TAG_A2 = "DELETE-TEST-RBAC-002"  # For negative operational test (must remain intact)
    TAG_B1 = "MACHINE-TENANT-B-001"  # Belongs to tenant_b

    try:
        # ---------------------------------------------------------------------
        # SEED ASSETS AND MULTI-LAYER DATA
        # ---------------------------------------------------------------------
        # Clean residual test fixtures
        db.assets.delete_many({"tag": {"$in": [TAG_A1, TAG_A2, TAG_B1]}})
        db.documents.delete_many({"asset_tag": {"$in": [TAG_A1, TAG_A2, TAG_B1]}})
        db.document_chunks.delete_many({"asset_tag": {"$in": [TAG_A1, TAG_A2, TAG_B1]}})
        qdrant_store.delete_by_asset_tag(TAG_A1)
        qdrant_store.delete_by_asset_tag(TAG_A2)
        qdrant_store.delete_by_asset_tag(TAG_B1)
        # Asset A1 (tenant_default)
        db.assets.insert_one({
            "tag": TAG_A1,
            "name": "RBAC Machine A1",
            "unit": "Unit 1",
            "criticality": "High",
            "status": "Operational",
            "tenant_id": "tenant_default"
        })
        db.documents.insert_one({
            "document_id": "doc_rbac_a1",
            "asset_tag": TAG_A1,
            "filename": "rbac_exclusive_01.pdf",
            "file_path": str(rbac_file_1),
            "sha256_hash": "hash_rbac_a1",
            "governance_status": "Approved",
            "tenant_id": "tenant_default"
        })
        chunk_a1 = DocumentChunk(
            chunk_id="chunk_rbac_a1",
            document_id="doc_rbac_a1",
            asset_tag=TAG_A1,
            section_title="Operating Specs A1",
            content="RBAC A1 content for vector store verification.",
            tenant_id="tenant_default"
        )
        db.document_chunks.insert_one(chunk_a1.model_dump())
        qdrant_store.add_chunks([chunk_a1])
        vector_store.add_chunks([chunk_a1])
        neo4j_kg.add_node(f"asset_{TAG_A1}", "Asset", {"tag": TAG_A1, "tenant_id": "tenant_default"})

        # Asset A2 (tenant_default) - For Negative Test
        db.assets.insert_one({
            "tag": TAG_A2,
            "name": "RBAC Machine A2 Negative",
            "unit": "Unit 2",
            "criticality": "Medium",
            "status": "Operational",
            "tenant_id": "tenant_default"
        })
        db.documents.insert_one({
            "document_id": "doc_rbac_a2",
            "asset_tag": TAG_A2,
            "filename": "rbac_exclusive_02.pdf",
            "file_path": str(rbac_file_2),
            "sha256_hash": "hash_rbac_a2",
            "governance_status": "Approved",
            "tenant_id": "tenant_default"
        })
        chunk_a2 = DocumentChunk(
            chunk_id="chunk_rbac_a2",
            document_id="doc_rbac_a2",
            asset_tag=TAG_A2,
            section_title="Operating Specs A2",
            content="RBAC A2 negative test content.",
            tenant_id="tenant_default"
        )
        db.document_chunks.insert_one(chunk_a2.model_dump())
        db.telemetry.insert_one({"asset_tag": TAG_A2, "vibration_rms": 1.8, "tenant_id": "tenant_default"})
        db.maintenance_records.insert_one({"record_id": "wo_a2_01", "asset_tag": TAG_A2, "work_order_number": "WO-A2"})
        qdrant_store.add_chunks([chunk_a2])
        vector_store.add_chunks([chunk_a2])
        neo4j_kg.add_node(f"asset_{TAG_A2}", "Asset", {"tag": TAG_A2, "tenant_id": "tenant_default"})

        # Asset B1 (tenant_b) - Cross-tenant machine
        db.assets.insert_one({
            "tag": TAG_B1,
            "name": "Tenant B Machine 1",
            "unit": "Plant B",
            "criticality": "High",
            "status": "Operational",
            "tenant_id": "tenant_b"
        })
        db.documents.insert_one({
            "document_id": "doc_rbac_b1",
            "asset_tag": TAG_B1,
            "filename": "rbac_tenant_b_doc.pdf",
            "file_path": str(rbac_file_b),
            "sha256_hash": "hash_rbac_b1",
            "governance_status": "Approved",
            "tenant_id": "tenant_b"
        })
        chunk_b1 = DocumentChunk(
            chunk_id="chunk_rbac_b1",
            document_id="doc_rbac_b1",
            asset_tag=TAG_B1,
            section_title="Specs B1",
            content="Tenant B machine content.",
            tenant_id="tenant_b"
        )
        db.document_chunks.insert_one(chunk_b1.model_dump())
        qdrant_store.add_chunks([chunk_b1])
        vector_store.add_chunks([chunk_b1])
        neo4j_kg.add_node(f"asset_{TAG_B1}", "Asset", {"tag": TAG_B1, "tenant_id": "tenant_b"})

        # Authenticate sessions
        admin_a = auth_service.authenticate("admin@intelgraph.local", "AdminPassword123!")
        eng_a = auth_service.authenticate("engineer@plant-ops.local", "Password123!")
        mgr_a = auth_service.authenticate("manager@plant-ops.local", "Password123!")
        tech_a = auth_service.authenticate("technician@plant-ops.local", "Password123!")
        auditor_a = auth_service.authenticate("auditor@compliance.local", "Password123!")
        ops_a = auth_service.authenticate("operations@plant-ops.local", "Password123!")
        rel_a = auth_service.authenticate("reliability@plant-ops.local", "Password123!")
        admin_b = auth_service.authenticate("admin@tenant-b.local", "AdminPassword123!")

        assert admin_a.user.tenant_id == "tenant_default"
        assert admin_b.user.tenant_id == "tenant_b"

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:

            # =================================================================
            # TEST 1: OPERATIONAL ROLES DELETE REJECTION (HTTP 403)
            # =================================================================
            operational_sessions = [
                (eng_a, "Maintenance Engineer"),
                (tech_a, "Field Technician"),
                (ops_a, "Operations Engineer"),
                (rel_a, "Reliability Engineer"),
                (auditor_a, "Quality / Compliance Auditor"),
                (mgr_a, "Plant Manager")
            ]

            for sess, role_name in operational_sessions:
                res = await ac.delete(
                    f"/api/machines/{TAG_A2}?exact_tag_confirm={TAG_A2}",
                    headers={"Authorization": f"Bearer {sess.token}"}
                )
                assert res.status_code == 403, f"Role {role_name} should receive 403, got {res.status_code}"
                assert "strictly restricted to Platform Administrator" in res.json()["detail"]

            # =================================================================
            # TEST 2: NEGATIVE OPERATIONAL TEST - ZERO DATA DELETION OCCURS
            # =================================================================
            # After multiple 403 attempts on TAG_A2, verify that NO data was wiped in ANY layer:
            assert db.assets.count_documents({"tag": TAG_A2}) == 1, "Asset document must be intact"
            assert db.documents.count_documents({"asset_tag": TAG_A2}) == 1, "Documents must be intact"
            assert db.document_chunks.count_documents({"asset_tag": TAG_A2}) == 1, "Chunks must be intact"
            assert db.telemetry.count_documents({"asset_tag": TAG_A2}) == 1, "Telemetry must be intact"
            assert db.maintenance_records.count_documents({"asset_tag": TAG_A2}) == 1, "Maintenance must be intact"
            assert rbac_file_2.exists(), "File on disk must not be deleted on 403"
            assert f"asset_{TAG_A2}" in neo4j_kg.nodes, "Neo4j node must not be deleted on 403"
            assert qdrant_store.count_by_asset_tag(TAG_A2) == 1, "Qdrant vector point must not be deleted on 403"

            # =================================================================
            # TEST 3: CLIENT HEADER SPOOFING PROTECTION
            # =================================================================
            # 3.1 Maintenance Engineer claiming X-User-Role: Platform Administrator
            res_spoof_role = await ac.delete(
                f"/api/machines/{TAG_A2}?exact_tag_confirm={TAG_A2}",
                headers={
                    "Authorization": f"Bearer {eng_a.token}",
                    "X-User-Role": "Platform Administrator"
                }
            )
            assert res_spoof_role.status_code == 403, "Spoofed X-User-Role must be rejected"

            # 3.2 Anonymous user sending only X-User-Role
            res_anon_spoof = await ac.delete(
                f"/api/machines/{TAG_A2}?exact_tag_confirm={TAG_A2}",
                headers={"X-User-Role": "Platform Administrator"}
            )
            assert res_anon_spoof.status_code == 403, "Anonymous spoofed role must be rejected"

            # =================================================================
            # TEST 4: CROSS-TENANT ISOLATION (HTTP 403)
            # =================================================================
            # 4.1 Tenant A Admin attempting to delete Tenant B asset
            res_cross_a_to_b = await ac.delete(
                f"/api/machines/{TAG_B1}?exact_tag_confirm={TAG_B1}",
                headers={"Authorization": f"Bearer {admin_a.token}"}
            )
            assert res_cross_a_to_b.status_code == 403, "Admin A cannot delete Tenant B asset"
            assert "Machine not found or you do not have permission to manage this machine" in res_cross_a_to_b.json()["detail"]

            # 4.2 Tenant B Admin attempting to delete Tenant A asset
            res_cross_b_to_a = await ac.delete(
                f"/api/machines/{TAG_A1}?exact_tag_confirm={TAG_A1}",
                headers={"Authorization": f"Bearer {admin_b.token}"}
            )
            assert res_cross_b_to_a.status_code == 403, "Admin B cannot delete Tenant A asset"
            assert "Machine not found or you do not have permission to manage this machine" in res_cross_b_to_a.json()["detail"]

            # 4.3 Tenant B Admin attempting to spoof X-Tenant-ID to tenant_default
            res_spoof_tenant = await ac.delete(
                f"/api/machines/{TAG_A1}?exact_tag_confirm={TAG_A1}",
                headers={
                    "Authorization": f"Bearer {admin_b.token}",
                    "X-Tenant-ID": "tenant_default"
                }
            )
            assert res_spoof_tenant.status_code == 403, "Tenant spoofing via header must be rejected"

            # 4.4 Tenant A Operational User attempting to delete Tenant B asset
            res_ops_cross = await ac.delete(
                f"/api/machines/{TAG_B1}?exact_tag_confirm={TAG_B1}",
                headers={"Authorization": f"Bearer {eng_a.token}"}
            )
            assert res_ops_cross.status_code == 403

            # =================================================================
            # TEST 5: DELETION PREVIEW AUTHORIZATION & TENANT ISOLATION
            # =================================================================
            # 5.1 Same-tenant Admin preview succeeds
            res_prev_ok = await ac.get(
                f"/api/machines/{TAG_A1}/deletion-preview",
                headers={"Authorization": f"Bearer {admin_a.token}"}
            )
            assert res_prev_ok.status_code == 200
            assert res_prev_ok.json()["asset_tag"] == TAG_A1

            # 5.2 Cross-tenant Admin preview denied
            res_prev_cross = await ac.get(
                f"/api/machines/{TAG_B1}/deletion-preview",
                headers={"Authorization": f"Bearer {admin_a.token}"}
            )
            assert res_prev_cross.status_code == 403

            # =================================================================
            # TEST 6: ARCHIVE & RESTORE AUTHORIZATION
            # =================================================================
            # 6.1 Operational role (Maintenance Engineer) denied archive -> 403
            res_arch_forbid = await ac.post(
                f"/api/machines/{TAG_A1}/archive",
                headers={"Authorization": f"Bearer {eng_a.token}"}
            )
            assert res_arch_forbid.status_code == 403

            # 6.2 Plant Manager allowed archive -> 200
            res_arch_mgr = await ac.post(
                f"/api/machines/{TAG_A1}/archive",
                headers={"Authorization": f"Bearer {mgr_a.token}"}
            )
            assert res_arch_mgr.status_code == 200
            assert res_arch_mgr.json()["status"] == "Archived"

            # 6.3 Plant Manager allowed restore -> 200
            res_rest_mgr = await ac.post(
                f"/api/machines/{TAG_A1}/restore",
                headers={"Authorization": f"Bearer {mgr_a.token}"}
            )
            assert res_rest_mgr.status_code == 200
            assert res_rest_mgr.json()["status"] == "Operational"

            # =================================================================
            # TEST 7: PLATFORM ADMINISTRATOR SAME-TENANT DELETE SAGA (HTTP 200)
            # =================================================================
            res_del_ok = await ac.delete(
                f"/api/machines/{TAG_A1}?exact_tag_confirm={TAG_A1}",
                headers={"Authorization": f"Bearer {admin_a.token}"}
            )
            assert res_del_ok.status_code == 200
            del_body = res_del_ok.json()
            assert del_body["success"] is True
            assert del_body["report"]["all_layers_verified_clean"] is True

            # Assert clean all-layer removal for TAG_A1
            assert db.assets.count_documents({"tag": TAG_A1}) == 0
            assert db.documents.count_documents({"asset_tag": TAG_A1}) == 0
            assert db.document_chunks.count_documents({"asset_tag": TAG_A1}) == 0
            assert not rbac_file_1.exists(), "Exclusive disk file must be deleted"
            assert f"asset_{TAG_A1}" not in neo4j_kg.nodes
            assert qdrant_store.count_by_asset_tag(TAG_A1) == 0

            # =================================================================
            # TEST 8: PROTECTED ASSET P-194 REMAINS 100% INTACT
            # =================================================================
            p194_docs_after = db.documents.count_documents({"asset_tag": "P-194"})
            p194_chunks_after = db.document_chunks.count_documents({"asset_tag": "P-194"})
            assert p194_docs_after == 12, f"P-194 documents must remain 12, got {p194_docs_after}"
            assert p194_chunks_after == 14, f"P-194 chunks must remain 14, got {p194_chunks_after}"

    finally:
        # Cleanup test files and test machines
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        db.assets.delete_many({"tag": {"$in": [TAG_A1, TAG_A2, TAG_B1]}})
        db.documents.delete_many({"asset_tag": {"$in": [TAG_A1, TAG_A2, TAG_B1]}})
        db.document_chunks.delete_many({"asset_tag": {"$in": [TAG_A1, TAG_A2, TAG_B1]}})
        db.telemetry.delete_many({"asset_tag": {"$in": [TAG_A1, TAG_A2, TAG_B1]}})
        db.maintenance_records.delete_many({"asset_tag": {"$in": [TAG_A1, TAG_A2, TAG_B1]}})
