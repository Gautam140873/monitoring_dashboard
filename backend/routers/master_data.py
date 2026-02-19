"""
Master Data router for SkillFlow CRM - Job Roles and Work Orders
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone
import uuid
import logging

from database import db
from models.user import User
from models.schemas import (
    JobRoleMasterCreate, JobRoleMasterUpdate,
    MasterWorkOrderCreate, MasterWorkOrderUpdate,
    SDCDistrictAllocation, SDCFromMasterCreate
)
from services.auth import get_current_user, require_ho_role
from services.soft_delete import soft_delete_document
from services.utils import create_training_roadmap
from services.ledger import (
    validate_allocation,
    record_allocation,
    check_resource_availability,
    lock_resource
)
from config import CATEGORY_RATES

router = APIRouter(prefix="/master", tags=["Master Data"])
logger = logging.getLogger(__name__)


# ==================== JOB ROLES ====================

@router.get("/job-roles")
async def list_job_roles(user: User = Depends(require_ho_role)):
    """List all Job Roles from Master Data (HO only)"""
    job_roles = await db.job_role_master.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(1000)
    return job_roles


@router.get("/job-roles/active")
async def list_active_job_roles(user: User = Depends(get_current_user)):
    """List active Job Roles (for dropdown selection)"""
    job_roles = await db.job_role_master.find({"is_active": True, "is_deleted": {"$ne": True}}, {"_id": 0}).to_list(1000)
    return job_roles


@router.post("/job-roles")
async def create_job_role(jr_data: JobRoleMasterCreate, user: User = Depends(require_ho_role)):
    """Create a new Job Role in Master Data (HO only)"""
    rate = jr_data.rate_per_hour
    if rate is None:
        rate = CATEGORY_RATES.get(jr_data.category.upper(), 0)
    
    existing = await db.job_role_master.find_one({"job_role_code": jr_data.job_role_code, "is_deleted": {"$ne": True}})
    if existing:
        raise HTTPException(status_code=400, detail=f"Job Role Code {jr_data.job_role_code} already exists")
    
    job_role = {
        "job_role_id": f"jr_{uuid.uuid4().hex[:8]}",
        "job_role_code": jr_data.job_role_code,
        "job_role_name": jr_data.job_role_name,
        "category": jr_data.category.upper(),
        "rate_per_hour": rate,
        "total_training_hours": jr_data.total_training_hours,
        "awarding_body": jr_data.awarding_body,
        "scheme_name": jr_data.scheme_name,
        "default_daily_hours": jr_data.default_daily_hours,
        "default_batch_size": jr_data.default_batch_size,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.user_id,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.job_role_master.insert_one(job_role.copy())
    logger.info(f"Created Job Role: {jr_data.job_role_code} - {jr_data.job_role_name}")
    return job_role


@router.get("/job-roles/{job_role_id}")
async def get_job_role(job_role_id: str, user: User = Depends(require_ho_role)):
    """Get Job Role details (HO only)"""
    job_role = await db.job_role_master.find_one({"job_role_id": job_role_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not job_role:
        raise HTTPException(status_code=404, detail="Job Role not found")
    return job_role


@router.put("/job-roles/{job_role_id}")
async def update_job_role(job_role_id: str, jr_update: JobRoleMasterUpdate, user: User = Depends(require_ho_role)):
    """Update Job Role in Master Data (HO only)"""
    job_role = await db.job_role_master.find_one({"job_role_id": job_role_id})
    if not job_role:
        raise HTTPException(status_code=404, detail="Job Role not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if jr_update.job_role_name is not None:
        update_data["job_role_name"] = jr_update.job_role_name
    if jr_update.category is not None:
        update_data["category"] = jr_update.category.upper()
        if jr_update.rate_per_hour is None:
            update_data["rate_per_hour"] = CATEGORY_RATES.get(jr_update.category.upper(), job_role.get("rate_per_hour", 0))
    if jr_update.rate_per_hour is not None:
        update_data["rate_per_hour"] = jr_update.rate_per_hour
    if jr_update.total_training_hours is not None:
        update_data["total_training_hours"] = jr_update.total_training_hours
    if jr_update.awarding_body is not None:
        update_data["awarding_body"] = jr_update.awarding_body
    if jr_update.scheme_name is not None:
        update_data["scheme_name"] = jr_update.scheme_name
    if jr_update.default_daily_hours is not None:
        update_data["default_daily_hours"] = jr_update.default_daily_hours
    if jr_update.default_batch_size is not None:
        update_data["default_batch_size"] = jr_update.default_batch_size
    if jr_update.is_active is not None:
        update_data["is_active"] = jr_update.is_active
    
    await db.job_role_master.update_one({"job_role_id": job_role_id}, {"$set": update_data})
    return {"message": "Job Role updated successfully"}


@router.delete("/job-roles/{job_role_id}")
async def delete_job_role(job_role_id: str, user: User = Depends(require_ho_role)):
    """Soft delete Job Role (HO only) - Can be recovered within 30 days"""
    job_role = await db.job_role_master.find_one({"job_role_id": job_role_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not job_role:
        raise HTTPException(status_code=404, detail="Job Role not found")
    
    success = await soft_delete_document(
        collection_name="job_role_master",
        query={"job_role_id": job_role_id},
        user_id=user.user_id,
        user_email=user.email
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete Job Role")
    
    await db.job_role_master.update_one({"job_role_id": job_role_id}, {"$set": {"is_active": False}})
    
    return {"message": "Job Role deleted successfully. Can be recovered within 30 days.", "job_role_id": job_role_id}


# ==================== MASTER WORK ORDERS ====================

@router.get("/work-orders")
async def list_master_work_orders(user: User = Depends(require_ho_role)):
    """List all Master Work Orders (HO only)"""
    work_orders = await db.master_work_orders.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(1000)
    
    for wo in work_orders:
        sdcs = await db.sdcs.find({"master_wo_id": wo["master_wo_id"], "is_deleted": {"$ne": True}}, {"_id": 0}).to_list(100)
        wo["sdcs_created"] = sdcs
        wo["sdcs_created_count"] = len(sdcs)
        
        wo_batches = await db.work_orders.find({"master_wo_id": wo["master_wo_id"], "is_deleted": {"$ne": True}}, {"_id": 0}).to_list(100)
        wo["actual_students"] = sum(b.get("num_students", 0) for b in wo_batches)
        wo["actual_value"] = sum(b.get("total_contract_value", 0) for b in wo_batches)
    
    return work_orders


@router.post("/work-orders")
async def create_master_work_order(mwo_data: MasterWorkOrderCreate, user: User = Depends(require_ho_role)):
    """Create a Master Work Order (HO only)"""
    existing = await db.master_work_orders.find_one({"work_order_number": mwo_data.work_order_number, "is_deleted": {"$ne": True}})
    if existing:
        raise HTTPException(status_code=400, detail=f"Work Order {mwo_data.work_order_number} already exists")
    
    job_roles_data = []
    total_contract_value = 0
    
    for jr_alloc in mwo_data.job_roles:
        job_role = await db.job_role_master.find_one({"job_role_id": jr_alloc.job_role_id}, {"_id": 0})
        if not job_role:
            raise HTTPException(status_code=404, detail=f"Job Role {jr_alloc.job_role_id} not found")
        if not job_role.get("is_active", True):
            raise HTTPException(status_code=400, detail=f"Job Role {job_role['job_role_code']} is not active")
        
        jr_value = jr_alloc.target * job_role["total_training_hours"] * job_role["rate_per_hour"]
        total_contract_value += jr_value
        
        job_roles_data.append({
            "job_role_id": job_role["job_role_id"],
            "job_role_code": job_role["job_role_code"],
            "job_role_name": job_role["job_role_name"],
            "category": job_role["category"],
            "rate_per_hour": job_role["rate_per_hour"],
            "total_training_hours": job_role["total_training_hours"],
            "target": jr_alloc.target,
            "value": jr_value
        })
    
    sdc_districts_data = []
    for sdc_dist in mwo_data.sdc_districts:
        sdc_districts_data.append({
            "district_name": sdc_dist.district_name,
            "sdc_count": sdc_dist.sdc_count,
            "sdcs_created": []
        })
    
    master_wo = {
        "master_wo_id": f"mwo_{uuid.uuid4().hex[:8]}",
        "work_order_number": mwo_data.work_order_number,
        "awarding_body": mwo_data.awarding_body,
        "scheme_name": mwo_data.scheme_name,
        "total_training_target": mwo_data.total_training_target,
        "job_roles": job_roles_data,
        "num_sdcs": sum(d.sdc_count for d in mwo_data.sdc_districts),
        "sdc_districts": sdc_districts_data,
        "total_contract_value": total_contract_value,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.user_id,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.master_work_orders.insert_one(master_wo.copy())
    logger.info(f"Created Master Work Order: {mwo_data.work_order_number}")
    return master_wo


@router.get("/work-orders/{master_wo_id}")
async def get_master_work_order(master_wo_id: str, user: User = Depends(require_ho_role)):
    """Get Master Work Order with linked SDCs (HO only)"""
    master_wo = await db.master_work_orders.find_one({"master_wo_id": master_wo_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not master_wo:
        raise HTTPException(status_code=404, detail="Master Work Order not found")
    
    sdcs = await db.sdcs.find({"master_wo_id": master_wo_id, "is_deleted": {"$ne": True}}, {"_id": 0}).to_list(100)
    
    for sdc in sdcs:
        work_orders = await db.work_orders.find(
            {"sdc_id": sdc["sdc_id"], "master_wo_id": master_wo_id, "is_deleted": {"$ne": True}}, 
            {"_id": 0}
        ).to_list(100)
        sdc["work_orders"] = work_orders
        sdc["batch_count"] = len(work_orders)
        sdc["total_students"] = sum(wo.get("num_students", 0) for wo in work_orders)
        sdc["total_value"] = sum(wo.get("total_contract_value", 0) for wo in work_orders)
    
    master_wo["sdcs_created"] = sdcs
    master_wo["sdcs_created_count"] = len(sdcs)
    
    return master_wo


@router.get("/work-orders/{master_wo_id}/allocation-status")
async def get_job_role_allocation_status(master_wo_id: str, user: User = Depends(require_ho_role)):
    """Get allocation status for each job role in a Master Work Order"""
    master_wo = await db.master_work_orders.find_one({"master_wo_id": master_wo_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not master_wo:
        raise HTTPException(status_code=404, detail="Master Work Order not found")
    
    work_orders = await db.work_orders.find(
        {"master_wo_id": master_wo_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "job_role_id": 1, "num_students": 1, "sdc_id": 1}
    ).to_list(1000)
    
    allocation_by_job_role = {}
    for wo in work_orders:
        jr_id = wo.get("job_role_id")
        if jr_id:
            if jr_id not in allocation_by_job_role:
                allocation_by_job_role[jr_id] = {"allocated": 0, "sdcs": []}
            allocation_by_job_role[jr_id]["allocated"] += wo.get("num_students", 0)
            allocation_by_job_role[jr_id]["sdcs"].append(wo.get("sdc_id"))
    
    job_roles_status = []
    total_target = 0
    total_allocated = 0
    
    for jr in master_wo.get("job_roles", []):
        jr_id = jr["job_role_id"]
        target = jr.get("target", 0)
        allocated = allocation_by_job_role.get(jr_id, {}).get("allocated", 0)
        remaining = max(0, target - allocated)
        
        total_target += target
        total_allocated += allocated
        
        job_roles_status.append({
            "job_role_id": jr_id,
            "job_role_code": jr.get("job_role_code", ""),
            "job_role_name": jr.get("job_role_name", ""),
            "rate_per_hour": jr.get("rate_per_hour", 0),
            "total_training_hours": jr.get("total_training_hours", 0),
            "target": target,
            "allocated": allocated,
            "remaining": remaining,
            "sdcs_count": len(allocation_by_job_role.get(jr_id, {}).get("sdcs", [])),
            "is_fully_allocated": remaining == 0
        })
    
    num_sdcs_planned = master_wo.get("num_sdcs", 0)
    sdcs_created = await db.sdcs.count_documents({"master_wo_id": master_wo_id, "is_deleted": {"$ne": True}})
    
    return {
        "master_wo_id": master_wo_id,
        "work_order_number": master_wo.get("work_order_number"),
        "total_training_target": master_wo.get("total_training_target", 0),
        "total_allocated": total_allocated,
        "total_remaining": max(0, master_wo.get("total_training_target", 0) - total_allocated),
        "sdcs_planned": num_sdcs_planned,
        "sdcs_created": sdcs_created,
        "job_roles": job_roles_status,
        "is_fully_allocated": total_allocated >= master_wo.get("total_training_target", 0)
    }


@router.put("/work-orders/{master_wo_id}")
async def update_master_work_order(master_wo_id: str, mwo_update: MasterWorkOrderUpdate, user: User = Depends(require_ho_role)):
    """Update Master Work Order (HO only)"""
    master_wo = await db.master_work_orders.find_one({"master_wo_id": master_wo_id})
    if not master_wo:
        raise HTTPException(status_code=404, detail="Master Work Order not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if mwo_update.awarding_body is not None:
        update_data["awarding_body"] = mwo_update.awarding_body
    if mwo_update.scheme_name is not None:
        update_data["scheme_name"] = mwo_update.scheme_name
    if mwo_update.total_training_target is not None:
        update_data["total_training_target"] = mwo_update.total_training_target
    if mwo_update.status is not None:
        update_data["status"] = mwo_update.status
    
    await db.master_work_orders.update_one({"master_wo_id": master_wo_id}, {"$set": update_data})
    return {"message": "Master Work Order updated successfully"}


@router.post("/work-orders/{master_wo_id}/add-sdc-district")
async def add_sdc_district(master_wo_id: str, district: SDCDistrictAllocation, user: User = Depends(require_ho_role)):
    """Add a new SDC district to existing Master Work Order (HO only)"""
    master_wo = await db.master_work_orders.find_one({"master_wo_id": master_wo_id})
    if not master_wo:
        raise HTTPException(status_code=404, detail="Master Work Order not found")
    
    sdc_districts = master_wo.get("sdc_districts", [])
    sdc_districts.append({
        "district_name": district.district_name,
        "sdc_count": district.sdc_count,
        "sdcs_created": []
    })
    
    await db.master_work_orders.update_one(
        {"master_wo_id": master_wo_id},
        {"$set": {
            "sdc_districts": sdc_districts,
            "num_sdcs": sum(d.get("sdc_count", 1) for d in sdc_districts),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": f"District {district.district_name} added successfully"}


@router.post("/work-orders/{master_wo_id}/complete")
async def complete_master_work_order(master_wo_id: str, user: User = Depends(require_ho_role)):
    """Mark Master Work Order as completed and release all resources (HO only)"""
    master_wo = await db.master_work_orders.find_one({"master_wo_id": master_wo_id})
    if not master_wo:
        raise HTTPException(status_code=404, detail="Master Work Order not found")
    
    if master_wo.get("status") == "completed":
        return {"message": "Work Order is already completed"}
    
    sdcs = await db.sdcs.find({"master_wo_id": master_wo_id}, {"_id": 0}).to_list(100)
    
    released_resources = {"trainers": 0, "managers": 0, "infrastructure": 0}
    
    for sdc in sdcs:
        sdc_id = sdc.get("sdc_id")
        
        trainer_result = await db.trainers.update_many(
            {"assigned_sdc_id": sdc_id, "status": "assigned"},
            {"$set": {
                "status": "available",
                "assigned_sdc_id": None,
                "assigned_work_order_id": None,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        released_resources["trainers"] += trainer_result.modified_count
        
        manager_result = await db.center_managers.update_many(
            {"assigned_sdc_id": sdc_id, "status": "assigned"},
            {"$set": {
                "status": "available",
                "assigned_sdc_id": None,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        released_resources["managers"] += manager_result.modified_count
    
    infra_result = await db.sdc_infrastructure.update_many(
        {"assigned_work_order_id": master_wo_id, "status": "in_use"},
        {"$set": {
            "status": "available",
            "assigned_work_order_id": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    released_resources["infrastructure"] += infra_result.modified_count
    
    await db.work_orders.update_many(
        {"master_wo_id": master_wo_id},
        {"$set": {"status": "completed"}}
    )
    
    await db.master_work_orders.update_one(
        {"master_wo_id": master_wo_id},
        {"$set": {
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logger.info(f"Completed Master Work Order {master_wo_id}. Released: {released_resources}")
    
    return {
        "message": "Work Order completed and all resources released",
        "released_resources": released_resources
    }


@router.post("/work-orders/{master_wo_id}/sdcs")
async def create_sdc_from_master(master_wo_id: str, sdc_data: SDCFromMasterCreate, user: User = Depends(require_ho_role)):
    """Create/Open SDC from Master Work Order (HO only) with allocation validation and resource locking"""
    master_wo = await db.master_work_orders.find_one({"master_wo_id": master_wo_id}, {"_id": 0})
    if not master_wo:
        raise HTTPException(status_code=404, detail="Master Work Order not found")
    
    # ==================== TARGET LEDGER VALIDATION ====================
    # Validate allocation before proceeding
    allocation_result = await validate_allocation(
        master_wo_id=master_wo_id,
        job_role_id=sdc_data.job_role_id,
        requested_students=sdc_data.target_students
    )
    
    if not allocation_result["is_valid"]:
        raise HTTPException(
            status_code=400, 
            detail={
                "error": "Over-allocation prevented",
                "message": allocation_result["error"],
                "remaining": allocation_result.get("remaining", 0),
                "requested": sdc_data.target_students
            }
        )
    
    # ==================== RESOURCE LOCKING ====================
    # Check and lock resources if provided
    locked_resources = []
    
    # Check Infrastructure availability
    if sdc_data.infra_id:
        infra_check = await check_resource_availability("infrastructure", sdc_data.infra_id)
        if not infra_check["is_available"]:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "Resource conflict",
                    "resource_type": "infrastructure",
                    "message": infra_check.get("error"),
                    "conflict": infra_check.get("conflict")
                }
            )
        locked_resources.append(("infrastructure", sdc_data.infra_id))
    
    # Check Manager availability
    if sdc_data.manager_id:
        manager_check = await check_resource_availability("manager", sdc_data.manager_id)
        if not manager_check["is_available"]:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "Resource conflict",
                    "resource_type": "manager",
                    "message": manager_check.get("error"),
                    "conflict": manager_check.get("conflict")
                }
            )
        locked_resources.append(("manager", sdc_data.manager_id))
    
    # Check Trainer availability
    if sdc_data.trainer_id:
        trainer_check = await check_resource_availability("trainer", sdc_data.trainer_id)
        if not trainer_check["is_available"]:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "Resource conflict",
                    "resource_type": "trainer",
                    "message": trainer_check.get("error"),
                    "conflict": trainer_check.get("conflict")
                }
            )
        locked_resources.append(("trainer", sdc_data.trainer_id))
    
    # ==================== CONTINUE WITH SDC CREATION ====================
    job_role = None
    for jr in master_wo.get("job_roles", []):
        if jr["job_role_id"] == sdc_data.job_role_id:
            job_role = jr
            break
    
    if not job_role:
        job_role_doc = await db.job_role_master.find_one({"job_role_id": sdc_data.job_role_id}, {"_id": 0})
        if not job_role_doc:
            raise HTTPException(status_code=404, detail="Job Role not found")
        job_role = job_role_doc
    
    district_key = sdc_data.district_name.upper().replace(" ", "_")
    if sdc_data.sdc_suffix:
        sdc_id = f"sdc_{district_key}{sdc_data.sdc_suffix}".lower()
        sdc_name = f"SDC {sdc_data.district_name.title()} {sdc_data.sdc_suffix}"
    else:
        sdc_id = f"sdc_{district_key}".lower()
        sdc_name = f"SDC {sdc_data.district_name.title()}"
    
    existing_sdc = await db.sdcs.find_one({"sdc_id": sdc_id}, {"_id": 0})
    
    if existing_sdc:
        await db.sdcs.update_one(
            {"sdc_id": sdc_id},
            {"$set": {
                "master_wo_id": master_wo_id,
                "target_students": sdc_data.target_students,
                "job_role_id": sdc_data.job_role_id,
                "address_line1": sdc_data.address_line1,
                "address_line2": sdc_data.address_line2,
                "city": sdc_data.city,
                "state": sdc_data.state,
                "pincode": sdc_data.pincode,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }}
        )
        sdc = existing_sdc
        sdc["master_wo_id"] = master_wo_id
        sdc["target_students"] = sdc_data.target_students
    else:
        sdc = {
            "sdc_id": sdc_id,
            "name": sdc_name,
            "district": sdc_data.district_name,
            "location": sdc_data.district_name,
            "master_wo_id": master_wo_id,
            "job_role_id": sdc_data.job_role_id,
            "target_students": sdc_data.target_students,
            "manager_email": sdc_data.manager_email,
            "address_line1": sdc_data.address_line1,
            "address_line2": sdc_data.address_line2,
            "city": sdc_data.city,
            "state": sdc_data.state,
            "pincode": sdc_data.pincode,
            "infra_id": sdc_data.infra_id,
            "manager_id": sdc_data.manager_id,
            "trainer_id": sdc_data.trainer_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        await db.sdcs.insert_one(sdc.copy())
    
    # Lock resources using the resource locking service
    if sdc_data.infra_id:
        await lock_resource(
            resource_type="infrastructure",
            resource_id=sdc_data.infra_id,
            sdc_id=sdc_id,
            work_order_id=master_wo_id,
            user_id=user.user_id,
            user_email=user.email
        )
    
    if sdc_data.manager_id:
        await lock_resource(
            resource_type="manager",
            resource_id=sdc_data.manager_id,
            sdc_id=sdc_id,
            work_order_id=master_wo_id,
            user_id=user.user_id,
            user_email=user.email
        )
    
    if sdc_data.trainer_id:
        await lock_resource(
            resource_type="trainer",
            resource_id=sdc_data.trainer_id,
            sdc_id=sdc_id,
            work_order_id=master_wo_id,
            user_id=user.user_id,
            user_email=user.email
        )
    
    training_hours = job_role.get("total_training_hours", 0)
    rate = job_role.get("rate_per_hour", 0)
    contract_value = sdc_data.target_students * training_hours * rate
    
    wo_suffix = sdc_data.sdc_suffix or district_key[:3]
    work_order = {
        "work_order_id": f"wo_{uuid.uuid4().hex[:8]}",
        "work_order_number": f"{master_wo['work_order_number']}/{wo_suffix}",
        "master_wo_id": master_wo_id,
        "sdc_id": sdc_id,
        "location": sdc_data.district_name,
        "job_role_id": sdc_data.job_role_id,
        "job_role_code": job_role.get("job_role_code", ""),
        "job_role_name": job_role.get("job_role_name", ""),
        "awarding_body": master_wo.get("awarding_body", ""),
        "scheme_name": master_wo.get("scheme_name", ""),
        "total_training_hours": training_hours,
        "sessions_per_day": sdc_data.daily_hours,
        "num_students": sdc_data.target_students,
        "rate_per_hour": rate,
        "cost_per_student": training_hours * rate,
        "total_contract_value": contract_value,
        "manager_email": sdc_data.manager_email,
        "start_date": None,
        "calculated_end_date": None,
        "manual_end_date": None,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.user_id
    }
    
    await db.work_orders.insert_one(work_order.copy())
    await create_training_roadmap(work_order["work_order_id"], sdc_id, sdc_data.target_students)
    
    # Record allocation in target ledger
    await record_allocation(
        master_wo_id=master_wo_id,
        job_role_id=sdc_data.job_role_id,
        sdc_id=sdc_id,
        work_order_id=work_order["work_order_id"],
        num_students=sdc_data.target_students,
        user_id=user.user_id,
        user_email=user.email
    )
    
    sdc_districts = master_wo.get("sdc_districts", [])
    for dist in sdc_districts:
        if dist["district_name"].lower() == sdc_data.district_name.lower():
            if "sdcs_created" not in dist:
                dist["sdcs_created"] = []
            dist["sdcs_created"].append(sdc_id)
            break
    
    await db.master_work_orders.update_one(
        {"master_wo_id": master_wo_id},
        {"$set": {"sdc_districts": sdc_districts, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    logger.info(f"Created SDC {sdc_name} for Master WO {master_wo['work_order_number']}")
    
    return {
        "message": "SDC created successfully from Master Data",
        "sdc": sdc,
        "sdc_id": sdc_id,
        "sdc_name": sdc_name,
        "work_order": work_order,
        "contract_value": contract_value,
        "calculation": f"{sdc_data.target_students} students × {training_hours} hrs × ₹{rate}/hr",
        "allocation": {
            "allocated": sdc_data.target_students,
            "remaining_after": allocation_result.get("remaining_after", 0),
            "job_role": allocation_result.get("job_role")
        },
        "resources_locked": len(locked_resources)
    }


@router.get("/summary")
async def get_master_summary(user: User = Depends(require_ho_role)):
    """Get Master Data Summary (HO only)"""
    job_roles = await db.job_role_master.find({"is_active": True, "is_deleted": {"$ne": True}}, {"_id": 0}).to_list(1000)
    master_wos = await db.master_work_orders.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(1000)
    
    total_contract_value = sum(wo.get("total_contract_value", 0) for wo in master_wos)
    total_students = sum(wo.get("total_training_target", 0) for wo in master_wos)
    sdc_count = await db.sdcs.count_documents({"is_deleted": {"$ne": True}})
    
    return {
        "job_roles": {
            "total": len(job_roles),
            "category_a": len([jr for jr in job_roles if jr.get("category") == "A"]),
            "category_b": len([jr for jr in job_roles if jr.get("category") == "B"]),
            "custom": len([jr for jr in job_roles if jr.get("category") not in ["A", "B"]])
        },
        "work_orders": {
            "total": len(master_wos),
            "active": len([wo for wo in master_wos if wo.get("status") == "active"]),
            "completed": len([wo for wo in master_wos if wo.get("status") == "completed"])
        },
        "financials": {
            "total_contract_value": total_contract_value,
            "total_students": total_students,
            "average_per_student": round(total_contract_value / total_students, 2) if total_students > 0 else 0
        },
        "sdcs": {"total": sdc_count}
    }
