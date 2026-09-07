from typing import Optional, List
from pydantic import BaseModel, Field

class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    asset_tag: str
    page_number: int = 1
    section_title: str = "General"
    content: str
    record_date: Optional[str] = None
    category: str = "Other"
    version: str = "v1.0"
    governance_status: str = "Approved"

class Document(BaseModel):
    document_id: str
    title: str
    filename: str
    file_type: str  # pdf, docx, xlsx, csv, pid, txt
    category: str  # OEM Manual, SOP, Maintenance, Inspection, Incident, Engineering, Safety, Regulatory, P&ID, Other
    asset_tag: str
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
