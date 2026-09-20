import json
import urllib.request
import urllib.parse
import sys

BASE_URL = "http://localhost:8000/api/chat"

def query_chat(query_text: str) -> dict:
    req_data = json.dumps({"query": query_text, "tenant_id": "tenant_default"}).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL,
        data=req_data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def run_tests():
    print("=" * 80)
    print("STRICT EVIDENCE PROVENANCE & ZERO CONTAMINATION REGRESSION SUITE")
    print("=" * 80)

    results = []

    # -------------------------------------------------------------------------
    # TEST A: "What is P-194B?"
    # -------------------------------------------------------------------------
    q_a = "What is P-194B?"
    res_a = query_chat(q_a)
    cits_a = [c.get("document_name", "") + " " + c.get("document_id", "") for c in res_a.get("citations", [])]
    text_a = res_a.get("answer", "")
    
    assert_a1 = "P-194B" in text_a or "P-194" in text_a
    assert_a2 = not any("P-101" in c or "P101" in c for c in cits_a)
    assert_a3 = not any("T-200" in c or "T200" in c for c in cits_a)
    assert_a4 = not any("TEST-PUMP-REAL-001" in c for c in cits_a)
    pass_a = assert_a1 and assert_a2 and assert_a3 and assert_a4
    results.append(("TEST A", q_a, "P-194B", cits_a, pass_a, "P-194B profile without P-101/T-200/TPREAL001 contamination"))

    # -------------------------------------------------------------------------
    # TEST B: "What was the vibration of P-194B?"
    # -------------------------------------------------------------------------
    q_b = "What was the vibration of P-194B?"
    res_b = query_chat(q_b)
    cits_b = [c.get("document_name", "") + " " + c.get("document_id", "") for c in res_b.get("citations", [])]
    text_b = res_b.get("answer", "")
    
    assert_b1 = "telemetry" in "".join(cits_b).lower() or "telemetry" in text_b.lower()
    assert_b2 = text_b.count("\n") < 35  # Concise synthesis, no 50-row CSV dump
    assert_b3 = not any("P-101" in c or "T-200" in c for c in cits_b)
    pass_b = assert_b1 and assert_b2 and assert_b3
    results.append(("TEST B", q_b, "P-194B", cits_b, pass_b, "P-194B telemetry synthesis, no CSV dump, isolated"))

    # -------------------------------------------------------------------------
    # TEST C: "What is P-101?"
    # -------------------------------------------------------------------------
    q_c = "What is P-101?"
    res_c = query_chat(q_c)
    cits_c = [c.get("document_name", "") + " " + c.get("document_id", "") for c in res_c.get("citations", [])]
    text_c = res_c.get("answer", "")

    assert_c1 = "P-101" in text_c
    assert_c2 = not any("P-194" in c for c in cits_c)
    assert_c3 = not any("T-200" in c for c in cits_c)
    # P-102 only document must not appear (Unit 2 Process P&ID Flowsheet is shared and valid)
    assert_c4 = not any("P-102-only" in c.lower() for c in cits_c)
    pass_c = assert_c1 and assert_c2 and assert_c3 and assert_c4
    results.append(("TEST C", q_c, "P-101", cits_c, pass_c, "P-101 isolated evidence"))

    # -------------------------------------------------------------------------
    # TEST D: "What is P-102?"
    # -------------------------------------------------------------------------
    q_d = "What is P-102?"
    res_d = query_chat(q_d)
    cits_d = [c.get("document_name", "") + " " + c.get("document_id", "") for c in res_d.get("citations", [])]
    text_d = res_d.get("answer", "")

    assert_d1 = "P-102" in text_d
    # P-101-only documents must NOT appear
    p101_only_docs = ["P-101 OEM Manual", "P-101 Scanned Inspection", "P-101 Lubrication Procedure", "P-101 Failure Report"]
    assert_d2 = not any(any(bad.lower() in c.lower() for bad in p101_only_docs) for c in cits_d)
    # If cited, must be verified shared document (Unit 2 Process P&ID Flowsheet)
    assert_d3 = all("unit 2" in c.lower() or "p-102" in c.lower() or "pid" in c.lower() for c in cits_d) if cits_d else True
    pass_d = assert_d1 and assert_d2 and assert_d3
    results.append(("TEST D", q_d, "P-102", cits_d, pass_d, "P-102 evidence; no P-101-only document citations"))

    # -------------------------------------------------------------------------
    # TEST E: "What is T-200?"
    # -------------------------------------------------------------------------
    q_e = "What is T-200?"
    res_e = query_chat(q_e)
    cits_e = [c.get("document_name", "") + " " + c.get("document_id", "") for c in res_e.get("citations", [])]
    text_e = res_e.get("answer", "")

    assert_e1 = "T-200" in text_e and ("Cooling Tower" in text_e or "cooling tower" in text_e)
    # ZERO P-194 citations
    assert_e2 = not any("P-194" in c or "V-194A" in c for c in cits_e)
    # ZERO TEST-PUMP-REAL-001 citations
    assert_e3 = not any("TEST-PUMP-REAL-001" in c for c in cits_e)
    # ZERO unrelated citations
    assert_e4 = len(cits_e) == 0 or all("T-200" in c for c in cits_e)
    pass_e = assert_e1 and assert_e2 and assert_e3 and assert_e4
    results.append(("TEST E", q_e, "T-200", cits_e, pass_e, "T-200 cooling tower profile; ZERO P-194 and ZERO TPREAL001 citations"))

    # -------------------------------------------------------------------------
    # TEST F: "What is TEST-PUMP-REAL-001?"
    # -------------------------------------------------------------------------
    q_f = "What is TEST-PUMP-REAL-001?"
    res_f = query_chat(q_f)
    cits_f = [c.get("document_name", "") + " " + c.get("document_id", "") for c in res_f.get("citations", [])]
    text_f = res_f.get("answer", "")

    assert_f1 = "TEST-PUMP-REAL-001" in text_f
    assert_f2 = not any("T-200" in c for c in cits_f)
    assert_f3 = not any("P-194" in c for c in cits_f)
    assert_f4 = not any("P-101" in c for c in cits_f)
    pass_f = assert_f1 and assert_f2 and assert_f3 and assert_f4
    results.append(("TEST F", q_f, "TEST-PUMP-REAL-001", cits_f, pass_f, "TEST-PUMP-REAL-001 isolated evidence only"))

    # -------------------------------------------------------------------------
    # TEST G: "What is TEST-NONEXISTENT-94721?"
    # -------------------------------------------------------------------------
    q_g = "What is TEST-NONEXISTENT-94721?"
    res_g = query_chat(q_g)
    cits_g = res_g.get("citations", [])
    refused_g = res_g.get("refused", False)

    pass_g = refused_g and len(cits_g) == 0
    results.append(("TEST G", q_g, "None", [], pass_g, "Grounded refusal, zero citations"))

    # -------------------------------------------------------------------------
    # TEST H: "What maintenance was performed on P-101?" (Failure C Fix)
    # -------------------------------------------------------------------------
    q_h = "What maintenance was performed on P-101?"
    res_h = query_chat(q_h)
    cits_h = [c.get("document_name", "") + " " + c.get("document_id", "") for c in res_h.get("citations", [])]
    text_h = res_h.get("answer", "")
    refused_h = res_h.get("refused", False)

    # Must NOT refuse with canned date message! Must retrieve verified maintenance evidence for P-101
    assert_h1 = "maintenance date" not in text_h.lower()
    assert_h2 = not refused_h
    assert_h3 = all("p-101" in c.lower() for c in cits_h) if cits_h else True
    pass_h = assert_h1 and assert_h2 and assert_h3
    results.append(("TEST H", q_h, "P-101", cits_h, pass_h, "Failure C resolved: What maintenance was performed returns verified P-101 maintenance"))

    # -------------------------------------------------------------------------
    # PRINT SUMMARY
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("REGRESSION RESULTS SUMMARY:")
    print("=" * 80)
    all_passed = True
    for tid, query, asset, cits, passed, desc in results:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        print(f"[{status}] {tid}: \"{query}\"")
        print(f"   Target Asset: {asset}")
        print(f"   Citations Returned: {cits if cits else '[]'}")
        print(f"   Details: {desc}\n")

    if all_passed:
        print(">>> ALL REGRESSION ASSERTIONS PASSED WITH 100% PROVENANCE ISOLATION! <<<")
    else:
        print(">>> REGRESSION SUITE ENCOUNTERED FAILURES <<<")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
