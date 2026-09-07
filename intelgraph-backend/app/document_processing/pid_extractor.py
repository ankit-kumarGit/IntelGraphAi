import re
from typing import List, Dict, Any

class PIDTagExtractor:
    PID_PATTERNS = [
        (r"\b(P-\d{3}[A-Z]?)\b", "Pump"),
        (r"\b(C-\d{3}[A-Z]?)\b", "Compressor"),
        (r"\b(M-\d{3}[A-Z]?)\b", "Motor"),
        (r"\b(T-\d{3}[A-Z]?)\b", "Tank / Vessel"),
        (r"\b(V-\d{3}[A-Z]?)\b", "Control Valve"),
        (r"\b(PT-\d{3}[A-Z]?)\b", "Pressure Transmitter"),
        (r"\b(TT-\d{3}[A-Z]?)\b", "Temperature Transmitter"),
        (r"\b(FT-\d{3}[A-Z]?)\b", "Flow Transmitter"),
        (r"\b(PSV-\d{3}[A-Z]?)\b", "Pressure Safety Valve")
    ]

    @classmethod
    def extract_pid_tags(cls, text: str, drawing_title: str = "P&ID Drawing") -> List[Dict[str, Any]]:
        extracted = []
        lines = text.split("\n")
        seen_tags = set()

        for line_idx, line in enumerate(lines):
            for pattern, tag_type in cls.PID_PATTERNS:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for m in matches:
                    raw_tag = m.group(1).upper()
                    if raw_tag not in seen_tags:
                        seen_tags.add(raw_tag)
                        # Estimate grid coordinates based on line index and match offset
                        col = m.start()
                        grid_x = f"Grid-{chr(65 + (col % 6))}"
                        grid_y = f"Zone-{(line_idx % 8) + 1}"
                        extracted.append({
                            "tag": raw_tag,
                            "type": tag_type,
                            "drawing": drawing_title,
                            "location_grid": f"{grid_x}/{grid_y}",
                            "line_number": line_idx + 1,
                            "context_snippet": line.strip()[:100],
                            "linked_asset_tag": raw_tag if tag_type in ["Pump", "Compressor", "Motor"] else None
                        })
        return extracted
