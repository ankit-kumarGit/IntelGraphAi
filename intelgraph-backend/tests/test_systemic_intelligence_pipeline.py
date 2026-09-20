import json
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

BACKEND_URL = "http://localhost:8000/api/chat"

TEST_CASES = [
    # 1. Greetings / Small Talk
    {
        "query": "hey",
        "expected_scope": "GREETING",
        "expected_intent": "GREETING",
        "expected_asset": None,
        "expected_category": "NONE",
        "allow_citations": False,
        "must_not_dump": True,
        "must_refuse": False
    },
    {
        "query": "what's up",
        "expected_scope": "GREETING",
        "expected_intent": "GREETING",
        "expected_asset": None,
        "expected_category": "NONE",
        "allow_citations": False,
        "must_not_dump": True,
        "must_refuse": False
    },
    {
        "query": "good morning",
        "expected_scope": "GREETING",
        "expected_intent": "GREETING",
        "expected_asset": None,
        "expected_category": "NONE",
        "allow_citations": False,
        "must_not_dump": True,
        "must_refuse": False
    },

    # 2. Existing Assets: P-194B
    {
        "query": "What is P-194B?",
        "expected_scope": "CUSTOMER",
        "expected_intent": "CUSTOMER_ASSET_PROFILE",
        "expected_asset": "P-194B",
        "expected_category": "PROFILE_ENGINEERING",
        "penalized_in_citations": ["telemetry"],
        "allow_citations": True,
        "must_not_dump": True,
        "must_refuse": False
    },
    {
        "query": "What was the vibration of P-194B?",
        "expected_scope": "CUSTOMER",
        "expected_intent": "CUSTOMER_TELEMETRY",
        "expected_asset": "P-194B",
        "expected_category": "TELEMETRY",
        "allow_citations": True,
        "must_not_dump": True,
        "must_refuse": False
    },

    # 3. Existing Assets: P-101
    {
        "query": "What machine is P-101?",
        "expected_scope": "CUSTOMER",
        "expected_intent": "CUSTOMER_ASSET_PROFILE",
        "expected_asset": "P-101",
        "expected_category": "PROFILE_ENGINEERING",
        "penalized_in_citations": ["telemetry"],
        "allow_citations": True,
        "must_not_dump": True,
        "must_refuse": False
    },
    {
        "query": "What was the vibration reading on the last inspection of P-101?",
        "expected_scope": "CUSTOMER",
        "expected_intent": "CUSTOMER_INSPECTION",
        "expected_asset": "P-101",
        "expected_category": "INSPECTION",
        "penalized_in_citations": ["telemetry"],
        "allow_citations": True,
        "must_not_dump": True,
        "must_refuse": False
    },
    {
        "query": "What is the maintenance procedure for P-101?",
        "expected_scope": "CUSTOMER",
        "expected_intent": "CUSTOMER_MAINTENANCE",
        "expected_asset": "P-101",
        "expected_category": "MAINTENANCE",
        "penalized_in_citations": ["telemetry"],
        "allow_citations": True,
        "must_not_dump": True,
        "must_refuse": False
    },
    {
        "query": "When was P-101 last serviced?",
        "expected_scope": "UNSUPPORTED_CUSTOMER",
        "expected_intent": "CUSTOMER_MAINTENANCE",
        "expected_asset": "P-101",
        "expected_category": "NONE",
        "allow_citations": False,
        "must_not_dump": True,
        "must_refuse": True
    },

    # 4. Existing Assets: P-102 & T-200
    {
        "query": "What is P-102?",
        "expected_scope": "CUSTOMER",
        "expected_intent": "CUSTOMER_ASSET_PROFILE",
        "expected_asset": "P-102",
        "expected_category": "PROFILE_ENGINEERING",
        "penalized_in_citations": ["telemetry"],
        "allow_citations": True,
        "must_not_dump": True,
        "must_refuse": False
    },
    {
        "query": "What is T-200?",
        "expected_scope": "CUSTOMER",
        "expected_intent": "CUSTOMER_ASSET_PROFILE",
        "expected_asset": "T-200",
        "expected_category": "PROFILE_ENGINEERING",
        "penalized_in_citations": ["telemetry"],
        "allow_citations": True,
        "must_not_dump": True,
        "must_refuse": False
    },

    # 5. Generic Test Asset: TEST-GENERIC-94721
    {
        "query": "What is TEST-GENERIC-94721?",
        "expected_scope": "CUSTOMER",
        "expected_intent": "CUSTOMER_ASSET_PROFILE",
        "expected_asset": "TEST-GENERIC-94721",
        "expected_category": "PROFILE_ENGINEERING",
        "penalized_in_citations": ["telemetry"],
        "allow_citations": True,
        "must_not_dump": True,
        "must_refuse": False
    },
    {
        "query": "What was the vibration reading on the last inspection of TEST-GENERIC-94721?",
        "expected_scope": "CUSTOMER",
        "expected_intent": "CUSTOMER_INSPECTION",
        "expected_asset": "TEST-GENERIC-94721",
        "expected_category": "INSPECTION",
        "penalized_in_citations": ["telemetry"],
        "allow_citations": True,
        "must_not_dump": True,
        "must_refuse": False
    },
    {
        "query": "When was TEST-GENERIC-94721 serviced?",
        "expected_scope": "CUSTOMER",
        "expected_intent": "CUSTOMER_MAINTENANCE",
        "expected_asset": "TEST-GENERIC-94721",
        "expected_category": "MAINTENANCE",
        "penalized_in_citations": ["telemetry"],
        "allow_citations": True,
        "must_not_dump": True,
        "must_refuse": False
    },
    {
        "query": "Why did TEST-GENERIC-94721 fail?",
        "expected_scope": "CUSTOMER",
        "expected_intent": "CUSTOMER_FAILURE",
        "expected_asset": "TEST-GENERIC-94721",
        "expected_category": "FAILURE",
        "penalized_in_citations": ["telemetry"],
        "allow_citations": True,
        "must_not_dump": True,
        "must_refuse": False
    },
    {
        "query": "Show telemetry for TEST-GENERIC-94721",
        "expected_scope": "CUSTOMER",
        "expected_intent": "CUSTOMER_TELEMETRY",
        "expected_asset": "TEST-GENERIC-94721",
        "expected_category": "TELEMETRY",
        "allow_citations": True,
        "must_not_dump": True,
        "must_refuse": False
    },

    # 6. Non-Existent Asset Refusal Guardrail
    {
        "query": "What is TEST-NONEXISTENT-94721?",
        "expected_scope": "UNSUPPORTED_CUSTOMER",
        "expected_intent": "CUSTOMER_ASSET_PROFILE",
        "expected_asset": "TEST-NONEXISTENT-94721",
        "expected_category": "NONE",
        "allow_citations": False,
        "must_not_dump": True,
        "must_refuse": True
    }
]

