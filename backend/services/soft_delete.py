"""
Soft delete and recovery services for SkillFlow CRM
"""
import logging
from datetime import datetime, timezone

from ..database import db
from .audit import AuditAction, create_audit_log

logger = logging.getLogger(__name__)


async def soft_delete_document(
    collection_name: str,
    query: dict,
    user_id: str,
    user_email: str
) -> bool:
    """Soft delete a document by setting is_deleted flag"""
    collection = db[collection_name]
    
    # Get original document for audit
    original = await collection.find_one(query, {"_id": 0})
    if not original:
        return False
    
    # Get the entity ID field (varies by collection)
    entity_id = original.get("sdc_id") or original.get("trainer_id") or \
                original.get("manager_id") or original.get("infra_id") or \
                original.get("job_role_id") or original.get("master_wo_id") or \
                original.get("work_order_id") or str(original.get("_id", "unknown"))
    
    # Soft delete
    result = await collection.update_one(
        query,
        {
            "$set": {
                "is_deleted": True,
                "deleted_at": datetime.now(timezone.utc).isoformat(),
                "deleted_by": user_id,
                "deleted_by_email": user_email,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.modified_count > 0:
        # Create audit log
        await create_audit_log(
            action=AuditAction.SOFT_DELETE,
            entity_type=collection_name,
            entity_id=entity_id,
            user_id=user_id,
            user_email=user_email,
            old_values={"is_deleted": False},
            new_values={"is_deleted": True}
        )
        return True
    return False


async def restore_document(
    collection_name: str,
    query: dict,
    user_id: str,
    user_email: str
) -> bool:
    """Restore a soft-deleted document"""
    collection = db[collection_name]
    
    # Get original document
    original = await collection.find_one({**query, "is_deleted": True}, {"_id": 0})
    if not original:
        return False
    
    entity_id = original.get("sdc_id") or original.get("trainer_id") or \
                original.get("manager_id") or original.get("infra_id") or \
                original.get("job_role_id") or original.get("master_wo_id") or \
                original.get("work_order_id") or "unknown"
    
    # Restore
    result = await collection.update_one(
        {**query, "is_deleted": True},
        {
            "$set": {
                "is_deleted": False,
                "restored_at": datetime.now(timezone.utc).isoformat(),
                "restored_by": user_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "$unset": {
                "deleted_at": "",
                "deleted_by": "",
                "deleted_by_email": ""
            }
        }
    )
    
    if result.modified_count > 0:
        await create_audit_log(
            action=AuditAction.RESTORE,
            entity_type=collection_name,
            entity_id=entity_id,
            user_id=user_id,
            user_email=user_email,
            old_values={"is_deleted": True},
            new_values={"is_deleted": False}
        )
        return True
    return False


async def check_duplicate(
    collection_name: str,
    field: str,
    value: str,
    exclude_id: str = None,
    id_field: str = None
) -> dict:
    """Check for duplicate values in a collection"""
    collection = db[collection_name]
    query = {field: value, "is_deleted": {"$ne": True}}
    
    if exclude_id and id_field:
        query[id_field] = {"$ne": exclude_id}
    
    existing = await collection.find_one(query, {"_id": 0})
    if existing:
        return {
            "is_duplicate": True,
            "existing_record": existing,
            "field": field,
            "value": value
        }
    return {"is_duplicate": False}
