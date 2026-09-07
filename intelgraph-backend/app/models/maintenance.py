from typing import Optional, List
from pydantic import BaseModel, Field

class MaintenanceRecord(BaseModel):
    record_id: str
    asset_tag: str
    work_order_number: str
    record_type: str = "Preventive"  # Preventive, Corrective, Overhaul, Emergency
    date: str
    technician: str
    description: str
    components_replaced: List[str] = Field(default_factory=list)
    hours_spent: float = 0.0
    findings: Optional[str] = None
    document_ref: Optional[str] = None
    status: str = "Completed"

class InspectionRecord(BaseModel):
    inspection_id: str
    asset_tag: str
    date: str
    inspector: str
    inspection_type: str = "Routine Condition Monitoring"
    parameters_checked: List[str] = Field(default_factory=list)
    observations: str
    vibration_level_mm_s: Optional[float] = None
    result: str = "Passed"  # Passed, Warning, Failed
    document_ref: Optional[str] = None

class FailureRecord(BaseModel):
    failure_id: str
    asset_tag: str
    date: str
    title: str
    failure_mode: str
    component: str
    severity: str = "High"  # Critical, High, Medium, Low
    root_cause_hypothesis: Optional[str] = None
    corrective_action: Optional[str] = None
    downtime_hours: float = 0.0
    document_ref: Optional[str] = None

class Finding(BaseModel):
    finding_id: str
    asset_tag: str
    title: str
    severity: str = "Medium"  # Critical, High, Medium, Low
    status: str = "Open"  # Open, In Review, Resolved
    detected_date: str
    evidence_summary: str
    supporting_records: List[str] = Field(default_factory=list)
    recommended_action: str
    source_procedure: str
    owner: str = "Maintenance Lead"

class TelemetryPoint(BaseModel):
    asset_tag: str
    timestamp: str
    vibration_rms: float
    bearing_temp_c: float
    discharge_pressure_bar: float
    rpm: float
    operating_hours: float
    is_synthetic: bool = True
