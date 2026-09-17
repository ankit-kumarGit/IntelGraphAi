import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class ConnectorStatus(BaseModel):
    connector_id: str
    name: str
    system_type: str  # ERP | CMMS | QMS | MES | IoT | DocumentRepository
    status: str  # Connected (Prototype/Mock Integration) | Active | Disconnected
    endpoint_target: str
    last_sync_timestamp: str
    records_synced_count: int
    is_demo_connector: bool = True
    health_latency_ms: float

class BaseEnterpriseConnector(ABC):
    def __init__(self, connector_id: str, name: str, system_type: str, endpoint: str):
        self.connector_id = connector_id
        self.name = name
        self.system_type = system_type
        self.endpoint = endpoint
        self.last_sync = time.strftime("%Y-%m-%d %H:%M:%S")
        self.sync_count = 0

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def sync_records(self, asset_tag: Optional[str] = None) -> Dict[str, Any]:
        pass

    def get_status(self) -> ConnectorStatus:
        t0 = time.time()
        conn_ok = self.test_connection()
        latency = round((time.time() - t0) * 1000, 2)
        return ConnectorStatus(
            connector_id=self.connector_id,
            name=self.name,
            system_type=self.system_type,
            status="Connected (Prototype/Mock Integration)" if conn_ok["connected"] else "Disconnected",
            endpoint_target=self.endpoint,
            last_sync_timestamp=self.last_sync,
            records_synced_count=self.sync_count,
            is_demo_connector=True,
            health_latency_ms=max(latency, 1.2)
        )

# 1. SAP Plant Maintenance (PM / ERP)
class SAPPMConnector(BaseEnterpriseConnector):
    def __init__(self):
        super().__init__(
            connector_id="conn_sap_pm",
            name="SAP S/4HANA Plant Maintenance (PM)",
            system_type="ERP / CMMS",
            endpoint="https://sap-gateway.industrial-net.local/odata/v4/MaintenanceService"
        )
        self.sync_count = 142

    def test_connection(self) -> Dict[str, Any]:
        return {"connected": True, "ping_ms": 1.4, "sap_system_id": "SAP_PRD_01"}

    def sync_records(self, asset_tag: Optional[str] = None) -> Dict[str, Any]:
        self.last_sync = time.strftime("%Y-%m-%d %H:%M:%S")
        return {
            "status": "success",
            "message": f"Prototype connector synchronized 4 open work orders from SAP PM for {asset_tag or 'all fleet assets'}.",
            "system": "SAP S/4HANA",
            "records_imported": 4
        }

# 2. IBM Maximo CMMS
class IBMMaximoConnector(BaseEnterpriseConnector):
    def __init__(self):
        super().__init__(
            connector_id="conn_ibm_maximo",
            name="IBM Maximo Enterprise CMMS",
            system_type="CMMS",
            endpoint="https://maximo.industrial-net.local/maxrest/os/mbo/workorder"
        )
        self.sync_count = 389

    def test_connection(self) -> Dict[str, Any]:
        return {"connected": True, "ping_ms": 2.1, "maximo_version": "7.6.1.2"}

    def sync_records(self, asset_tag: Optional[str] = None) -> Dict[str, Any]:
        self.last_sync = time.strftime("%Y-%m-%d %H:%M:%S")
        return {
            "status": "success",
            "message": "Prototype connector polled asset meter readings and planned PM work orders from IBM Maximo.",
            "system": "IBM Maximo",
            "records_imported": 7
        }

# 3. Veeva QMS (Quality Management System)
class VeevaQMSConnector(BaseEnterpriseConnector):
    def __init__(self):
        super().__init__(
            connector_id="conn_veeva_qms",
            name="Veeva Vault QualityDocs / QMS",
            system_type="QMS",
            endpoint="https://quality.industrial-net.local/api/v24.1/quality"
        )
        self.sync_count = 56

    def test_connection(self) -> Dict[str, Any]:
        return {"connected": True, "ping_ms": 3.8, "vault_status": "Active"}

    def sync_records(self, asset_tag: Optional[str] = None) -> Dict[str, Any]:
        self.last_sync = time.strftime("%Y-%m-%d %H:%M:%S")
        return {
            "status": "success",
            "message": "Synchronized approved SOP revisions and regulatory change controls from Veeva QMS.",
            "system": "Veeva QMS",
            "records_imported": 2
        }

# 4. Rockwell FactoryTalk MES (Manufacturing Execution System)
class RockwellMESConnector(BaseEnterpriseConnector):
    def __init__(self):
        super().__init__(
            connector_id="conn_rockwell_mes",
            name="Rockwell FactoryTalk MES / Production Intelligence",
            system_type="MES",
            endpoint="https://mes-api.industrial-net.local/v2/production"
        )
        self.sync_count = 512

    def test_connection(self) -> Dict[str, Any]:
        return {"connected": True, "ping_ms": 1.9, "system_id": "FTMES_PLANT_A"}

    def sync_records(self, asset_tag: Optional[str] = None) -> Dict[str, Any]:
        self.last_sync = time.strftime("%Y-%m-%d %H:%M:%S")
        return {
            "status": "success",
            "message": f"Polled unit production batches, operating runtime logs, and shift downtime events from MES for {asset_tag or 'Plant Unit 2'}.",
            "system": "Rockwell FactoryTalk MES",
            "records_imported": 8
        }

