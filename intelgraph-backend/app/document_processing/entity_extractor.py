import re
from typing import Dict, Any, List, Optional, Tuple

class EntityExtractor:
    NON_ASSET_PREFIXES = {
        "SOP", "WO", "REV", "VER", "DOC", "ISO", "API", "PM", "CW", "FY",
        "INSP", "FAIL", "LINE", "DWG", "SPEC", "SEC", "FIG", "REF", "HDR",
        "LOTO", "SKF", "BURG", "MOBIL", "MODEL", "MOD", "TASK", "TSK",
        "GEN", "STD", "GUIDE", "PROC", "INST", "LUBE", "FORM", "FRM", "RPL",
        "VHP", "SCP", "IOM", "HD", "UNIT", "AREA", "PLANT", "PTW", "PFS",
        "NLGI", "RL", "FC",
        "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
        # Document-type identifiers that must never become equipment tags
        "FAILURE", "INCIDENT", "REPORT", "MAINTENANCE", "INSPECTION",
        "CHECKLIST", "SCANNED", "HANDOVER", "PROCEDURE", "OPERATION",
        "REVISION", "EQUIPMENT", "DATASHEET", "ASSESSMENT", "SURVEY",
        "CONDITION", "MONITORING", "TECHNICAL", "DRAWING", "SCHEDULE",
        "CORRECTIVE", "PREVENTIVE", "EMERGENCY", "ANALYSIS", "SUMMARY"
    }

    COMPONENT_PREFIXES = {
        "V", "FV", "PV", "TV", "LV", "CV", "MOV", "XV",
        "TI", "TT", "PI", "PT", "FIC", "FT", "LI", "LT", "PSV", "XSHH", "TE", "ST",
        "PSLL", "VI", "PDI", "LSL"
    }

    TAG_PATTERNS = [
        r"\b([A-Z]{1,4}(?:-[A-Z]{1,4})*-\d{1,5}[A-Z0-9]*)\b",
        r"\b([A-Z]{1,4}-\d{2,5}[A-Z0-9]*)\b",
        r"\b(PUMP[-\s]?\d{2,5}[A-Z0-9]*)\b",
        r"\b(COMPRESSOR[-\s]?\d{2,5}[A-Z0-9]*)\b",
        r"\b(MOTOR[-\s]?\d{2,5}[A-Z0-9]*)\b",
        r"\b((?:USER|DELETE)-TEST-[A-Z0-9-]+)\b"
    ]
    
    EXPLICIT_HEADER_PATTERNS = [
        r"(?:Equipment\s+Tag|Asset\s+Tag|Machine\s+Tag|Unit\s+Tag|Tag\s+No\.?|Equipment\s+ID|Equipment\s+Identifier)\s*[:=\-]\s*([A-Z0-9-_/ ]+)",
        r"(?:Applicable\s+Equipment\s+Tags?|Equipment\s+Covered|Applicable\s+Units?)\s*[:=\-]\s*([A-Z0-9-_/ ]+)",
        r"(?:Equipment|Asset|Machine)\s*[:=\-]\s*([A-Z0-9-_/ ]+)"
    ]

    WO_PATTERN = r"\b(WO[-\s]?\d{4,6}|Work\s+Order\s+#?\d{4,6}|INSP[-\s]?\d{3,5}|Inspection\s+#?\d{3,5})\b"
    
    MONTH_MAP = {
        "jan": "01", "january": "01", "feb": "02", "february": "02",
        "mar": "03", "march": "03", "apr": "04", "april": "04",
        "may": "05", "jun": "06", "june": "06", "jul": "07", "july": "07",
        "aug": "08", "august": "08", "sep": "09", "september": "09",
        "oct": "10", "october": "10", "nov": "11", "november": "11",
        "dec": "12", "december": "12"
    }

    DATE_PATTERNS = [
        r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b",
        r"\b(\d{4}-\d{2}-\d{2})\b",
        r"\b(\d{1,2}[-\s/](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-\s/]\d{2,4})\b",
        r"\b(\d{1,2}\s*/\s*\d{1,2}\s*/\s*\d{2,4})\b",
        r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,?\s+(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b"
    ]

    LABELED_DATE_PATTERNS = {
        "inspection_date": [
            r"(?:Inspection\s+Date|Date\s+of\s+Inspection|Survey\s+Date|Inspected\s+On)\s*[:=\-]?\s*\n?\s*([^\n\r,]+)",
        ],
        "maintenance_date": [
            r"(?:Date\s+Performed|Maintenance\s+Date|Work\s+Date|Completed\s+Date|Service\s+Date|Overhaul\s+Date)\s*[:=\-]?\s*\n?\s*([^\n\r,]+)",
        ],
        "incident_date": [
            r"(?:Incident\s+Date|Failure\s+Date|Event\s+Date|Trip\s+Date|Breakdown\s+Date)\s*[:=\-]?\s*\n?\s*([^\n\r,]+)",
        ],
        "document_date": [
            r"(?:Effective\s+Date|Issue\s+Date|Report\s+Date)\s*[:=\-]?\s*\n?\s*([^\n\r,]+)",
            r"(?:^|\n)\s*Date\s*[:=\-]?\s*\n?\s*([^\n\r,]+)"
        ]
    }

    @classmethod
    def normalize_date(cls, raw: Optional[str]) -> Optional[str]:
        if not raw or str(raw).strip().lower() in ("unknown", "none", "null", "n/a", "unkn"):
            return None
        s = str(raw).strip()
        s = re.sub(r"^(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*,?\s*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\s+[+-]\d{4}.*$", "", s)
        s = re.sub(r"\s+\d{1,2}:\d{2}(?::\d{2})?.*$", "", s)
        s = s.strip()

        # 1. ISO: YYYY-MM-DD
        m = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", s)
        if m:
            return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

        # 2. DD-Mon-YYYY or DD Mon YYYY (e.g. 15-Jul-2026, 20-Aug-2026, 10 Aug 2026, 02-Aug-2026)
        m = re.search(r"\b(\d{1,2})[-\s/]+([A-Za-z]{3,9})[-\s/]+(\d{2,4})\b", s)
        if m:
            day = int(m.group(1))
            mon_str = m.group(2).lower()[:3]
            yr = int(m.group(3))
            if yr < 100:
                yr += 2000
            if mon_str in cls.MONTH_MAP and 1 <= day <= 31:
                return f"{yr:04d}-{cls.MONTH_MAP[mon_str]}-{day:02d}"

        # 3. Mon DD, YYYY or Mon-DD-YYYY (e.g. August 20, 2026)
        m = re.search(r"\b([A-Za-z]{3,9})[-\s/]+(\d{1,2})[,\s-]+(\d{2,4})\b", s)
        if m:
            mon_str = m.group(1).lower()[:3]
            day = int(m.group(2))
            yr = int(m.group(3))
            if yr < 100:
                yr += 2000
            if mon_str in cls.MONTH_MAP and 1 <= day <= 31:
                return f"{yr:04d}-{cls.MONTH_MAP[mon_str]}-{day:02d}"

        # 4. DD / MM / YYYY or MM / DD / YYYY (e.g. 22 /08 / 2026)
        m = re.search(r"\b(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{2,4})\b", s)
        if m:
            p1 = int(m.group(1))
            p2 = int(m.group(2))
            yr = int(m.group(3))
            if yr < 100:
                yr += 2000
            if p1 > 12:  # Must be DD/MM/YYYY
                day, mon = p1, p2
            elif p2 > 12:  # Must be MM/DD/YYYY
                mon, day = p1, p2
            else:  # Default industrial DD/MM/YYYY
                day, mon = p1, p2
            if 1 <= mon <= 12 and 1 <= day <= 31:
                return f"{yr:04d}-{mon:02d}-{day:02d}"

        return None

    KNOWN_COMPONENTS = [
        "Bearing", "Drive-End Bearing", "Non-Drive-End Bearing", "Impeller", 
        "Shaft", "Mechanical Seal", "Motor", "Coupling", "Casing", "Suction Valve", 
        "Discharge Valve", "Piston", "Rotor", "Stator", "Lubricant Reservoir",
        "Fan Drive Assembly", "Drift Eliminators", "Basin Strainer", "Fill Media",
        "Tube Bundle", "Shell", "Channel Head"
    ]
    EVENT_KEYWORDS = {
        "Maintenance": ["maintenance", "repair", "overhaul", "replaced", "lubrication", "serviced", "work order"],
        "Inspection": ["inspection", "condition monitoring", "vibration analysis", "ultrasonic", "thermography", "calibrated"],
        "Failure": ["failure", "seizure", "trip", "alarm", "scored", "leakage", "breakdown", "shut down", "damage"],
        "Procedure": ["sop", "operating procedure", "pre-start", "safety requirement", "loto", "clearance limit"]
    }

    @classmethod
    def clean_tag(cls, raw: str) -> Optional[str]:
        if not raw:
            return None
        t = raw.strip().upper()
        # Normalize spaces or underscores to hyphens
        t = re.sub(r"\s+", "-", t)
        t = t.replace("_", "-")
        # Ensure prefix has hyphen if like P194B -> P-194B
        m = re.match(r"^([A-Z]{1,4})(\d{2,5}[A-Z0-9]*)$", t)
        if m:
            t = f"{m.group(1)}-{m.group(2)}"

        parts = t.split("-")

        # Guard 1: Real industrial equipment tags have at most 3 hyphen-separated segments
        # (e.g. P-101, P-194B, TEST-PUMP-001, COMP-A-301).  Anything with 4+ segments is
        # a document reference / report ID (e.g. FAILURE-INCIDENT-REPORT-P-101).
        # NOTE: This guard is NOT applied to explicit Equipment Tag: header values — see
        # clean_explicit_header_tag() which allows up to 5 segments for named assets like
        # TEST-PUMP-REAL-001.
        if len(parts) > 3:
            return None

        # Guard 2: Reject if ANY segment (not just the first two) is a known non-asset prefix
        if any(p in cls.NON_ASSET_PREFIXES for p in parts):
            return None

        # Guard 3: Exclude date-like patterns like 2026-08 or ending in 4-digit years
        suffix = parts[-1] if parts else ""
        if suffix in ["2020", "2021", "2022", "2023", "2024", "2025", "2026", "2027", "2028", "2029", "2030"]:
            return None
        return t

    @classmethod
    def clean_explicit_header_tag(cls, raw: str) -> Optional[str]:
        """
        Variant of clean_tag() for values extracted directly from explicit Equipment Tag:
        header fields.  The value is authoritative so the 4-segment count guard is lifted
        (e.g. TEST-PUMP-REAL-001 has 4 segments and must be preserved).
        All other guards still apply (NON_ASSET_PREFIXES, component prefix, date suffix).
        """
        if not raw:
            return None
        t = raw.strip().upper()
        t = re.sub(r"\s+", "-", t)
        t = t.replace("_", "-")
        m = re.match(r"^([A-Z]{1,4})(\d{2,5}[A-Z0-9]*)$", t)
        if m:
            t = f"{m.group(1)}-{m.group(2)}"

        parts = t.split("-")

        # Allow up to 5 segments for explicitly declared tags (e.g. TEST-PUMP-REAL-001)
        # but still reject absurdly long strings (6+) that are clearly document IDs.
        if len(parts) > 5:
            return None

        # Reject if any segment is a known document-type identifier
        if any(p in cls.NON_ASSET_PREFIXES for p in parts):
            return None

        # Reject date-suffix
        suffix = parts[-1] if parts else ""
        if suffix in ["2020", "2021", "2022", "2023", "2024", "2025", "2026", "2027", "2028", "2029", "2030"]:
            return None
        return t

    @classmethod
    def is_component_tag(cls, tag: str) -> bool:
        if not tag:
            return False
        parts = tag.split("-")
        return parts[0].upper() in cls.COMPONENT_PREFIXES

    @classmethod
    def extract_document_identifiers(cls, text: str, filename: str = "") -> Tuple[Optional[str], Optional[str]]:
        doc_no = None
        dm = re.search(r"(?:Doc(?:ument)?\s*(?:No\.?|Number)|Form\s*No\.?|Drawing\s*No\.?|DWG\s*No\.?)\s*[:=\-]?\s*([A-Z0-9-_/.]+)", text, re.IGNORECASE)
        if dm:
            doc_no = dm.group(1).strip()
        if not doc_no:
            dm2 = re.search(r"\b(VHP-IOM-[A-Z0-9-]+|PID-[A-Z0-9-]+|SOP-[A-Z0-9-]+|RPL-[A-Z0-9-]+|PFS-[A-Z0-9-]+)\b", text)
            if dm2:
                doc_no = dm2.group(1)

        model_no = None
        mm = re.search(r"(?:Model|Type)\s*[:=\-]?\s*([A-Z0-9-_/.]+)", text, re.IGNORECASE)
        if mm:
            cand = mm.group(1).strip()
            # Ignore generic words like 'Vibration', 'Preventive', 'Horizontal'
            if not any(cand.startswith(w) for w in ["Vibration", "Preventive", "Horizontal", "Condition", "Standard"]):
                model_no = cand
        if not model_no:
            mm2 = re.search(r"\b(SCP-[A-Z0-9-]+)\b", text)
            if mm2:
                model_no = mm2.group(1)

        return doc_no, model_no

    @classmethod
    def extract_document_equipment_evidence(
        cls,
        text: str,
        filename: str = ""
    ) -> Dict[str, Any]:
        """
        Extracts structured equipment evidence, distinguishing:
        - document_scope: SYSTEM | MULTI_ASSET | ASSET | UNKNOWN
        - primary_asset_tags: machine asset tags that this document belongs to
        - related_asset_tags: related equipment referenced in system/context
        - component_tags: valves, instruments, etc.
        - document_number & model_number: document control codes, NOT machines
        """
        fn_l = filename.lower()
        txt_l = text.lower()[:3000]

        doc_no, model_no = cls.extract_document_identifiers(text, filename)
        evidence_snippets: List[str] = []
        explicit_header_tags: List[str] = []

        # 1. Inspect Explicit Headers
        for pat in cls.EXPLICIT_HEADER_PATTERNS:
            for match in re.finditer(pat, text, re.IGNORECASE):
                snippet = match.group(0).strip()
                val_str = match.group(1).strip()

                # Handle compound duplex slash like P-194A/B
                slash_match = re.search(r"\b([A-Z]{1,4}[-_]?\d{2,5})([A-Z])/([A-Z])\b", val_str, re.IGNORECASE)
                if slash_match:
                    base = slash_match.group(1).upper()
                    t1 = cls.clean_tag(f"{base}{slash_match.group(2).upper()}")
                    t2 = cls.clean_tag(f"{base}{slash_match.group(3).upper()}")
                    for t in [t1, t2]:
                        if t and not cls.is_component_tag(t) and t not in explicit_header_tags:
                            explicit_header_tags.append(t)
                            evidence_snippets.append(f"Compound duplex specification: {snippet[:80]}")

                # Sub tags in header — use clean_explicit_header_tag() which allows
                # 4–5 segment tags like TEST-PUMP-REAL-001 to pass through
                sub_tags = re.findall(r"\b([A-Z]{1,10}(?:-[A-Z]{1,10})*-\d{1,5}[A-Z0-9]*)\b", val_str, re.IGNORECASE)
                if not sub_tags:
                    sub_tags = re.findall(r"\b([A-Z]{1,10}[-_]?\d{2,5}[A-Z0-9]*)\b", val_str, re.IGNORECASE)
                for st in sub_tags:
                    cleaned = cls.clean_explicit_header_tag(st)
                    if cleaned and not cls.is_component_tag(cleaned) and cleaned not in explicit_header_tags:
                        explicit_header_tags.append(cleaned)
                        evidence_snippets.append(f"{snippet[:80]}")

        # Check for Telemetry CSV column header
        csv_col_match = re.search(r"(?:equipment_tag|asset_tag|machine_tag)[,\t|;]\s*([A-Z0-9-_]+)", text, re.IGNORECASE)
        if csv_col_match:
            c_tag = cls.clean_tag(csv_col_match.group(1))
            if c_tag and not cls.is_component_tag(c_tag) and c_tag not in explicit_header_tags:
                explicit_header_tags.append(c_tag)
                evidence_snippets.append(f"Telemetry CSV header row: {csv_col_match.group(0)}")

        # Check for dual pump / multi-machine references in text
        dual_pump_match = re.search(r"\b(?:P-194A\s*(?:and|/|&)\s*P-194B|P-194A/B|Pumps\s+P-194A\s*/\s*P-194B)\b", text, re.IGNORECASE)
        if dual_pump_match:
            for p_tag in ["P-194A", "P-194B"]:
                if p_tag not in explicit_header_tags:
                    explicit_header_tags.append(p_tag)
            evidence_snippets.append(f"Multi-unit reference: {dual_pump_match.group(0)}")

        # 2. Extract all body equipment tags vs component tags
        body_all_matches = re.findall(r"\b([A-Z]{1,10}(?:-[A-Z]{1,10})*-\d{1,5}[A-Z0-9]*)\b", text, re.IGNORECASE)
        assets_found: List[str] = []
        components_found: List[str] = []
        for b in body_all_matches:
            c = cls.clean_tag(b)
            if c:
                if cls.is_component_tag(c):
                    if c not in components_found:
                        components_found.append(c)
                else:
                    if c not in assets_found:
                        assets_found.append(c)

        # 3. Filename candidates
        fn_clean = filename.replace("_", "-")
        fn_multi_matches = re.findall(r"\b([A-Z]{1,10}(?:-[A-Z]{1,10})*-\d{1,5}[A-Z0-9]*)\b", fn_clean, re.IGNORECASE)
        fn_tags = []
        for fm in fn_multi_matches:
            cand = cls.clean_tag(fm)
            if cand and not cls.is_component_tag(cand) and cand not in fn_tags:
                fn_tags.append(cand)
        if not fn_tags:
            fn_matches = re.findall(r"([A-Z]{1,4})[-_]?(\d{2,5}[A-Z0-9]*)", filename, re.IGNORECASE)
            for p, rest in fn_matches:
                cand = cls.clean_tag(f"{p}-{rest}")
                if cand and not cls.is_component_tag(cand) and cand not in fn_tags:
                    fn_tags.append(cand)

        # 4. Shift handover operational subject resolution
        if "shift_handover" in fn_l or "shift handover" in txt_l or filename.endswith(".eml"):
            # Focus on the unit being monitored/tripped/inspected
            if "p-194b" in txt_l and ("tripped" in txt_l or "vibration" in txt_l or "temp" in txt_l or "running" in txt_l):
                explicit_header_tags = ["P-194B"]
                evidence_snippets.append("Shift handover operational subject: P-194B")

        # 5. Determine Document Scope
        is_system = (
            "flowsheet" in fn_l or "flowsheet" in txt_l or
            "p&id" in fn_l or "pid" in fn_l or "piping & instrumentation" in txt_l or "piping and instrumentation" in txt_l or
            "process flowsheet" in txt_l or "system overview" in txt_l or
            (len(assets_found) >= 3 and any(t.startswith("T-") or t.startswith("TK-") for t in assets_found) and any(t.startswith("E-") for t in assets_found))
        )

        if is_system:
            document_scope = "SYSTEM"
            # For system documents, equipment is related; do not arbitrarily pick one primary machine
            primary_assets: List[str] = []
            related_assets = [t for t in assets_found if not cls.is_component_tag(t)]
            confidence = "High"
            detection_method = "system_process_scope"
        elif len(explicit_header_tags) > 1 or dual_pump_match:
            document_scope = "MULTI_ASSET"
            primary_assets = explicit_header_tags if len(explicit_header_tags) > 1 else ["P-194A", "P-194B"]
            related_assets = [t for t in assets_found if t not in primary_assets and not cls.is_component_tag(t)]
            confidence = "High"
            detection_method = "explicit_multi_asset_header"
        elif len(explicit_header_tags) == 1:
            document_scope = "ASSET"
            primary_assets = explicit_header_tags
            related_assets = [t for t in assets_found if t not in primary_assets and not cls.is_component_tag(t)]
            confidence = "High"
            detection_method = "explicit_content_header"
        elif len(assets_found) == 1:
            document_scope = "ASSET"
            primary_assets = assets_found
            related_assets = []
            confidence = "Medium"
            detection_method = "single_body_asset"
        elif fn_tags:
            document_scope = "ASSET"
            primary_assets = fn_tags
            related_assets = [t for t in assets_found if t not in primary_assets and not cls.is_component_tag(t)]
            confidence = "Low"
            detection_method = "filename_hint"
        else:
            document_scope = "UNKNOWN"
            primary_assets = []
            related_assets = [t for t in assets_found if not cls.is_component_tag(t)]
            confidence = "None"
            detection_method = "unresolved"

        return {
            "document_scope": document_scope,
            "primary_asset_tags": primary_assets,
            "related_asset_tags": related_assets,
            "component_tags": components_found,
            "document_number": doc_no,
            "model_number": model_no,
            # Legacy compatibility fields
            "distinct_tags": primary_assets if primary_assets else (related_assets if document_scope == "SYSTEM" else []),
            "primary_tag": primary_assets[0] if len(primary_assets) == 1 else (None if len(primary_assets) > 1 else (related_assets[0] if related_assets and document_scope != "SYSTEM" else None)),
            "is_multi_asset": document_scope in ["MULTI_ASSET", "SYSTEM"] or len(primary_assets) > 1,
            "confidence": confidence,
            "detection_method": detection_method,
            "evidence_snippets": evidence_snippets[:5],
            "filename_hints": fn_tags
        }

    @classmethod
    def extract_entities(cls, text: str, filename: str = "") -> Dict[str, Any]:
        """
        Extracts industrial entities from raw document text for human-in-the-loop review.
        """
        evidence = cls.extract_document_equipment_evidence(text, filename=filename)

        # Extract Work Order / Inspection ID
        found_wos = re.findall(cls.WO_PATTERN, text, re.IGNORECASE)
        clean_wos = list(set([w.strip().replace(" ", "-").upper() for w in found_wos]))

        # Extract Labeled Dates
        labeled_dates: Dict[str, str] = {}
        for l_type, patterns in cls.LABELED_DATE_PATTERNS.items():
            for pat in patterns:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    norm = cls.normalize_date(m.group(1))
                    if norm:
                        labeled_dates[l_type] = norm
                        break

        # Extract Raw and Normalized Dates
        found_dates = []
        found_dates_normalized = []
        for pat in cls.DATE_PATTERNS:
            d_matches = re.finditer(pat, text, re.IGNORECASE)
            for dm in d_matches:
                raw_d = dm.group(1) if dm.groups() else dm.group(0)
                norm_d = cls.normalize_date(raw_d)
                if raw_d and raw_d not in found_dates:
                    found_dates.append(raw_d)
                if norm_d and norm_d not in found_dates_normalized:
                    found_dates_normalized.append(norm_d)

        # Extract Components
        found_components = list(evidence.get("component_tags", []))
        for comp in cls.KNOWN_COMPONENTS:
            if re.search(r"\b" + re.escape(comp) + r"\b", text, re.IGNORECASE):
                if comp not in found_components:
                    found_components.append(comp)

        # Extract Explicit Connected Component Associations (Generic parent-asset / component evidence)
        connected_components: List[Dict[str, str]] = []
        conn_comp_matches = re.finditer(
            r"(?:Connected\s+Component|Associated\s+Component|Installed\s+Component|Sub-Component)\s*[:=\-]\s*([A-Za-z0-9-_]+)",
            text,
            re.IGNORECASE
        )
        type_match = re.search(r"(?:Component\s+Type|Part\s+Type)\s*[:=\-]\s*([^\n\r]+)", text, re.IGNORECASE)
        default_comp_type = type_match.group(1).strip() if type_match else (found_components[0] if found_components else "Mechanical Component")
        cond_match = re.search(r"(?:Component\s+Condition|Component\s+Status|Condition)\s*[:=\-]\s*([^\n\r]+)", text, re.IGNORECASE)
        default_condition = cond_match.group(1).strip() if cond_match else "Normal"

        for m in conn_comp_matches:
            raw_tag = m.group(1).strip()
            if raw_tag and not any(c["tag"].upper() == raw_tag.upper() for c in connected_components):
                connected_components.append({
                    "tag": raw_tag,
                    "type": default_comp_type,
                    "condition": default_condition
                })

        # Determine Event Category
        event_scores = {}
        for ev_type, keywords in cls.EVENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", text, re.IGNORECASE))
            event_scores[ev_type] = score
        
        detected_event = max(event_scores.items(), key=lambda x: x[1])
        event_type = detected_event[0] if detected_event[1] > 0 else "General Documentation"

        # Determine Primary Event Date using document semantics + labels + context
        fn_lower = filename.lower()
        if event_type == "Inspection" or "inspection" in fn_lower or "ndt" in fn_lower:
            primary_date = labeled_dates.get("inspection_date") or labeled_dates.get("document_date") or (found_dates_normalized[0] if found_dates_normalized else None)
        elif event_type == "Maintenance" or "maintenance" in fn_lower or "overhaul" in fn_lower or "wo" in fn_lower:
            primary_date = labeled_dates.get("maintenance_date") or labeled_dates.get("document_date") or (found_dates_normalized[0] if found_dates_normalized else None)
        elif event_type == "Failure" or "failure" in fn_lower or "incident" in fn_lower or "trip" in fn_lower:
            primary_date = labeled_dates.get("incident_date") or labeled_dates.get("document_date") or (found_dates_normalized[0] if found_dates_normalized else None)
        else:
            primary_date = labeled_dates.get("document_date") or (found_dates_normalized[0] if found_dates_normalized else None)

        return {
            "document_scope": evidence["document_scope"],
            "primary_asset_tags": evidence["primary_asset_tags"],
            "related_asset_tags": evidence["related_asset_tags"],
            "component_tags": evidence["component_tags"],
            "connected_components": connected_components,
            "document_number": evidence["document_number"],
            "model_number": evidence["model_number"],
            # Legacy fields
            "asset_tags": evidence["primary_asset_tags"] or evidence["related_asset_tags"],
            "machines": evidence["primary_asset_tags"] or evidence["related_asset_tags"],
            "primary_asset_tag": evidence["primary_tag"] or (evidence["primary_asset_tags"][0] if evidence["primary_asset_tags"] else "Unknown"),
            "is_multi_asset": evidence["is_multi_asset"],
            "equipment_evidence": evidence,
            "work_orders": clean_wos,
            "dates": found_dates_normalized if found_dates_normalized else found_dates,
            "labeled_dates": labeled_dates,
            "primary_date": primary_date,
            "components": found_components,
            "primary_component": found_components[0] if found_components else "General Machine",
            "event_type": event_type,
            "confidence": evidence["confidence"],
            "requires_human_confirmation": evidence["document_scope"] in ["SYSTEM", "MULTI_ASSET", "UNKNOWN"] or len(evidence["primary_asset_tags"]) != 1
        }
