import time
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.models.audit import AuditLogEntry

class AuditService:
    @staticmethod
    def log_event(
        user: str,
        role: str,
        action: str,
        target_type: str,
        target_id: str,
        details: str
    ) -> Dict[str, Any]:
        db = get_db()
        entry = AuditLogEntry(
            event_id=f"evt_{int(time.time() * 1000)}",
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            user=user,
            role=role,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details
        )
        if db is not None:
            db.audit_logs.insert_one(entry.model_dump())
        return entry.model_dump()

    @staticmethod
    def get_audit_logs(target_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        db = get_db()
        if db is None:
            return []

        query = {"target_id": target_id} if target_id else {}
        cursor = db.audit_logs.find(query).sort("timestamp", -1).limit(limit)
        logs = []
        for l in cursor:
            l["_id"] = str(l.get("_id", ""))
            logs.append(l)
        return logs

audit_service = AuditService()
