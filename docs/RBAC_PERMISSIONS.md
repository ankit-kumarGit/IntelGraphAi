# Enterprise Role-Based Access Control (RBAC) & Separation of Duties Matrix

## 1. Overview & Principle of Separation of Duties (SoD)
IntelGraphAI strictly enforces server-side Role-Based Access Control (RBAC). Permissions are never delegated to the frontend UI; every state-modifying API endpoint independently verifies authorization and raises **HTTP 403 Forbidden** if an operator role attempts an unauthorized action.

The system incorporates the industrial Principle of **Separation of Duties (SoD)**:
- **Maintenance Engineers** log work orders and investigate findings, but cannot close operational overhaul actions or certify regulatory compliance packages.
- **Compliance Auditors** inspect evidence gaps and generate official audit dossiers, but cannot modify mechanical work orders.
- **Plant Managers** hold operational change approval authority to resolve critical actions across the fleet.
- **Administrators** hold global configuration, user management, and benchmark execution rights.

---

## 2. Enterprise Personas

| Persona Name | User ID | Role | Department | Plant Scope |
|:---|:---|:---|:---|:---|
| **Marcus Vance** | `usr_vance` | Maintenance Engineer | Mechanical Reliability & Overhauls | Plant A - Gulf Coast |
| **Elena Rostova** | `usr_rostova` | Plant Manager | Plant Operations Leadership | Fleet Operations (Plants A & B) |
| **David Chen** | `usr_chen` | Quality / Compliance Auditor | Quality Assurance & Regulatory Affairs | Corporate Audit & Compliance |
| **Sarah Jenkins** | `usr_jenkins` | Administrator | Industrial IT & Platform Governance | Global Industrial System Admin |

---

## 3. Discrete Permissions Matrix

| Permission Key | Maintenance Engineer | Plant Manager | Compliance Auditor | Administrator |
|:---|:---:|:---:|:---:|:---:|
| `view_assets` | ✓ | ✓ | ✓ | ✓ |
| `edit_assets` | ✓ | — | — | ✓ |
| `log_maintenance` | ✓ | — | — | ✓ |
| `add_operator_notes` | ✓ | ✓ | — | ✓ |
| `confirm_extraction` | ✓ | — | — | ✓ |
| `investigate_finding` | ✓ | — | — | ✓ |
| `prioritize_actions` | — | ✓ | — | ✓ |
| `assign_actions` | — | ✓ | — | ✓ |
| `approve_operational_change` | — | ✓ | — | ✓ |
| `view_cross_asset_trends` | ✓ | ✓ | ✓ | ✓ |
| `audit_compliance` | — | ✓ | ✓ | ✓ |
| `update_compliance_status` | — | — | ✓ | ✓ |
| `generate_audit_package` | — | — | ✓ | ✓ |
| `update_document_governance` | — | — | ✓ | ✓ |
| `admin_manage_users` | — | — | — | ✓ |
| `admin_configure_agents` | — | — | — | ✓ |
| `admin_configure_system` | — | — | — | ✓ |
| `admin_run_benchmarks` | — | — | — | ✓ |
| `admin_view_audit_logs` | — | — | — | ✓ |

---

## 4. Enforcement Mechanics
When an unauthorized role attempts to transition an action status (e.g. `PATCH /api/actions/{id}/status` to "Closed" by Marcus Vance):
1. `auth_service.require_permission("approve_operational_change", user_role)` raises `HTTPException(403)`.
2. The attempt is immediately recorded to `audit_logs` as an unauthorized access event.
3. The frontend displays an interactive **RBAC Separation of Duties Violation Modal**, informing the operator that operational resolution requires Plant Manager or Administrator credentials.
