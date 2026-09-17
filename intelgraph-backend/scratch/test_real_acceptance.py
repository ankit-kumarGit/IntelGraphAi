import httpx
import json

BASE_URL = "http://localhost:8000"

client = httpx.Client(timeout=30.0)

def query_chat(q, asset_tag="P-194B"):
    res = client.post(
        f"{BASE_URL}/api/chat",
        json={
            "query": q,
            "asset_tag": asset_tag,
            "tenant_id": "tenant_default"
        }
    )
    if res.status_code != 200:
        print(f"Error {res.status_code}: {res.text}")
        return None
    data = res.json()
    print(f"\n========================================================")
    print(f"QUERY: {q} [Asset: {asset_tag}]")
    print(f"ANSWER: {data.get('answer')}")
    print(f"REFUSED: {data.get('refused')}")
    print(f"CITATIONS ({len(data.get('citations', []))}):")
    for c in data.get("citations", []):
        print(f"  - Document: {c.get('document_name')} | Page: {c.get('page_number')} | Excerpt: {c.get('excerpt')[:100]}...")
    return data

if __name__ == "__main__":
    # Test 1: Inspection Date
    q1 = query_chat("What was the inspection date of P-194B?", "P-194B")

    # Test 2: Maintenance Date
    q2 = query_chat("What was the maintenance date of P-194B?", "P-194B")

    # Test 3: Inspection Condition
    q3 = query_chat("What was the inspection condition of P-194B?", "P-194B")

    # Test 4: Maintenance Work
    q4 = query_chat("What was done during maintenance on P-194B?", "P-194B")

    # Test 5: Shift Handover
    q5 = query_chat("What happened during the shift handover for P-194B?", "P-194B")
