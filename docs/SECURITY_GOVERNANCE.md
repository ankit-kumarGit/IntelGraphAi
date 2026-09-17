# Security & Regulatory Compliance Governance

## 1. Regulatory Alignment (Conceptual & Architecture)
IntelGraphAI is engineered to align with global industrial standards and regulations:
- **API 610 (11th & 12th Editions)**: Centrifugal Pumps for Petroleum, Petrochemical, and Natural Gas Industries.
- **ISO 10816-3**: Mechanical Vibration — Evaluation of Machine Vibration by Measurements on Non-Rotating Parts.
- **ISO 27001**: Information Security Management System (ISMS) controls:
  - Role-based separation of duties (A.9.2.3)
  - Immutable audit trails (A.12.4.1)
  - Least privilege access principle (A.9.1.2)
- **OISD 119**: Oil Industry Safety Directorate standards for rotating equipment inspection and maintenance intervals.
- **PESO**: Petroleum and Explosives Safety Organisation compliance tracking for high-pressure plant machinery.

*Disclaimer: The platform provides architectural and procedural alignment tools; it does not claim third-party certification without formal accredited body audit.*

---

## 2. Cryptographic Audit Dossiers
When the Compliance Intelligence Agent issues an **Audit Evidence Package**, it generates an official verification dossier containing:
1. **Digital Package Identifier** (e.g. `PKG-2026-API610-P101`).
2. **Cryptographic SHA-256 Fingerprint**: Calculated across the canonicalized JSON payload of all cited evidence documents, inspection timestamps, and requirement clauses.
3. **Auditor Declaration**: Explicit statement of compliance based solely on verified engineering documentation.
4. **Itemized Evidence Matrix**: Direct mapping between standard clauses and verified engineering files.

---

## 3. Immutable System Audit Logging
All state-modifying actions produce real-time audit records stored in MongoDB and queryable via `/api/audit-logs`:
- User authentication & persona switching sessions
- Document uploads, OCR scans, and bounding-box entity confirmations
- Document governance transitions (Approved $\to$ Obsolete $\to$ Draft)
- Graph updates and Neo4j node/edge additions
- AI query requests and generated answers
- Action status updates with before/after state transitions
- Permission denied (HTTP 403) security violations
- Enterprise connector synchronizations
