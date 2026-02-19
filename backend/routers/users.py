"""
User management router for SkillFlow CRM
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone, timedelta

from ..database import db
from ..models.user import User
from ..models.schemas import UserRoleUpdate
from ..services.auth import get_current_user, require_ho_role
from ..services.audit import AuditAction, create_audit_log
from ..services.soft_delete import check_duplicate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("")
async def list_users(user: User = Depends(require_ho_role)):
    """List all users (HO only)"""
    users = await db.users.find({}, {"_id": 0}).to_list(1000)
    return users


@router.put("/{user_id}/role")
async def update_user_role(user_id: str, role_update: UserRoleUpdate, user: User = Depends(require_ho_role)):
    """Update user role (HO only)"""
    old_user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not old_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_role = old_user.get("role")
    
    result = await db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "role": role_update.role,
            "assigned_sdc_id": role_update.assigned_sdc_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.modified_count > 0:
        await create_audit_log(
            action=AuditAction.PERMISSION_CHANGE,
            entity_type="users",
            entity_id=user_id,
            user_id=user.user_id,
            user_email=user.email,
            old_values={"role": old_role, "assigned_sdc_id": old_user.get("assigned_sdc_id")},
            new_values={"role": role_update.role, "assigned_sdc_id": role_update.assigned_sdc_id}
        )
    
    return {"message": "User role updated"}


# Audit Log endpoints
@router.get("/audit/logs")
async def get_audit_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    user: User = Depends(require_ho_role)
):
    """Get audit logs with filtering (HO/Admin only)"""
    query = {}
    
    if entity_type:
        query["entity_type"] = entity_type
    if entity_id:
        query["entity_id"] = entity_id
    if action:
        query["action"] = action
    if user_id:
        query["user_id"] = user_id
    if start_date:
        query["timestamp"] = {"$gte": start_date}
    if end_date:
        if "timestamp" not in query:
            query["timestamp"] = {}
        query["timestamp"]["$lte"] = end_date
    
    total = await db.audit_logs.count_documents(query)
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    
    return {
        "logs": logs,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/audit/entity/{entity_type}/{entity_id}")
async def get_entity_audit_history(
    entity_type: str,
    entity_id: str,
    user: User = Depends(require_ho_role)
):
    """Get complete audit history for a specific entity"""
    logs = await db.audit_logs.find(
        {"entity_type": entity_type, "entity_id": entity_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(100)
    return logs


# Soft Delete & Recovery endpoints
@router.get("/deleted/items")
async def list_deleted_items(
    entity_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    user: User = Depends(require_ho_role)
):
    """List all soft-deleted items that can be recovered (HO/Admin only)"""
    soft_delete_collections = [
        ("job_role_master", "job_role_id", "job_role_name"),
        ("master_work_orders", "master_wo_id", "work_order_number"),
        ("trainers", "trainer_id", "name"),
        ("center_managers", "manager_id", "name"),
        ("sdc_infrastructure", "infra_id", "center_name"),
        ("sdcs", "sdc_id", "name"),
        ("work_orders", "work_order_id", "work_order_number")
    ]
    
    deleted_items = []
    
    for collection_name, id_field, name_field in soft_delete_collections:
        if entity_type and entity_type != collection_name:
            continue
            
        collection = db[collection_name]
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        
        items = await collection.find(
            {
                "is_deleted": True,
                "deleted_at": {"$gte": cutoff_date}
            },
            {"_id": 0}
        ).to_list(100)
        
        for item in items:
            deleted_items.append({
                "entity_type": collection_name,
                "entity_id": item.get(id_field),
                "name": item.get(name_field, "Unknown"),
                "deleted_at": item.get("deleted_at"),
                "deleted_by_email": item.get("deleted_by_email"),
                "can_restore": True,
                "days_until_permanent": max(0, 30 - (datetime.now(timezone.utc) - datetime.fromisoformat(item.get("deleted_at", datetime.now(timezone.utc).isoformat()).replace("Z", "+00:00"))).days)
            })
    
    deleted_items.sort(key=lambda x: x.get("deleted_at", ""), reverse=True)
    
    return {
        "items": deleted_items[skip:skip+limit],
        "total": len(deleted_items),
        "skip": skip,
        "limit": limit
    }


@router.post("/deleted/restore/{entity_type}/{entity_id}")
async def restore_deleted_item(
    entity_type: str,
    entity_id: str,
    user: User = Depends(require_ho_role)
):
    """Restore a soft-deleted item (HO/Admin only)"""
    from ..services.soft_delete import restore_document
    
    id_field_map = {
        "job_role_master": "job_role_id",
        "master_work_orders": "master_wo_id",
        "trainers": "trainer_id",
        "center_managers": "manager_id",
        "sdc_infrastructure": "infra_id",
        "sdcs": "sdc_id",
        "work_orders": "work_order_id"
    }
    
    if entity_type not in id_field_map:
        raise HTTPException(status_code=400, detail=f"Invalid entity type: {entity_type}")
    
    id_field = id_field_map[entity_type]
    query = {id_field: entity_id}
    
    success = await restore_document(
        collection_name=entity_type,
        query=query,
        user_id=user.user_id,
        user_email=user.email
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Deleted item not found or already restored")
    
    return {"message": f"Successfully restored {entity_type}/{entity_id}"}


@router.post("/validate/duplicate")
async def check_for_duplicate(
    collection: str,
    field: str,
    value: str,
    exclude_id: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """Check if a value already exists in a collection"""
    id_field_map = {
        "trainers": "trainer_id",
        "center_managers": "manager_id",
        "sdc_infrastructure": "infra_id",
        "users": "user_id",
        "job_role_master": "job_role_id"
    }
    
    id_field = id_field_map.get(collection)
    result = await check_duplicate(collection, field, value, exclude_id, id_field)
    return result
