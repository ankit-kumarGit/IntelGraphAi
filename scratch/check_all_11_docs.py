from app.database import get_db
import json

db = get_db()
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

for fn in files:
    docs = list(db.documents.find({"filename": fn}))
    print("=" * 60)
    print(f"FILENAME: {fn} (found {len(docs)} entries in db.documents)")
    for d in docs:
        d_id = str(d.get("_id"))
        doc_id = d.get("document_id")
        asset_tag = d.get("asset_tag")
        category = d.get("category")
        sha = d.get("sha256_hash")
        u_date = d.get("upload_date")
        f_path = d.get("file_path")
        extracted_tags = d.get("extracted_entities", {}).get("asset_tags")
        primary_tag = d.get("extracted_entities", {}).get("primary_asset_tag")
        evidence = d.get("extracted_entities", {}).get("equipment_evidence", {})
        print(f"  _id: {d_id}")
        print(f"  document_id: {doc_id}")
        print(f"  asset_tag: {asset_tag}")
        print(f"  category: {category}")
        print(f"  sha256_hash: {sha}")
        print(f"  upload_date: {u_date}")
        print(f"  file_path: {f_path}")
        print(f"  extracted_asset_tags: {extracted_tags}")
        print(f"  extracted_primary: {primary_tag}")
        print(f"  evidence_distinct: {evidence.get('distinct_tags')}")
        print(f"  evidence_method: {evidence.get('detection_method')}")
        print(f"  evidence_snippets: {evidence.get('evidence_snippets')}")
