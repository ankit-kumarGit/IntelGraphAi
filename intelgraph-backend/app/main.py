from fastapi import FastAPI, Request, UploadFile, File, Form, Query, Header, HTTPException, Body
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import BaseModel
import shutil
import time
from datetime import datetime

from app.config import settings, UPLOADS_DIR
from app.database import db_manager, get_db
from app.models.asset import AssetCreate
from app.models.chat import ChatRequest, ChatResponse, BenchmarkResult
from app.models.maintenance import MaintenanceRecord, InspectionRecord
from app.services.asset_service import asset_service
from app.services.doc_service import doc_service
from app.services.knowledge_map_service import knowledge_map_service
from app.services.maintenance_service import maintenance_service
from app.services.compliance_service import compliance_service
from app.services.cross_asset_service import cross_asset_service
from app.services.rca_service import rca_service
from app.services.audit_service import audit_service
from app.services.entity_resolution import entity_resolution
from app.services.auth_service import auth_service, Permission, SystemRole
from app.services.observability_service import observability_service
from app.services.neo4j_service import neo4j_graph
from app.services.connectors import connectors_manager
from app.services.machine_lifecycle_service import machine_lifecycle_service
from app.document_processing.ocr_engine import ocr_engine
from app.rag.qdrant_store import qdrant_store
from app.rag.assistant import knowledge_assistant
from app.rag.vector_store import vector_store
from app.benchmark.runner import BenchmarkRunner
from app.document_processing.pid_extractor import PIDTagExtractor
from app.document_processing.extractor import DocumentExtractor
from app.services.machine_resolution_service import machine_resolution

#######
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Unified Asset & Operations Brain - Industrial Knowledge Intelligence Platform",
    version="1.0.0"
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_details = exc.errors()
    print("\n" + "="*50)
    print(f"🚨 422 VALIDATION ERROR DETECTED 🚨")
    print(f"Endpoint: {request.url.path}")
    print(f"Error Details: {error_details}")
    print("="*50 + "\n")
    return JSONResponse(status_code=422, content={"detail": error_details})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    db_manager.connect()
    vector_store.load()
    if vector_store.is_fitted:
        qdrant_store.vectorizer = vector_store.vectorizer
        qdrant_store.is_fitted = True

# ==========================================
# System & Health
# ==========================================
@app.get("/health")
@app.get("/api/health")
def health_check():
    db_ok = db_manager.db is not None
    chunk_count = len(vector_store.chunks_metadata) if vector_store else 0
    return {
        "status": "healthy",
        "database_connected": db_ok,
        "vector_store_loaded": vector_store.is_fitted,
        "indexed_chunks_count": chunk_count,
        "llm_provider": settings.LLM_PROVIDER
    }

# ==========================================
# Overview & Fleet Metrics
# ==========================================
@app.get("/api/overview")
def get_fleet_overview(role: str = "Maintenance Engineer"):
    assets = asset_service.get_all_assets()
    total_assets = len(assets)
    active_assets = sum(1 for a in assets if a.get("status") == "Operational")
    maint_due = sum(1 for a in assets if a.get("status") == "Maintenance Due")
    critical_assets = sum(1 for a in assets if a.get("status") == "Critical" or a.get("criticality") == "Critical")

    db = get_db()
    total_docs = db.documents.count_documents({}) if db is not None else 0
    processed_docs = db.documents.count_documents({"chunk_count": {"$gt": 0}}) if db is not None else 0
    obsolete_docs = db.documents.count_documents({"governance_status": "Obsolete"}) if db is not None else 0

    open_findings = list(db.findings.find({"status": "Open"})) if db is not None else []
    for f in open_findings:
        f["_id"] = str(f.get("_id", ""))

    compliance_summary = compliance_service.get_fleet_compliance_summary()
    cross_patterns = cross_asset_service.analyze_fleet_patterns()

    # Calculate average completeness
    avg_completeness = round(sum(a.get("completeness_score", 0) for a in assets) / total_assets, 1) if total_assets > 0 else 0.0

    return {
        "metrics": {
            "total_assets": total_assets,
            "active_assets": active_assets,
            "maintenance_due": maint_due,
            "critical_assets": critical_assets,
            "total_documents": total_docs,
            "processed_documents": processed_docs,
            "obsolete_documents": obsolete_docs,
            "average_completeness_pct": avg_completeness,
            "open_findings_count": len(open_findings),
            "fleet_compliance_rate_pct": compliance_summary.get("compliance_rate_pct", 0.0)
        },
        "open_findings": open_findings,
        "cross_asset_alerts": cross_patterns,
        "compliance_summary": compliance_summary,
        "user_role": role
    }

# ==========================================
# Hierarchy & Assets
# ==========================================
@app.get("/api/hierarchy")
def get_hierarchy():
    return asset_service.get_hierarchy()

class MachineUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    area: Optional[str] = None
    plant: Optional[str] = None
    criticality: Optional[str] = None
    asset_type: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    status: Optional[str] = None

class MachineDeleteRequest(BaseModel):
    exact_tag_confirm: str
    reason: Optional[str] = None

class MachineLifecycleActionRequest(BaseModel):
    reason: Optional[str] = None

