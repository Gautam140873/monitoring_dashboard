"""
Target Ledger and Resource Locking services for SkillFlow CRM
Implements strict allocation tracking and double-booking prevention
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict

from database import db
from services.audit import AuditAction, create_audit_log

logger = logging.getLogger(__name__)


# ==================== TARGET LEDGER ====================

async def get_target_ledger(master_wo_id: str) -> Dict:
    """
    Get the complete target allocation ledger for a Master Work Order.
    Shows allocated vs remaining targets for each job role.
    """
    master_wo = await db.master_work_orders.find_one(
        {"master_wo_id": master_wo_id, "is_deleted": {"$ne": True}}, 
        {"_id": 0}
    )
    if not master_wo:
        return None
    
    # Get all SDC allocations for this work order
    allocations = await db.target_ledger.find(
        {"master_wo_id": master_wo_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).to_list(1000)
    
    # Get all work orders linked to this master WO
    work_orders = await db.work_orders.find(
        {"master_wo_id": master_wo_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).to_list(1000)
    
    # Calculate allocation by job role
    job_role_ledger = {}
    for jr in master_wo.get("job_roles", []):
        jr_id = jr["job_role_id"]
        total_target = jr.get("target", 0)
        
        # Sum up allocated students for this job role
        allocated = sum(
            wo.get("num_students", 0) 
            for wo in work_orders 
            if wo.get("job_role_id") == jr_id
        )
        
        # Get SDC-wise breakdown
        sdc_allocations = [
            {
                "sdc_id": wo.get("sdc_id"),
                "work_order_id": wo.get("work_order_id"),
                "allocated": wo.get("num_students", 0),
                "status": wo.get("status", "active")
            }
            for wo in work_orders
            if wo.get("job_role_id") == jr_id
        ]
        
        job_role_ledger[jr_id] = {
            "job_role_id": jr_id,
            "job_role_code": jr.get("job_role_code", ""),
            "job_role_name": jr.get("job_role_name", ""),
            "total_target": total_target,
            "allocated": allocated,
            "remaining": max(0, total_target - allocated),
            "utilization_percent": round((allocated / total_target * 100) if total_target > 0 else 0, 1),
            "is_fully_allocated": allocated >= total_target,
            "sdc_allocations": sdc_allocations
        }
    
    return {
        "master_wo_id": master_wo_id,
        "work_order_number": master_wo.get("work_order_number"),
        "total_training_target": master_wo.get("total_training_target", 0),
        "total_allocated": sum(jr["allocated"] for jr in job_role_ledger.values()),
        "total_remaining": sum(jr["remaining"] for jr in job_role_ledger.values()),
        "job_roles": list(job_role_ledger.values()),
        "is_fully_allocated": all(jr["is_fully_allocated"] for jr in job_role_ledger.values()),
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


async def validate_allocation(
    master_wo_id: str, 
    job_role_id: str, 
    requested_students: int,
    exclude_wo_id: str = None
) -> Dict:
    """
    Validate if the requested allocation is possible without over-allocation.
    Returns validation result with remaining capacity.
    """
    ledger = await get_target_ledger(master_wo_id)
    if not ledger:
        return {
            "is_valid": False,
            "error": "Master Work Order not found",
            "remaining": 0
        }
    
    jr_data = next((jr for jr in ledger["job_roles"] if jr["job_role_id"] == job_role_id), None)
    if not jr_data:
        return {
            "is_valid": False,
            "error": f"Job Role {job_role_id} not found in this Work Order",
            "remaining": 0
        }
    
    # Calculate remaining (excluding the work order being updated if any)
    current_allocation = jr_data["allocated"]
    if exclude_wo_id:
        wo = await db.work_orders.find_one(
            {"work_order_id": exclude_wo_id, "job_role_id": job_role_id},
            {"_id": 0}
        )
        if wo:
            current_allocation -= wo.get("num_students", 0)
    
    remaining = jr_data["total_target"] - current_allocation
    
    if requested_students > remaining:
        return {
            "is_valid": False,
            "error": f"Over-allocation: Requested {requested_students} but only {remaining} remaining for {jr_data['job_role_name']}",
            "remaining": remaining,
            "requested": requested_students,
            "total_target": jr_data["total_target"],
            "currently_allocated": current_allocation
        }
    
    return {
        "is_valid": True,
        "remaining": remaining,
        "remaining_after": remaining - requested_students,
        "requested": requested_students,
        "job_role": jr_data["job_role_name"]
    }


async def record_allocation(
    master_wo_id: str,
    job_role_id: str,
    sdc_id: str,
    work_order_id: str,
    num_students: int,
    user_id: str,
    user_email: str
) -> Dict:
    """
    Record a new allocation in the target ledger.
    Called when creating SDC from Master Work Order.
    """
    allocation = {
        "ledger_id": f"ledger_{uuid.uuid4().hex[:8]}",
        "master_wo_id": master_wo_id,
        "job_role_id": job_role_id,
        "sdc_id": sdc_id,
        "work_order_id": work_order_id,
        "allocated_students": num_students,
        "status": "active",
        "allocated_at": datetime.now(timezone.utc).isoformat(),
        "allocated_by": user_id,
        "allocated_by_email": user_email,
        "is_deleted": False
    }
    
    await db.target_ledger.insert_one(allocation.copy())
    
    await create_audit_log(
        action=AuditAction.CREATE,
        entity_type="target_ledger",
        entity_id=allocation["ledger_id"],
        user_id=user_id,
        user_email=user_email,
        new_values=allocation
    )
    
    logger.info(f"Recorded allocation: {num_students} students to SDC {sdc_id} for WO {master_wo_id}")
    return allocation


# ==================== RESOURCE LOCKING ====================

async def check_resource_availability(
    resource_type: str,  # "trainer" or "manager" or "infrastructure"
    resource_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    exclude_sdc_id: str = None
) -> Dict:
    """
    Check if a resource is available for assignment.
    Prevents double-booking during overlapping timeframes.
    """
    collection_map = {
        "trainer": ("trainers", "trainer_id"),
        "manager": ("center_managers", "manager_id"),
        "infrastructure": ("sdc_infrastructure", "infra_id")
    }
    
    if resource_type not in collection_map:
        return {
            "is_available": False,
            "error": f"Unknown resource type: {resource_type}"
        }
    
    collection_name, id_field = collection_map[resource_type]
    collection = db[collection_name]
    
    # Get current resource
    resource = await collection.find_one({id_field: resource_id}, {"_id": 0})
    if not resource:
        return {
            "is_available": False,
            "error": f"{resource_type.capitalize()} not found"
        }
    
    # Check if already assigned
    current_status = resource.get("status", "available")
    current_assignment = resource.get("assigned_sdc_id") or resource.get("assigned_work_order_id")
    
    if current_status == "assigned" and current_assignment:
        # If we're excluding an SDC (update case), check if it's the same
        if exclude_sdc_id and resource.get("assigned_sdc_id") == exclude_sdc_id:
            return {
                "is_available": True,
                "message": "Resource already assigned to this SDC"
            }
        
        # Get the conflicting work order details
        conflict_sdc = await db.sdcs.find_one(
            {"sdc_id": resource.get("assigned_sdc_id")}, 
            {"_id": 0}
        )
        conflict_wo = await db.work_orders.find_one(
            {"work_order_id": resource.get("assigned_work_order_id")},
            {"_id": 0}
        )
        
        return {
            "is_available": False,
            "error": f"{resource_type.capitalize()} is already assigned",
            "conflict": {
                "sdc_id": resource.get("assigned_sdc_id"),
                "sdc_name": conflict_sdc.get("name") if conflict_sdc else "Unknown",
                "work_order_id": resource.get("assigned_work_order_id"),
                "work_order_number": conflict_wo.get("work_order_number") if conflict_wo else "Unknown"
            },
            "resource": {
                "id": resource_id,
                "name": resource.get("name") or resource.get("center_name"),
                "status": current_status
            }
        }
    
    # Check for date overlap if dates provided
    if start_date and end_date:
        # Check resource booking history for overlaps
        bookings = await db.resource_bookings.find({
            "resource_type": resource_type,
            "resource_id": resource_id,
            "status": "active",
            "$or": [
                # New booking starts during existing
                {"start_date": {"$lte": start_date}, "end_date": {"$gte": start_date}},
                # New booking ends during existing
                {"start_date": {"$lte": end_date}, "end_date": {"$gte": end_date}},
                # New booking encompasses existing
                {"start_date": {"$gte": start_date}, "end_date": {"$lte": end_date}}
            ]
        }, {"_id": 0}).to_list(100)
        
        if bookings:
            return {
                "is_available": False,
                "error": f"{resource_type.capitalize()} has conflicting bookings during this period",
                "conflicts": bookings
            }
    
    return {
        "is_available": True,
        "resource": {
            "id": resource_id,
            "name": resource.get("name") or resource.get("center_name"),
            "status": current_status
        }
    }


async def lock_resource(
    resource_type: str,
    resource_id: str,
    sdc_id: str,
    work_order_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_id: str = None,
    user_email: str = None
) -> Dict:
    """
    Lock a resource for assignment, preventing double-booking.
    """
    # First check availability
    availability = await check_resource_availability(
        resource_type, resource_id, start_date, end_date
    )
    
    if not availability["is_available"]:
        return {
            "success": False,
            **availability
        }
    
    collection_map = {
        "trainer": ("trainers", "trainer_id"),
        "manager": ("center_managers", "manager_id"),
        "infrastructure": ("sdc_infrastructure", "infra_id")
    }
    
    collection_name, id_field = collection_map[resource_type]
    collection = db[collection_name]
    
    # Update resource status
    update_data = {
        "status": "assigned",
        "assigned_sdc_id": sdc_id,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if resource_type == "trainer":
        update_data["assigned_work_order_id"] = work_order_id
    elif resource_type == "infrastructure":
        update_data["assigned_work_order_id"] = work_order_id
    
    await collection.update_one({id_field: resource_id}, {"$set": update_data})
    
    # Create booking record for tracking
    booking = {
        "booking_id": f"book_{uuid.uuid4().hex[:8]}",
        "resource_type": resource_type,
        "resource_id": resource_id,
        "sdc_id": sdc_id,
        "work_order_id": work_order_id,
        "start_date": start_date,
        "end_date": end_date,
        "status": "active",
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "locked_by": user_id,
        "locked_by_email": user_email
    }
    await db.resource_bookings.insert_one(booking.copy())
    
    logger.info(f"Locked {resource_type} {resource_id} for SDC {sdc_id}")
    
    return {
        "success": True,
        "booking_id": booking["booking_id"],
        "resource_type": resource_type,
        "resource_id": resource_id,
        "sdc_id": sdc_id
    }


async def release_resource(
    resource_type: str,
    resource_id: str,
    user_id: str = None,
    user_email: str = None
) -> Dict:
    """
    Release a locked resource, making it available again.
    """
    collection_map = {
        "trainer": ("trainers", "trainer_id"),
        "manager": ("center_managers", "manager_id"),
        "infrastructure": ("sdc_infrastructure", "infra_id")
    }
    
    if resource_type not in collection_map:
        return {"success": False, "error": f"Unknown resource type: {resource_type}"}
    
    collection_name, id_field = collection_map[resource_type]
    collection = db[collection_name]
    
    # Update resource status
    await collection.update_one(
        {id_field: resource_id},
        {"$set": {
            "status": "available",
            "assigned_sdc_id": None,
            "assigned_work_order_id": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Mark booking as completed
    await db.resource_bookings.update_many(
        {"resource_id": resource_id, "status": "active"},
        {"$set": {
            "status": "completed",
            "released_at": datetime.now(timezone.utc).isoformat(),
            "released_by": user_id
        }}
    )
    
    logger.info(f"Released {resource_type} {resource_id}")
    
    return {"success": True, "message": f"{resource_type.capitalize()} released successfully"}


async def get_resource_booking_history(resource_type: str, resource_id: str) -> List:
    """Get booking history for a resource."""
    bookings = await db.resource_bookings.find(
        {"resource_type": resource_type, "resource_id": resource_id},
        {"_id": 0}
    ).sort("locked_at", -1).to_list(100)
    return bookings


# ==================== BURN-DOWN DATA ====================

async def get_burndown_data(master_wo_id: str = None) -> Dict:
    """
    Get burn-down data for Work Order progress visualization.
    Shows: Unallocated → In-Training → Placed
    """
    query = {"is_deleted": {"$ne": True}}
    if master_wo_id:
        query["master_wo_id"] = master_wo_id
    
    # Get all master work orders
    master_wos = await db.master_work_orders.find(query, {"_id": 0}).to_list(1000)
    
    burndown_data = []
    
    for mwo in master_wos:
        mwo_id = mwo["master_wo_id"]
        total_target = mwo.get("total_training_target", 0)
        
        # Get all work orders for this master WO
        work_orders = await db.work_orders.find(
            {"master_wo_id": mwo_id, "is_deleted": {"$ne": True}},
            {"_id": 0}
        ).to_list(1000)
        
        # Get all SDC processes for progress data
        sdc_ids = [wo.get("sdc_id") for wo in work_orders]
        processes = await db.sdc_processes.find(
            {"sdc_id": {"$in": sdc_ids}},
            {"_id": 0}
        ).to_list(1000)
        
        # Calculate totals
        total_allocated = sum(wo.get("num_students", 0) for wo in work_orders)
        unallocated = max(0, total_target - total_allocated)
        
        # Sum up process stages
        total_mobilized = 0
        total_in_training = 0
        total_ojt = 0
        total_assessed = 0
        total_placed = 0
        
        for proc in processes:
            stages = proc.get("stages", {})
            total_mobilized += stages.get("mobilization", {}).get("completed", 0)
            total_in_training += stages.get("training", {}).get("completed", 0)
            total_ojt += stages.get("ojt", {}).get("completed", 0)
            total_assessed += stages.get("assessment", {}).get("completed", 0)
            total_placed += stages.get("placement", {}).get("completed", 0)
        
        # Also get from training_roadmaps for backward compatibility
        roadmaps = await db.training_roadmaps.find(
            {"work_order_id": {"$in": [wo["work_order_id"] for wo in work_orders]}},
            {"_id": 0}
        ).to_list(1000)
        
        for rm in roadmaps:
            stage_id = rm.get("stage_id")
            completed = rm.get("completed_count", 0)
            if stage_id == "mobilization":
                total_mobilized = max(total_mobilized, completed)
            elif stage_id == "classroom_training":
                total_in_training = max(total_in_training, completed)
            elif stage_id == "ojt":
                total_ojt = max(total_ojt, completed)
            elif stage_id == "assessment":
                total_assessed = max(total_assessed, completed)
            elif stage_id == "placement":
                total_placed = max(total_placed, completed)
        
        # Calculate pipeline stages
        awaiting_training = max(0, total_mobilized - total_in_training)
        in_training = max(0, total_in_training - total_ojt)
        in_ojt = max(0, total_ojt - total_assessed)
        awaiting_placement = max(0, total_assessed - total_placed)
        
        burndown_data.append({
            "master_wo_id": mwo_id,
            "work_order_number": mwo.get("work_order_number"),
            "awarding_body": mwo.get("awarding_body"),
            "scheme_name": mwo.get("scheme_name"),
            "total_target": total_target,
            "pipeline": {
                "unallocated": unallocated,
                "allocated_not_started": max(0, total_allocated - total_mobilized),
                "mobilized": total_mobilized,
                "awaiting_training": awaiting_training,
                "in_training": in_training,
                "in_ojt": in_ojt,
                "awaiting_placement": awaiting_placement,
                "placed": total_placed
            },
            "summary": {
                "total_allocated": total_allocated,
                "total_mobilized": total_mobilized,
                "total_placed": total_placed,
                "completion_percent": round((total_placed / total_target * 100) if total_target > 0 else 0, 1)
            },
            "sdcs_count": len(set(sdc_ids)),
            "status": mwo.get("status", "active")
        })
    
    # Calculate overall totals
    overall = {
        "total_work_orders": len(master_wos),
        "total_target": sum(d["total_target"] for d in burndown_data),
        "total_allocated": sum(d["summary"]["total_allocated"] for d in burndown_data),
        "total_mobilized": sum(d["summary"]["total_mobilized"] for d in burndown_data),
        "total_placed": sum(d["summary"]["total_placed"] for d in burndown_data),
        "total_unallocated": sum(d["pipeline"]["unallocated"] for d in burndown_data)
    }
    overall["overall_completion"] = round(
        (overall["total_placed"] / overall["total_target"] * 100) 
        if overall["total_target"] > 0 else 0, 1
    )
    
    return {
        "work_orders": burndown_data,
        "overall": overall,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
