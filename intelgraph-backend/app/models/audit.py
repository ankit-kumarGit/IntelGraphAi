from typing import Optional, Dict, Any, Union
from pydantic import BaseModel

class AuditLogEntry(BaseModel):
    event_id: str
    timestamp: str
    user: str
    role: str
    action: str  # Document Ingested, Extraction Confirmed, Maintenance Logged, Status Changed, Note Added, Governance Updated, MACHINE_DELETED
    target_type: str  # Asset, Document, Finding, Maintenance, Compliance, Note
    target_id: str
    details: Union[str, Dict[str, Any]]
