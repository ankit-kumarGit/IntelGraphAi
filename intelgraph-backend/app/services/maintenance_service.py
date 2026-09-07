from typing import List, Dict, Any, Optional
from app.database import get_db
from app.models.maintenance import MaintenanceRecord, InspectionRecord, FailureRecord, Finding, TelemetryPoint

class MaintenanceService:
    @staticmethod
    def get_asset_maintenance(asset_tag: str) -> Dict[str, Any]:
        db = get_db()
        if db is None:
            return {"work_orders": [], "inspections": [], "failures": [], "findings": [], "recurring_patterns": []}

        tag = asset_tag.upper()
        work_orders = list(db.maintenance_records.find({"asset_tag": tag}).sort("date", -1))
        inspections = list(db.inspection_records.find({"asset_tag": tag}).sort("date", -1))
        failures = list(db.failures.find({"asset_tag": tag}).sort("date", -1))
        findings = list(db.findings.find({"asset_tag": tag}))

        for itm in work_orders + inspections + failures + findings:
            itm["_id"] = str(itm.get("_id", ""))

        # Detect recurring patterns
        replaced_counts = {}
        for wo in work_orders:
            for c in wo.get("components_replaced", []):
                clean_c = c.strip().title()
                replaced_counts[clean_c] = replaced_counts.get(clean_c, 0) + 1

        recurring = []
        for comp, count in replaced_counts.items():
            if count >= 2:
                recurring.append({
                    "component": comp,
                    "occurrences": count,
                    "pattern": f"Recurring {comp} replacement recorded ({count} times)",
                    "severity": "High" if "Bearing" in comp else "Medium",
                    "observation": f"Historical work orders show multiple interventions on {comp}. Review lubrication and alignment procedures."
                })

        return {
            "asset_tag": tag,
            "work_orders": work_orders,
            "inspections": inspections,
            "failures": failures,
            "findings": findings,
            "recurring_patterns": recurring,
            "last_maintenance": work_orders[0] if work_orders else None
        }

    @staticmethod
    def get_telemetry(asset_tag: str) -> Dict[str, Any]:
        db = get_db()
        if db is None:
            return {"points": [], "is_synthetic": True}

        points = list(db.telemetry.find({"asset_tag": asset_tag.upper()}).sort("timestamp", 1))
        for p in points:
            p["_id"] = str(p.get("_id", ""))

        return {
            "asset_tag": asset_tag.upper(),
            "points": points,
            "is_synthetic": True,
            "disclaimer": "Demo / Synthetic Data for operational condition monitoring simulation."
        }

    @staticmethod
    def add_maintenance_record(rec: MaintenanceRecord) -> Dict[str, Any]:
        db = get_db()
        if db is not None:
            db.maintenance_records.update_one(
                {"record_id": rec.record_id},
                {"$set": rec.model_dump()},
                upsert=True
            )
        return rec.model_dump()

    @staticmethod
    def add_inspection_record(rec: InspectionRecord) -> Dict[str, Any]:
        db = get_db()
        if db is not None:
            db.inspection_records.update_one(
                {"inspection_id": rec.inspection_id},
                {"$set": rec.model_dump()},
                upsert=True
            )
        return rec.model_dump()

maintenance_service = MaintenanceService()