# 5. OSIsoft PI IoT Historian
class OSIsoftPIConnector(BaseEnterpriseConnector):
    def __init__(self):
        super().__init__(
            connector_id="conn_osisoft_pi",
            name="OSIsoft PI System / AVEVA IoT Historian",
            system_type="IoT",
            endpoint="https://pi-webapi.industrial-net.local/piwebapi"
        )
        self.sync_count = 12450

    def test_connection(self) -> Dict[str, Any]:
        return {"connected": True, "ping_ms": 0.8, "server_role": "Primary Historian"}

    def sync_records(self, asset_tag: Optional[str] = None) -> Dict[str, Any]:
        self.last_sync = time.strftime("%Y-%m-%d %H:%M:%S")
        return {
            "status": "success",
            "message": "Polled high-frequency 1-second telemetry stream points for vibration, temperature, and discharge pressure.",
            "system": "OSIsoft PI Historian",
            "records_imported": 60
        }

# 6. SharePoint Document Repository
class SharePointConnector(BaseEnterpriseConnector):
    def __init__(self):
        super().__init__(
            connector_id="conn_sharepoint",
            name="Microsoft SharePoint Document Center",
            system_type="DocumentRepository",
            endpoint="https://docs.industrial-net.local/sites/PlantEngineeringDocs"
        )
        self.sync_count = 88

    def test_connection(self) -> Dict[str, Any]:
        return {"connected": True, "ping_ms": 4.1, "library_status": "Synchronized"}

    def sync_records(self, asset_tag: Optional[str] = None) -> Dict[str, Any]:
        self.last_sync = time.strftime("%Y-%m-%d %H:%M:%S")
        return {
            "status": "success",
            "message": "Scanned SharePoint engineering libraries for newly released OEM manuals and engineering drawing updates.",
            "system": "SharePoint Online",
            "records_imported": 3
        }

class ConnectorsManager:
    def __init__(self):
        self.connectors: Dict[str, BaseEnterpriseConnector] = {
            "conn_sap_pm": SAPPMConnector(),
            "conn_ibm_maximo": IBMMaximoConnector(),
            "conn_veeva_qms": VeevaQMSConnector(),
            "conn_rockwell_mes": RockwellMESConnector(),
            "conn_osisoft_pi": OSIsoftPIConnector(),
            "conn_sharepoint": SharePointConnector()
        }

    def list_connectors(self) -> List[ConnectorStatus]:
        return [c.get_status() for c in self.connectors.values()]

    def trigger_sync(self, connector_id: str, asset_tag: Optional[str] = None) -> Dict[str, Any]:
        connector = self.connectors.get(connector_id)
        if not connector:
            return {"status": "error", "message": f"Connector {connector_id} not found."}
        return connector.sync_records(asset_tag=asset_tag)

    def export_action_to_cmms(
        self,
        action_id: str,
        action_title: str,
        asset_tag: str,
        target_system: str = "SAP_PM",  # "SAP_PM" | "IBM_MAXIMO" | "ROCKWELL_MES"
        operator: str = "Lead Maintenance Engineer",
        priority: str = "High",
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Clean adapter interface to dispatch an IntelGraph Action item
        to an external enterprise CMMS/ERP/MES system as an actionable work order or maintenance notification.
        """
        import uuid
        dispatch_ts = time.strftime("%Y-%m-%d %H:%M:%S")

        if target_system == "SAP_PM":
            ref_id = f"SAP-NOTIF-{uuid.uuid4().hex[:6].upper()}"
            connector = self.connectors.get("conn_sap_pm")
            sys_name = "SAP S/4HANA Plant Maintenance"
            msg = f"Created Maintenance Notification {ref_id} in SAP PM for asset {asset_tag}."
        elif target_system == "ROCKWELL_MES":
            ref_id = f"MES-HOLD-{uuid.uuid4().hex[:6].upper()}"
            connector = self.connectors.get("conn_rockwell_mes")
            sys_name = "Rockwell FactoryTalk MES"
            msg = f"Logged Production Maintenance Hold {ref_id} in MES for asset {asset_tag}."
        else:
            ref_id = f"MAX-WO-{uuid.uuid4().hex[:6].upper()}"
            connector = self.connectors.get("conn_ibm_maximo")
            sys_name = "IBM Maximo CMMS"
            msg = f"Generated Corrective Work Order {ref_id} in IBM Maximo for asset {asset_tag}."

        return {
            "status": "success",
            "is_mock_integration": True,
            "target_system": sys_name,
            "external_reference_id": ref_id,
            "action_id": action_id,
            "asset_tag": asset_tag,
            "dispatched_by": operator,
            "dispatched_at": dispatch_ts,
            "endpoint_dispatched": connector.endpoint if connector else "https://gateway.industrial-net.local",
            "message": msg,
            "notes": notes or f"Dispatched via IntelGraph AI Action Center: {action_title}"
        }

connectors_manager = ConnectorsManager()
