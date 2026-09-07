import re
from typing import Dict, Any, List

class EntityExtractor:
    TAG_PATTERNS = [
        r"\b([A-Z]{1,3}-\d{3,4})\b",
        r"\b(PUMP[-\s]?\d{3})\b",
        r"\b(COMPRESSOR[-\s]?\d{3})\b",
        r"\b(MOTOR[-\s]?\d{3})\b"
    ]
    WO_PATTERN = r"\b(WO[-\s]?\d{4}|Work\s+Order\s+#?\d{4}|INSP[-\s]?\d{3}|Inspection\s+#?\d{3})\b"
    DATE_PATTERNS = [
        r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b",
        r"\b(\d{4}-\d{2}-\d{2})\b",
        r"\b(\d{1,2}/\d{1,2}/\d{4})\b"
    ]
    KNOWN_COMPONENTS = [
        "Bearing", "Drive-End Bearing", "Non-Drive-End Bearing", "Impeller", 
        "Shaft", "Mechanical Seal", "Motor", "Coupling", "Casing", "Suction Valve", 
        "Discharge Valve", "Piston", "Rotor", "Stator", "Lubricant Reservoir"
    ]
    EVENT_KEYWORDS = {
        "Maintenance": ["maintenance", "repair", "overhaul", "replaced", "lubrication", "serviced", "work order"],
        "Inspection": ["inspection", "condition monitoring", "vibration analysis", "ultrasonic", "thermography", "calibrated"],
        "Failure": ["failure", "seizure", "trip", "alarm", "scored", "leakage", "breakdown", "shut down", "damage"],
        "Procedure": ["sop", "operating procedure", "pre-start", "safety requirement", "loto", "clearance limit"]
    }

    @classmethod
    def extract_entities(cls, text: str) -> Dict[str, Any]:
        """
        Extracts industrial entities from raw document text for human-in-the-loop review.
        """
        # Extract Asset Tag
        found_tags = []
        for pat in cls.TAG_PATTERNS:
            matches = re.findall(pat, text, re.IGNORECASE)
            for m in matches:
                normalized = m.upper().replace(" ", "-")
                if normalized not in found_tags:
                    found_tags.append(normalized)

        # Extract Work Order / Inspection ID
        found_wos = re.findall(cls.WO_PATTERN, text, re.IGNORECASE)
        clean_wos = list(set([w.strip().replace(" ", "-").upper() for w in found_wos]))

        # Extract Dates
        found_dates = []
        for pat in cls.DATE_PATTERNS:
            d_matches = re.findall(pat, text, re.IGNORECASE)
            for d in d_matches:
                if d not in found_dates:
                    found_dates.append(d)

        # Extract Components
        found_components = []
        for comp in cls.KNOWN_COMPONENTS:
            if re.search(r"\b" + re.escape(comp) + r"\b", text, re.IGNORECASE):
                found_components.append(comp)

        # Determine Event Category
        event_scores = {}
        for ev_type, keywords in cls.EVENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", text, re.IGNORECASE))
            event_scores[ev_type] = score
        
        detected_event = max(event_scores.items(), key=lambda x: x[1])
        event_type = detected_event[0] if detected_event[1] > 0 else "General Documentation"

        # Determine Confidence
        confidence = "High" if (found_tags and found_dates and found_components) else ("Medium" if (found_tags or found_components) else "Low")

        return {
            "asset_tags": found_tags,
            "primary_asset_tag": found_tags[0] if found_tags else "Unknown",
            "work_orders": clean_wos,
            "dates": found_dates,
            "primary_date": found_dates[0] if found_dates else "Unknown",
            "components": found_components,
            "primary_component": found_components[0] if found_components else "General Machine",
            "event_type": event_type,
            "confidence": confidence,
            "requires_human_confirmation": True
        }
