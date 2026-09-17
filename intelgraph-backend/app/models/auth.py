from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SystemRole(str, Enum):
    MAINTENANCE_ENGINEER = "Maintenance Engineer"
    FIELD_TECHNICIAN = "Field Technician"
    OPERATIONS_ENGINEER = "Operations Engineer"
    RELIABILITY_ENGINEER = "Reliability Engineer"
    PLANT_MANAGER = "Plant Manager"
    COMPLIANCE_AUDITOR = "Quality / Compliance Auditor"
    PLATFORM_ADMIN = "Platform Administrator"
    ADMIN = "Platform Administrator"

class Permission(str, Enum):
    # Maintenance Permissions
    VIEW_ASSETS = "view_assets"
    EDIT_ASSETS = "edit_assets"
    LOG_MAINTENANCE = "log_maintenance"
    ADD_OPERATOR_NOTES = "add_operator_notes"
    CONFIRM_EXTRACTION = "confirm_extraction"
    INVESTIGATE_FINDING = "investigate_finding"

    # Operations & Plant Management Permissions
    PRIORITIZE_ACTIONS = "prioritize_actions"
    ASSIGN_ACTIONS = "assign_actions"
    APPROVE_OPERATIONAL_CHANGE = "approve_operational_change"
    VIEW_CROSS_ASSET_TRENDS = "view_cross_asset_trends"
    ARCHIVE_ASSETS = "archive_assets"
    RESTORE_ASSETS = "restore_assets"

    # Quality & Compliance Permissions
    AUDIT_COMPLIANCE = "audit_compliance"
    UPDATE_COMPLIANCE_STATUS = "update_compliance_status"
    GENERATE_AUDIT_PACKAGE = "generate_audit_package"
    UPDATE_DOCUMENT_GOVERNANCE = "update_document_governance"

    # Platform Administrator Permissions
    ADMIN_MANAGE_ORGANIZATIONS = "admin_manage_organizations"
    ADMIN_MANAGE_USERS = "admin_manage_users"
    ADMIN_MANAGE_ROLES = "admin_manage_roles"
    ADMIN_CONFIGURE_AGENTS = "admin_configure_agents"
    ADMIN_CONFIGURE_SYSTEM = "admin_configure_system"
    ADMIN_RUN_BENCHMARKS = "admin_run_benchmarks"
    ADMIN_VIEW_AUDIT_LOGS = "admin_view_audit_logs"
    ADMIN_IMPERSONATE_USER = "admin_impersonate_user"
    DELETE_ASSETS = "delete_assets"

class UserProfile(BaseModel):
    user_id: str
    tenant_id: str
    email: str
    full_name: str
    role: SystemRole
    department: str
    plant_scope: str
    permissions: List[Permission]
    is_active: bool = True
    created_at: str = "2026-01-01T00:00:00Z"

class LoginRequest(BaseModel):
    email: str
    password: str

class ImpersonationInfo(BaseModel):
    session_id: str
    admin_user_id: str
    admin_email: str
    target_user_id: str
    reason: str
    started_at: str
    expires_at: str

class AuthResponse(BaseModel):
    token: str
    user: UserProfile
    tenant_id: str
    organization_name: str
    industry: str
    is_impersonating: bool = False
    impersonation_info: Optional[ImpersonationInfo] = None

class ImpersonateRequest(BaseModel):
    target_user_id: str
    reason: str
    duration_minutes: int = 30

class PermissionCheckRequest(BaseModel):
    user_role: str
    required_permission: str
    action_description: str