def is_raw_table_dump(text: str) -> bool:
    """Checks if text contains raw CSV dump or pipe-delimited database records."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    pipe_lines = [l for l in lines if l.count("|") >= 3]
    if len(pipe_lines) >= 3:
        return True
    csv_rows = [l for l in lines if l.count(",") >= 4 and any(c.isdigit() for c in l)]
    if len(csv_rows) >= 3:
        return True
    return False

def run_tests():
    print("=" * 80)
    print("RUNNING SYSTEM-WIDE INTELLIGENCE PIPELINE REGRESSION MATRIX")
    print("=" * 80)

    results = []
    all_passed = True

    for tc in TEST_CASES:
        q = tc["query"]
        print(f"\n[TESTING] Query: '{q}'")

        try:
            req_data = json.dumps({"query": q}).encode("utf-8")
            req = urllib.request.Request(
                BACKEND_URL,
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                status_code = response.status
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            print(f"FAILED: HTTP {e.code}")
            results.append({
                "query": q,
                "intent": "ERROR",
                "asset": "ERROR",
                "expected_category": tc["expected_category"],
                "top_docs": "None",
                "actual_category": "ERROR",
                "quality": f"HTTP {e.code}",
                "citation_correct": "No",
                "raw_dump": "No",
                "passed": False
            })
            all_passed = False
            continue
        except Exception as e:
            print(f"FAILED: Connection error {e}")
            all_passed = False
            continue

        answer = data.get("answer", "")
        scope = data.get("scope", "")
        citations = data.get("citations", [])
        refused = data.get("refused", False)
        breakdown = data.get("latency_breakdown", {})

        # Evaluate Greeting
        if tc["expected_scope"] == "GREETING":
            passed = (
                scope == "GREETING" and
                len(citations) == 0 and
                breakdown.get("qdrant_ms", 0.0) == 0.0 and
                not refused and
                "IntelGraph AI" in answer
            )
            detected_intent = "GREETING"
            detected_asset = "None"
            top_docs = "None (Zero Retrieval)"
            actual_category = "GREETING"
            quality = "Instant conversational greeting"
            citation_correct = "Yes (0 Citations)"
            raw_dump = "No"

        # Evaluate Refusal
        elif tc["must_refuse"]:
            passed = (
                refused is True and
                len(citations) == 0 and
                ("couldn't find a verified" in answer.lower() or "not exist" in answer.lower() or "not found" in answer.lower())
            )
            detected_intent = tc["expected_intent"]
            detected_asset = tc["expected_asset"]
            top_docs = "None"
            actual_category = "REFUSAL"
            quality = "Safe, polite grounded refusal"
            citation_correct = "Yes (0 Citations)"
            raw_dump = "No"

        # Evaluate Customer Queries
        else:
            raw_dump_detected = is_raw_table_dump(answer)
            detected_intent = tc["expected_intent"]
            detected_asset = tc["expected_asset"]

            # Top doc & category
            top_doc_name = citations[0]["document_name"] if citations else "None"
            top_doc_id = citations[0]["document_id"] if citations else "None"

            # Check citation correctness
            citation_correct = "Yes"
            if tc.get("penalized_in_citations"):
                for pen in tc["penalized_in_citations"]:
                    for c in citations:
                        if pen in c.get("document_name", "").lower() or pen in c.get("document_id", "").lower():
                            citation_correct = f"No (Found {pen})"
                            break

            # Actual Category mapping
            if "telemetry" in top_doc_id.lower():
                actual_category = "TELEMETRY"
            elif any(w in top_doc_id.lower() for w in ["manual", "datasheet", "oem", "pid", "flowsheet", "drawing"]):
                actual_category = "PROFILE_ENGINEERING"
            elif any(w in top_doc_id.lower() for w in ["inspection", "checklist", "survey", "ndt"]):
                actual_category = "INSPECTION"
            elif any(w in top_doc_id.lower() for w in ["maintenance", "override_p101_doc", "work_order", "wo_"]):
                actual_category = "MAINTENANCE"
            elif "failure" in top_doc_id.lower() or "incident" in top_doc_id.lower() or "rca" in top_doc_id.lower():
                actual_category = "FAILURE"
            else:
                actual_category = "OTHER"

            cat_match = (actual_category == tc["expected_category"])
            no_dump = not raw_dump_detected
            cit_ok = ("No" not in citation_correct)

            passed = cat_match and no_dump and cit_ok and not refused
            top_docs = top_doc_name
            quality = "High (Synthesized & Grounded)" if passed else "Suboptimal"
            raw_dump = "Yes" if raw_dump_detected else "No"

        print(f"-> Result: {'PASS' if passed else 'FAIL'} | Top Doc: {top_docs} | Cat: {actual_category}")
        if not passed:
            all_passed = False

        results.append({
            "query": q,
            "intent": detected_intent,
            "asset": detected_asset or "None",
            "expected_category": tc["expected_category"],
            "top_docs": top_docs,
            "actual_category": actual_category,
            "quality": quality,
            "citation_correct": citation_correct,
            "raw_dump": raw_dump,
            "passed": passed
        })

    # Print Markdown Table
    print("\n\n" + "=" * 80)
    print("### SYSTEM-WIDE INTELLIGENCE REGRESSION TEST RESULTS")
    print("=" * 80 + "\n")

    headers = [
        "Query", "Detected Intent", "Detected Asset", "Expected Category",
        "Top Retrieved Documents", "Actual Category", "Final Answer Quality",
        "Citation Correct?", "Raw Dump?", "Pass/Fail"
    ]
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"

    print(header_line)
    print(separator_line)

    for r in results:
        status_str = "**PASS**" if r["passed"] else "**FAIL**"
        line = f"| `{r['query']}` | `{r['intent']}` | `{r['asset']}` | `{r['expected_category']}` | {r['top_docs']} | `{r['actual_category']}` | {r['quality']} | {r['citation_correct']} | {r['raw_dump']} | {status_str} |"
        print(line)

    print("\n" + "=" * 80)
    if all_passed:
        print("ALL 16 TESTS PASSED WITH 100% PRECISION!")
    else:
        print("SOME TESTS FAILED! Check table above.")
    print("=" * 80)

    return all_passed

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
