from typing import Optional, Dict, Any
from pydantic import BaseModel

class AuditLogEntry(BaseModel):
    event_id: str
    timestamp: str
    user: str
    role: str
    action: str  # Document Ingested, Extraction Confirmed, Maintenance Logged, Status Changed, Note Added, Governance Updated
    target_type: str  # Asset, Document, Finding, Maintenance, Compliance, Note
    target_id: str
    details: str
