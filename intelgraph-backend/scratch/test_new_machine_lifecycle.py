import httpx
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"
client = httpx.Client(timeout=30.0)

def run_new_machine_test():
    # 1. Clean any old test records for NEW-TEST-ASSET-999
    from app.database import get_db
    db = get_db()
    if db is not None:
        db.assets.delete_many({"tag": "NEW-TEST-ASSET-999"})
        db.documents.delete_many({"asset_tag": "NEW-TEST-ASSET-999"})
        db.document_chunks.delete_many({"asset_tag": "NEW-TEST-ASSET-999"})
        db.inspection_records.delete_many({"asset_tag": "NEW-TEST-ASSET-999"})

    # 2. Create test document
    scratch_dir = Path("scratch")
    scratch_dir.mkdir(exist_ok=True)
    doc_path = scratch_dir / "NEW_TEST_ASSET_999_Datasheet.txt"
    doc_content = """EQUIPMENT SPECIFICATION & COMMISSIONING DATASHEET
Equipment Tag: NEW-TEST-ASSET-999
Equipment Name: High Pressure Feed Pump
Maximum Operating Pressure: 13.73 bar
Design Flow Rate: 165 m3/h
Manufacturer: Advanced Thermal Dynamics
Operating Temperature Limit: 185 deg C
"""
    doc_path.write_text(doc_content)

    print("=== STEP 1: Uploading New Machine Document ===")
    with open(doc_path, "rb") as f:
        res = client.post(
            f"{BASE_URL}/api/documents/upload",
            files={"file": ("NEW_TEST_ASSET_999_Datasheet.txt", f, "text/plain")},
            data={
                "asset_tag": "NEW-TEST-ASSET-999",
                "create_missing_machine": "true",
                "category": "OEM Technical Manual",
                "tenant_id": "tenant_default"
            }
        )
    print("Upload status:", res.status_code)
    upload_json = res.json()
    print("Upload result message:", upload_json.get("message"))
    assert res.status_code == 200, f"Upload failed: {res.text}"

    # 3. Query chat for the unique fact: 13.73 bar
    print("\n=== STEP 2: Querying Unique Fact (13.73 bar) ===")
    res_pressure = client.post(
        f"{BASE_URL}/api/chat",
        json={
            "query": "What is the maximum operating pressure of NEW-TEST-ASSET-999?",
            "asset_tag": "NEW-TEST-ASSET-999",
            "tenant_id": "tenant_default"
        }
    )
    print("Pressure Query Status:", res_pressure.status_code)
    data_pressure = res_pressure.json()
    print("ANSWER:", data_pressure.get("answer"))
    print("REFUSED:", data_pressure.get("refused"))
    print("CITATIONS:", [c.get("document_name") for c in data_pressure.get("citations", [])])
    assert "13.73" in data_pressure.get("answer"), "Expected 13.73 bar in answer"
    assert len(data_pressure.get("citations", [])) >= 1, "Expected at least 1 citation"
    assert "NEW_TEST_ASSET_999" in str(data_pressure.get("citations", [])), "Expected citation to point to newly uploaded document"

    # 4. Query chat for missing inspection date -> Grounded Refusal
    print("\n=== STEP 3: Querying Missing Inspection Date (Grounded Refusal) ===")
    res_insp = client.post(
        f"{BASE_URL}/api/chat",
        json={
            "query": "What was the inspection date of NEW-TEST-ASSET-999?",
            "asset_tag": "NEW-TEST-ASSET-999",
            "tenant_id": "tenant_default"
        }
    )
    print("Inspection Query Status:", res_insp.status_code)
    data_insp = res_insp.json()
    print("ANSWER:", data_insp.get("answer"))
    print("REFUSED:", data_insp.get("refused"))
    assert data_insp.get("refused") is True or "couldn't find" in data_insp.get("answer", "").lower() or "not found" in data_insp.get("answer", "").lower(), "Expected grounded refusal for missing inspection date"

    print("\n>>> ALL CRITICAL NEW-MACHINE TEST CHECKS PASSED! <<<")

if __name__ == "__main__":
    run_new_machine_test()
