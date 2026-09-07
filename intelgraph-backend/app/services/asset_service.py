from typing import List, Dict, Any, Optional
from app.database import get_db
from app.models.asset import Asset, AssetCreate, CompletenessItem, Component

class AssetService:
    @staticmethod
    def calculate_completeness(asset_tag: str) -> tuple[int, List[CompletenessItem]]:
        db = get_db()
        if db is None:
            return (0, [])

        docs = list(db.documents.find({"asset_tag": asset_tag, "governance_status": {"$ne": "Obsolete"}}))
        categories = set(d.get("category") for d in docs)
        
        maint_count = db.maintenance_records.count_documents({"asset_tag": asset_tag})
        insp_count = db.inspection_records.count_documents({"asset_tag": asset_tag})
        fail_count = db.failures.count_documents({"asset_tag": asset_tag})
        
        items = [
            CompletenessItem(
                category="OEM Manual",
                label="Original Equipment Manufacturer Manual",
                status="completed" if "OEM Manual" in categories else "missing",
                details="Defines operating clearances, lubrication specs, and torque limits."
            ),
            CompletenessItem(
                category="SOP",
                label="Standard Operating Procedure (SOP)",
                status="completed" if "SOP" in categories else "missing",
                details="Step-by-step startup, operation, and shutdown protocol."
            ),
            CompletenessItem(
                category="Maintenance",
                label="Historical Work Orders & Service Logs",
                status="completed" if maint_count > 0 else "missing",
                details=f"{maint_count} maintenance records registered."
            ),
            CompletenessItem(
                category="Inspection",
                label="Condition Monitoring & Vibration Records",
                status="completed" if insp_count > 0 else "missing",
                details=f"{insp_count} inspection logs on file."
            ),
            CompletenessItem(
                category="Failure History",
                label="Root Cause & Incident Reports",
                status="completed" if fail_count > 0 else "missing",
                details=f"{fail_count} failure/incident reports captured."
            ),
            CompletenessItem(
                category="Safety",
                label="LOTO & Safety Precautions",
                status="completed" if "Safety" in categories else "missing",
                details="Lockout/tagout and hazard isolation procedures."
            ),
            CompletenessItem(
                category="Calibration",
                label="Instrumentation Calibration Record",
                status="completed" if "Calibration" in categories else "warning",
                details="Pressure transmitter & sensor calibration certificate."
            )
        ]

        completed_weights = {
            "OEM Manual": 20,
            "SOP": 20,
            "Maintenance": 15,
            "Inspection": 15,
            "Failure History": 12,
            "Safety": 10,
            "Calibration": 8
        }

        total_score = sum(
            completed_weights[item.category] for item in items if item.status == "completed"
        )
        return (min(total_score, 100), items)

    @staticmethod
    def get_all_assets() -> List[Dict[str, Any]]:
        db = get_db()
        if db is None:
            return []
        
        assets_cursor = db.assets.find({})
        result = []
        for a in assets_cursor:
            a["_id"] = str(a.get("_id", ""))
            score, breakdown = AssetService.calculate_completeness(a["tag"])
            a["completeness_score"] = score
            a["completeness_breakdown"] = [b.model_dump() for b in breakdown]
            a["document_count"] = db.documents.count_documents({"asset_tag": a["tag"]})
            a["open_findings_count"] = db.findings.count_documents({"asset_tag": a["tag"], "status": "Open"})
            result.append(a)
        return result

    @staticmethod
    def get_asset(tag: str) -> Optional[Dict[str, Any]]:
        db = get_db()
        if db is None:
            return None
        
        asset = db.assets.find_one({"tag": tag.upper()})
        if not asset:
            return None
        
        asset["_id"] = str(asset.get("_id", ""))
        score, breakdown = AssetService.calculate_completeness(asset["tag"])
        asset["completeness_score"] = score
        asset["completeness_breakdown"] = [b.model_dump() for b in breakdown]
        asset["document_count"] = db.documents.count_documents({"asset_tag": asset["tag"]})
        asset["open_findings_count"] = db.findings.count_documents({"asset_tag": asset["tag"], "status": "Open"})
        return asset

    @staticmethod
    def create_asset(data: AssetCreate) -> Dict[str, Any]:
        db = get_db()
        if db is None:
            return {}

        asset_dict = data.model_dump()
        asset_dict["tag"] = asset_dict["tag"].upper().strip()
        asset_dict["completeness_score"] = 15  # Day-1 baseline for new machine
        
        db.assets.update_one({"tag": asset_dict["tag"]}, {"$set": asset_dict}, upsert=True)
        return AssetService.get_asset(asset_dict["tag"])

    @staticmethod
    def get_hierarchy() -> Dict[str, Any]:
        assets = AssetService.get_all_assets()
        hierarchy = {}

        for a in assets:
            org = a.get("organization", "Apex Industrial Energy")
            sec = a.get("sector", "Energy & Chemicals")
            plt = a.get("plant", "Plant A - Gulf Coast")
            ara = a.get("area", "Unit 2 - Fluid Processing")
            tag = a["tag"]

            if org not in hierarchy:
                hierarchy[org] = {}
            if sec not in hierarchy[org]:
                hierarchy[org][sec] = {}
            if plt not in hierarchy[org][sec]:
                hierarchy[org][sec][plt] = {}
            if ara not in hierarchy[org][sec][plt]:
                hierarchy[org][sec][plt][ara] = []
            
            hierarchy[org][sec][plt][ara].append({
                "tag": tag,
                "name": a.get("name"),
                "status": a.get("status"),
                "completeness_score": a.get("completeness_score")
            })
        return hierarchy

asset_service = AssetService()
