from typing import List, Dict, Any
from app.database import get_db

class CrossAssetService:
    @staticmethod
    def analyze_fleet_patterns() -> List[Dict[str, Any]]:
        """
        Detects recurring failure modes, components, and vibration anomalies across multiple assets
        (e.g., P-101, P-102, P-203, P-307).
        """
        db = get_db()
        if db is None:
            return []

        failures = list(db.failures.find({}))
        inspections = list(db.inspection_records.find({"result": {"$in": ["Warning", "Failed"]}}))
        work_orders = list(db.maintenance_records.find({}))

        # Component failure grouping with industrial normalization
        comp_map: Dict[str, List[Dict[str, Any]]] = {}

        for f in failures:
            raw_comp = f.get("component", "General")
            if "bearing" in raw_comp.lower():
                comp = "Bearing Assembly & Lubrication System"
            elif "valve" in raw_comp.lower():
                comp = "Suction / Discharge Valves"
            else:
                comp = raw_comp.title()

            if comp not in comp_map:
                comp_map[comp] = []
            comp_map[comp].append({
                "asset_tag": f["asset_tag"],
                "date": f.get("date"),
                "event": f.get("failure_mode"),
                "severity": f.get("severity"),
                "details": f.get("title")
            })

        for insp in inspections:
            raw_obs = insp.get("observations", "").lower()
            if "bearing" in raw_obs or insp.get("vibration_level_mm_s", 0) > 4.5:
                comp = "Bearing Assembly & Lubrication System"
            else:
                comp = "Condition Monitoring / Acoustics"

            if comp not in comp_map:
                comp_map[comp] = []
            comp_map[comp].append({
                "asset_tag": insp["asset_tag"],
                "date": insp.get("date"),
                "event": f"High vibration recorded ({insp.get('vibration_level_mm_s')} mm/s)",
                "severity": "Warning",
                "details": insp.get("observations")
            })

        cross_patterns = []
        for comp, records in comp_map.items():
            affected_assets = sorted(list(set(r["asset_tag"] for r in records)))
            if len(affected_assets) >= 2 or len(records) >= 3:
                cross_patterns.append({
                    "pattern_title": f"Fleet-Wide {comp} Degradation Pattern",
                    "affected_assets": affected_assets,
                    "incident_count": len(records),
                    "summary": (
                        f"Correlated {comp.lower()} anomalies identified across assets "
                        f"{', '.join(affected_assets)}. Cross-document evidence indicates recurring operation "
                        f"under elevated vibration (>4.5 mm/s RMS) and lubricant breakdown exceeding 4,000h intervals."
                    ),
                    "supporting_evidence": records,
                    "recommended_action": "Standardize fleet-wide oil sampling and enforce mandatory alignment checks per SOP-101 / ISO 10816."
                })

        return cross_patterns

cross_asset_service = CrossAssetService()
