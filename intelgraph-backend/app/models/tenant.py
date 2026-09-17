from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Tenant(BaseModel):
    tenant_id: str
    name: str
    industry: str
    sites: List[str] = Field(default_factory=list)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: str = "2026-01-01T00:00:00Z"

class TenantContext(BaseModel):
    tenant_id: str
    tenant_name: str
    industry: str
    active_site: Optional[str] = None
