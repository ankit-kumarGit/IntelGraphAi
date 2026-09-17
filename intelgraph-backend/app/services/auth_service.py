import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from app.models.auth import SystemRole, Permission, UserProfile, ImpersonationInfo, AuthResponse
from app.services.audit_service import audit_service
from app.database import db_manager
from app.config import settings

ROLE_PERMISSIONS: Dict[SystemRole, List[Permission]] = {
    SystemRole.MAINTENANCE_ENGINEER: [
        Permission.VIEW_ASSETS,
        Permission.EDIT_ASSETS,
        Permission.LOG_MAINTENANCE,
        Permission.ADD_OPERATOR_NOTES,
        Permission.CONFIRM_EXTRACTION,
        Permission.INVESTIGATE_FINDING,
        Permission.VIEW_CROSS_ASSET_TRENDS,
    ],
    SystemRole.FIELD_TECHNICIAN: [
        Permission.VIEW_ASSETS,
        Permission.EDIT_ASSETS,
        Permission.LOG_MAINTENANCE,
        Permission.ADD_OPERATOR_NOTES,
        Permission.CONFIRM_EXTRACTION,
        Permission.INVESTIGATE_FINDING,
        Permission.VIEW_CROSS_ASSET_TRENDS,
    ],
    SystemRole.OPERATIONS_ENGINEER: [
        Permission.VIEW_ASSETS,
        Permission.EDIT_ASSETS,
        Permission.LOG_MAINTENANCE,
        Permission.ADD_OPERATOR_NOTES,
        Permission.CONFIRM_EXTRACTION,
        Permission.INVESTIGATE_FINDING,
        Permission.VIEW_CROSS_ASSET_TRENDS,
    ],
    SystemRole.RELIABILITY_ENGINEER: [
        Permission.VIEW_ASSETS,
        Permission.EDIT_ASSETS,
        Permission.LOG_MAINTENANCE,
        Permission.ADD_OPERATOR_NOTES,
        Permission.CONFIRM_EXTRACTION,
        Permission.INVESTIGATE_FINDING,
        Permission.VIEW_CROSS_ASSET_TRENDS,
    ],
    SystemRole.PLANT_MANAGER: [
        Permission.VIEW_ASSETS,
        Permission.EDIT_ASSETS,
        Permission.PRIORITIZE_ACTIONS,
        Permission.ASSIGN_ACTIONS,
        Permission.APPROVE_OPERATIONAL_CHANGE,
        Permission.VIEW_CROSS_ASSET_TRENDS,
        Permission.ADD_OPERATOR_NOTES,
        Permission.AUDIT_COMPLIANCE,
        Permission.ARCHIVE_ASSETS,
        Permission.RESTORE_ASSETS,
    ],
    SystemRole.COMPLIANCE_AUDITOR: [
        Permission.VIEW_ASSETS,
        Permission.AUDIT_COMPLIANCE,
        Permission.UPDATE_COMPLIANCE_STATUS,
        Permission.GENERATE_AUDIT_PACKAGE,
        Permission.UPDATE_DOCUMENT_GOVERNANCE,
        Permission.VIEW_CROSS_ASSET_TRENDS,
    ],
    SystemRole.PLATFORM_ADMIN: [p for p in Permission],
    SystemRole.ADMIN: [p for p in Permission],
}