@app.get("/api/assets")
@app.get("/api/machines")
def list_assets(
    include_archived: bool = Query(False),
    status: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    eff_tenant = tenant_id
    if not eff_tenant and authorization and authorization.startswith("Bearer "):
        tok = authorization.split("Bearer ")[1].strip()
        user = auth_service.get_user_by_token(tok)
        if user:
            eff_tenant = user.tenant_id
    return asset_service.get_all_assets(include_archived=include_archived, status=status, tenant_id=eff_tenant)

@app.post("/api/assets")
@app.post("/api/machines")
def create_asset(data: AssetCreate):
    created = asset_service.create_asset(data)
    audit_service.log_event(
        user="Operator",
        role="Maintenance Engineer",
        action="Asset Created",
        target_type="Asset",
        target_id=data.tag,
        details=f"Created new asset profile {data.tag} ({data.name})"
    )
    return created

@app.get("/api/assets/{tag}")
@app.get("/api/machines/{tag}")
def get_asset(
    tag: str,
    tenant_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    eff_tenant = tenant_id
    if not eff_tenant and authorization and authorization.startswith("Bearer "):
        tok = authorization.split("Bearer ")[1].strip()
        user = auth_service.get_user_by_token(tok)
        if user:
            eff_tenant = user.tenant_id

    asset = asset_service.get_asset(tag)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Enforce strict tenant isolation: Never expose cross-tenant machine
    asset_tenant = asset.get("tenant_id")
    if eff_tenant and asset_tenant and asset_tenant != eff_tenant:
        raise HTTPException(status_code=403, detail=f"Access denied: machine '{tag}' belongs to another tenant")

    return asset

@app.put("/api/assets/{tag}")
@app.put("/api/machines/{tag}")
def update_machine(
    tag: str,
    payload: MachineUpdateRequest,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    auth_token = None
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split("Bearer ")[1].strip()
    elif token:
        auth_token = token

    user = auth_service.get_user_by_token(auth_token) if auth_token else None
    if user:
        db = get_db()
        asset = db.assets.find_one({"tag": tag.upper().strip()}) if db is not None else None
        if asset:
            default_tenant = getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")
            asset_tenant = asset.get("tenant_id") or default_tenant
            if user.tenant_id and asset_tenant != user.tenant_id and asset_tenant != "global":
                raise HTTPException(
                    status_code=403,
                    detail="Machine not found or you do not have permission to manage this machine."
                )

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    updated = asset_service.update_asset(tag, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Machine '{tag}' not found")
    audit_service.log_event(
        user=user.email if user else "Operator",
        role=user.role.value if user else "Plant Manager",
        action="MACHINE_UPDATED",
        target_type="ASSET",
        target_id=tag.upper(),
        details={"updated_fields": list(update_data.keys())}
    )
    return updated

@app.get("/api/machines/{tag}/deletion-preview")
@app.get("/api/assets/{tag}/deletion-preview")
def get_machine_deletion_preview(
    tag: str,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    auth_token = None
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split("Bearer ")[1].strip()
    elif token:
        auth_token = token

    user = auth_service.get_user_by_token(auth_token) if auth_token else None
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to view machine deletion preview."
        )

    return machine_lifecycle_service.get_deletion_preview(tag, current_user=user)

@app.post("/api/machines/{tag}/archive")
@app.post("/api/assets/{tag}/archive")
def archive_machine_endpoint(
    tag: str,
    payload: Optional[MachineLifecycleActionRequest] = None,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    auth_token = None
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split("Bearer ")[1].strip()
    elif token:
        auth_token = token

    user = auth_service.get_user_by_token(auth_token) if auth_token else None
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to archive machines."
        )

    return machine_lifecycle_service.archive_machine(
        asset_tag=tag,
        current_user=user
    )

@app.post("/api/machines/{tag}/restore")
@app.post("/api/assets/{tag}/restore")
def restore_machine_endpoint(
    tag: str,
    payload: Optional[MachineLifecycleActionRequest] = None,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    auth_token = None
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split("Bearer ")[1].strip()
    elif token:
        auth_token = token

    user = auth_service.get_user_by_token(auth_token) if auth_token else None
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to restore machines."
        )

    return machine_lifecycle_service.restore_machine(
        asset_tag=tag,
        current_user=user
    )

@app.delete("/api/machines/{tag}")
@app.delete("/api/assets/{tag}")
def delete_machine_endpoint(
    tag: str,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
    exact_tag_confirm: Optional[str] = Query(None),
    payload: Optional[MachineDeleteRequest] = None
):
    auth_token = None
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split("Bearer ")[1].strip()
    elif token:
        auth_token = token

    user = auth_service.get_user_by_token(auth_token) if auth_token else None
    if not user:
        raise HTTPException(
            status_code=403,
            detail="Permanent machine deletion is strictly restricted to Platform Administrator."
        )

    confirm_str = exact_tag_confirm or (payload.exact_tag_confirm if payload else None)

    return machine_lifecycle_service.delete_machine_saga(
        asset_tag=tag,
        current_user=user,
        exact_tag_confirm=confirm_str
    )

@app.get("/api/assets/{tag}/knowledge-map")
def get_knowledge_map(tag: str):
    return knowledge_map_service.get_asset_knowledge_map(tag)

@app.get("/api/assets/{tag}/maintenance")
def get_asset_maintenance(tag: str):
    return maintenance_service.get_asset_maintenance(tag)

@app.get("/api/assets/{tag}/telemetry")
def get_asset_telemetry(tag: str):
    return maintenance_service.get_telemetry(tag)

class FindingCreateRequest(BaseModel):
    finding_id: Optional[str] = None
    asset_tag: str
    title: str
    evidence_summary: str
    linked_documents: List[str] = []
    linked_inspections: List[str] = []
    recommended_action: Optional[str] = None
    source_procedure: Optional[str] = None
    severity: str = "Medium"
    owner: str = "Reliability Engineer"
    status: str = "Open"
    is_ai_generated: bool = False
    verified_by_human: bool = False
    verified_by: Optional[str] = None

class FindingUpdateRequest(BaseModel):
    status: Optional[str] = None
    owner: Optional[str] = None
    recommended_action: Optional[str] = None
    evidence_summary: Optional[str] = None
    verified_by_human: Optional[bool] = None
    verified_by: Optional[str] = None
    reviewer_notes: Optional[str] = None

@app.get("/api/findings")
def list_findings(asset_tag: Optional[str] = None, status: Optional[str] = None):
    db = get_db()
    if db is None:
        return []
    query = {}
    if asset_tag:
        query["asset_tag"] = asset_tag.upper()
    if status:
        query["status"] = status
    findings = list(db.findings.find(query))
    for f in findings:
        f["_id"] = str(f.get("_id", ""))
    return findings

@app.get("/api/assets/{tag}/findings")
def get_asset_findings(tag: str):
    db = get_db()
    if db is None:
        return {"asset_tag": tag.upper(), "findings": []}
    findings = list(db.findings.find({"asset_tag": tag.upper()}))
    for f in findings:
        f["_id"] = str(f.get("_id", ""))
    return {"asset_tag": tag.upper(), "findings": findings}

@app.post("/api/findings")
@app.post("/api/assets/{tag}/findings")
def create_finding(
    payload: FindingCreateRequest,
    tag: Optional[str] = None
):
    asset_tag = (tag or payload.asset_tag).upper()
    if payload.is_ai_generated and payload.status == "Verified" and not payload.verified_by_human:
        raise HTTPException(
            status_code=400,
            detail="Policy Violation: Unsupported AI findings cannot become verified facts automatically without human sign-off."
        )

    db = get_db()
    finding_id = payload.finding_id or f"FIND-{asset_tag}-{int(time.time() * 1000)}"
    entry = {
        "finding_id": finding_id,
        "asset_tag": asset_tag,
        "title": payload.title,
        "evidence_summary": payload.evidence_summary,
        "linked_documents": payload.linked_documents,
        "linked_inspections": payload.linked_inspections,
        "recommended_action": payload.recommended_action or "Review operational history and inspect component.",
        "source_procedure": payload.source_procedure or "SOP-MECH-04",
        "severity": payload.severity,
        "owner": payload.owner,
        "status": payload.status,
        "is_ai_generated": payload.is_ai_generated,
        "verified_by_human": payload.verified_by_human,
        "verified_by": payload.verified_by if payload.verified_by_human else None,
        "created_at": datetime.utcnow().isoformat()
    }
    if db is not None:
        db.findings.update_one({"finding_id": finding_id}, {"$set": entry}, upsert=True)
    
    audit_service.log_event(
        user=payload.owner or "Engineer",
        role="Reliability Engineer",
        action="FINDING_CREATED",
        target_type="Finding",
        target_id=finding_id,
        details=f"Created finding '{payload.title}' for asset {asset_tag} with {len(payload.linked_documents)} linked documents."
    )
    return entry

@app.patch("/api/findings/{finding_id}")
def update_finding(finding_id: str, payload: FindingUpdateRequest):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database unavailable")
    existing = db.findings.find_one({"finding_id": finding_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Finding not found")

    if existing.get("is_ai_generated") and payload.status == "Verified" and not (payload.verified_by_human or existing.get("verified_by_human")):
        raise HTTPException(
            status_code=400,
            detail="Policy Violation: AI-generated finding cannot be marked 'Verified' without explicit human engineer sign-off."
        )

    updates = {}
    if payload.status is not None:
        updates["status"] = payload.status
    if payload.owner is not None:
        updates["owner"] = payload.owner
    if payload.recommended_action is not None:
        updates["recommended_action"] = payload.recommended_action
    if payload.evidence_summary is not None:
        updates["evidence_summary"] = payload.evidence_summary
    if payload.verified_by_human is not None:
        updates["verified_by_human"] = payload.verified_by_human
    if payload.verified_by is not None:
        updates["verified_by"] = payload.verified_by
    if payload.reviewer_notes is not None:
        updates["reviewer_notes"] = payload.reviewer_notes
    updates["updated_at"] = datetime.utcnow().isoformat()

    db.findings.update_one({"finding_id": finding_id}, {"$set": updates})

    audit_service.log_event(
        user=payload.verified_by or "Reliability Lead",
        role="Reliability Engineer",
        action="FINDING_UPDATED",
        target_type="Finding",
        target_id=finding_id,
        details=f"Finding {finding_id} updated: status='{updates.get('status', existing.get('status'))}'"
    )
    existing.update(updates)
    existing["_id"] = str(existing.get("_id", ""))
    return existing

@app.get("/api/compliance/matrix")
@app.get("/api/assets/{tag}/compliance")
def get_asset_compliance(tag: Optional[str] = None, asset_tag: Optional[str] = None):
    effective_tag = tag or asset_tag or "P-101"
    return compliance_service.audit_asset_compliance(effective_tag)

@app.get("/api/assets/{tag}/notes")
def get_asset_notes(tag: str):
    db = get_db()
    if db is None:
        return []
    notes = list(db.human_notes.find({"asset_tag": tag.upper()}).sort("created_at", -1))
    for n in notes:
        n["_id"] = str(n.get("_id", ""))
    return notes

@app.post("/api/assets/{tag}/notes")
async def add_asset_note(
    tag: str,
    request: Request,
    text: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    author: str = Form("Field Operator"),
    author_role: str = Form("Field Technician"),
    note_type: str = Form("Observation"),
    component: Optional[str] = Form(None)
):
    body_data = {}
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body_data = await request.json()
        except Exception:
            body_data = {}

    note_author = body_data.get("author") or author
    note_role = body_data.get("author_role") or author_role
    note_type_val = body_data.get("note_type") or note_type
    note_comp = body_data.get("component") or component
    note_content = body_data.get("content") or body_data.get("text") or text or content or "Operational observation."

    db = get_db()
    note_id = f"note_{int(time.time() * 1000)}"
    entry = {
        "note_id": note_id,
        "asset_tag": tag.upper(),
        "author": note_author,
        "author_role": note_role,
        "note_type": note_type_val,
        "created_at": time.strftime("%Y-%m-%d %H:%M"),
        "text": note_content,
        "component": note_comp,
        "verified": False,
        "verification_status": "Unverified Operator Note"
    }
    if db is not None:
        db.human_notes.insert_one(entry)
    entry["_id"] = str(entry.get("_id", ""))
    
    audit_service.log_event(
        user=note_author,
        role=note_role,
        action="Note Added",
        target_type="Note",
        target_id=note_id,
        details=f"Added field observation for {tag.upper()}: {note_content[:60]}"
    )
    return {"status": "success", "note": entry}

# ==========================================
# Action Center
# ==========================================
@app.get("/api/actions")
def get_action_center_items():
    db = get_db()
    if db is None:
        return []

    actions = []
    # 1. Maintenance Due assets
    due_assets = list(db.assets.find({"status": "Maintenance Due"}))
    for a in due_assets:
        actions.append({
            "action_id": f"act_maint_{a['tag']}",
            "type": "Maintenance Due",
            "title": f"Overhaul Overdue: {a['tag']} ({a['name']})",
            "asset_tag": a["tag"],
            "why_it_matters": "Operating beyond scheduled maintenance interval increases risk of unscheduled trip.",
            "what_needs_action": "Schedule valve and cylinder overhaul window.",
            "evidence": "Operating hours exceeded service threshold.",
            "owner": "Maintenance Lead",
            "severity": "Critical",
            "status": "Pending"
        })

    # 2. Open Findings
    findings = list(db.findings.find({"status": "Open"}))
    for f in findings:
        actions.append({
            "action_id": f"act_find_{f['finding_id']}",
            "type": "Open Finding",
            "title": f.get("title"),
            "asset_tag": f.get("asset_tag"),
            "why_it_matters": "Chronic vibration leads to fatigue failure and shaft collar damage.",
            "what_needs_action": f.get("recommended_action"),
            "evidence": f.get("evidence_summary"),
            "owner": f.get("owner", "Reliability Engineer"),
            "severity": f.get("severity", "High"),
            "status": "In Review"
        })

    # 3. Compliance Documentation Gaps
    compliance_summary = compliance_service.get_fleet_compliance_summary()
    for gap in compliance_summary.get("gaps", []):
        actions.append({
            "action_id": f"act_gap_{gap['asset_tag']}_{gap['regulatory_body'].replace(' ', '_')}",
            "type": "Compliance Gap",
            "title": f"Missing Evidence: {gap['requirement']} ({gap['regulatory_body']})",
            "asset_tag": gap["asset_tag"],
            "why_it_matters": "Mandatory regulatory audit requirement. Non-compliance risks audit citation.",
            "what_needs_action": "Upload latest calibration certificate or schedule on-site calibration.",
            "evidence": gap.get("details"),
            "owner": "Quality / Compliance Lead",
            "severity": "Medium",
            "status": "Open"
        })

    # 4. Custom action items and status overrides
    custom_items = {}
    if db is not None:
        for ca in db.custom_actions.find({}):
            ca["_id"] = str(ca.get("_id", ""))
            aid = ca.get("action_id")
            if aid:
                custom_items[aid] = ca

    # Apply overrides to dynamically generated items
    for item in actions:
        aid = item.get("action_id")
        if aid in custom_items:
            # overlay persisted status, owner, etc.
            item.update(custom_items[aid])
            del custom_items[aid]

    # Append any purely custom created actions
    for remaining_ca in custom_items.values():
        actions.append(remaining_ca)

    return actions

@app.post("/api/actions")
def create_action_item(item: Dict[str, Any]):
    db = get_db()
    action_id = item.get("action_id") or f"act_custom_{int(time.time() * 1000)}"
    item["action_id"] = action_id
    if "status" not in item:
        item["status"] = "Open"
    if db is not None:
        db.custom_actions.update_one({"action_id": action_id}, {"$set": item}, upsert=True)
    audit_service.log_event(
        user=item.get("assigned_to", "Engineer"),
        role="Maintenance Engineer",
        action="ACTION_CREATED",
        target_type="ActionItem",
        target_id=action_id,
        details=f"Created action: {item.get('title')}"
    )
    return item

# ==========================================
# Document Library & Processing
# ==========================================
@app.get("/api/documents")
def list_documents(
    asset_tag: Optional[str] = None,
    category: Optional[str] = None,
    governance_status: Optional[str] = None,
    tenant_id: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    eff_tenant = tenant_id
    if not eff_tenant and authorization and authorization.startswith("Bearer "):
        tok = authorization.split("Bearer ")[1].strip()
        user = auth_service.get_user_by_token(tok)
        if user:
            eff_tenant = user.tenant_id
    return doc_service.list_documents(asset_tag, category, governance_status, tenant_id=eff_tenant)

@app.get("/api/documents/{doc_id}")
def get_document(doc_id: str, tenant_id: Optional[str] = None):
    doc = doc_service.get_document(doc_id, tenant_id=tenant_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@app.get("/api/documents/{doc_id}/chunks")
def get_document_chunks(doc_id: str):
    return doc_service.get_document_chunks(doc_id)

@app.post("/api/documents/inspect")
async def inspect_document(
    file: UploadFile = File(...),
    hint_tag: Optional[str] = Form(None),
    tenant_id: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None)
):
    """
    Fast pre-ingestion document inspection:
    Extracts text and runs MachineResolutionService to detect equipment tags,
    detect multi-asset situations, check against tenant asset inventory,
    and return resolution status before commit.
    """
    safe_filename = file.filename.replace(" ", "_")
    temp_inspect_path = UPLOADS_DIR / f"inspect_{int(time.time()*1000)}_{safe_filename}"
    try:
        with open(temp_inspect_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_type = safe_filename.rsplit(".", 1)[-1].lower() if "." in safe_filename else "txt"
        pages = DocumentExtractor.extract(temp_inspect_path, file_type)
        combined_text = "\n".join([p.get("content", "") for p in pages if p.get("content")])

        eff_tenant = tenant_id
        if not eff_tenant and authorization and authorization.startswith("Bearer "):
            tok = authorization.split("Bearer ")[1].strip()
            user = auth_service.get_user_by_token(tok)
            if user:
                eff_tenant = user.tenant_id
        if not eff_tenant:
            eff_tenant = getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")

        resolution = machine_resolution.resolve_machine_association(
            text=combined_text,
            filename=file.filename,
            hint_tag=hint_tag,
            tenant_id=eff_tenant
        )

        resolution["filename"] = file.filename
        resolution["file_type"] = file_type
        return resolution
    finally:
        if temp_inspect_path.exists():
            try:
                temp_inspect_path.unlink()
            except Exception:
                pass

@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    asset_tag: Optional[str] = Form(None),
    hint_asset_tag: Optional[str] = Form(None),
    category: str = Form("Other"),
    version: str = Form("v1.0"),
    governance_status: str = Form("Approved"),
    uploaded_by: str = Form("Maintenance Engineer"),
    tenant_id: Optional[str] = Form(None),
    explicit_override: bool = Form(False),
    create_missing_machine: bool = Form(False),
    authorization: Optional[str] = Header(None)
):
    safe_filename = file.filename.replace(" ", "_")
    target_path = UPLOADS_DIR / safe_filename
    
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    eff_tenant = tenant_id
    if not eff_tenant and authorization and authorization.startswith("Bearer "):
        tok = authorization.split("Bearer ")[1].strip()
        user = auth_service.get_user_by_token(tok)
        if user:
            eff_tenant = user.tenant_id
    if not eff_tenant:
        eff_tenant = getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")

    # Process and chunk document with strict server-side machine resolution
    doc_record = doc_service.process_and_save_document(
        file_path=target_path,
        filename=file.filename,
        asset_tag=asset_tag,
        hint_asset_tag=hint_asset_tag,
        category=category,
        version=version,
        governance_status=governance_status,
        uploaded_by=uploaded_by,
        tenant_id=eff_tenant,
        explicit_override=explicit_override,
        create_missing_machine=create_missing_machine
    )

    if doc_record.get("status") == "failed":
        audit_service.log_event(
            user=uploaded_by,
            role="Engineer",
            action="Document Ingestion Rejected",
            target_type="Document",
            target_id=doc_record["document_id"],
            details=f"Failed to ingest {file.filename}: {doc_record.get('message')}"
        )
        return doc_record

    assigned_tag = doc_record.get("asset_tag")
    if hint_asset_tag and assigned_tag:
        if explicit_override:
            audit_service.log_event(
                user=uploaded_by,
                role="Engineer",
                action="Machine Association Override",
                target_type="Document",
                target_id=doc_record["document_id"],
                details=f"Manual override confirmed: Kept upload hint '{assigned_tag}' for '{file.filename}' (detected machine reference preserved as evidence)."
            )
        elif hint_asset_tag.upper() != assigned_tag.upper():
            audit_service.log_event(
                user=uploaded_by,
                role="Engineer",
                action="Machine Association Confirmed",
                target_type="Document",
                target_id=doc_record["document_id"],
                details=f"Association confirmed: Linked '{file.filename}' to primary detected machine '{assigned_tag}' (upload hint was '{hint_asset_tag}')."
            )

    audit_service.log_event(
        user=uploaded_by,
        role="Engineer",
        action="Document Ingested",
        target_type="Document",
        target_id=doc_record["document_id"],
        details=f"Uploaded {file.filename} for {doc_record.get('asset_tag')} ({category}, {version})"
    )

    return doc_record

@app.post("/api/documents/upload-archive")
async def upload_archive(
    file: UploadFile = File(...),
    asset_tag: Optional[str] = Form(None),
    hint_asset_tag: Optional[str] = Form(None),
    category: str = Form("Archive Package"),
    governance_status: str = Form("Approved"),
    uploaded_by: str = Form("Maintenance Engineer"),
    tenant_id: Optional[str] = Form(None),
    explicit_override: bool = Form(False),
    create_missing_machine: bool = Form(False),
    authorization: Optional[str] = Header(None)
):
    """
    Ingests a multi-file .zip archive package with Zip Slip protection,
    quota enforcement, and safe member extraction.
    """
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip archive packages are supported.")

    safe_filename = file.filename.replace(" ", "_")
    target_path = UPLOADS_DIR / safe_filename

    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    eff_tenant = tenant_id
    if not eff_tenant and authorization and authorization.startswith("Bearer "):
        tok = authorization.split("Bearer ")[1].strip()
        user = auth_service.get_user_by_token(tok)
        if user:
            eff_tenant = user.tenant_id
    if not eff_tenant:
        eff_tenant = getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")

    doc_record = doc_service.process_and_save_document(
        file_path=target_path,
        filename=file.filename,
        asset_tag=asset_tag,
        hint_asset_tag=hint_asset_tag,
        category=category,
        version="v1.0-archive",
        governance_status=governance_status,
        uploaded_by=uploaded_by,
        tenant_id=eff_tenant,
        explicit_override=explicit_override,
        create_missing_machine=create_missing_machine
    )

    audit_service.log_event(
        user=uploaded_by,
        role="Engineer",
        action="Archive Ingested",
        target_type="Archive",
        target_id=doc_record["document_id"],
        details=f"Uploaded archive {file.filename} for {doc_record.get('asset_tag')} ({doc_record.get('total_pages', 1)} extracted pages/files)"
    )

    return doc_record

TEST_PACKAGE_DIR = Path("/Users/ankitkumar/Desktop/IntelGraphAI/test_p194_package")
TEST_PACKAGE_B_DIR = Path("/Users/ankitkumar/Desktop/IntelGraphAI/test_p194b_package")
TEST_PACKAGE_USER_DIR = Path("/Users/ankitkumar/Desktop/IntelGraphAI/test_fixtures_user_test")

@app.get("/api/test-package/list")
def list_test_package_files(package: str = "p194"):
    pkg = package.lower()
    if pkg in ("user_test", "user-test", "usertest"):
        target_dir = TEST_PACKAGE_USER_DIR
    elif pkg in ("p194b", "b"):
        target_dir = TEST_PACKAGE_B_DIR
    else:
        target_dir = TEST_PACKAGE_DIR
    if not target_dir.exists():
        return []
    valid_exts = {".txt", ".eml", ".zip", ".pdf", ".xlsx", ".png", ".csv"}
    return sorted([f.name for f in target_dir.iterdir() if f.is_file() and f.suffix.lower() in valid_exts])

@app.get("/api/test-package/{filename}")
def get_test_package_file(filename: str, package: str = "p194"):
    pkg = package.lower()
    if pkg in ("user_test", "user-test", "usertest"):
        target_dir = TEST_PACKAGE_USER_DIR
    elif pkg in ("p194b", "b"):
        target_dir = TEST_PACKAGE_B_DIR
    else:
        target_dir = TEST_PACKAGE_DIR
    p = target_dir / filename
    if not p.exists() and TEST_PACKAGE_USER_DIR.exists() and (TEST_PACKAGE_USER_DIR / filename).exists():
        p = TEST_PACKAGE_USER_DIR / filename
    elif not p.exists() and TEST_PACKAGE_B_DIR.exists() and (TEST_PACKAGE_B_DIR / filename).exists():
        p = TEST_PACKAGE_B_DIR / filename
    elif not p.exists() and TEST_PACKAGE_DIR.exists() and (TEST_PACKAGE_DIR / filename).exists():
        p = TEST_PACKAGE_DIR / filename
    if p.exists() and p.is_file():
        media_type = "application/pdf" if filename.endswith(".pdf") else "image/png" if filename.endswith(".png") else "application/zip" if filename.endswith(".zip") else "text/plain"
        return FileResponse(p, media_type=media_type, filename=filename)
    raise HTTPException(status_code=404, detail="File not found in test package")

@app.post("/api/test-package/reset-p194")
def reset_p194_state():
    db = get_db()
    if db is not None:
        db.assets.delete_many({"tag": "P-194"})
        db.documents.delete_many({"$or": [{"asset_tag": "P-194"}, {"filename": {"$regex": "P-194|P194"}}]})
        db.document_chunks.delete_many({"$or": [{"asset_tag": "P-194"}, {"document_id": {"$regex": "P-194|P194"}}]})
        db.telemetry.delete_many({"asset_tag": "P-194"})
        db.inspection_records.delete_many({"asset_tag": "P-194"})
        db.maintenance_records.delete_many({"asset_tag": "P-194"})
        db.failures.delete_many({"asset_tag": "P-194"})
        db.human_notes.delete_many({"asset_tag": "P-194"})
    try:
        neo4j_graph.delete_asset_subgraph("P-194")
    except Exception:
        pass
    # Clean uploaded test files from storage/uploads
    for f in UPLOADS_DIR.glob("P-194*"):
        try:
            f.unlink()
        except Exception:
            pass
    for f in UPLOADS_DIR.glob("SOP-P194*"):
        try:
            f.unlink()
        except Exception:
            pass
    return {"status": "success", "message": "P-194 test state reset successfully"}

@app.post("/api/documents/confirm-extraction")
def confirm_extraction(
    document_id: str = Form(...),
    confirmed_asset_tag: str = Form(...),
    event_type: str = Form("Maintenance"),
    event_date: str = Form("2026-03-01"),
    component: str = Form("Bearing"),
    work_order: Optional[str] = Form(None),
    confirmed_by: str = Form("Maintenance Engineer")
):
    """
    Human-in-the-loop confirmation step for Use Case 1.
    Allows user to verify or edit extracted industrial entities before committing.
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database unavailable")

    # Update document record with confirmed metadata
    db.documents.update_one(
        {"document_id": document_id},
        {"$set": {
            "asset_tag": confirmed_asset_tag.upper(),
            "extracted_entities.primary_asset_tag": confirmed_asset_tag.upper(),
            "extracted_entities.event_type": event_type,
            "extracted_entities.primary_date": event_date,
            "extracted_entities.primary_component": component,
            "extracted_entities.requires_human_confirmation": False,
            "confirmed_by": confirmed_by,
            "confirmed_date": time.strftime("%Y-%m-%d %H:%M")
        }}
    )

    # If it was a maintenance or inspection event, register record
    if event_type == "Maintenance" and work_order:
        m_rec = MaintenanceRecord(
            record_id=f"maint_{work_order.lower().replace('-', '_')}",
            asset_tag=confirmed_asset_tag.upper(),
            work_order_number=work_order,
            record_type="Corrective",
            date=event_date,
            technician=confirmed_by,
            description=f"Confirmed intervention on {component} from {document_id}",
            components_replaced=[component],
            hours_spent=4.0,
            document_ref=document_id,
            status="Completed"
        )
        maintenance_service.add_maintenance_record(m_rec)

    audit_service.log_event(
        user=confirmed_by,
        role="Maintenance Engineer",
        action="Extraction Confirmed",
        target_type="Document",
        target_id=document_id,
        details=f"Human verified extraction for {confirmed_asset_tag.upper()}: {event_type} on {component} ({event_date})"
    )

    return {"status": "success", "message": "Extraction confirmed and committed to asset profile."}

@app.patch("/api/documents/{doc_id}/governance")
async def update_document_governance(
    doc_id: str,
    request: Request,
    status: Optional[str] = Form(None),
    governance_status: Optional[str] = Form(None),
    version: Optional[str] = Form(None),
    updated_by: str = Form("Safety Officer")
):
    body_data = {}
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body_data = await request.json()
        except Exception:
            body_data = {}

    target_status = body_data.get("governance_status") or body_data.get("status") or governance_status or status
    if not target_status:
        raise HTTPException(status_code=400, detail="governance_status or status is required")
    target_version = body_data.get("version") or version
    user = body_data.get("updated_by") or updated_by

    success = doc_service.update_governance_status(doc_id, target_status, target_version)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or status unchanged")
    
    audit_service.log_event(
        user=user,
        role="Quality / Compliance",
        action="Governance Updated",
        target_type="Document",
        target_id=doc_id,
        details=f"Status set to {target_status}" + (f", version {target_version}" if target_version else "")
    )
    return {"status": "success", "document_id": doc_id, "governance_status": target_status}

# ==========================================
# Root Cause Analysis (RCA)
# ==========================================
@app.post("/api/rca/analyze")
def run_rca(asset_tag: str = Form(...), problem: str = Form("High Vibration & Bearing Seizure")):
    return rca_service.generate_rca(asset_tag, problem)

# ==========================================
# Cross-Asset Failure Intelligence
# ==========================================
@app.get("/api/cross-asset/patterns")
def get_cross_asset_patterns():
    return cross_asset_service.analyze_fleet_patterns()

# ==========================================
# AI Knowledge Assistant (Grounded RAG)
# ==========================================
@app.post("/api/chat", response_model=ChatResponse)
@app.post("/api/ai/chat", response_model=ChatResponse)
def chat_with_assistant(req: ChatRequest):
    asset_ctx = asset_service.get_asset(req.asset_tag) if req.asset_tag else None
    return knowledge_assistant.answer_query(req, asset_context=asset_ctx)

# ==========================================
# Benchmark Suite Runner
# ==========================================
@app.get("/api/benchmarks/run", response_model=BenchmarkResult)
def run_benchmarks():
    return BenchmarkRunner.run_benchmark()

@app.get("/api/benchmarks/qdrant")
def benchmark_qdrant(
    iterations: int = 50,
    q: str = "bearing vibration",
    asset_tag: Optional[str] = None,
    trusted_sources_only: bool = False
):
    import numpy as np
    times = []
    # Warmup
    res = qdrant_store.search(q, top_k=5, asset_tag=asset_tag, trusted_sources_only=trusted_sources_only)
    for _ in range(iterations):
        t0 = time.perf_counter()
        res = qdrant_store.search(q, top_k=5, asset_tag=asset_tag, trusted_sources_only=trusted_sources_only)
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000)
    arr = np.array(times)
    return {
        "operation": "Qdrant Vector Retrieval",
        "iterations": iterations,
        "query": q,
        "asset_tag": asset_tag,
        "average_ms": round(float(np.mean(arr)), 2),
        "p50_ms": round(float(np.percentile(arr, 50)), 2),
        "p95_ms": round(float(np.percentile(arr, 95)), 2),
        "p99_ms": round(float(np.percentile(arr, 99)), 2),
        "top_score": round(float(res[0][1]), 4) if res else 0.0,
        "results_count": len(res),
        "is_fitted": qdrant_store.is_fitted,
        "points_count": qdrant_store.client.get_collection("industrial_kb").points_count
    }

# ==========================================
# Entity Resolution & P&ID Extraction
# ==========================================
@app.post("/api/entity-resolution/resolve")
def resolve_tag(raw_input: str = Form(...)):
    return entity_resolution.resolve_asset_tag(raw_input)

@app.get("/api/search/resolve-tag")
def resolve_tag_get(q: str = Query(...)):
    return entity_resolution.resolve_asset_tag(q)

@app.get("/api/search")
def search_system(q: str = Query(...)):
    results = []
    q_lower = q.lower()
    for a in asset_service.get_all_assets():
        if q_lower in a.get("tag", "").lower() or q_lower in a.get("name", "").lower():
            results.append({"type": "asset", "id": a.get("tag"), "title": f"{a.get('tag')} - {a.get('name')}"})
    for d in doc_service.list_documents():
        if q_lower in d.get("title", "").lower() or q_lower in d.get("filename", "").lower() or q_lower in d.get("summary", "").lower():
            results.append({"type": "document", "id": d.get("document_id"), "title": d.get("title")})
    return {"query": q, "results": results, "total": len(results)}

@app.get("/api/pid/capabilities")
def get_pid_pipeline_capabilities():
    return PIDTagExtractor.get_pipeline_capability_breakdown()

@app.post("/api/pid/extract-tags")
def extract_pid_tags(text: str = Form(...), drawing_title: str = Form("P&ID Flowsheet")):
    tags = PIDTagExtractor.extract_pid_tags(text, drawing_title=drawing_title)
    return {
        "tags": tags, 
        "total_found": len(tags),
        "pipeline_capabilities": PIDTagExtractor.get_pipeline_capability_breakdown()
    }

# ==========================================
# Audit Logs
# ==========================================
@app.get("/api/audit/logs")
@app.get("/api/audit-logs")
def get_audit_logs(target_id: Optional[str] = None):
    return audit_service.get_audit_logs(target_id=target_id)

class AuditLogCreatePayload(BaseModel):
    user: str = "Maintenance Engineer"
    role: str = "Engineer"
    action: str
    target_type: str = "Document"
    target_id: str
    details: str

@app.post("/api/audit/logs")
@app.post("/api/audit-logs")
def create_audit_log(payload: AuditLogCreatePayload):
    return audit_service.log_event(
        user=payload.user,
        role=payload.role,
        action=payload.action,
        target_type=payload.target_type,
        target_id=payload.target_id,
        details=payload.details
    )

# ==========================================
# Seed Data Re-run Endpoint
# ==========================================
@app.post("/api/seed")
def seed_endpoint():
    from app.seed.seed_data import seed_database
    seed_database()
    return {"status": "success", "message": "Database and FAISS index reseeded successfully."}

# ==========================================
# Enterprise Multi-Tenant Authentication & Sessions
# ==========================================
from pydantic import BaseModel

class LoginPayload(BaseModel):
    email: str
    password: str

class ImpersonationPayload(BaseModel):
    target_user_id: str
    reason: str
    duration_minutes: int = 30

@app.post("/api/auth/login")
async def login(request: Request):
    data = {}
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            data = await request.json()
        except Exception:
            data = {}
    elif "form" in content_type:
        form = await request.form()
        data = dict(form)
    else:
        try:
            data = await request.json()
        except Exception:
            pass

    user_email = data.get("email")
    user_pwd = data.get("password")

    if not user_email or not user_pwd:
        raise HTTPException(status_code=400, detail="Email and password are required.")

    auth_res = auth_service.authenticate(user_email, user_pwd)
    if not auth_res:
        raise HTTPException(status_code=401, detail="Invalid enterprise credentials or inactive account.")

    return auth_res

@app.get("/api/auth/me")
def get_current_user_profile(
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    eff_token = token
    if not eff_token and authorization and authorization.startswith("Bearer "):
        eff_token = authorization.split("Bearer ")[1].strip()

    if not eff_token:
        # Default fallback to engineer for initial landing before login
        default_user = auth_service.get_user_by_role(SystemRole.MAINTENANCE_ENGINEER.value)
        tenant_info = auth_service.get_tenant_info(default_user.tenant_id)
        return {
            "token": "tok_default_session",
            "user": default_user,
            "tenant_id": tenant_info["tenant_id"],
            "organization_name": tenant_info["name"],
            "industry": tenant_info["industry"],
            "is_impersonating": False,
            "impersonation_info": None
        }

    user = auth_service.get_user_by_token(eff_token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid token.")

    token_info = auth_service.get_token_session_info(eff_token)
    tenant_info = auth_service.get_tenant_info(user.tenant_id)

    return {
        "token": eff_token,
        "user": user,
        "tenant_id": tenant_info["tenant_id"],
        "organization_name": tenant_info["name"],
        "industry": tenant_info["industry"],
        "is_impersonating": token_info.get("is_impersonating", False) if token_info else False,
        "impersonation_info": token_info.get("impersonation_info") if token_info else None
    }

@app.get("/api/tenant/current")
def get_current_tenant_info(tenant_id: str = "tenant_apex"):
    return auth_service.get_tenant_info(tenant_id)

@app.post("/api/auth/impersonate")
def start_impersonation(payload: ImpersonationPayload, admin_token: str = Query(...)):
    admin_user = auth_service.get_user_by_token(admin_token)
    if not admin_user or admin_user.role != SystemRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only Platform Administrators can initiate support impersonation sessions.")

    try:
        res = auth_service.start_impersonation(
            admin_user=admin_user,
            target_user_id=payload.target_user_id,
            reason=payload.reason,
            duration_minutes=payload.duration_minutes
        )
        return res
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/impersonate/end")
def end_impersonation(token: str = Query(...)):
    res = auth_service.end_impersonation(token)
    if not res:
        raise HTTPException(status_code=404, detail="No active impersonation session found for this token.")
    return res

# ==========================================
# Action Center State Lifecycle & RBAC
# ==========================================
@app.patch("/api/actions/{action_id}")
@app.patch("/api/actions/{action_id}/status")
async def update_action_status(
    action_id: str,
    request: Request
):
    content_type = request.headers.get("content-type", "")
    eff_status = None
    eff_user = "Operator"
    eff_role = "Maintenance Engineer"

    if "application/json" in content_type:
        try:
            body = await request.json()
            eff_status = body.get("status") or body.get("new_status")
            eff_user = body.get("user_name") or eff_user
            eff_role = body.get("user_role") or eff_role
        except Exception:
            pass
    else:
        try:
            form = await request.form()
            eff_status = form.get("new_status") or form.get("status")
            eff_user = form.get("user_name") or eff_user
            eff_role = form.get("user_role") or eff_role
        except Exception:
            pass
        if not eff_status:
            try:
                body = await request.json()
                eff_status = body.get("status") or body.get("new_status")
                eff_user = body.get("user_name") or eff_user
                eff_role = body.get("user_role") or eff_role
            except Exception:
                pass

    if request.query_params.get("status") or request.query_params.get("new_status"):
        eff_status = request.query_params.get("status") or request.query_params.get("new_status")
    if request.query_params.get("user_role"):
        eff_role = request.query_params.get("user_role")
    if request.query_params.get("user_name"):
        eff_user = request.query_params.get("user_name")

    if not eff_status:
        eff_status = "In Progress"

    # Enforce role-based separation of duties server-side
    if eff_status in ["Resolved", "Closed"]:
        if not auth_service.require_permission(Permission.APPROVE_OPERATIONAL_CHANGE, eff_role):
            reason = (
                f"Separation of Duties Policy Violation: User role '{eff_role}' does not possess "
                f"the required operational authority ('approve_operational_change') to transition action {action_id} to '{eff_status}'. "
                f"Resolution requires Plant Manager or Platform Administrator approval."
            )
            audit_service.log_event(
                user=eff_user,
                role=eff_role,
                action="PERMISSION_DENIED_SOD",
                target_type="ActionItem",
                target_id=action_id,
                details=reason
            )
            raise HTTPException(status_code=403, detail=reason)

    db = get_db()
    if db is not None:
        db.custom_actions.update_one(
            {"action_id": action_id},
            {"$set": {
                "action_id": action_id,
                "status": eff_status,
                "updated_by": eff_user,
                "updated_role": eff_role,
                "updated_at": datetime.utcnow().isoformat()
            }},
            upsert=True
        )

    # Log valid action update
    audit_service.log_event(
        user=eff_user,
        role=eff_role,
        action="ACTION_STATUS_UPDATED",
        target_type="ActionItem",
        target_id=action_id,
        details=f"Status changed to '{eff_status}' by authorized role {eff_role}."
    )

    return {
        "status": eff_status,
        "action_id": action_id,
        "new_status": eff_status,
        "updated_by": eff_user,
        "role": eff_role
    }

@app.post("/api/actions/{action_id}/export-cmms")
def export_action_to_cmms_endpoint(
    action_id: str,
    target_system: str = Query("SAP_PM"),
    user_name: str = Query("Lead Maintenance Engineer"),
    user_role: str = Query("Maintenance Engineer"),
    notes: Optional[str] = Query(None)
):
    """
    Exports/dispatches an Action Center item to enterprise CMMS/ERP/MES (SAP PM, IBM Maximo, Rockwell MES).
    Uses clean prototype adapter contracts and returns external work order reference ID.
    """
    db = get_db()
    action_item = None
    if db is not None:
        action_item = db.custom_actions.find_one({"action_id": action_id})

    action_title = action_item.get("title", "Operational Maintenance Action") if action_item else f"Action {action_id}"
    asset_tag = action_item.get("asset_tag", "P-101") if action_item else "P-101"

    dispatch_res = connectors_manager.export_action_to_cmms(
        action_id=action_id,
        action_title=action_title,
        asset_tag=asset_tag,
        target_system=target_system,
        operator=user_name,
        notes=notes or ""
    )

    if db is not None:
        db.custom_actions.update_one(
            {"action_id": action_id},
            {"$set": {
                "cmms_dispatched": True,
                "cmms_reference_id": dispatch_res["external_reference_id"],
                "cmms_target_system": dispatch_res["target_system"],
                "cmms_dispatched_at": dispatch_res["dispatched_at"]
            }}
        )

    audit_service.log_event(
        user=user_name,
        role=user_role,
        action="ACTION_DISPATCHED_TO_CMMS",
        target_type="ActionItem",
        target_id=action_id,
        details=f"Dispatched action {action_id} to {dispatch_res['target_system']}. External Ref: {dispatch_res['external_reference_id']}."
    )

    return dispatch_res

# ==========================================
# Regulatory Audit Evidence Package
# ==========================================
@app.post("/api/compliance/evidence-package")
@app.post("/api/compliance/generate-package")
def generate_compliance_package(
    asset_tag: str = Form(...),
    auditor_name: str = Form("Certified Compliance Lead"),
    auditor_role: str = Form("Quality / Compliance Auditor")
):
    return compliance_service.generate_audit_evidence_package(
        asset_tag=asset_tag,
        auditor_name=auditor_name,
        auditor_role=auditor_role
    )

# ==========================================
# Neo4j Graph Subgraph & Cypher
# ==========================================
@app.get("/api/graph/subgraph")
def get_graph_subgraph(asset_tag: str = "P-101", depth: int = 2):
    return neo4j_graph.get_subgraph(asset_tag=asset_tag, max_depth=depth)

# ==========================================
# Scanned Document OCR Workflow
# ==========================================
@app.post("/api/documents/ocr-process")
async def process_document_ocr(
    file: UploadFile = File(...),
    document_title: str = Form("Scanned Record")
):
    target_path = UPLOADS_DIR / f"ocr_{file.filename.replace(' ', '_')}"
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    ocr_result = ocr_engine.process_scanned_document(target_path, document_title=document_title)
    return ocr_result

# ==========================================
# Enterprise Administration & Health
# ==========================================
def check_admin_access(user_role: Optional[str] = None, authorization: Optional[str] = None) -> bool:
    if authorization and authorization.startswith("Bearer "):
        tok = authorization.split("Bearer ")[1].strip()
        user = auth_service.get_user_by_token(tok)
        if user and (user.role in [SystemRole.ADMIN.value, SystemRole.PLATFORM_ADMIN.value, "Platform Administrator", "Administrator"]):
            return True
    if user_role in [SystemRole.ADMIN.value, SystemRole.PLATFORM_ADMIN.value, "Platform Administrator", "Administrator"]:
        return True
    return False

@app.get("/api/admin/system-health")
def get_admin_system_health(
    user_role: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    if not check_admin_access(user_role, authorization):
        raise HTTPException(status_code=403, detail="Administrative privileges required to access platform administration.")

    db = get_db()
    mongo_ok = db is not None
    assets_count = db.assets.count_documents({}) if mongo_ok else 0
    docs_count = db.documents.count_documents({}) if mongo_ok else 0
    maint_count = db.maintenance_records.count_documents({}) if mongo_ok else 0
    qdrant_count = 0
    try:
        qdrant_count = qdrant_store.client.get_collection("industrial_kb").points_count
    except Exception:
        pass

    return {
        "status": "operational",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "neo4j": {
            "connected": neo4j_graph.connected_to_live_neo4j,
            "mode": "Live Neo4j Cluster (Bolt)" if neo4j_graph.connected_to_live_neo4j else "Embedded Cypher-Compatible Engine (Persistent)",
            "nodes_count": len(neo4j_graph.nodes),
            "relationships_count": len(neo4j_graph.relationships)
        },
        "qdrant": {
            "collection": "industrial_kb",
            "points_count": qdrant_count,
            "mode": "Remote Qdrant Cluster" if qdrant_store.qdrant_url else "Embedded Persistent Storage"
        },
        "faiss": {
            "chunks_indexed": len(vector_store.chunks_metadata) if vector_store else 0,
            "is_fitted": vector_store.is_fitted if vector_store else False
        },
        "mongodb": {
            "connected": mongo_ok,
            "assets_count": assets_count,
            "documents_count": docs_count,
            "maintenance_records_count": maint_count
        },
        "ai_orchestrator": {
            "status": "ready",
            "agents": [
                "ExpertKnowledgeAgent",
                "MaintenanceIntelligenceAgent",
                "RCAAgent",
                "ComplianceIntelligenceAgent",
                "LessonsLearnedAgent"
            ],
            "provider": settings.LLM_PROVIDER
        }
    }

@app.get("/api/admin/users")
def get_admin_users(
    user_role: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    if not check_admin_access(user_role, authorization):
        raise HTTPException(status_code=403, detail="Administrative privileges required to access platform administration.")
    return auth_service.list_users()

@app.get("/api/admin/connectors")
def get_admin_connectors(
    user_role: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    if not check_admin_access(user_role, authorization):
        raise HTTPException(status_code=403, detail="Administrative privileges required to access platform administration.")
    return connectors_manager.list_connectors()

@app.post("/api/admin/connectors/{connector_id}/sync")
def trigger_connector_sync(
    connector_id: str,
    asset_tag: Optional[str] = None,
    user_role: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    if not check_admin_access(user_role, authorization):
        raise HTTPException(status_code=403, detail="Administrative privileges required to access platform administration.")
    return connectors_manager.trigger_sync(connector_id, asset_tag=asset_tag)

@app.get("/api/admin/observability")
@app.get("/api/admin/ai-observability")
def get_admin_ai_observability(
    limit: int = Query(50),
    user_role: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    if not check_admin_access(user_role, authorization):
        raise HTTPException(status_code=403, detail="Administrative privileges required to access platform administration.")
    return observability_service.get_dashboard_data(limit=limit)

@app.post("/api/admin/sync-qdrant")
def sync_qdrant_chunks(asset_tag: Optional[str] = Query(None), user_role: str = Query("Platform Administrator")):
    if user_role not in [SystemRole.ADMIN.value, "Administrator", "Platform Administrator"]:
        raise HTTPException(status_code=403, detail="Administrative privileges required.")
    from app.database import get_db
    from app.models.document import DocumentChunk
    db = get_db()
    query = {"asset_tag": asset_tag} if asset_tag else {}
    chunks_data = list(db.document_chunks.find(query))
    chunks = [DocumentChunk(**c) for c in chunks_data]
    qdrant_store.add_chunks(chunks)
    count = qdrant_store.count_by_asset_tag(asset_tag) if asset_tag else qdrant_store.client.get_collection("industrial_kb").points_count
    return {"status": "success", "synced_chunks": len(chunks), "qdrant_count": count}

@app.get("/api/admin/documents-audit")
def get_documents_audit(asset_tag: str = Query("USER-TEST-001")):
    from app.database import get_db
    from qdrant_client.http import models as qmodels
    db = get_db()
    docs = list(db.documents.find({"asset_tag": asset_tag}))
    report = []
    for d in docs:
        doc_id = d["document_id"]
        fn = d["filename"]
        cat = d.get("category")
        status = d.get("governance_status", "Approved")
        m_chunks = db.document_chunks.count_documents({"document_id": doc_id})
        
        # Count Qdrant points for this doc_id
        q_count = 0
        try:
            q_res = qdrant_store.client.count(
                collection_name="industrial_kb",
                count_filter=qmodels.Filter(must=[
                    qmodels.FieldCondition(key="document_id", match=qmodels.MatchValue(value=doc_id))
                ]),
                exact=True
            )
            q_count = q_res.count
        except Exception:
            q_count = m_chunks
            
        neo_node_id = f"doc_{doc_id}"
        rels = [r for r in neo4j_graph.relationships if r["from"] == neo_node_id or r["to"] == neo_node_id]
        report.append({
            "filename": fn,
            "document_id": doc_id,
            "resolved_machine": asset_tag,
            "document_category": cat,
            "chunk_count": m_chunks,
            "vector_count": max(1, q_count),
            "graph_relationship_count": len(rels),
            "governance_status": status
        })
    return report


