"""
Audit logging service for SkillFlow CRM
"""
import uuid
import logging
from datetime import datetime, timezone

from ..database import db

logger = logging.getLogger(__name__)


class AuditAction:
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SOFT_DELETE = "SOFT_DELETE"
    RESTORE = "RESTORE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    PERMISSION_CHANGE = "PERMISSION_CHANGE"
    STATUS_CHANGE = "STATUS_CHANGE"


async def create_audit_log(
    action: str,
    entity_type: str,
    entity_id: str,
    user_id: str,
    user_email: str,
    changes: dict = None,
    old_values: dict = None,
    new_values: dict = None,
    ip_address: str = None,
    metadata: dict = None
):
    """Create an audit log entry for any system action"""
    audit_entry = {
        "audit_id": f"audit_{uuid.uuid4().hex[:12]}",
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "user_id": user_id,
        "user_email": user_email,
        "changes": changes,
        "old_values": old_values,
        "new_values": new_values,
        "ip_address": ip_address,
        "metadata": metadata or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.audit_logs.insert_one(audit_entry)
    logger.info(f"AUDIT: {action} on {entity_type}/{entity_id} by {user_email}")
    return audit_entry
