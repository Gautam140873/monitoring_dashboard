"""
Ledger and Burndown router for SkillFlow CRM
Provides Target Ledger, Resource Locking, and Burn-down visualization endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel

from database import db
from models.user import User
from services.auth import get_current_user, require_ho_role
from services.ledger import (
    get_target_ledger,
    validate_allocation,
    check_resource_availability,
    lock_resource,
    release_resource,
    get_resource_booking_history,
    get_burndown_data,
)

router = APIRouter(prefix="/ledger", tags=["Ledger & Burndown"])


# ==================== REQUEST MODELS ====================

class AllocationValidationRequest(BaseModel):
    master_wo_id: str
    job_role_id: str
    requested_students: int
    exclude_wo_id: Optional[str] = None


class ResourceLockRequest(BaseModel):
    resource_type: str  # trainer, manager, infrastructure
    resource_id: str
    sdc_id: str
    work_order_id: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


# ==================== TARGET LEDGER ENDPOINTS ====================

@router.get("/target/{master_wo_id}")
async def get_target_ledger_endpoint(master_wo_id: str, user: User = Depends(require_ho_role)):
    """
    Get complete target allocation ledger for a Master Work Order.
    Shows allocated vs remaining targets for each job role.
    """
    ledger = await get_target_ledger(master_wo_id)
    if not ledger:
        raise HTTPException(status_code=404, detail="Master Work Order not found")
    return ledger


@router.post("/validate-allocation")
async def validate_allocation_endpoint(
    request: AllocationValidationRequest,
    user: User = Depends(require_ho_role)
):
    """
    Validate if a requested allocation is possible without over-allocation.
    Use before creating SDC from Master Work Order.
    """
    result = await validate_allocation(
        master_wo_id=request.master_wo_id,
        job_role_id=request.job_role_id,
        requested_students=request.requested_students,
        exclude_wo_id=request.exclude_wo_id
    )
    
    if not result["is_valid"]:
        raise HTTPException(status_code=400, detail=result)
    
    return result


@router.get("/all-ledgers")
async def get_all_ledgers(user: User = Depends(require_ho_role)):
    """Get target ledgers for all active Master Work Orders."""
    master_wos = await db.master_work_orders.find(
        {"is_deleted": {"$ne": True}, "status": "active"},
        {"_id": 0, "master_wo_id": 1}
    ).to_list(1000)
    
    ledgers = []
    for mwo in master_wos:
        ledger = await get_target_ledger(mwo["master_wo_id"])
        if ledger:
            ledgers.append(ledger)
    
    return ledgers


# ==================== RESOURCE LOCKING ENDPOINTS ====================

@router.get("/resource/check/{resource_type}/{resource_id}")
async def check_resource_availability_endpoint(
    resource_type: str,
    resource_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    exclude_sdc_id: Optional[str] = None,
    user: User = Depends(require_ho_role)
):
    """
    Check if a resource (trainer/manager/infrastructure) is available.
    Prevents double-booking during overlapping timeframes.
    """
    result = await check_resource_availability(
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        exclude_sdc_id=exclude_sdc_id
    )
    return result


@router.post("/resource/lock")
async def lock_resource_endpoint(
    request: ResourceLockRequest,
    user: User = Depends(require_ho_role)
):
    """
    Lock a resource for assignment, preventing double-booking.
    Returns error if resource is already assigned.
    """
    result = await lock_resource(
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        sdc_id=request.sdc_id,
        work_order_id=request.work_order_id,
        start_date=request.start_date,
        end_date=request.end_date,
        user_id=user.user_id,
        user_email=user.email
    )
    
    if not result["success"]:
        raise HTTPException(status_code=409, detail=result)
    
    return result


@router.post("/resource/release/{resource_type}/{resource_id}")
async def release_resource_endpoint(
    resource_type: str,
    resource_id: str,
    user: User = Depends(require_ho_role)
):
    """Release a locked resource, making it available again."""
    result = await release_resource(
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user.user_id,
        user_email=user.email
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result)
    
    return result


@router.get("/resource/history/{resource_type}/{resource_id}")
async def get_resource_history_endpoint(
    resource_type: str,
    resource_id: str,
    user: User = Depends(require_ho_role)
):
    """Get booking history for a resource."""
    history = await get_resource_booking_history(resource_type, resource_id)
    return history


@router.get("/resource/summary")
async def get_resource_lock_summary(user: User = Depends(require_ho_role)):
    """Get summary of all resource locks."""
    trainers = await db.trainers.find({"is_active": True}, {"_id": 0}).to_list(1000)
    managers = await db.center_managers.find({"is_active": True}, {"_id": 0}).to_list(1000)
    infrastructure = await db.sdc_infrastructure.find({"is_active": True}, {"_id": 0}).to_list(1000)
    
    return {
        "trainers": {
            "total": len(trainers),
            "available": len([t for t in trainers if t.get("status") == "available"]),
            "assigned": len([t for t in trainers if t.get("status") == "assigned"]),
            "on_leave": len([t for t in trainers if t.get("status") == "on_leave"])
        },
        "managers": {
            "total": len(managers),
            "available": len([m for m in managers if m.get("status") == "available"]),
            "assigned": len([m for m in managers if m.get("status") == "assigned"])
        },
        "infrastructure": {
            "total": len(infrastructure),
            "available": len([i for i in infrastructure if i.get("status") == "available"]),
            "in_use": len([i for i in infrastructure if i.get("status") == "in_use"]),
            "maintenance": len([i for i in infrastructure if i.get("status") == "maintenance"])
        }
    }


# ==================== BURN-DOWN ENDPOINTS ====================

@router.get("/burndown")
async def get_burndown_dashboard(
    master_wo_id: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """
    Get burn-down data for Work Order progress visualization.
    Shows pipeline: Unallocated → Allocated → Mobilized → In-Training → Placed
    """
    # For SDC role, filter by assigned SDC
    if user.role == "sdc" and user.assigned_sdc_id:
        # Get work orders for assigned SDC
        pass  # Will be filtered in the service
    
    data = await get_burndown_data(master_wo_id)
    return data


@router.get("/burndown/{master_wo_id}")
async def get_single_burndown(master_wo_id: str, user: User = Depends(get_current_user)):
    """Get burn-down data for a specific Master Work Order."""
    data = await get_burndown_data(master_wo_id)
    
    # Find the specific work order
    wo_data = next((wo for wo in data["work_orders"] if wo["master_wo_id"] == master_wo_id), None)
    if not wo_data:
        raise HTTPException(status_code=404, detail="Work Order not found")
    
    return wo_data
