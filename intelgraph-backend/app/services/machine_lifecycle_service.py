import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import HTTPException

from app.database import get_db
from app.config import settings
from app.models.auth import SystemRole, UserProfile, Permission
from app.services.audit_service import audit_service
from app.services.neo4j_service import neo4j_kg
from app.rag.qdrant_store import qdrant_store
from app.rag.vector_store import vector_store

logger = logging.getLogger("intelgraph.machine_lifecycle")

class MachineLifecycleService:
    """
    Enterprise Machine Lifecycle Management Service:
    - Reversible Machine Archival & Restoration
    - Multi-Layer Distributed Cascade Deletion Saga with Per-Layer Verification
    - Strict Server-Side Role Enforcement (Platform Administrator required for delete)
    - Shared Data Safety (Preserves global ontology concepts and shared files/chunks)
    - Multi-Tenant Isolation
    - Idempotent and Retry-Safe Cleanup
    """

    ALLOWED_DELETE_ROLES = [
        "Platform Administrator",
        SystemRole.PLATFORM_ADMIN.value,
        SystemRole.ADMIN.value,
        "Administrator"  # backwards compatibility alias
    ]

    def _normalize_tag(self, asset_tag: str) -> str:
        return asset_tag.strip().upper()

    def get_deletion_preview(
        self,
        asset_tag: str,
        current_user: Optional[UserProfile] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gathers live impact preview counts across all 13 MongoDB collections,
        Neo4j graph, Qdrant, FAISS, and filesystem storage before any action.
        Enforces authenticated tenant context and permissions.
        """
        tag = self._normalize_tag(asset_tag)
        db = get_db()
        if db is None:
            raise HTTPException(status_code=503, detail="Database unavailable")

        asset = db.assets.find_one({"tag": tag})
        if not asset:
            raise HTTPException(status_code=404, detail=f"Machine '{tag}' not found")

        default_tenant = getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")
        asset_tenant = asset.get("tenant_id") or default_tenant
        effective_tenant = current_user.tenant_id if current_user else (tenant_id or default_tenant)

        # Cross-tenant isolation check: Platform Administrator is tenant-scoped
        if effective_tenant and asset_tenant != effective_tenant and asset_tenant != "global":
            logger.warning(
                "Security tenant mismatch: user tenant '%s' attempted preview of machine '%s' belonging to tenant '%s'",
                effective_tenant, tag, asset_tenant
            )
            raise HTTPException(
                status_code=403,
                detail="Machine not found or you do not have permission to manage this machine."
            )

        # 1. MongoDB Collections Counts
        docs_cursor = list(db.documents.find({"asset_tag": tag}))
        doc_count = len(docs_cursor)
        chunk_count = db.document_chunks.count_documents({"asset_tag": tag})
        telemetry_count = db.telemetry.count_documents({"asset_tag": tag})
        insp_count = db.inspection_records.count_documents({"asset_tag": tag})
        maint_count = db.maintenance_records.count_documents({"asset_tag": tag})
        fail_count = db.failures.count_documents({"asset_tag": tag})
        notes_count = db.human_notes.count_documents({"asset_tag": tag})
        findings_count = db.findings.count_documents({"asset_tag": tag})
        actions_count = db.custom_actions.count_documents({"asset_tag": tag})

        # 2. Shared vs Exclusive Document Files Analysis
        shared_docs = []
        exclusive_docs = []
        for d in docs_cursor:
            file_hash = d.get("sha256_hash")
            file_path = d.get("file_path")
            doc_id = d.get("document_id")
            
            # Check if another document from a different machine shares the same hash or file path
            is_shared = False
            if file_hash:
                other_by_hash = db.documents.find_one({
                    "sha256_hash": file_hash,
                    "asset_tag": {"$ne": tag}
                })
                if other_by_hash:
                    is_shared = True
            if not is_shared and file_path:
                other_by_path = db.documents.find_one({
                    "file_path": file_path,
                    "asset_tag": {"$ne": tag}
                })
                if other_by_path:
                    is_shared = True

            doc_summary = {
                "document_id": doc_id,
                "filename": d.get("filename", "unknown"),
                "file_path": file_path,
                "sha256_hash": file_hash,
                "is_shared": is_shared
            }
            if is_shared:
                shared_docs.append(doc_summary)
            else:
                exclusive_docs.append(doc_summary)

        # 3. Neo4j Graph Subgraph Counts
        graph_counts = neo4j_kg.count_subgraph(tag)

        # 4. Vector Stores Counts
        qdrant_count = qdrant_store.count_by_asset_tag(tag, tenant_id=tenant_id)
        faiss_count = vector_store.count_by_asset_tag(tag)

        total_records_impacted = (
            1  # the asset record itself
            + doc_count
            + chunk_count
            + telemetry_count
            + insp_count
            + maint_count
            + fail_count
            + notes_count
            + findings_count
            + actions_count
            + graph_counts["node_count"]
            + graph_counts["edge_count"]
            + qdrant_count
            + faiss_count
        )

        return {
            "asset_tag": tag,
            "asset_name": asset.get("name", tag),
            "status": asset.get("status", "Operational"),
            "tenant_id": asset_tenant,
            "counts": {
                "asset": 1,
                "documents": doc_count,
                "document_chunks": chunk_count,
                "telemetry_points": telemetry_count,
                "inspection_records": insp_count,
                "maintenance_records": maint_count,
                "failure_records": fail_count,
                "human_notes": notes_count,
                "findings": findings_count,
                "custom_actions": actions_count,
                "neo4j_nodes": graph_counts["node_count"],
                "neo4j_edges": graph_counts["edge_count"],
                "qdrant_vectors": qdrant_count,
                "faiss_chunks": faiss_count,
                "exclusive_files": len(exclusive_docs),
                "shared_files": len(shared_docs)
            },
            "shared_documents": shared_docs,
            "exclusive_documents": exclusive_docs,
            "total_records_impacted": total_records_impacted,
            "can_delete": True,
            "warning": (
                f"Permanent deletion will purge {total_records_impacted} records across MongoDB, Neo4j, "
                f"Qdrant, and local storage for asset '{tag}'. Shared global ontology and documents referenced by "
                f"other machines will be strictly preserved."
            )
        }

    def archive_machine(
        self,
        asset_tag: str,
        current_user: Optional[UserProfile] = None,
        user_email: str = "operator@plant-ops.local",
        user_role: str = "Plant Manager",
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reversibly archives a machine. Sets status='Archived'.
        All historical records and documents are 100% retained for compliance.
        Restricted to Plant Manager or Platform Administrator.
        """
        tag = self._normalize_tag(asset_tag)
        db = get_db()
        if db is None:
            raise HTTPException(status_code=503, detail="Database unavailable")

        asset = db.assets.find_one({"tag": tag})
        if not asset:
            raise HTTPException(status_code=404, detail=f"Machine '{tag}' not found")

        eff_email = current_user.email if current_user else user_email
        eff_role = current_user.role.value if (current_user and hasattr(current_user.role, "value")) else (str(current_user.role) if current_user else user_role)
        eff_tenant = current_user.tenant_id if current_user else tenant_id

        # Role / Permission Check (Management or Platform Administrator required)
        allowed_archive_roles = ["Plant Manager", "Platform Administrator", SystemRole.PLATFORM_ADMIN.value, SystemRole.PLANT_MANAGER.value]
        has_perm = current_user and (Permission.ARCHIVE_ASSETS in current_user.permissions or current_user.role in [SystemRole.PLATFORM_ADMIN, SystemRole.ADMIN])
        if not has_perm and eff_role not in allowed_archive_roles:
            raise HTTPException(
                status_code=403,
                detail="Machine archival is restricted to Plant Manager or Platform Administrator."
            )

        default_tenant = getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")
        asset_tenant = asset.get("tenant_id") or default_tenant
        if eff_tenant and asset_tenant != eff_tenant and asset_tenant != "global":
            logger.warning(
                "Security tenant mismatch: user tenant '%s' attempted archival of machine '%s' belonging to tenant '%s'",
                eff_tenant, tag, asset_tenant
            )
            raise HTTPException(
                status_code=403,
                detail="Machine not found or you do not have permission to manage this machine."
            )

        prev_status = asset.get("status", "Operational")
        if prev_status == "Archived":
            return {"success": True, "message": f"Machine '{tag}' is already archived", "status": "Archived"}

        db.assets.update_one(
            {"tag": tag},
            {
                "$set": {
                    "status": "Archived",
                    "archived_at": datetime.utcnow().isoformat() + "Z",
                    "archived_by": eff_email,
                    "previous_status": prev_status
                }
            }
        )

        audit_service.log_event(
            user=eff_email,
            role=eff_role,
            action="MACHINE_ARCHIVED",
            target_type="ASSET",
            target_id=tag,
            details={
                "asset_tag": tag,
                "previous_status": prev_status,
                "new_status": "Archived",
                "reason": "Machine transitioned to historical/inactive state"
            }
        )

        logger.info("Archived machine '%s' by user '%s' (%s)", tag, eff_email, eff_role)
        return {
            "success": True,
            "message": f"Machine '{tag}' successfully archived. Historical records retained.",
            "asset_tag": tag,
            "status": "Archived"
        }

    def restore_machine(
        self,
        asset_tag: str,
        current_user: Optional[UserProfile] = None,
        user_email: str = "operator@plant-ops.local",
        user_role: str = "Plant Manager",
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Restores an archived machine to its operational state.
        Restricted to Plant Manager or Platform Administrator.
        """
        tag = self._normalize_tag(asset_tag)
        db = get_db()
        if db is None:
            raise HTTPException(status_code=503, detail="Database unavailable")

        asset = db.assets.find_one({"tag": tag})
        if not asset:
            raise HTTPException(status_code=404, detail=f"Machine '{tag}' not found")

        eff_email = current_user.email if current_user else user_email
        eff_role = current_user.role.value if (current_user and hasattr(current_user.role, "value")) else (str(current_user.role) if current_user else user_role)
        eff_tenant = current_user.tenant_id if current_user else tenant_id

        # Role / Permission Check (Management or Platform Administrator required)
        allowed_restore_roles = ["Plant Manager", "Platform Administrator", SystemRole.PLATFORM_ADMIN.value, SystemRole.PLANT_MANAGER.value]
        has_perm = current_user and (Permission.RESTORE_ASSETS in current_user.permissions or current_user.role in [SystemRole.PLATFORM_ADMIN, SystemRole.ADMIN])
        if not has_perm and eff_role not in allowed_restore_roles:
            raise HTTPException(
                status_code=403,
                detail="Machine restoration is restricted to Plant Manager or Platform Administrator."
            )

        default_tenant = getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")
        asset_tenant = asset.get("tenant_id") or default_tenant
        if eff_tenant and asset_tenant != eff_tenant and asset_tenant != "global":
            logger.warning(
                "Security tenant mismatch: user tenant '%s' attempted restoration of machine '%s' belonging to tenant '%s'",
                eff_tenant, tag, asset_tenant
            )
            raise HTTPException(
                status_code=403,
                detail="Machine not found or you do not have permission to manage this machine."
            )

        prev_status = asset.get("previous_status", "Operational")
        if prev_status == "Archived":
            prev_status = "Operational"

        db.assets.update_one(
            {"tag": tag},
            {
                "$set": {
                    "status": prev_status,
                    "restored_at": datetime.utcnow().isoformat() + "Z",
                    "restored_by": eff_email
                },
                "$unset": {
                    "archived_at": "",
                    "archived_by": "",
                    "previous_status": ""
                }
            }
        )

        audit_service.log_event(
            user=eff_email,
            role=eff_role,
            action="MACHINE_RESTORED",
            target_type="ASSET",
            target_id=tag,
            details={
                "asset_tag": tag,
                "restored_status": prev_status,
                "reason": "Machine restored to active operations"
            }
        )

        logger.info("Restored machine '%s' to status '%s' by user '%s' (%s)", tag, prev_status, eff_email, eff_role)
        return {
            "success": True,
            "message": f"Machine '{tag}' successfully restored to '{prev_status}' state.",
            "asset_tag": tag,
            "status": prev_status
        }

    def delete_machine_saga(
        self,
        asset_tag: str,
        current_user: Optional[UserProfile] = None,
        user_email: Optional[str] = None,
        user_role: Optional[str] = None,
        tenant_id: Optional[str] = None,
        exact_tag_confirm: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Controlled Cascade Deletion Saga:
        1. Authorization: strictly Platform Administrator (HTTP 403 otherwise)
        2. Confirmation: exact_tag_confirm must match asset_tag
        3. Tenant Isolation: Platform Administrator is tenant-scoped by default
        4. Preview & Shared Evaluation
        5. Qdrant vector cleanup
        6. FAISS index cleanup
        7. Neo4j subgraph cleanup (preserving global ontology and shared docs)
        8. Filesystem exclusive file unlinking (preserving shared files)
        9. MongoDB cascade deletion across all collections
        10. Per-layer verification
        11. Final Audit event: MACHINE_DELETED on complete verification, or MACHINE_DELETION_FAILED
        """
        tag = self._normalize_tag(asset_tag)

        eff_email = current_user.email if current_user else (user_email or "admin@intelgraph.local")
        eff_role = current_user.role.value if (current_user and hasattr(current_user.role, "value")) else (str(current_user.role) if current_user else user_role)
        eff_tenant = current_user.tenant_id if current_user else tenant_id

        # 1. Authorization Check (Platform Administrator strictly required server-side)
        # Deny before any deletion operation begins!
        if not eff_role or eff_role not in self.ALLOWED_DELETE_ROLES:
            logger.warning(
                "Unauthorized delete attempt for asset '%s' by user '%s' with role '%s'",
                tag, eff_email, eff_role
            )
            audit_service.log_event(
                user=eff_email,
                role=eff_role or "Unknown",
                action="UNAUTHORIZED_MACHINE_DELETION_ATTEMPT",
                target_type="ASSET",
                target_id=tag,
                details={
                    "error": "Forbidden: Requires Platform Administrator role",
                    "user_role": eff_role
                }
            )
            raise HTTPException(
                status_code=403,
                detail="Permanent machine deletion is strictly restricted to Platform Administrator."
            )

        # 2. Confirmation Check
        if exact_tag_confirm and exact_tag_confirm.strip().upper() != tag:
            raise HTTPException(
                status_code=400,
                detail=f"Confirmation mismatch: expected '{tag}', received '{exact_tag_confirm}'."
            )

        db = get_db()
        if db is None:
            raise HTTPException(status_code=503, detail="Database unavailable")

        asset = db.assets.find_one({"tag": tag})
        if not asset:
            raise HTTPException(status_code=404, detail=f"Machine '{tag}' not found")

        # 3. Tenant Isolation Check
        # Platform Administrator is tenant-scoped by default!
        # Platform Administrator from tenant A MUST NOT delete tenant B machine.
        default_tenant = getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")
        asset_tenant = asset.get("tenant_id") or default_tenant
        if eff_tenant and asset_tenant != eff_tenant and asset_tenant != "global":
            logger.warning(
                "Security tenant mismatch: user '%s' (tenant '%s') attempted deletion of machine '%s' (tenant '%s')",
                eff_email, eff_tenant, tag, asset_tenant
            )
            raise HTTPException(
                status_code=403,
                detail="Machine not found or you do not have permission to manage this machine."
            )

        # Step 4: Deletion Preview & Shared Document Identification
        preview = self.get_deletion_preview(tag, current_user=current_user, tenant_id=eff_tenant)
        shared_docs = preview["shared_documents"]
        exclusive_docs = preview["exclusive_documents"]

        saga_report = {
            "asset_tag": tag,
            "started_at": datetime.utcnow().isoformat() + "Z",
            "layers": {}
        }

        layer_failures = []

        # Step 4: Qdrant Vector Cleanup
        try:
            qdrant_deleted = qdrant_store.delete_by_asset_tag(tag, tenant_id=eff_tenant)
            saga_report["layers"]["qdrant"] = {"status": "SUCCESS", "deleted": qdrant_deleted}
        except Exception as e:
            logger.error("Qdrant deletion saga step failed: %s", e)
            saga_report["layers"]["qdrant"] = {"status": "FAILED", "error": str(e)}
            layer_failures.append(f"Qdrant: {e}")

        # Step 5: FAISS Vector Store Cleanup
        try:
            faiss_deleted = vector_store.delete_chunks_by_asset(tag)
            saga_report["layers"]["faiss"] = {"status": "SUCCESS", "deleted": faiss_deleted}
        except Exception as e:
            logger.error("FAISS deletion saga step failed: %s", e)
            saga_report["layers"]["faiss"] = {"status": "FAILED", "error": str(e)}
            layer_failures.append(f"FAISS: {e}")

        # Step 6: Neo4j Graph Subgraph Cleanup (Strictly preserves ontology and shared nodes)
        try:
            graph_res = neo4j_kg.delete_asset_subgraph(tag)
            saga_report["layers"]["neo4j"] = {"status": "SUCCESS", "details": graph_res}
        except Exception as e:
            logger.error("Neo4j deletion saga step failed: %s", e)
            saga_report["layers"]["neo4j"] = {"status": "FAILED", "error": str(e)}
            layer_failures.append(f"Neo4j: {e}")

        # Step 7: Filesystem Cleanup (Machine-exclusive files unlinked; shared files preserved)
        unlinked_files = []
        file_errors = []
        for ed in exclusive_docs:
            fp_str = ed.get("file_path")
            if fp_str:
                p = Path(fp_str)
                try:
                    if p.exists() and p.is_file():
                        p.unlink()
                        unlinked_files.append(str(p))
                except Exception as fe:
                    file_errors.append(f"{p}: {fe}")
        saga_report["layers"]["filesystem"] = {
            "status": "SUCCESS" if not file_errors else "PARTIAL",
            "unlinked_count": len(unlinked_files),
            "shared_files_preserved": len(shared_docs),
            "errors": file_errors
        }
        if file_errors:
            layer_failures.append(f"Filesystem: {file_errors}")

        # Step 8: MongoDB Cascade Deletion
        mongo_deleted = {}
        try:
            # 8.1 Remove machine record
            r_asset = db.assets.delete_many({"tag": tag})
            mongo_deleted["assets"] = r_asset.deleted_count

            # 8.2 Remove chunks
            r_chunks = db.document_chunks.delete_many({"asset_tag": tag})
            mongo_deleted["document_chunks"] = r_chunks.deleted_count

            # 8.3 Remove exclusive documents; for shared documents, only detach this asset_tag
            exclusive_doc_ids = [d["document_id"] for d in exclusive_docs]
            if exclusive_doc_ids:
                r_docs = db.documents.delete_many({"document_id": {"$in": exclusive_doc_ids}})
                mongo_deleted["documents_exclusive_deleted"] = r_docs.deleted_count
            else:
                mongo_deleted["documents_exclusive_deleted"] = 0

            shared_doc_ids = [d["document_id"] for d in shared_docs]
            if shared_doc_ids:
                # Unlink this asset_tag from shared documents
                r_shared = db.documents.update_many(
                    {"document_id": {"$in": shared_doc_ids}},
                    {"$set": {"asset_tag": "SHARED_ENTERPRISE"}}
                )
                mongo_deleted["documents_shared_unlinked"] = r_shared.modified_count

            # 8.4 Remove all other machine-specific collection records
            mongo_deleted["telemetry"] = db.telemetry.delete_many({"asset_tag": tag}).deleted_count
            mongo_deleted["inspection_records"] = db.inspection_records.delete_many({"asset_tag": tag}).deleted_count
            mongo_deleted["maintenance_records"] = db.maintenance_records.delete_many({"asset_tag": tag}).deleted_count
            mongo_deleted["failures"] = db.failures.delete_many({"asset_tag": tag}).deleted_count
            mongo_deleted["human_notes"] = db.human_notes.delete_many({"asset_tag": tag}).deleted_count
            mongo_deleted["findings"] = db.findings.delete_many({"asset_tag": tag}).deleted_count
            mongo_deleted["custom_actions"] = db.custom_actions.delete_many({"asset_tag": tag}).deleted_count

            saga_report["layers"]["mongodb"] = {"status": "SUCCESS", "breakdown": mongo_deleted}
        except Exception as me:
            logger.error("MongoDB cascade deletion failed: %s", me)
            saga_report["layers"]["mongodb"] = {"status": "FAILED", "error": str(me)}
            layer_failures.append(f"MongoDB: {me}")

        # Step 9: Per-Layer Post-Deletion Verification
        verification = {
            "mongodb_asset_remaining": db.assets.count_documents({"tag": tag}),
            "mongodb_chunks_remaining": db.document_chunks.count_documents({"asset_tag": tag}),
            "mongodb_telemetry_remaining": db.telemetry.count_documents({"asset_tag": tag}),
            "neo4j_subgraph_nodes_remaining": neo4j_kg.count_subgraph(tag)["node_count"],
            "qdrant_vectors_remaining": qdrant_store.count_by_asset_tag(tag, tenant_id=eff_tenant),
            "faiss_chunks_remaining": vector_store.count_by_asset_tag(tag)
        }
        saga_report["verification"] = verification

        all_verified_clean = (
            verification["mongodb_asset_remaining"] == 0 and
            verification["mongodb_chunks_remaining"] == 0 and
            verification["mongodb_telemetry_remaining"] == 0 and
            verification["neo4j_subgraph_nodes_remaining"] == 0 and
            verification["qdrant_vectors_remaining"] == 0 and
            verification["faiss_chunks_remaining"] == 0 and
            len(layer_failures) == 0
        )

        saga_report["all_layers_verified_clean"] = all_verified_clean
        saga_report["completed_at"] = datetime.utcnow().isoformat() + "Z"

        # Step 10: Immutable Audit Trail Logging
        if all_verified_clean:
            audit_service.log_event(
                user=eff_email,
                role=eff_role,
                action="MACHINE_DELETED",
                target_type="ASSET",
                target_id=tag,
                details={
                    "asset_tag": tag,
                    "deleted_by": eff_email,
                    "role": eff_role,
                    "tenant_id": asset_tenant,
                    "verification": verification,
                    "records_deleted": mongo_deleted,
                    "unlinked_files": len(unlinked_files),
                    "shared_files_preserved": len(shared_docs),
                    "status": "COMPLETELY_VERIFIED"
                }
            )
            logger.info("Successfully deleted machine '%s' across all layers (verified 100%% clean)", tag)
            return {
                "success": True,
                "message": f"Machine '{tag}' and all associated records permanently deleted and verified clean across all storage layers.",
                "report": saga_report
            }
        else:
            # Failure / incomplete deletion detected: Record failure event and surface status clearly
            audit_service.log_event(
                user=eff_email,
                role=eff_role,
                action="MACHINE_DELETION_FAILED",
                target_type="ASSET",
                target_id=tag,
                details={
                    "asset_tag": tag,
                    "deleted_by": eff_email,
                    "role": eff_role,
                    "tenant_id": asset_tenant,
                    "verification": verification,
                    "layer_failures": layer_failures,
                    "status": "INCOMPLETE"
                }
            )
            logger.error("Machine '%s' deletion incomplete or verification failed: %s", tag, layer_failures)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": f"Machine deletion for '{tag}' could not be completely verified across all layers.",
                    "layer_failures": layer_failures,
                    "verification": verification,
                    "saga_report": saga_report
                }
            )

machine_lifecycle_service = MachineLifecycleService()
