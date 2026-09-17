from pathlib import Path
from app.document_processing.extractor import DocumentExtractor
from app.document_processing.entity_extractor import EntityExtractor
from app.services.machine_resolution_service import machine_resolution
import json

files = [
    "P-194_Process_Flowsheet.txt",
    "P-194_Shift_Handover_20260810.eml",
    "P-194_Failure_Incident_Report_20260812.pdf",
    "P-194_Inspection_Report_20260715.pdf",
    "P-194_Maintenance_Report_20260802.pdf",
    "P-194_Maintenance_Schedule.xlsx",
    "P-194_OEM_Manual.pdf",
    "P-194_PID_Diagram.png",
    "P-194_Scanned_Field_Checklist.png",
    "P-194B_Telemetry_20260810_20260812.csv",
    "SOP-P194-01_Startup_Shutdown.pdf"
]

base_dirs = [
    Path("/Users/ankitkumar/Desktop/IntelGraphAI/intelgraph-backend/storage/uploads"),
    Path("/Users/ankitkumar/Desktop/IntelGraphAI/test_p194_package"),
    Path("/Users/ankitkumar/Desktop/IntelGraphAI/test_p194b_package")
]

for fn in files:
    found_path = None
    for bd in base_dirs:
        p = bd / fn
        if p.exists():
            found_path = p
            break
        for cand in bd.glob(f"*{fn[:10]}*"):
            if cand.name == fn or cand.name.replace("-", "_") == fn.replace("-", "_"):
                found_path = cand
                break
    if not found_path:
        print(f"FILE NOT FOUND: {fn}")
        continue
    
    file_type = found_path.suffix.lstrip(".").lower()
    pages = DocumentExtractor.extract(found_path, file_type)
    text = "\n".join([pg.get("content", "") for pg in pages if pg.get("content")])
    
    # Run EntityExtractor
    evidence = EntityExtractor.extract_document_equipment_evidence(text, filename=fn)
    entities = EntityExtractor.extract_entities(text)
    
    # Run MachineResolution
    res = machine_resolution.resolve_machine_association(text=text, filename=fn, hint_tag=None)
    
    print("=" * 70)
    print(f"FILE: {fn}")
    print(f"Found At: {found_path}")
    print(f"Text Snippet (first 200 chars): {repr(text[:200])}")
    print(f"Evidence Distinct Tags: {evidence.get('distinct_tags')}")
    print(f"Evidence Primary Tag: {evidence.get('primary_tag')}")
    print(f"Evidence Confidence: {evidence.get('confidence')}")
    print(f"Evidence Method: {evidence.get('detection_method')}")
    print(f"Evidence Snippets: {evidence.get('evidence_snippets')}")
    print(f"Extracted Asset Tags: {entities.get('asset_tags')}")
    print(f"Extracted Machines: {entities.get('machines')}")
    print(f"Machine Resolution Status: {res.get('status')}")
    print(f"Machine Resolution Resolved Tag: {res.get('resolved_tag')}")
    print(f"Machine Resolution Detected Tags: {res.get('detected_tags')}")
    print(f"Machine Resolution Message: {res.get('message')}")
