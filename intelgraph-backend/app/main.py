from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pathlib import Path
import shutil
import time

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
from app.rag.assistant import knowledge_assistant
from app.rag.vector_store import vector_store
from app.benchmark.runner import BenchmarkRunner
from app.document_processing.pid_extractor import PIDTagExtractor

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Unified Asset & Operations Brain - Industrial Knowledge Intelligence Platform",
    version="1.0.0"
)

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

# ==========================================
# System & Health
# ==========================================
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

@app.get("/api/assets")
def list_assets():
    return asset_service.get_all_assets()

@app.post("/api/assets")
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
def get_asset(tag: str):
    asset = asset_service.get_asset(tag)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@app.get("/api/assets/{tag}/knowledge-map")
def get_knowledge_map(tag: str):
    return knowledge_map_service.get_asset_knowledge_map(tag)

@app.get("/api/assets/{tag}/maintenance")
def get_asset_maintenance(tag: str):
    return maintenance_service.get_asset_maintenance(tag)

@app.get("/api/assets/{tag}/telemetry")
def get_asset_telemetry(tag: str):
    return maintenance_service.get_telemetry(tag)

@app.get("/api/assets/{tag}/compliance")
def get_asset_compliance(tag: str):
    return compliance_service.audit_asset_compliance(tag)

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
def add_asset_note(
    tag: str,
    text: str = Form(...),
    author: str = Form("Field Operator"),
    author_role: str = Form("Field Technician"),
    component: Optional[str] = Form(None)
):
    db = get_db()
    note_id = f"note_{int(time.time() * 1000)}"
    entry = {
        "note_id": note_id,
        "asset_tag": tag.upper(),
        "author": author,
        "author_role": author_role,
        "created_at": time.strftime("%Y-%m-%d %H:%M"),
        "text": text,
        "component": component,
        "verified": False,
        "verification_status": "Unverified Operator Note"
    }
    if db is not None:
        db.human_notes.insert_one(entry)
    
    audit_service.log_event(
        user=author,
        role=author_role,
        action="Note Added",
        target_type="Note",
        target_id=note_id,
        details=f"Added field observation for {tag.upper()}: {text[:60]}"
    )
    return entry

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

    return actions

# ==========================================
# Document Library & Processing
# ==========================================
@app.get("/api/documents")
def list_documents(
    asset_tag: Optional[str] = None,
    category: Optional[str] = None,
    governance_status: Optional[str] = None
):
    return doc_service.list_documents(asset_tag, category, governance_status)

@app.get("/api/documents/{doc_id}")
def get_document(doc_id: str):
    doc = doc_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@app.get("/api/documents/{doc_id}/chunks")
def get_document_chunks(doc_id: str):
    return doc_service.get_document_chunks(doc_id)

@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    asset_tag: str = Form(...),
    category: str = Form("Other"),
    version: str = Form("v1.0"),
    governance_status: str = Form("Approved"),
    uploaded_by: str = Form("Maintenance Engineer")
):
    safe_filename = file.filename.replace(" ", "_")
    target_path = UPLOADS_DIR / safe_filename
    
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process and chunk document
    doc_record = doc_service.process_and_save_document(
        file_path=target_path,
        filename=file.filename,
        asset_tag=asset_tag.upper(),
        category=category,
        version=version,
        governance_status=governance_status,
        uploaded_by=uploaded_by
    )

    audit_service.log_event(
        user=uploaded_by,
        role="Engineer",
        action="Document Ingested",
        target_type="Document",
        target_id=doc_record["document_id"],
        details=f"Uploaded {file.filename} for {asset_tag.upper()} ({category}, {version})"
    )

    return doc_record

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
def update_document_governance(
    doc_id: str,
    status: str = Form(...),
    version: Optional[str] = Form(None),
    updated_by: str = Form("Safety Officer")
):
    success = doc_service.update_governance_status(doc_id, status, version)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or status unchanged")
    
    audit_service.log_event(
        user=updated_by,
        role="Quality / Compliance",
        action="Governance Updated",
        target_type="Document",
        target_id=doc_id,
        details=f"Status set to {status}" + (f", version {version}" if version else "")
    )
    return {"status": "success", "document_id": doc_id, "governance_status": status}

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
def chat_with_assistant(req: ChatRequest):
    asset_ctx = asset_service.get_asset(req.asset_tag) if req.asset_tag else None
    return knowledge_assistant.answer_query(req, asset_context=asset_ctx)

# ==========================================
# Benchmark Suite Runner
# ==========================================
@app.get("/api/benchmarks/run", response_model=BenchmarkResult)
def run_benchmarks():
    return BenchmarkRunner.run_benchmark()

# ==========================================
# Entity Resolution & P&ID Extraction
# ==========================================
@app.post("/api/entity-resolution/resolve")
def resolve_tag(raw_input: str = Form(...)):
    return entity_resolution.resolve_asset_tag(raw_input)

@app.post("/api/pid/extract-tags")
def extract_pid_tags(text: str = Form(...), drawing_title: str = Form("P&ID Flowsheet")):
    tags = PIDTagExtractor.extract_pid_tags(text, drawing_title=drawing_title)
    return {"tags": tags, "total_found": len(tags)}

# ==========================================
# Audit Logs
# ==========================================
@app.get("/api/audit-logs")
def get_audit_logs(target_id: Optional[str] = None):
    return audit_service.get_audit_logs(target_id=target_id)

# ==========================================
# Seed Data Re-run Endpoint
# ==========================================
@app.post("/api/seed")
def seed_endpoint():
    from app.seed.seed_data import seed_database
    seed_database()
    return {"status": "success", "message": "Database and FAISS index reseeded successfully."}
