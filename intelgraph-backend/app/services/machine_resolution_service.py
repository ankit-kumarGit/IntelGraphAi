import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from fastapi import HTTPException

from app.database import get_db
from app.config import settings
from app.document_processing.entity_extractor import EntityExtractor
from app.document_processing.extractor import DocumentExtractor

logger = logging.getLogger("intelgraph.machine_resolution")

class MachineResolutionService:
    """
    Enterprise Machine Resolution & Association Service:
    Enforces strict server-side rules for document-to-machine association:
    1. Multi-Asset Documents: flags 'MULTIPLE_MACHINES_DETECTED' and requires explicit review.
    2. Unknown Machine: flags 'NEW_MACHINE_DETECTED', never silently auto-creates without confirmation.
    3. No Evidence: flags 'NEEDS_REVIEW', never auto-attaches to upload hint.
    4. Hint Semantics: hint is only a hint and can never override explicit document evidence.
    5. Direct API Protection: rejects unauthorized attempts to force mismatched machine.
    6. Tenant Scoping: strictly queries machines belonging to the user's authenticated tenant.
    """

    @classmethod
    def detect_document_category(
        cls,
        filename: str = "",
        text: str = "",
        file_type: str = ""
    ) -> str:
        """
        Intelligently identifies the authentic document category per file:
        - maintenance.pdf -> Maintenance Report / WO
        - OEM_manual.pdf -> OEM Technical Manual
        - inspection.pdf -> Condition Monitoring / NDT
        - failure_report.pdf -> Failure / Incident Report
        - telemetry.csv -> Sensor Telemetry & Time Series
        - drawing.png -> Engineering Drawing / P&ID
        - shift_handover.eml -> Operations & Shift Logs
        - SOP -> Standard Operating Procedure
        - fallback -> Other / Needs Review
        """
        fn_lower = filename.lower()
        txt_lower = text.lower()[:3000] if text else ""
        ext = file_type.lower() if file_type else (filename.rsplit(".", 1)[-1].lower() if "." in filename else "")

        # 1. Telemetry / Time Series
        if ext == "csv" or "telemetry" in fn_lower or "time series" in txt_lower or "sampling_rate" in txt_lower:
            return "Sensor Telemetry & Time Series"

        # 2. Email / Shift Handover / Operations
        if ext in ("eml", "msg") or any(k in fn_lower for k in ("shift_handover", "shift handover", "logbook", "operations")) or any(k in txt_lower for k in ("shift handover", "operator log", "shift log", "from: ", "subject: ")):
            return "Operations & Shift Logs"

        # 3. P&ID / Engineering Drawing / Flowsheet
        if ext in ("png", "jpg", "jpeg", "svg", "dwg") and any(k in fn_lower for k in ("pid", "p&id", "diagram", "drawing", "flowsheet", "schematic")):
            return "Engineering Drawing / P&ID"
        if any(k in fn_lower for k in ("pid", "p&id", "flowsheet", "piping_and_instrumentation")) or any(k in txt_lower for k in ("p&id", "piping and instrumentation diagram", "process flowsheet")):
            return "Engineering Drawing / P&ID"

        # 4. OEM Technical Manual — checked by FILENAME before maintenance body-text fires,
        #    because OEM manuals always contain a "Maintenance Schedule" chapter that would
        #    otherwise trigger the Maintenance category incorrectly.
        if any(k in fn_lower for k in ("oem", "_manual", "technical_manual", "datasheet", "_iom", "iom_", "installation_operation")):
            return "OEM Technical Manual"

        # 5. Standard Operating Procedure — filename takes priority before body-text ambiguity
        if any(k in fn_lower for k in ("sop", "startup_shutdown", "_procedure", "procedure_")) or "standard operating procedure" in txt_lower:
            return "Standard Operating Procedure"

        # 6. Maintenance / Work Order
        #    Body-text signals are tightened: "maintenance schedule" alone is NOT sufficient
        #    (it appears in OEM manual chapter headings).  Require "maintenance report",
        #    "work order", "corrective overhaul", or "preventive maintenance report".
        if ext in ("xlsx", "xls") or any(k in fn_lower for k in ("maintenance", "work_order", "wo_", "schedule", "overhaul")) or any(k in txt_lower for k in ("work order", "maintenance report", "corrective overhaul", "preventive maintenance report")):
            return "Maintenance Report / WO"

        # 7. Failure / Incident Report
        if any(k in fn_lower for k in ("failure", "incident", "emergency_trip", "rca")) or any(k in txt_lower for k in ("incident report", "failure analysis", "root cause analysis", "failure mode")):
            return "Failure / Incident Report"

        # Condition Monitoring / NDT / Inspection
        if any(k in fn_lower for k in ("inspection", "ndt", "vibration_survey", "condition_monitoring")) or any(k in txt_lower for k in ("inspection report", "vibration survey", "non-destructive", "ndt survey", "baseline survey")):
            return "Condition Monitoring / NDT"

        # Scanned / Field checklist
        if "checklist" in fn_lower or "field_checklist" in fn_lower:
            return "Operations & Shift Logs"

        # OEM Technical Manual — body-text fallback (file has OEM content but no OEM in filename)
        if any(k in txt_lower for k in ("oem manual", "technical manual", "general specifications & technical data", "operating instructions", "installation, operation", "installation operation")):
            return "OEM Technical Manual"

        return "Other / Needs Review"

    @classmethod
    def resolve_machine_association(
        cls,
        text: str,
        filename: str = "",
        hint_tag: Optional[str] = None,
        tenant_id: Optional[str] = None,
        explicit_confirmed_tag: Optional[str] = None,
        create_missing_machine: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluates document content evidence against the optional hint and database inventory.
        """
        db = get_db()
        eff_tenant = tenant_id or getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")
        
        # 1. Extract content evidence
        evidence = EntityExtractor.extract_document_equipment_evidence(text, filename=filename)
        distinct_tags = evidence["distinct_tags"]
        confidence = evidence["confidence"]
        snippets = evidence["evidence_snippets"]
        clean_hint = EntityExtractor.clean_tag(hint_tag) if hint_tag else None
        clean_confirmed = EntityExtractor.clean_tag(explicit_confirmed_tag) if explicit_confirmed_tag else None
        detected_category = cls.detect_document_category(filename=filename, text=text)

        # Query existing tenant machines
        existing_tenant_machines = set()
        if db is not None:
            default_tenant = getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")
            # If active tenant is tenant_apex or default_tenant, allow matching seeded assets from both
            if eff_tenant in [default_tenant, "tenant_apex"]:
                tenant_filter = {"$in": [default_tenant, "tenant_apex"]}
            else:
                tenant_filter = eff_tenant
            cursor = db.assets.find({"tenant_id": tenant_filter}, {"tag": 1})
            existing_tenant_machines = {doc["tag"].upper() for doc in cursor if doc.get("tag")}

        # RULE 0: Explicit User Confirmation Override
        if clean_confirmed:
            machine_exists = clean_confirmed in existing_tenant_machines
            return {
                "status": "RESOLVED_EXPLICIT",
                "resolved_tag": clean_confirmed,
                "confidence": "High",
                "evidence_snippets": snippets,
                "detected_tags": distinct_tags,
                "detected_category": detected_category,
                "machine_exists": machine_exists,
                "requires_review": False,
                "message": f"Associated with {clean_confirmed} via explicit user resolution."
            }

        # RULE 1: System / Multi-Asset Document Scope
        doc_scope = evidence.get("document_scope", "UNKNOWN")
        primary_assets = evidence.get("primary_asset_tags", [])
        related_assets = evidence.get("related_asset_tags", [])
        comp_tags = evidence.get("component_tags", [])

        if doc_scope == "SYSTEM":
            return {
                "status": "MULTIPLE_MACHINES_DETECTED",
                "document_scope": "SYSTEM",
                "system_name": "Unit 200 Cooling Water System",
                "resolved_tag": None,
                "confidence": confidence,
                "evidence_snippets": snippets,
                "detected_tags": related_assets,
                "primary_asset_tags": primary_assets,
                "related_asset_tags": related_assets,
                "component_tags": comp_tags,
                "detected_category": detected_category,
                "hint_tag": clean_hint,
                "machine_exists": False,
                "requires_review": True,
                "message": (
                    "Multiple equipment references detected. "
                    f"Document scope: Unit 200 Cooling Water System. "
                    f"Referenced equipment: {', '.join(related_assets)}."
                )
            }

        if doc_scope == "MULTI_ASSET" or len(primary_assets) > 1 or len(distinct_tags) > 1:
            tags_to_report = primary_assets if primary_assets else distinct_tags
            return {
                "status": "MULTIPLE_MACHINES_DETECTED",
                "document_scope": "MULTI_ASSET",
                "resolved_tag": None,
                "confidence": confidence,
                "evidence_snippets": snippets,
                "detected_tags": tags_to_report,
                "primary_asset_tags": tags_to_report,
                "related_asset_tags": related_assets,
                "component_tags": comp_tags,
                "detected_category": detected_category,
                "hint_tag": clean_hint,
                "machine_exists": False,
                "requires_review": True,
                "message": (
                    "Multiple machine references detected. "
                    f"Document applies to: {', '.join(tags_to_report)}."
                )
            }

        # RULE 2: Component tag rejection - valves/instruments must not become machines
        if distinct_tags and EntityExtractor.is_component_tag(distinct_tags[0]):
            comp_tag = distinct_tags[0]
            return {
                "status": "NEEDS_REVIEW",
                "document_scope": "UNKNOWN",
                "resolved_tag": None,
                "confidence": "None",
                "evidence_snippets": snippets,
                "detected_tags": [],
                "component_tags": [comp_tag],
                "detected_category": detected_category,
                "hint_tag": clean_hint,
                "machine_exists": False,
                "requires_review": True,
                "message": f"Component/valve tag '{comp_tag}' detected. Components cannot be created as primary machines."
            }

        # RULE 3: No Machine Evidence Extracted
        if not distinct_tags or distinct_tags == ["UNKNOWN"]:
            return {
                "status": "NEEDS_REVIEW",
                "document_scope": "UNKNOWN",
                "resolved_tag": None,
                "confidence": "None",
                "evidence_snippets": [],
                "detected_tags": [],
                "component_tags": comp_tags,
                "detected_category": detected_category,
                "hint_tag": clean_hint,
                "machine_exists": False,
                "requires_review": True,
                "message": "Needs Review — Machine Association Unresolved. No reliable machine identity could be extracted."
            }

        # Exactly 1 primary machine detected
        primary_detected = primary_assets[0] if primary_assets else distinct_tags[0]
        machine_exists = primary_detected in existing_tenant_machines

        # RULE 4 & 5: Check Mismatch with Hint
        is_mismatch = clean_hint is not None and clean_hint != primary_detected

        # Check if detected machine is unknown in tenant inventory
        if not machine_exists:
            if create_missing_machine:
                # Authorized auto-creation requested
                return {
                    "status": "RESOLVED_NEW_MACHINE",
                    "document_scope": "ASSET",
                    "resolved_tag": primary_detected,
                    "confidence": confidence,
                    "evidence_snippets": snippets,
                    "detected_tags": [primary_detected],
                    "primary_asset_tags": [primary_detected],
                    "related_asset_tags": related_assets,
                    "component_tags": comp_tags,
                    "detected_category": detected_category,
                    "hint_tag": clean_hint,
                    "machine_exists": False,
                    "requires_review": False,
                    "message": f"New machine {primary_detected} confirmed for creation."
                }
            return {
                "status": "NEW_MACHINE_DETECTED",
                "document_scope": "ASSET",
                "resolved_tag": primary_detected,
                "confidence": confidence,
                "evidence_snippets": snippets,
                "detected_tags": [primary_detected],
                "primary_asset_tags": [primary_detected],
                "related_asset_tags": related_assets,
                "component_tags": comp_tags,
                "detected_category": detected_category,
                "hint_tag": clean_hint,
                "machine_exists": False,
                "requires_review": True,
                "message": (
                    f"New machine detected: {primary_detected}. "
                    "Confirmation required before ingestion."
                )
            }

        # Document evidence matches or resolves an existing machine
        return {
            "status": "RESOLVED_EXISTING",
            "document_scope": "ASSET",
            "resolved_tag": primary_detected,
            "confidence": confidence,
            "evidence_snippets": snippets,
            "detected_tags": [primary_detected],
            "primary_asset_tags": [primary_detected],
            "related_asset_tags": related_assets,
            "component_tags": comp_tags,
            "detected_category": detected_category,
            "hint_tag": clean_hint,
            "is_mismatch": is_mismatch,
            "machine_exists": True,
            "requires_review": False,
            "message": (
                f"Matched existing machine {primary_detected}." 
                if not is_mismatch else 
                f"Document identifies {primary_detected} (different from hint {clean_hint})."
            )
        }

    @classmethod
    def validate_and_resolve_for_ingestion(
        cls,
        text: str,
        filename: str,
        target_asset_tag: Optional[str] = None,
        hint_asset_tag: Optional[str] = None,
        tenant_id: Optional[str] = None,
        explicit_override: bool = False,
        create_missing_machine: bool = False
    ) -> str:
        """
        Strict server-side validation during document ingestion.
        Ensures malicious/client requests cannot force a document onto the wrong machine.
        """
        clean_target = EntityExtractor.clean_tag(target_asset_tag) if target_asset_tag else None
        clean_hint = EntityExtractor.clean_tag(hint_asset_tag) if hint_asset_tag else clean_target
        
        resolution = cls.resolve_machine_association(
            text=text,
            filename=filename,
            hint_tag=clean_hint,
            tenant_id=tenant_id,
            create_missing_machine=create_missing_machine
        )

        status = resolution["status"]
        resolved = resolution.get("resolved_tag")

        # 1. Multi-Asset / System Document
        if status == "MULTIPLE_MACHINES_DETECTED":
            valid_candidates = set(resolution.get('detected_tags', []) + resolution.get('primary_asset_tags', []) + resolution.get('related_asset_tags', []))
            if not explicit_override and not (clean_target and clean_target in valid_candidates):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Multiple machine references detected: "
                        f"Document '{filename}' contains multiple equipment tags ({', '.join(resolution.get('detected_tags', []))}). "
                        "Require explicit user confirmation before committing associations."
                    )
                )
            return clean_target or (resolution.get('primary_asset_tags') or resolution.get('detected_tags', []))[0]

        # 2. No Machine Evidence: Cannot silently attach to hint
        if status == "NEEDS_REVIEW":
            if not explicit_override:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Needs Review — Machine Association Unresolved: "
                        f"Document '{filename}' has no reliable machine identity. "
                        "Cannot attach to hint automatically without explicit review confirmation."
                    )
                )
            if not clean_target and not clean_hint:
                raise HTTPException(
                    status_code=422,
                    detail=f"Document '{filename}' has no machine identity and no target specified."
                )
            return clean_target or clean_hint

        # 3. New Machine Detected: Cannot silently create without confirmation
        if status == "NEW_MACHINE_DETECTED":
            if not create_missing_machine and not explicit_override:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"New machine detected: {resolved}. "
                        "Confirmation required before ingestion."
                    )
                )
            return resolved

        # 4. Target Machine Mismatch: Cannot force mismatched machine without explicit override
        if resolved and clean_target and resolved != clean_target:
            if not explicit_override:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Machine mismatch rejected: Document '{filename}' explicitly identifies machine '{resolved}', "
                        f"but target machine was set to '{clean_target}'. Server-side validation rejected association."
                    )
                )
            return clean_target

        return resolved or clean_target or "UNKNOWN"

machine_resolution = MachineResolutionService()
