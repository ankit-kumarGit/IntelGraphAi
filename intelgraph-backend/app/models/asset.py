from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Component(BaseModel):
    id: str
    name: str
    component_type: str = "Mechanical"
    part_number: Optional[str] = None
    serial_number: Optional[str] = None
    status: str = "Operational"
    installed_date: Optional[str] = None
    description: Optional[str] = None

class CompletenessItem(BaseModel):
    category: str
    label: str
    status: str  # "completed" | "missing" | "warning"
    document_id: Optional[str] = None
    details: Optional[str] = None

class AssetBase(BaseModel):
    tag: str
    name: str
    asset_type: str
    manufacturer: str
    model: str
    serial_number: str
    organization: str = "Apex Industrial Energy"
    sector: str = "Energy & Chemicals"
    plant: str = "Plant A - Gulf Coast"
    area: str = "Unit 2 - Fluid Processing"
    status: str = "Operational"  # Operational | Maintenance Due | Under Maintenance | Critical
    installation_date: Optional[str] = None
    criticality: str = "High"  # High | Medium | Low
    description: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)

class AssetCreate(AssetBase):
    components: List[Component] = Field(default_factory=list)

class Asset(AssetBase):
    components: List[Component] = Field(default_factory=list)
    completeness_score: int = 0
    completeness_breakdown: List[CompletenessItem] = Field(default_factory=list)
    open_findings_count: int = 0
    next_maintenance_date: Optional[str] = None
    last_maintenance_date: Optional[str] = None
    document_count: int = 0
