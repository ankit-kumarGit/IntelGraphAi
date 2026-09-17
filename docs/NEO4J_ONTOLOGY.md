# Neo4j Industrial Knowledge Graph Ontology & Schema

## 1. Architectural Overview
IntelGraphAI uses **Neo4j** as its primary structural entity and relationship brain. The knowledge graph encodes the physical, procedural, operational, regulatory, and causal interconnections across industrial machinery and technical documentation.

The service operates in dual-mode:
- **Live Bolt Cluster**: Connects to `bolt://localhost:7687` or remote enterprise Neo4j instances.
- **Embedded Cypher-Compatible Engine**: A persistent, file-backed engine (`storage/neo4j_graph.json`) that supports directional graph traversals, Cypher-pattern matching, multi-hop path expansion, and dynamic subgraph queries when a live cluster is not actively provisioned.

---

## 2. Core Entity Node Types
The ontology defines 22 primary industrial entity classes:

| Node Label | Description | Primary Attributes |
|:---|:---|:---|
| `Asset` | Physical machinery / industrial equipment | `id`, `tag`, `name`, `type`, `criticality`, `status`, `plant` |
| `Component` | Sub-assembly or mechanical part | `id`, `name`, `part_number`, `parent_asset_tag` |
| `EquipmentTag` | Instrument/equipment tag from P&ID | `id`, `tag_name`, `service_description`, `drawing_id` |
| `Document` | Governed industrial record/manual | `id`, `title`, `document_id`, `category`, `governance_status`, `version` |
| `DocumentChunk` | Semantic chunk for vector indexing | `id`, `chunk_id`, `page_number`, `section_title`, `document_id` |
| `Procedure` | Standard operating procedure (SOP) | `id`, `code`, `title`, `step_count`, `safety_critical` |
| `MaintenanceEvent` | Overhaul or corrective repair session | `id`, `event_id`, `date`, `technician`, `hours_at_service` |
| `WorkOrder` | CMMS / SAP maintenance ticket | `id`, `wo_number`, `status`, `priority`, `asset_tag` |
| `Inspection` | Condition monitoring survey / reading | `id`, `report_id`, `surveyor`, `vibration_mm_s`, `temp_c` |
| `Failure` | Unscheduled breakdown or trip | `id`, `failure_id`, `failure_mode`, `downtime_hours`, `date` |
| `Finding` | Operational anomaly or warning | `id`, `finding_id`, `severity`, `status`, `recommended_action` |
| `ComplianceRequirement`| Mandatory regulatory standard clause | `id`, `standard_code`, `clause`, `mandatory_evidence` |
| `Regulation` | Governing regulatory body / framework | `id`, `body_name`, `standard_family` |
| `ProcessParameter` | Operating limits (flow, head, power) | `id`, `name`, `design_value`, `unit`, `tolerance` |
| `TelemetrySignal` | Live IoT sensor reading channel | `id`, `sensor_tag`, `parameter`, `engineering_unit` |
| `HumanObservation` | Operator field shift log / note | `id`, `note_id`, `author`, `shift`, `content` |
| `Person/Role` | Plant personnel or certified role | `id`, `name`, `role`, `department`, `certifications` |
| `Site` | Industrial plant complex | `id`, `site_name`, `location`, `operational_status` |
| `System` | Plant operating subsystem (Unit) | `id`, `unit_name`, `site_id`, `process_fluid` |
| `Action` | Operational remediation task | `id`, `action_id`, `priority`, `owner`, `due_date` |
| `Recommendation` | AI / Engineering suggested action | `id`, `summary`, `confidence`, `source_agent` |
| `LessonLearned` | Fleet-wide reusable knowledge item | `id`, `lesson_id`, `failure_mode`, `preventive_protocol` |

---

## 3. Industrial Relationships (Edges)
All relationships maintain directional semantic integrity:

```text
(Asset)-[:ASSET_HAS_COMPONENT]->(Component)
(Asset)-[:ASSET_HAS_DOCUMENT]->(Document)
(Asset)-[:HAS_MAINTENANCE_EVENT]->(MaintenanceEvent)
(Asset)-[:HAS_WORK_ORDER]->(WorkOrder)
(Asset)-[:HAS_INSPECTION]->(Inspection)
(Asset)-[:HAS_FAILURE]->(Failure)
(Asset)-[:HAS_FINDING]->(Finding)
(Asset)-[:MEASURED_BY]->(TelemetrySignal)
(Asset)-[:GOVERNED_BY]->(ComplianceRequirement)

(Document)-[:DOCUMENT_HAS_CHUNK]->(DocumentChunk)
(Document)-[:DOCUMENT_DESCRIBES_ASSET]->(Asset)
(Document)-[:EVIDENCED_BY]->(ComplianceRequirement)

(Failure)-[:DOCUMENTS_FAILURE]->(WorkOrder)
(Failure)-[:RESULTED_IN]->(Finding)
(Failure)-[:ASSOCIATED_WITH]->(Component)
(Failure)-[:RESOLVED_BY]->(Action)
(Failure)-[:SIMILAR_TO]->(Failure)

(ComplianceRequirement)-[:REQUIRES]->(Procedure)
(ComplianceRequirement)-[:APPLIES_TO]->(Asset)
(ComplianceRequirement)-[:GOVERNED_BY]->(Regulation)

(MaintenanceEvent)-[:MAINTAINED_BY]->(Person)
(MaintenanceEvent)-[:HAS_WORK_ORDER]->(WorkOrder)
(MaintenanceEvent)-[:REPLACED_COMPONENT]->(Component)

(Finding)-[:EVIDENCED_BY]->(Inspection)
(Finding)-[:REQUIRES_ACTION]->(Action)
```

---

## 4. Graph Seeding & Current Statistics
- **Total Entities Seeded**: 51 nodes
- **Total Structural Relationships**: 59 relationships
- **Hero Machinery Nodes**:
  - `P-101`: Centrifugal Water Injection Pump
  - `P-102`: Standby High-Pressure Booster Pump
  - `P-203`: Secondary Water Injection Pump
  - `P-307`: Produced Water Disposal Pump
  - `C-201`: Flash Gas Compressor
  - `M-301`: Reboiler Circulation Pump
  - `P-205`: Slurry Circulation Pump
