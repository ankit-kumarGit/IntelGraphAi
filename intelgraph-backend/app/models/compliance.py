from typing import Optional, List
from pydantic import BaseModel

class ComplianceRequirement(BaseModel):
    req_id: str
    title: str
    regulatory_body: str  # OSHA, API 610, ISO 14224, Site Safety Standard
    requirement_type: str  # Inspection, Calibration, Overhaul, Safety LOTO
    target_asset_types: List[str]
    description: str
    required_evidence_type: str
    frequency_days: int

class ComplianceAuditItem(BaseModel):
    audit_id: str
    asset_tag: str
    requirement_id: str
    requirement_title: str
    regulatory_body: str
    required_evidence: str
    available_evidence: Optional[str] = None
    evidence_document_id: Optional[str] = None
    status: str  # Compliant | Missing Evidence | Pending Review
    last_evaluated: str
