# Enterprise Integration Contracts & Adapters

## 1. Overview
IntelGraphAI provides production-grade integration interfaces for enterprise plant systems. For deployment environments without live enterprise credentials, the platform includes certified **Mock Connectors** that fulfill identical interface contracts and generate realistic synthetic industrial payloads.

All mock connectors are explicitly labeled with `is_demo_connector: true` and `(Demo Connector)` in UI consoles.

---

## 2. Standard Connector Interface Contract
Every enterprise connector inherits from the abstract base `EnterpriseConnector`:

```python
class EnterpriseConnector(ABC):
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Validates network connectivity and authentication tokens."""
        pass

    @abstractmethod
    def sync_records(self, asset_tag: Optional[str] = None) -> Dict[str, Any]:
        """Synchronizes external enterprise records into the platform."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Returns connector telemetry, latency, and synchronization stats."""
        pass
```

---

## 3. Implemented Enterprise Adapters

| Connector ID | Target Enterprise System | System Type | Mock Target Endpoint | Records Synced |
|:---|:---|:---|:---|:---|
| `conn_sap_pm` | **SAP S/4HANA Plant Maintenance (PM)** | ERP / CMMS | `https://sap-gateway.apex-energy.local/odata/v4/MaintenanceService` | 142 Work Orders |
| `conn_ibm_maximo` | **IBM Maximo Enterprise CMMS** | CMMS | `https://maximo.apex-energy.local/maxrest/os/mbo/workorder` | 389 Preventive Orders |
| `conn_veeva_qms` | **Veeva Vault QualityDocs / QMS** | QMS | `https://apex-energy.veevavault.com/api/v24.1/quality` | 56 SOPs & Audit Findings |
| `conn_osisoft_pi` | **OSIsoft PI System / AVEVA Historian** | IoT Historian | `https://pi-webapi.apex-energy.local/piwebapi` | 12,450 Telemetry Points |
| `conn_sharepoint` | **Microsoft SharePoint Document Center** | Document Repository | `https://apexenergy.sharepoint.com/sites/PlantEngineeringDocs` | 88 P&IDs / OEM Manuals |

---

## 4. Real-Time Synchronization API
- `GET /api/admin/connectors`: Lists all active connectors, endpoint targets, status, and records count.
- `POST /api/admin/connectors/{connector_id}/sync`: Triggers synchronization, increments record count, refreshes last sync timestamp, and logs the event to the immutable audit trail.
