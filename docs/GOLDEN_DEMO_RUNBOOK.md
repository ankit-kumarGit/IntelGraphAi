# Golden Demo Runbook — Step-by-Step Operator Guide

This runbook guides evaluators and Deloitte invigilators through the end-to-end capabilities of **IntelGraphAI — The Unified Asset & Operations Brain**.

---

## Pre-Requisites & Services Verification
1. Ensure the platform is running:
   - Backend: `http://localhost:8000/docs` (FastAPI)
   - Frontend: `http://localhost:5173/` (Vite React)
   - MongoDB: Port `27017`
2. In the top bar, verify the indicator:
   - `Grounded in approved records` (Green)
   - `GraphRAG (Neo4j + Qdrant)` (Cyan pulse)

---

## Scenario 1: Existing Machine Brain (P-101)
1. Navigate to **Assets** in the sidebar. Select **P-101 (Centrifugal Water Injection Pump)**.
2. Observe the **Machine Brain** layout answering:
   - *What is this machine?* (API 610 Centrifugal Pump, Model XYZ-200, 75 kW).
   - *What is happening?* (Critical vibration anomaly on drive-end bearing).
   - *Why?* (Operating past 4,000h relubrication interval per WO-1189).
   - *What evidence supports it?* (Direct links to OEM Manual, WO-1023, Inspection INSP-492).
   - *What needs attention?* (Drive-End Bearing replacement and laser coupling alignment).
3. Click on the **Knowledge Graph** tab:
   - Explore the real graph visualization (51 nodes, 59 edges).
   - Filter by Components, Documents, or Failures.
   - Click any node to open the **Entity Inspector** showing type, relationships, source document, and confidence.

---

## Scenario 2: Expert Copilot & "Ask Knowledge AI"
1. Click the purple **"Ask Knowledge AI"** button in the top navigation or use `Cmd+K`.
2. Ask the expert question:
   > *"What is the drive motor power rating for P-101?"*
   - Response: `75 kW Induction Motor` with direct citation to `Pump_P101_OEM_Manual`, Page 1.
3. Ask a technical tolerance question:
   > *"What coupling alignment tolerance is specified in SOP-101?"*
   - Response: `Maximum allowable radial angular misalignment: 0.05 mm` with citation to `SOP-101`, Page 3.
4. Test the strict refusal guardrail:
   > *"What is the replacement schedule for the titanium submarine propeller on P-101?"*
   - Response: `I could not find sufficient information in the available industrial records.` Zero hallucination.

---

## Scenario 3: Fleet-Wide Cross-Asset Intelligence & RCA
1. Navigate to **Reports** in the sidebar.
2. In the **AI-Assisted Root Cause Analysis Studio**, select **P-101** and click **Run Analysis**:
   - Inspect the reconstructed timeline: `WO-1023 (March 2024)` $\to$ `INSP-492 (Jan 2026)` $\to$ `WO-1189 (Feb 2026)`.
   - Review supported root causes: Extended runtime past relubrication threshold (92% confidence).
3. Scroll to **Fleet-Wide Failure Intelligence & Correlation**:
   - Observe recurring bearing fatigue detected across **all 4 hero machinery assets**: `P-101`, `P-102`, `P-203`, and `P-307`.
   - Read the recommended fleet action: *Mandate lubrication compliance reviews across Gulf Coast Unit 2 before reaching 4,000h service interval.*

---

## Scenario 4: Regulatory Compliance & Audit Evidence Package Generation
1. Navigate to **Compliance** in the sidebar.
2. Select target machine **P-101**.
3. Notice the compliance summary: 3 standard requirements evaluated against API 610, ISO 10816-3, and OISD 119.
4. Click **"Generate Audit Evidence Package"**:
   - The official regulatory modal opens with package ID `PKG-2026-API610-P101`.
   - View the cryptographic **SHA-256 digital fingerprint**.
   - Review the itemized requirement-to-evidence matrix.
   - Click **"Download Audit Package (.json)"** to export the verified evidence dossier.

---

## Scenario 5: Server-Enforced RBAC & Separation of Duties (SoD)
1. In the Topbar, click **VIEW AS (DEMO MODE)**. Select **Marcus Vance (Maintenance Engineer)**.
2. Navigate to **Action Center**.
3. Select an open critical action item (e.g. `ACT-01: P-101 Drive-End Bearing Replacement`).
4. Attempt to change the Status from `Open` to **`Closed`**:
   - **Result**: The server returns **HTTP 403 Forbidden**.
   - The interactive **RBAC Authorization Denied** modal pops up:
     > *"Separation of Duties Policy Violation: Role 'Maintenance Engineer' cannot transition action items to 'Closed'. Resolving or closing overhaul actions requires Plant Manager or Administrator authorization."*
5. Now, switch persona in the Topbar to **Elena Rostova (Plant Manager)**.
6. Try changing the status to **`Resolved`** or **`Closed`**:
   - **Result**: Status transitions smoothly to `Closed` with green badge confirmation, logged in the audit trail!

---

## Scenario 6: Admin Console & System Health
1. Navigate to **Admin** in the sidebar.
2. **System Health**:
   - Review live telemetry: Neo4j (51 nodes, 59 relationships), Qdrant (`industrial_kb`, 12 points), MongoDB (7 assets, 8 documents), Multi-Agent AI Orchestrator (5 active agents).
3. **Enterprise Connectors**:
   - Inspect SAP PM, IBM Maximo, Veeva Vault QMS, OSIsoft PI, and Microsoft SharePoint connectors.
   - Click **"Sync Now"** on SAP S/4HANA PM: observes real-time record count update and audit log recording.
4. **Users & RBAC**:
   - Inspect the 4 enterprise personas, departments, and discrete permissions.
5. **Evaluation Dashboard**:
   - Click **"Run 25-Question Benchmark"**.
   - Watch the platform evaluate all 25 benchmark queries, achieving **25/25 (100.0%) passed** with sub-millisecond answer latency.
