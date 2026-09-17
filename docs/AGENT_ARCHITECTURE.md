# Multi-Agent AI Orchestrator Architecture

## 1. Architectural Swarm
IntelGraphAI replaces monolithic LLM handlers with a modular **Multi-Agent AI Orchestrator** comprising five specialized industrial intelligence agents:

```text
                        AIOrchestrator
                              │
       ┌──────────────────────┼──────────────────────┐
       │                      │                      │
ExpertKnowledgeAgent    MaintenanceAgent       RCAAgent
       │                      │                      │
       └────────────── ComplianceAgent ──────────────┘
                              │
                     LessonsLearnedAgent
```

---

## 2. Specialized Agent Roles & Contracts

### 1. ExpertKnowledgeAgent
- **Domain**: Technical specifications, OEM manuals, operating tolerances, design parameters, P&ID line connections, and safety/LOTO procedures.
- **Evidence Sources**: OEM manuals (`Pump_P101_OEM_Manual`), standard operating procedures (`SOP-101`), P&ID flowsheets (`Unit2_Process_PID_Flowsheet`).

### 2. MaintenanceIntelligenceAgent
- **Domain**: Work order history, overhaul records, replacement intervals, lead technicians, and recurring maintenance tasks.
- **Evidence Sources**: SAP/Maximo work orders (`WO-1023`, `WO-1189`, `WO-2031`, `WO-3042`), component logs.

### 3. RCAAgent (Root Cause Analysis)
- **Domain**: Failure incident correlation, 5-Why evidence reconstruction, vibration trend escalation, and causal hypothesis generation.
- **Strict Distinction**: Explicitly separates:
  - **OBSERVED**: Direct sensor readings & physical damage recorded in work orders.
  - **SUPPORTED BY RECORDS**: Manufacturer limits and past failure similarities.
  - **HYPOTHESIS**: AI causal inferences requiring human engineering validation.

### 4. ComplianceIntelligenceAgent
- **Domain**: API 610, ISO 10816-3, OISD 119, and PESO regulatory mapping, evidence gap detection, and regulatory audit package generation.
- **Output**: Official Audit Evidence Packages complete with cryptographic SHA-256 digital fingerprints.

### 5. LessonsLearnedAgent
- **Domain**: Fleet-wide cross-asset pattern discovery across P-101, P-102, P-203, and P-307.
- **Insight**: Identifies shared failure modes (e.g. bearing fatigue from extended runtime past 4,000h relubrication limit) across disparate machinery.

---

## 3. Orchestration Flow
When a query enters the system:
1. `AIOrchestrator` performs semantic intent classification to identify the primary and supporting agents required.
2. The orchestrator pulls relevant context from both Qdrant (vector chunks) and Neo4j (graph neighborhood).
3. The designated agent synthesizes the response using strict factual grounding rules.
4. If no verified records corroborate the query, the orchestrator triggers the refusal safety guardrail.
