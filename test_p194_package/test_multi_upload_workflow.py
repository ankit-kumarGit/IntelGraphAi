#!/usr/bin/env python3
import httpx
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api"
PACKAGE_DIR = Path("/Users/ankitkumar/Desktop/IntelGraphAI/test_p194_package")
NEG_DIR = Path("/Users/ankitkumar/Desktop/IntelGraphAI/test_negative_package")

print("=== 1. TESTING REAL MULTI-FILE UPLOAD FOR P-194 (12 FILES) ===")

files_to_test = [
    "P-194_Process_Flowsheet.txt",
    "P-194_Shift_Handover.eml",
    "P-194_Site_Upload_Package.zip",
    "P-194_Failure_Incident_Report.pdf",
    "P-194_Inspection_Report.pdf",
    "P-194_Maintenance_Report.pdf",
    "P-194_Maintenance_Schedule.xlsx",
    "P-194_OEM_Manual.pdf",
    "P-194_PID_Diagram.png",
    "P-194_Scanned_Field_Checklist.png",
    "P-194_Telemetry.csv",
    "SOP-P194-01-Operation.pdf"
]

client = httpx.Client(timeout=30.0)

results = []
for filename in files_to_test:
    file_path = PACKAGE_DIR / filename
    assert file_path.exists(), f"File {file_path} not found!"
    
    with open(file_path, "rb") as f:
        resp = client.post(
            f"{BASE_URL}/documents/upload",
            files={"file": (filename, f)},
            data={
                "asset_tag": "P-194",
                "category": "Maintenance" if "Maintenance" in filename else "OEM Manual" if "OEM" in filename else "Operations",
                "version": "v1.0",
                "governance_status": "Approved",
                "uploaded_by": "Senior Reliability Engineer"
            }
        )
    
    assert resp.status_code == 200, f"Upload of {filename} failed with HTTP {resp.status_code}: {resp.text}"
    data = resp.json()
    status = data.get("status")
    doc_id = data.get("document_id")
    msg = data.get("message")
    chunks = data.get("chunk_count", data.get("total_chunks", 0))
    print(f"✓ {filename:<35} | Status: {status} | Chunks: {chunks} | Msg: {msg}")
    results.append(data)

print(f"\nAll 12 files processed successfully!")

print("\n=== 2. TESTING DUPLICATE RE-UPLOAD (STEP 9) ===")
# Re-upload the exact same file
dup_file = "P-194_OEM_Manual.pdf"
with open(PACKAGE_DIR / dup_file, "rb") as f:
    resp = client.post(
        f"{BASE_URL}/documents/upload",
        files={"file": (dup_file, f)},
        data={"asset_tag": "P-194", "category": "OEM Manual"}
    )
dup_data = resp.json()
print(f"Re-upload response status: {dup_data.get('status')}")
print(f"Re-upload message: {dup_data.get('message')}")
assert dup_data.get("already_imported") == True or dup_data.get("status") == "already_imported", "Duplicate detection failed!"
assert "already imported" in dup_data.get("message", "").lower()
print("✓ Duplicate detection verified via SHA-256 fingerprint!")

print("\n=== 3. TESTING NEGATIVE FILES (STEP 13) ===")
neg_files = [
    ("bad_unsupported.exe", "Executable"),
    ("corrupted_sample.pdf", "Corrupted"),
    ("empty_file.txt", "Empty"),
    ("oversized_sample.zip", "Oversized"),
    ("malicious_zipslip.zip", "Zip Slip"),
    ("password_protected.pdf", "Password-protected")
]

for neg_file, reason in neg_files:
    path = NEG_DIR / neg_file
    with open(path, "rb") as f:
        resp = client.post(
            f"{BASE_URL}/documents/upload",
            files={"file": (neg_file, f)},
            data={"asset_tag": "P-194"}
        )
    data = resp.json()
    status = data.get("status")
    msg = data.get("message", "")
    print(f"Negative test [{reason}] {neg_file:<25} | Status: {status} | Msg: {msg}")
    assert status == "failed", f"Expected failure for {neg_file} but got {status}"

print("✓ All negative test files rejected safely without killing the system!")

print("\n=== 4. VERIFYING P-194 ASSET RECORD & ISOLATION FROM P-101 ===")
resp = client.get(f"{BASE_URL}/assets/P-194")
assert resp.status_code == 200, f"Asset P-194 not found: {resp.text}"
asset_info = resp.json()
print(f"Asset P-194 Tag: {asset_info.get('tag')}")
print(f"Asset P-194 Name: {asset_info.get('name')}")
print(f"Asset P-194 Type: {asset_info.get('asset_type')}")
print(f"Asset P-194 Associated Documents: {asset_info.get('document_count')}")
assert asset_info.get("document_count") >= 12, "Expected at least 12 documents linked to P-194"

# Check that P-101 documents do not contain P-194 docs
resp_101 = client.get(f"{BASE_URL}/documents?asset_tag=P-101")
docs_101 = [d.get("filename") for d in resp_101.json()]
for f in files_to_test:
    assert f not in docs_101, f"Data leak: {f} found in P-101 documents!"
print("✓ Perfect asset isolation verified between P-194 and P-101!")

print("\n=== 5. VERIFYING AI CHAT FOR P-194 AND GENERAL PUMP (STEP 12) ===")
ai_queries = [
    ("What is P-194?", "P-194", "CP-194"),
    ("What documents do we have for P-194?", "12 verified", "OEM_Manual"),
    ("When was P-194 inspected?", "2026-03-02", "2.1 mm/s"),
    ("What maintenance history is available for P-194?", "WO-9412", "SKF-6314-2Z"),
    ("What telemetry information is available for P-194?", "2.1 to 2.4", "18.2"),
    ("What failures are recorded for P-194?", "2026-02-14", "4.2 hours"),
    ("What compliance evidence is available for P-194?", "OISD-STD-119", "Factories Act"),
    ("What does the shift handover email say about P-194?", "Marcus Vance", "68"),
    ("Summarize the knowledge we just imported for P-194.", "CP-194", "WO-9412"),
    ("What is a centrifugal pump?", "rotodynamic", "driver")
]

for q, expected1, expected2 in ai_queries:
    resp = client.post(
        f"{BASE_URL}/chat",
        json={"query": q, "asset_tag": "P-194" if "P-194" in q else None}
    )
    assert resp.status_code == 200, f"Query '{q}' failed: {resp.text}"
    data = resp.json()
    answer = data.get("answer", "")
    citations = data.get("citations", [])
    print(f"\nQuery: '{q}'")
    print(f"Scope: {data.get('scope')} | Confidence: {data.get('confidence')}")
    print(f"Answer excerpt: {answer[:120]}...")
    print(f"Citations count: {len(citations)}")
    assert expected1.lower() in answer.lower(), f"Expected '{expected1}' in answer for '{q}'"
    if expected2:
        assert expected2.lower() in answer.lower(), f"Expected '{expected2}' in answer for '{q}'"

print("\n=== ALL BACKEND VERIFICATIONS FOR P-194 MULTI-FILE UPLOAD PASSED! ===")
