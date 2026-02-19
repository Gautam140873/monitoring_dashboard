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


# ==================== RESOURCE CALENDAR ENDPOINTS ====================

@router.get("/resource/calendar")
async def get_resource_calendar(
    resource_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: User = Depends(require_ho_role)
):
    """
    Get resource calendar view showing availability and bookings.
    Returns all resources with their current assignments and booking history.
    """
    from datetime import datetime, timedelta
    
    # Default to current month if no dates provided
    if not start_date:
        start_date = datetime.now().strftime("%Y-%m-01")
    if not end_date:
        # End of next month
        next_month = datetime.now().replace(day=28) + timedelta(days=4)
        end_date = (next_month.replace(day=1) + timedelta(days=31)).replace(day=1).strftime("%Y-%m-%d")
    
    calendar_data = {
        "start_date": start_date,
        "end_date": end_date,
        "resources": []
    }
    
    # Get resources based on type filter
    resource_types = [resource_type] if resource_type else ["trainer", "manager", "infrastructure"]
    
    for r_type in resource_types:
        if r_type == "trainer":
            resources = await db.trainers.find({"is_active": True}, {"_id": 0}).to_list(1000)
            id_field = "trainer_id"
        elif r_type == "manager":
            resources = await db.center_managers.find({"is_active": True}, {"_id": 0}).to_list(1000)
            id_field = "manager_id"
        elif r_type == "infrastructure":
            resources = await db.sdc_infrastructure.find({"is_active": True}, {"_id": 0}).to_list(1000)
            id_field = "infra_id"
        else:
            continue
        
        for resource in resources:
            resource_id = resource.get(id_field)
            
            # Get booking history for this resource
            bookings = await db.resource_bookings.find({
                "resource_type": r_type,
                "resource_id": resource_id,
                "status": "active"
            }, {"_id": 0}).to_list(100)
            
            # Get current assignment details
            current_assignment = None
            if resource.get("status") == "assigned":
                sdc_id = resource.get("assigned_sdc_id")
                wo_id = resource.get("assigned_work_order_id")
                
                if sdc_id:
                    sdc = await db.sdcs.find_one({"sdc_id": sdc_id}, {"_id": 0, "name": 1, "location": 1})
                    if sdc:
                        current_assignment = {
                            "sdc_id": sdc_id,
                            "sdc_name": sdc.get("name"),
                            "location": sdc.get("location"),
                            "work_order_id": wo_id
                        }
                        
                        # Get work order details for dates
                        if wo_id:
                            wo = await db.work_orders.find_one(
                                {"work_order_id": wo_id}, 
                                {"_id": 0, "start_date": 1, "calculated_end_date": 1, "work_order_number": 1}
                            )
                            if wo:
                                current_assignment["start_date"] = wo.get("start_date")
                                current_assignment["end_date"] = wo.get("calculated_end_date")
                                current_assignment["work_order_number"] = wo.get("work_order_number")
            
            calendar_data["resources"].append({
                "resource_type": r_type,
                "resource_id": resource_id,
                "name": resource.get("name") or resource.get("center_name"),
                "email": resource.get("email"),
                "phone": resource.get("phone"),
                "status": resource.get("status", "available"),
                "specialization": resource.get("specialization") or resource.get("district"),
                "current_assignment": current_assignment,
                "booking_history": bookings
            })
    
    # Group by type for easier frontend rendering
    grouped = {
        "trainers": [r for r in calendar_data["resources"] if r["resource_type"] == "trainer"],
        "managers": [r for r in calendar_data["resources"] if r["resource_type"] == "manager"],
        "infrastructure": [r for r in calendar_data["resources"] if r["resource_type"] == "infrastructure"]
    }
    
    calendar_data["grouped"] = grouped
    calendar_data["summary"] = {
        "trainers": {
            "total": len(grouped["trainers"]),
            "available": len([r for r in grouped["trainers"] if r["status"] == "available"]),
            "assigned": len([r for r in grouped["trainers"] if r["status"] == "assigned"])
        },
        "managers": {
            "total": len(grouped["managers"]),
            "available": len([r for r in grouped["managers"] if r["status"] == "available"]),
            "assigned": len([r for r in grouped["managers"] if r["status"] == "assigned"])
        },
        "infrastructure": {
            "total": len(grouped["infrastructure"]),
            "available": len([r for r in grouped["infrastructure"] if r["status"] == "available"]),
            "in_use": len([r for r in grouped["infrastructure"] if r["status"] == "in_use"])
        }
    }
    
    return calendar_data


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
