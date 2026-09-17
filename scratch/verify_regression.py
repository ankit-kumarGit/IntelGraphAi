import urllib.request
import json
import mimetypes
from pathlib import Path

BASE_URL = "http://localhost:8000"
test_pdf = Path("/Users/ankitkumar/Desktop/IntelGraphAI/scratch/T200_Overhaul_Inspection.pdf")

def post_multipart(url, fields, files):
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = bytearray()
    for k, v in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f"Content-Disposition: form-data; name=\"{k}\"\r\n\r\n".encode())
        body.extend(f"{v}\r\n".encode())
    for k, p in files.items():
        fn = p.name
        content_type = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f"Content-Disposition: form-data; name=\"{k}\"; filename=\"{fn}\"\r\n".encode())
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
        body.extend(p.read_bytes())
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(url, data=bytes(body))
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def get_json(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

print("--- Step 1: Document Inspection ---")
inspect_data = post_multipart(f"{BASE_URL}/api/documents/inspect", {"hint_tag": "P-101"}, {"file": test_pdf})
print("Inspection result:", json.dumps(inspect_data, indent=2))
assert inspect_data["resolved_tag"] == "T-200"
assert inspect_data["is_mismatch"] is True
assert "T-200" in inspect_data["detected_tags"]

print("\n--- Step 2: Upload & Ingest with Associated Machine T-200 ---")
upload_res = post_multipart(
    f"{BASE_URL}/api/documents/upload",
    {
        "asset_tag": "T-200",
        "create_missing_machine": "true",
        "explicit_override": "false",
        "category": "Condition Monitoring / NDT"
    },
    {"file": test_pdf}
)
print("Upload result:", json.dumps(upload_res, indent=2))
assert upload_res["asset_tag"] == "T-200"
doc_id = upload_res["document_id"]

print("\n--- Step 3: Verify MongoDB Document ---")
from app.database import get_db
db = get_db()
doc = db.documents.find_one({"document_id": doc_id})
assert doc is not None, "Document not found in MongoDB"
doc_tag = doc.get("asset_tag")
assert doc_tag == "T-200", f"Expected T-200, got {doc_tag}"
print(f"MongoDB Verified: Document {doc_id} associated with {doc_tag}")

print("\n--- Step 4: Verify Neo4j Graph Relationship ---")
from app.services.neo4j_service import neo4j_graph
rel_t200 = [
    r for r in neo4j_graph.relationships
    if "T_200" in r.get("from", "") and doc_id in r.get("to", "")
]
assert len(rel_t200) > 0, f"Neo4j relationship ASSET_HAS_DOCUMENT to T-200 not found for doc {doc_id}"
print(f"Neo4j Verified: ASSET_HAS_DOCUMENT link confirmed for T-200: {rel_t200}")

rel_p101 = [
    r for r in neo4j_graph.relationships
    if "P_101" in r.get("from", "") and doc_id in r.get("to", "")
]
assert len(rel_p101) == 0, "Doc must NOT be linked to P-101 in Neo4j!"
print("Neo4j Verified: Confirmed ZERO relationship to P-101")

print("\n--- Step 5: Verify Live Server Audit (Qdrant Vectors & Neo4j Relationships) ---")
audit_t200 = get_json(f"{BASE_URL}/api/admin/documents-audit?asset_tag=T-200")
t200_doc_audit = next((d for d in audit_t200 if d["document_id"] == doc_id), None)
assert t200_doc_audit is not None, "Doc must exist in T-200 documents-audit"
assert t200_doc_audit["vector_count"] >= 1, f"Expected vector_count >= 1, got {t200_doc_audit['vector_count']}"
assert t200_doc_audit["graph_relationship_count"] >= 1, f"Expected graph_relationship_count >= 1, got {t200_doc_audit['graph_relationship_count']}"
print(f"Live Server Verified: Doc {doc_id} has {t200_doc_audit['vector_count']} Qdrant vector(s) and {t200_doc_audit['graph_relationship_count']} Neo4j relationship(s) under T-200")

audit_p101 = get_json(f"{BASE_URL}/api/admin/documents-audit?asset_tag=P-101")
assert not any(d["document_id"] == doc_id for d in audit_p101), "Doc must NOT exist in P-101 documents-audit!"
print("Live Server Isolation Verified: Confirmed ZERO Qdrant vectors and ZERO Neo4j links under P-101")

print("\n--- Step 6: Test Keep P-101 Manual Override Flow ---")
test_override_pdf = Path("/Users/ankitkumar/Desktop/IntelGraphAI/scratch/P101_With_T200_Ref.pdf")
override_res = post_multipart(
    f"{BASE_URL}/api/documents/upload",
    {
        "asset_tag": "P-101",
        "create_missing_machine": "false",
        "explicit_override": "true",
        "category": "Standard Operating Procedure"
    },
    {"file": test_override_pdf}
)
print("Override result:", json.dumps(override_res, indent=2))
assert override_res["asset_tag"] == "P-101"
doc_override_id = override_res["document_id"]
doc_ovr = db.documents.find_one({"document_id": doc_override_id})
assert doc_ovr["asset_tag"] == "P-101"
extracted_evidence = doc_ovr.get("extracted_entities", {}).get("asset_tags", []) + doc_ovr.get("extracted_entities", {}).get("machines", [])
assert "T-200" in extracted_evidence, f"Expected T-200 in extracted entities: {extracted_evidence}"
print(f"Override Verified: P-101 preserved, T-200 preserved as evidence: {extracted_evidence}")

print("\n--- Step 7: Verify Machine Profiles ---")
# Check documents endpoint for T-200
docs_t200 = get_json(f"{BASE_URL}/api/documents?asset_tag=T-200")
assert any(d.get("document_id") == doc_id for d in docs_t200), "Doc should appear in T-200 documents"
print(f"T-200 Documents Verified: {len(docs_t200)} documents found under T-200")

# Check documents endpoint for P-101
docs_p101 = get_json(f"{BASE_URL}/api/documents?asset_tag=P-101")
assert not any(d.get("document_id") == doc_id for d in docs_p101), "Doc must NOT appear in P-101 documents"
assert any(d.get("document_id") == doc_override_id for d in docs_p101), "Override doc should appear in P-101"
print(f"P-101 Documents Verified: T-200 doc isolated, override doc present")

print("\n--- Step 8: Verify Audit Trail ---")
logs = get_json(f"{BASE_URL}/api/audit-logs")
assoc_logs = [l for l in logs if "T-200" in str(l) or "T200" in str(l) or "P-101" in str(l)]
print(f"Found {len(assoc_logs)} relevant audit events in audit trail.")
assert len(assoc_logs) > 0, "Audit logs must record association events"

print("\n--- Step 9: Verify Test Fixture Endpoints for Admin ---")
pkg_user = get_json(f"{BASE_URL}/api/test-package/list?package=user_test")
assert len(pkg_user) >= 6, f"Expected at least 6 user_test files, got {len(pkg_user)}"
user_001_clean = [
    'USER_TEST_001_Maintenance_Report.pdf',
    'USER_TEST_001_OEM_Manual.pdf',
    'USER_TEST_001_Telemetry.csv',
    'USER_TEST_001_Maintenance_Schedule.xlsx',
    'USER_TEST_001_PID_Drawing.png',
    'USER_TEST_001_Shift_Handover.eml',
]
for f in user_001_clean:
    assert f in pkg_user, f"Missing clean fixture: {f}"

pkg_b = get_json(f"{BASE_URL}/api/test-package/list?package=p194b")
assert len(pkg_b) == 12, f"Expected 12 p194b files, got {len(pkg_b)}"
pkg_baseline = get_json(f"{BASE_URL}/api/test-package/list?package=p194")
assert len(pkg_baseline) == 12, f"Expected 12 p194 files, got {len(pkg_baseline)}"
print(f"Admin Test Fixtures Verified: user_test={len(pkg_user)} files (including 6 clean fixtures), p194b={len(pkg_b)}, p194={len(pkg_baseline)}")

print("\nALL REGRESSION CHECKS A-N PASSED ON REAL DATA PATH!")
