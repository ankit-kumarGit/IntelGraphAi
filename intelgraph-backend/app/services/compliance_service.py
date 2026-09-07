from typing import List, Dict, Any
import time
from app.database import get_db
from app.models.compliance import ComplianceRequirement, ComplianceAuditItem

class ComplianceService:
    @staticmethod
    def audit_asset_compliance(asset_tag: str) -> List[Dict[str, Any]]:
        db = get_db()
        if db is None:
            return []

        tag = asset_tag.upper()
        asset = db.assets.find_one({"tag": tag})
        if not asset:
            return []

        asset_type = asset.get("asset_type", "Centrifugal Pump")
        docs = list(db.documents.find({"asset_tag": tag, "governance_status": "Approved"}))
        inspections = list(db.inspection_records.find({"asset_tag": tag}))
        doc_categories = set(d.get("category") for d in docs)

        requirements = list(db.compliance_requirements.find({
            "$or": [
                {"target_asset_types": asset_type},
                {"target_asset_types": "All"}
            ]
        }))

        audit_items = []
        for req in requirements:
            req_id = req["req_id"]
            title = req["title"]
            body = req.get("regulatory_body", "Industry Standard")
            req_type = req.get("requirement_type", "Inspection")
            required_ev = req.get("required_evidence_type", "Report")

            status = "Missing Evidence"
            available_ev = None
            ev_doc_id = None

            if req_type == "Inspection":
                if inspections:
                    latest_insp = inspections[0]
                    status = "Compliant"
                    available_ev = f"{latest_insp.get('inspection_id')} ({latest_insp.get('date')}): {latest_insp.get('result')}"
                    ev_doc_id = latest_insp.get("document_ref")
            elif req_type == "Safety LOTO":
                safety_docs = [d for d in docs if d.get("category") in ["Safety", "SOP"]]
                if safety_docs:
                    status = "Compliant"
                    available_ev = f"{safety_docs[0].get('title')} ({safety_docs[0].get('version')})"
                    ev_doc_id = safety_docs[0].get("document_id")
            elif req_type == "Overhaul SOP":
                sop_docs = [d for d in docs if d.get("category") == "SOP"]
                if sop_docs:
                    status = "Compliant"
                    available_ev = f"{sop_docs[0].get('title')} ({sop_docs[0].get('version')})"
                    ev_doc_id = sop_docs[0].get("document_id")
            elif req_type == "Calibration":
                calib_docs = [d for d in docs if d.get("category") == "Calibration"]
                if calib_docs:
                    status = "Compliant"
                    available_ev = calib_docs[0].get("title")
                    ev_doc_id = calib_docs[0].get("document_id")
                else:
                    status = "Missing Evidence"
                    available_ev = "No active calibration certificate on record for pressure transmitter."

            audit_item = ComplianceAuditItem(
                audit_id=f"audit_{tag}_{req_id}",
                asset_tag=tag,
                requirement_id=req_id,
                requirement_title=title,
                regulatory_body=body,
                required_evidence=required_ev,
                available_evidence=available_ev,
                evidence_document_id=ev_doc_id,
                status=status,
                last_evaluated=time.strftime("%Y-%m-%d")
            )
            audit_items.append(audit_item.model_dump())

        return audit_items

    @staticmethod
    def get_fleet_compliance_summary() -> Dict[str, Any]:
        db = get_db()
        if db is None:
            return {"compliant": 0, "missing_evidence": 0, "total": 0, "compliance_rate_pct": 0.0}

        assets = list(db.assets.find({}))
        total_items = 0
        compliant_items = 0
        gaps = []

        for a in assets:
            items = ComplianceService.audit_asset_compliance(a["tag"])
            for itm in items:
                total_items += 1
                if itm["status"] == "Compliant":
                    compliant_items += 1
                else:
                    gaps.append({
                        "asset_tag": a["tag"],
                        "requirement": itm["requirement_title"],
                        "regulatory_body": itm["regulatory_body"],
                        "details": itm["available_evidence"]
                    })

        rate = round((compliant_items / total_items * 100), 1) if total_items > 0 else 0.0
        return {
            "compliant": compliant_items,
            "missing_evidence": total_items - compliant_items,
            "total": total_items,
            "compliance_rate_pct": rate,
            "gaps": gaps
        }

compliance_service = ComplianceService()