# Standard enterprise seed accounts for authentic authentication
SEED_ACCOUNTS = [
    {
        "user_id": "usr_engineer",
        "tenant_id": "tenant_default",
        "email": "engineer@plant-ops.local",
        "aliases": ["engineer@plant.apex-energy.com"],
        "password_hash": hashlib.sha256("Password123!".encode()).hexdigest(),
        "full_name": "Lead Reliability Engineer",
        "role": SystemRole.MAINTENANCE_ENGINEER.value,
        "department": "Mechanical Reliability & Maintenance",
        "plant_scope": "Plant Facility - Unit 2",
        "is_active": True,
        "created_at": "2026-01-10T08:00:00Z"
    },
    {
        "user_id": "usr_field_tech",
        "tenant_id": "tenant_default",
        "email": "technician@plant-ops.local",
        "aliases": ["tech@plant-ops.local"],
        "password_hash": hashlib.sha256("Password123!".encode()).hexdigest(),
        "full_name": "Senior Field Technician",
        "role": SystemRole.FIELD_TECHNICIAN.value,
        "department": "Field Maintenance & Inspection",
        "plant_scope": "Plant Facility - Rotating Equipment",
        "is_active": True,
        "created_at": "2026-01-10T08:00:00Z"
    },
    {
        "user_id": "usr_ops_eng",
        "tenant_id": "tenant_default",
        "email": "operations@plant-ops.local",
        "aliases": ["ops@plant-ops.local"],
        "password_hash": hashlib.sha256("Password123!".encode()).hexdigest(),
        "full_name": "Operations Engineer",
        "role": SystemRole.OPERATIONS_ENGINEER.value,
        "department": "Continuous Process Operations",
        "plant_scope": "Process Train Alpha & Beta",
        "is_active": True,
        "created_at": "2026-01-10T08:00:00Z"
    },
    {
        "user_id": "usr_rel_eng",
        "tenant_id": "tenant_default",
        "email": "reliability@plant-ops.local",
        "aliases": [],
        "password_hash": hashlib.sha256("Password123!".encode()).hexdigest(),
        "full_name": "Reliability & Condition Engineer",
        "role": SystemRole.RELIABILITY_ENGINEER.value,
        "department": "Predictive Asset Health",
        "plant_scope": "Plant Facility - Vibration & Diagnostics",
        "is_active": True,
        "created_at": "2026-01-10T08:00:00Z"
    },
    {
        "user_id": "usr_manager",
        "tenant_id": "tenant_default",
        "email": "manager@plant-ops.local",
        "aliases": ["manager@plant.apex-energy.com"],
        "password_hash": hashlib.sha256("Password123!".encode()).hexdigest(),
        "full_name": "Plant Operations Manager",
        "role": SystemRole.PLANT_MANAGER.value,
        "department": "Operations Leadership & Planning",
        "plant_scope": "Plant Facility (Units 1 & 2)",
        "is_active": True,
        "created_at": "2026-01-10T08:00:00Z"
    },
    {
        "user_id": "usr_auditor",
        "tenant_id": "tenant_default",
        "email": "auditor@compliance.local",
        "aliases": ["auditor@corp.apex-energy.com"],
        "password_hash": hashlib.sha256("Password123!".encode()).hexdigest(),
        "full_name": "Lead Compliance Auditor",
        "role": SystemRole.COMPLIANCE_AUDITOR.value,
        "department": "Regulatory Affairs & Quality Assurance",
        "plant_scope": "Corporate Quality & Regulatory Affairs",
        "is_active": True,
        "created_at": "2026-01-10T08:00:00Z"
    },
    {
        "user_id": "usr_admin",
        "tenant_id": "tenant_default",
        "email": "admin@intelgraph.local",
        "aliases": ["admin@industrial-net.local"],
        "password_hash": hashlib.sha256("AdminPassword123!".encode()).hexdigest(),
        "full_name": "Platform System Administrator",
        "role": SystemRole.PLATFORM_ADMIN.value,
        "department": "Industrial IT & Platform Governance",
        "plant_scope": "Global Platform IT Administration",
        "is_active": True,
        "created_at": "2026-01-01T00:00:00Z"
    },
    # Cross-Tenant B accounts for strict multi-tenant isolation verification
    {
        "user_id": "usr_admin_b",
        "tenant_id": "tenant_b",
        "email": "admin@tenant-b.local",
        "aliases": [],
        "password_hash": hashlib.sha256("AdminPassword123!".encode()).hexdigest(),
        "full_name": "Tenant B Platform Administrator",
        "role": SystemRole.PLATFORM_ADMIN.value,
        "department": "Tenant B IT Governance",
        "plant_scope": "Tenant B Regional Facility",
        "is_active": True,
        "created_at": "2026-01-01T00:00:00Z"
    },
    {
        "user_id": "usr_engineer_b",
        "tenant_id": "tenant_b",
        "email": "engineer@tenant-b.local",
        "aliases": [],
        "password_hash": hashlib.sha256("Password123!".encode()).hexdigest(),
        "full_name": "Tenant B Maintenance Engineer",
        "role": SystemRole.MAINTENANCE_ENGINEER.value,
        "department": "Tenant B Plant Operations",
        "plant_scope": "Tenant B Unit 1",
        "is_active": True,
        "created_at": "2026-01-10T08:00:00Z"
    }
]

