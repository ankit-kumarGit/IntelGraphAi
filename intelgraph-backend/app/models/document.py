from typing import Optional, List
from pydantic import BaseModel, Field

class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    asset_tag: str
    document_scope: str = "ASSET"  # ASSET, SYSTEM, MULTI_ASSET, UNKNOWN
    primary_asset_tags: List[str] = Field(default_factory=list)
    related_asset_tags: List[str] = Field(default_factory=list)
    page_number: int = 1
    section_title: str = "General"
    content: str
    record_date: Optional[str] = None
    category: str = "Other"
    version: str = "v1.0"
    governance_status: str = "Approved"
    tenant_id: Optional[str] = "tenant_default"

class Document(BaseModel):
    model_config = {"protected_namespaces": ()}

    document_id: str
    title: str
    filename: str
    file_type: str  # pdf, docx, xlsx, csv, pid, txt
    category: str  # OEM Manual, SOP, Maintenance, Inspection, Incident, Engineering, Safety, Regulatory, P&ID, Other
    asset_tag: str  # Maintained for legacy compatibility (primary asset or first primary tag)
    document_scope: str = "ASSET"  # ASSET, SYSTEM, MULTI_ASSET, UNKNOWN
    primary_asset_tags: List[str] = Field(default_factory=list)
    related_asset_tags: List[str] = Field(default_factory=list)
    component_tags: List[str] = Field(default_factory=list)
    document_number: Optional[str] = None
    model_number: Optional[str] = None
    extraction_confidence: Optional[dict] = None
    evidence_snippets: List[str] = Field(default_factory=list)
    association_status: str = "AUTO_RESOLVED"  # AUTO_RESOLVED, USER_CONFIRMED, REVIEW_REQUIRED
    version: str = "v1.0"
    effective_date: Optional[str] = None
    review_date: Optional[str] = None
    governance_status: str = "Approved"  # Approved, Draft, Under Review, Obsolete, Unverified
    summary: Optional[str] = None
    file_path: Optional[str] = None
    file_size_bytes: int = 0
    uploaded_by: str = "Engineering System"
    upload_date: str
    chunk_count: int = 0
    extracted_entities: Optional[dict] = None
    is_pid_drawing: bool = False
    sha256_hash: Optional[str] = None
    tenant_id: Optional[str] = "tenant_default"
    ocr_engine_used: Optional[str] = None
    ocr_engine_version: Optional[str] = None
    operated_on_pixels: Optional[bool] = None
    ocr_confidence: Optional[float] = None
