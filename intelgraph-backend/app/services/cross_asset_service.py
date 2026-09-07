from typing import List, Dict, Any
from app.database import get_db

class CrossAssetService:
    @staticmethod
    def analyze_fleet_patterns() -> List[Dict[str, Any]]:
        """
        Detects recurring failure modes, components, and vibration anomalies across multiple assets.
        """
        db = get_db()
        if db is None:
            return []

        failures = list(db.failures.find({}))
        inspections = list(db.inspection_records.find({"result": {"$in": ["Warning", "Failed"]}}))
        work_orders = list(db.maintenance_records.find({}))

        # Component failure grouping
        comp_map: Dict[str, List[Dict[str, Any]]] = {}
        for f in failures:
            comp = f.get("component", "General").title()
            if comp not in comp_map:
                comp_map[comp] = []
            comp_map[comp].append({
                "asset_tag": f["asset_tag"],
                "date": f.get("date"),
                "event": f.get("failure_mode"),
                "severity": f.get("severity")
            })

        for insp in inspections:
            if "vibration" in insp.get("observations", "").lower() or insp.get("vibration_level_mm_s", 0) > 4.5:
                comp = "Bearing / Vibration"
                if comp not in comp_map:
                    comp_map[comp] = []
                comp_map[comp].append({
                    "asset_tag": insp["asset_tag"],
                    "date": insp.get("date"),
                    "event": f"High vibration recorded ({insp.get('vibration_level_mm_s')} mm/s)",
                    "severity": "Warning"
                })

        cross_patterns = []
        for comp, records in comp_map.items():
            affected_assets = list(set(r["asset_tag"] for r in records))
            if len(affected_assets) >= 2 or len(records) >= 3:
                cross_patterns.append({
                    "pattern_title": f"Fleet-Wide {comp} Anomaly",
                    "affected_assets": affected_assets,
                    "incident_count": len(records),
                    "summary": (
                        f"Similar {comp.lower()} events detected across assets "
                        f"{', '.join(affected_assets)}. Historical evidence correlates lubrication breakdown "
                        f"and vibration threshold exceedances."
                    ),
                    "supporting_evidence": records,
                    "recommended_action": "Conduct fleet-wide alignment and lubricant verification per OEM standards."
                })

        return cross_patterns

cross_asset_service = CrossAssetService()