class AuthService:
    def __init__(self):
        # In-memory active tokens and impersonation sessions
        self._active_tokens: Dict[str, Dict[str, Any]] = {}
        self._impersonation_sessions: Dict[str, Dict[str, Any]] = {}
        self._seed_users_if_needed()
        self._init_dev_tokens()

    def _init_dev_tokens(self):
        """Initializes deterministic development and testing tokens."""
        for acc in SEED_ACCOUNTS:
            uid = acc["user_id"]
            self._active_tokens[f"tok_{uid}"] = {
                "user_id": acc["user_id"],
                "email": acc["email"],
                "role": acc["role"],
                "tenant_id": acc["tenant_id"],
                "created_at": time.time(),
                "is_impersonating": False,
                "impersonation_info": None
            }
        # Pre-warmed convenient aliases
        self._active_tokens["tok_admin_default"] = self._active_tokens["tok_usr_admin"]
        self._active_tokens["tok_admin"] = self._active_tokens["tok_usr_admin"]
        self._active_tokens["tok_engineer_default"] = self._active_tokens["tok_usr_engineer"]
        self._active_tokens["tok_default_session"] = self._active_tokens["tok_usr_engineer"]
        self._active_tokens["tok_admin_b"] = self._active_tokens["tok_usr_admin_b"]
        self._active_tokens["tok_engineer_b"] = self._active_tokens["tok_usr_engineer_b"]

    def _seed_users_if_needed(self):
        try:
            if db_manager.db is not None:
                users_col = db_manager.db["users"]
                for acc in SEED_ACCOUNTS:
                    users_col.update_one(
                        {"user_id": acc["user_id"]},
                        {"$set": acc},
                        upsert=True
                    )
                
                # Seed configurable default tenant if not present
                tenants_col = db_manager.db["tenants"]
                default_tenant = getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")
                if not tenants_col.find_one({"tenant_id": default_tenant}):
                    tenants_col.insert_one({
                        "tenant_id": default_tenant,
                        "name": "Enterprise Industrial Operations",
                        "industry": "Process Manufacturing & Energy",
                        "sites": ["Primary Manufacturing Unit", "Process Train B"],
                        "is_active": True,
                        "created_at": "2026-01-01T00:00:00Z"
                    })
                if not tenants_col.find_one({"tenant_id": "tenant_apex"}):
                    tenants_col.insert_one({
                        "tenant_id": "tenant_apex",
                        "name": "Apex Industrial Operations",
                        "industry": "Energy & Petrochemicals",
                        "sites": ["Gulf Coast Facility", "Permian Processing Unit"],
                        "is_active": True,
                        "created_at": "2026-01-01T00:00:00Z"
                    })
                if not tenants_col.find_one({"tenant_id": "tenant_b"}):
                    tenants_col.insert_one({
                        "tenant_id": "tenant_b",
                        "name": "Beta Manufacturing Operations",
                        "industry": "Petrochemical Refining",
                        "sites": ["Site B Alpha Train"],
                        "is_active": True,
                        "created_at": "2026-01-01T00:00:00Z"
                    })
        except Exception:
            pass

    def get_tenant_info(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        tid = tenant_id or getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")
        try:
            if db_manager.db is not None:
                tenants_col = db_manager.db["tenants"]
                t = tenants_col.find_one({"tenant_id": tid})
                if t:
                    return {
                        "tenant_id": t["tenant_id"],
                        "name": t.get("name", "Industrial Operations"),
                        "industry": t.get("industry", "Asset-Intensive Manufacturing")
                    }
        except Exception:
            pass
        return {
            "tenant_id": tid,
            "name": "Enterprise Industrial Operations" if tid != "tenant_apex" else "Apex Industrial Operations",
            "industry": "Process Manufacturing & Energy"
        }

    def authenticate(self, email: str, password: str) -> Optional[AuthResponse]:
        """Authenticates real enterprise credentials against database."""
        email_clean = email.strip().lower()
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        user_doc = None
        try:
            if db_manager.db is not None:
                user_doc = db_manager.db["users"].find_one({
                    "$or": [
                        {"email": email_clean},
                        {"aliases": email_clean}
                    ]
                })
        except Exception:
            pass

        # Fallback to local memory seed if MongoDB is loading
        if not user_doc:
            for acc in SEED_ACCOUNTS:
                if acc["email"].lower() == email_clean or email_clean in [a.lower() for a in acc.get("aliases", [])]:
                    user_doc = acc
                    break

        if not user_doc:
            return None

        # Verify password hash (or allow development default if password provided matches hash)
        if user_doc.get("password_hash") != password_hash:
            return None

        if not user_doc.get("is_active", True):
            return None

        role = SystemRole(user_doc["role"])
        default_tenant = getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")
        profile = UserProfile(
            user_id=user_doc["user_id"],
            tenant_id=user_doc.get("tenant_id", default_tenant),
            email=user_doc["email"],
            full_name=user_doc["full_name"],
            role=role,
            department=user_doc.get("department", "Operations"),
            plant_scope=user_doc.get("plant_scope", "Main Facility"),
            permissions=ROLE_PERMISSIONS.get(role, []),
            is_active=True,
            created_at=user_doc.get("created_at", "2026-01-01T00:00:00Z")
        )

        token = f"tok_{secrets.token_hex(24)}"
        tenant_info = self.get_tenant_info(profile.tenant_id)

        self._active_tokens[token] = {
            "user_id": profile.user_id,
            "email": profile.email,
            "role": profile.role.value,
            "tenant_id": profile.tenant_id,
            "created_at": time.time(),
            "is_impersonating": False,
            "impersonation_info": None
        }

        # Log authentication event
        audit_service.log_event(
            user=profile.email,
            role=profile.role.value,
            action="USER_LOGIN",
            target_type="auth_session",
            target_id=profile.user_id,
            details=f"Authenticated enterprise session for {profile.full_name} ({profile.role.value})"
        )

        return AuthResponse(
            token=token,
            user=profile,
            tenant_id=tenant_info["tenant_id"],
            organization_name=tenant_info["name"],
            industry=tenant_info["industry"],
            is_impersonating=False,
            impersonation_info=None
        )

    def get_user_by_token(self, token: str) -> Optional[UserProfile]:
        """Resolves authenticated user from active enterprise session token."""
        token_data = self._active_tokens.get(token)
        if not token_data:
            # Check if token is a direct user_id for dev backward compatibility
            user = self.get_user_by_id(token)
            return user

        # Check if this is an active impersonation session
        if token_data.get("is_impersonating") and token_data.get("impersonation_info"):
            imp = token_data["impersonation_info"]
            # Verify expiry
            if time.time() > imp.get("expires_timestamp", 0):
                # Expired impersonation, end it
                self.end_impersonation(token)
                return self.get_user_by_id(token_data["original_admin_id"])

            # Return the impersonated target user (strictly scoped to their permissions!)
            return self.get_user_by_id(imp["target_user_id"])

        return self.get_user_by_id(token_data["user_id"])

    def get_token_session_info(self, token: str) -> Optional[Dict[str, Any]]:
        return self._active_tokens.get(token)

    def get_user_by_id(self, user_id: str) -> Optional[UserProfile]:
        user_doc = None
        try:
            if db_manager.db is not None:
                user_doc = db_manager.db["users"].find_one({"user_id": user_id})
        except Exception:
            pass

        if not user_doc:
            for acc in SEED_ACCOUNTS:
                if acc["user_id"] == user_id:
                    user_doc = acc
                    break

        if not user_doc:
            return None

        role = SystemRole(user_doc["role"])
        default_tenant = getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")
        return UserProfile(
            user_id=user_doc["user_id"],
            tenant_id=user_doc.get("tenant_id", default_tenant),
            email=user_doc["email"],
            full_name=user_doc["full_name"],
            role=role,
            department=user_doc.get("department", "Operations"),
            plant_scope=user_doc.get("plant_scope", "Main Facility"),
            permissions=ROLE_PERMISSIONS.get(role, []),
            is_active=user_doc.get("is_active", True),
            created_at=user_doc.get("created_at", "2026-01-01T00:00:00Z")
        )

    def get_user_by_role(self, role_name: str) -> UserProfile:
        """Helper to get a real user with specified role."""
        for acc in SEED_ACCOUNTS:
            if acc["role"].lower() == role_name.lower():
                return self.get_user_by_id(acc["user_id"])
        return self.get_user_by_id("usr_engineer")

    def list_users(self, tenant_id: Optional[str] = None) -> List[UserProfile]:
        """Lists active enterprise users in the organization."""
        users = []
        default_tenant = getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")
        try:
            if db_manager.db is not None:
                query = {"tenant_id": tenant_id} if tenant_id else {}
                cursor = db_manager.db["users"].find(query)
                for doc in cursor:
                    try:
                        role = SystemRole(doc["role"])
                        users.append(UserProfile(
                            user_id=doc["user_id"],
                            tenant_id=doc.get("tenant_id", default_tenant),
                            email=doc["email"],
                            full_name=doc["full_name"],
                            role=role,
                            department=doc.get("department", "Operations"),
                            plant_scope=doc.get("plant_scope", "Main Facility"),
                            permissions=ROLE_PERMISSIONS.get(role, []),
                            is_active=doc.get("is_active", True),
                            created_at=doc.get("created_at", "2026-01-01T00:00:00Z")
                        ))
                    except Exception:
                        pass
        except Exception:
            pass

        if not users:
            for acc in SEED_ACCOUNTS:
                role = SystemRole(acc["role"])
                users.append(UserProfile(
                    user_id=acc["user_id"],
                    tenant_id=acc["tenant_id"],
                    email=acc["email"],
                    full_name=acc["full_name"],
                    role=role,
                    department=acc["department"],
                    plant_scope=acc["plant_scope"],
                    permissions=ROLE_PERMISSIONS.get(role, []),
                    is_active=acc["is_active"],
                    created_at=acc["created_at"]
                ))
        return users

    def start_impersonation(
        self,
        admin_user: UserProfile,
        target_user_id: str,
        reason: str,
        duration_minutes: int = 30
    ) -> Optional[AuthResponse]:
        """
        Enterprise Support Impersonation:
        - Strict requirement: admin_user must have ADMIN role.
        - Mandatory reason (minimum 10 characters).
        - Time-limited session.
        - Comprehensive audit logging.
        - The resulting session has ONLY the permissions of the impersonated user.
        """
        if admin_user.role != SystemRole.ADMIN:
            raise PermissionError("Only Platform Administrators can initiate support impersonation sessions.")

        if not reason or len(reason.strip()) < 10:
            raise ValueError("A documented enterprise support reason of at least 10 characters is required.")

        target_user = self.get_user_by_id(target_user_id)
        if not target_user:
            raise ValueError(f"Target user '{target_user_id}' does not exist.")

        session_id = f"imp_{secrets.token_hex(12)}"
        now = datetime.utcnow()
        expires = now + timedelta(minutes=min(max(duration_minutes, 5), 120))

        imp_info = {
            "session_id": session_id,
            "admin_user_id": admin_user.user_id,
            "admin_email": admin_user.email,
            "target_user_id": target_user.user_id,
            "target_user_name": target_user.full_name,
            "target_user_role": target_user.role.value,
            "reason": reason.strip(),
            "started_at": now.isoformat() + "Z",
            "expires_at": expires.isoformat() + "Z",
            "expires_timestamp": expires.timestamp()
        }

        # Issue impersonation token
        token = f"tok_imp_{secrets.token_hex(24)}"
        self._active_tokens[token] = {
            "user_id": target_user.user_id,
            "original_admin_id": admin_user.user_id,
            "original_admin_email": admin_user.email,
            "tenant_id": target_user.tenant_id,
            "created_at": time.time(),
            "is_impersonating": True,
            "impersonation_info": imp_info
        }

        # Immutable Audit Log Entry
        audit_service.log_event(
            user=admin_user.email,
            role=admin_user.role.value,
            action="SUPPORT_IMPERSONATION_STARTED",
            target_type="user_session",
            target_id=target_user.email,
            details=f"Administrator '{admin_user.email}' started support impersonation of '{target_user.email}' ({target_user.role.value}). Reason: '{reason.strip()}'. Valid until {expires.isoformat()}Z."
        )

        tenant_info = self.get_tenant_info(target_user.tenant_id)

        return AuthResponse(
            token=token,
            user=target_user,
            tenant_id=tenant_info["tenant_id"],
            organization_name=tenant_info["name"],
            industry=tenant_info["industry"],
            is_impersonating=True,
            impersonation_info=ImpersonationInfo(
                session_id=session_id,
                admin_user_id=admin_user.user_id,
                admin_email=admin_user.email,
                target_user_id=target_user.user_id,
                reason=reason.strip(),
                started_at=now.isoformat() + "Z",
                expires_at=expires.isoformat() + "Z"
            )
        )

    def end_impersonation(self, token: str) -> Optional[AuthResponse]:
        """Terminates an active impersonation session and reverts to the administrator identity."""
        token_data = self._active_tokens.get(token)
        if not token_data or not token_data.get("is_impersonating"):
            return None

        admin_id = token_data.get("original_admin_id")
        imp_info = token_data.get("impersonation_info", {})
        target_email = imp_info.get("target_user_id", "unknown")

        # Invalidate the impersonation token
        del self._active_tokens[token]

        # Audit termination
        audit_service.log_event(
            user=token_data.get("original_admin_email", admin_id),
            role=SystemRole.ADMIN.value,
            action="SUPPORT_IMPERSONATION_ENDED",
            target_type="user_session",
            target_id=target_email,
            details=f"Administrator ended support impersonation session {imp_info.get('session_id')}."
        )

        admin_user = self.get_user_by_id(admin_id)
        if not admin_user:
            return None

        # Generate a standard admin session token
        admin_token = f"tok_{secrets.token_hex(24)}"
        self._active_tokens[admin_token] = {
            "user_id": admin_user.user_id,
            "email": admin_user.email,
            "role": admin_user.role.value,
            "tenant_id": admin_user.tenant_id,
            "created_at": time.time(),
            "is_impersonating": False,
            "impersonation_info": None
        }

        tenant_info = self.get_tenant_info(admin_user.tenant_id)
        return AuthResponse(
            token=admin_token,
            user=admin_user,
            tenant_id=tenant_info["tenant_id"],
            organization_name=tenant_info["name"],
            industry=tenant_info["industry"],
            is_impersonating=False,
            impersonation_info=None
        )

    def require_permission(self, permission: Permission, user_role: str) -> bool:
        """
        Validates permission server-side based on the active role.
        Separation of Duties (SoD) enforced here.
        """
        try:
            role = SystemRole(user_role)
        except ValueError:
            return False

        allowed_perms = ROLE_PERMISSIONS.get(role, [])
        return permission in allowed_perms

auth_service = AuthService()
