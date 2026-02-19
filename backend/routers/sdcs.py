"""
SDC (Skill Development Center) router for SkillFlow CRM
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone
import uuid
import logging

from ..database import db
from ..models.user import User
from ..models.schemas import SDCCreate, StageUpdateRequest, DeliverableUpdateRequest
from ..services.auth import get_current_user, require_ho_role
from ..services.audit import AuditAction, create_audit_log
from ..services.soft_delete import soft_delete_document
from ..services.utils import get_or_create_sdc
from ..config import TRAINING_STAGES, PROCESS_STAGES, DELIVERABLES

router = APIRouter(prefix="/sdcs", tags=["SDCs"])
logger = logging.getLogger(__name__)


@router.get("")
async def list_sdcs(user: User = Depends(get_current_user)):
    """List SDCs (filtered by role)"""
    if user.role in ["ho", "admin"]:
        sdcs = await db.sdcs.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(1000)
    else:
        if user.assigned_sdc_id:
            sdcs = await db.sdcs.find({"sdc_id": user.assigned_sdc_id, "is_deleted": {"$ne": True}}, {"_id": 0}).to_list(1000)
        else:
            sdcs = []
    return sdcs


@router.post("")
async def create_sdc(sdc_data: SDCCreate, user: User = Depends(require_ho_role)):
    """Create new SDC (HO only)"""
    sdc = await get_or_create_sdc(sdc_data.location, sdc_data.manager_email)
    if sdc_data.name != sdc["name"]:
        await db.sdcs.update_one(
            {"sdc_id": sdc["sdc_id"]},
            {"$set": {"name": sdc_data.name}}
        )
        sdc["name"] = sdc_data.name
    return sdc


@router.get("/{sdc_id}")
async def get_sdc(sdc_id: str, user: User = Depends(get_current_user)):
    """Get SDC details with work orders and progress"""
    if user.role not in ["ho", "admin"] and user.assigned_sdc_id != sdc_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    sdc = await db.sdcs.find_one({"sdc_id": sdc_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not sdc:
        raise HTTPException(status_code=404, detail="SDC not found")
    
    work_orders = await db.work_orders.find({"sdc_id": sdc_id, "is_deleted": {"$ne": True}}, {"_id": 0}).to_list(1000)
    roadmaps = await db.training_roadmaps.find({"sdc_id": sdc_id}, {"_id": 0}).to_list(1000)
    
    stage_progress = {}
    for stage in TRAINING_STAGES:
        stage_roadmaps = [r for r in roadmaps if r["stage_id"] == stage["stage_id"]]
        total_target = sum(r.get("target_count", 0) for r in stage_roadmaps)
        total_completed = sum(r.get("completed_count", 0) for r in stage_roadmaps)
        stage_progress[stage["stage_id"]] = {
            "name": stage["name"],
            "order": stage["order"],
            "target": total_target,
            "completed": total_completed,
            "percent": round((total_completed / total_target * 100) if total_target > 0 else 0, 1)
        }
    
    invoices = await db.invoices.find({"sdc_id": sdc_id}, {"_id": 0}).to_list(1000)
    total_order_value = sum(inv.get("order_value", 0) for inv in invoices)
    total_billed = sum(inv.get("billing_value", 0) for inv in invoices)
    total_paid = sum(inv.get("payment_received", 0) for inv in invoices)
    total_outstanding = sum(inv.get("outstanding", 0) for inv in invoices)
    total_contract = sum(wo.get("total_contract_value", 0) for wo in work_orders)
    
    return {
        **sdc,
        "work_orders": work_orders,
        "stage_progress": stage_progress,
        "financial": {
            "total_contract": total_contract,
            "total_order_value": total_order_value,
            "total_billed": total_billed,
            "total_paid": total_paid,
            "total_outstanding": total_outstanding,
            "variance": total_order_value - total_billed if total_order_value > 0 else 0
        },
        "invoices": invoices
    }


@router.get("/{sdc_id}/process-status")
async def get_sdc_process_status(sdc_id: str, user: User = Depends(get_current_user)):
    """Get SDC process status with sequential stages and deliverables"""
    if user.role == "sdc" and user.assigned_sdc_id != sdc_id:
        raise HTTPException(status_code=403, detail="Access denied to this SDC")
    
    sdc = await db.sdcs.find_one({"sdc_id": sdc_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not sdc:
        raise HTTPException(status_code=404, detail="SDC not found")
    
    target_students = sdc.get("target_students", 0)
    process_data = await db.sdc_processes.find_one({"sdc_id": sdc_id}, {"_id": 0})
    
    if not process_data:
        process_data = {
            "process_id": f"proc_{uuid.uuid4().hex[:8]}",
            "sdc_id": sdc_id,
            "target_students": target_students,
            "stages": {},
            "deliverables": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        for stage in PROCESS_STAGES:
            process_data["stages"][stage["stage_id"]] = {
                "stage_id": stage["stage_id"],
                "name": stage["name"],
                "order": stage["order"],
                "description": stage["description"],
                "target": target_students,
                "completed": 0,
                "in_progress": 0,
                "pending": target_students,
                "status": "pending",
                "start_date": None,
                "end_date": None,
                "notes": ""
            }
        
        for deliv in DELIVERABLES:
            process_data["deliverables"][deliv["deliverable_id"]] = {
                "deliverable_id": deliv["deliverable_id"],
                "name": deliv["name"],
                "description": deliv["description"],
                "status": "pending",
                "completed_date": None,
                "notes": ""
            }
        
        await db.sdc_processes.insert_one(process_data.copy())
    
    stages_list = []
    prev_stage_status = "completed"
    prev_stage_completed = target_students
    
    for idx, stage in enumerate(PROCESS_STAGES):
        stage_data = process_data["stages"].get(stage["stage_id"], {})
        can_start = prev_stage_status in ["completed", "in_progress"]
        
        if idx == 0:
            max_allowed = target_students
        else:
            max_allowed = prev_stage_completed
        
        completed = stage_data.get("completed", 0)
        progress_percent = round((completed / max_allowed * 100) if max_allowed > 0 else 0, 1)
        
        stages_list.append({
            **stage,
            "target": target_students,
            "max_allowed": max_allowed,
            "completed": completed,
            "in_progress": stage_data.get("in_progress", 0),
            "pending": max(0, max_allowed - completed - stage_data.get("in_progress", 0)),
            "progress_percent": progress_percent,
            "status": stage_data.get("status", "pending"),
            "can_start": can_start,
            "start_date": stage_data.get("start_date"),
            "end_date": stage_data.get("end_date"),
            "notes": stage_data.get("notes", "")
        })
        
        prev_stage_status = stage_data.get("status", "pending")
        prev_stage_completed = completed
    
    deliverables_list = []
    for deliv in DELIVERABLES:
        deliv_data = process_data["deliverables"].get(deliv["deliverable_id"], {})
        deliverables_list.append({
            **deliv,
            "status": deliv_data.get("status", "pending"),
            "completed_date": deliv_data.get("completed_date"),
            "notes": deliv_data.get("notes", "")
        })
    
    total_completed = sum(s["completed"] for s in stages_list)
    total_target = sum(s["target"] for s in stages_list)
    overall_progress = round((total_completed / total_target * 100) if total_target > 0 else 0, 1)
    
    return {
        "sdc_id": sdc_id,
        "sdc_name": sdc.get("name", ""),
        "target_students": target_students,
        "overall_progress": overall_progress,
        "stages": stages_list,
        "deliverables": deliverables_list,
        "process_definitions": {
            "stages": PROCESS_STAGES,
            "deliverables": DELIVERABLES
        }
    }


@router.put("/{sdc_id}/process-status/stage/{stage_id}")
async def update_process_stage(
    sdc_id: str, 
    stage_id: str, 
    completed: int = None,
    in_progress: int = None,
    status: str = None,
    start_date: str = None,
    end_date: str = None,
    notes: str = None,
    user: User = Depends(require_ho_role)
):
    """Update a process stage for an SDC"""
    valid_stages = [s["stage_id"] for s in PROCESS_STAGES]
    if stage_id not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage_id. Must be one of: {valid_stages}")
    
    sdc = await db.sdcs.find_one({"sdc_id": sdc_id}, {"_id": 0, "target_students": 1})
    if not sdc:
        raise HTTPException(status_code=404, detail="SDC not found")
    target_students = sdc.get("target_students", 0)
    
    process_data = await db.sdc_processes.find_one({"sdc_id": sdc_id})
    if not process_data:
        await get_sdc_process_status(sdc_id, user)
        process_data = await db.sdc_processes.find_one({"sdc_id": sdc_id})
    
    # Validation: sequential stage completion
    if completed is not None:
        stages_data = process_data.get("stages", {})
        stage_order = ["mobilization", "training", "ojt", "assessment", "placement"]
        stage_idx = stage_order.index(stage_id) if stage_id in stage_order else -1
        
        if stage_idx == 0:
            max_allowed = target_students
            if completed > max_allowed:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Mobilization cannot exceed target students ({target_students})"
                )
        elif stage_idx > 0:
            prev_stage_id = stage_order[stage_idx - 1]
            prev_completed = stages_data.get(prev_stage_id, {}).get("completed", 0)
            
            if completed > prev_completed:
                prev_stage_name = next((s["name"] for s in PROCESS_STAGES if s["stage_id"] == prev_stage_id), prev_stage_id)
                current_stage_name = next((s["name"] for s in PROCESS_STAGES if s["stage_id"] == stage_id), stage_id)
                raise HTTPException(
                    status_code=400, 
                    detail=f"{current_stage_name} ({completed}) cannot exceed {prev_stage_name} completed ({prev_completed})"
                )
    
    update_fields = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if completed is not None:
        update_fields[f"stages.{stage_id}.completed"] = completed
        stages_data = process_data.get("stages", {})
        stage_order = ["mobilization", "training", "ojt", "assessment", "placement"]
        stage_idx = stage_order.index(stage_id) if stage_id in stage_order else -1
        
        if stage_idx == 0:
            max_for_stage = target_students
        else:
            prev_stage_id = stage_order[stage_idx - 1]
            max_for_stage = stages_data.get(prev_stage_id, {}).get("completed", 0)
        
        if completed >= max_for_stage and max_for_stage > 0:
            update_fields[f"stages.{stage_id}.status"] = "completed"
        elif completed > 0:
            update_fields[f"stages.{stage_id}.status"] = "in_progress"
    
    if in_progress is not None:
        update_fields[f"stages.{stage_id}.in_progress"] = in_progress
    
    if status is not None:
        if status not in ["pending", "in_progress", "completed"]:
            raise HTTPException(status_code=400, detail="Status must be: pending, in_progress, or completed")
        update_fields[f"stages.{stage_id}.status"] = status
    
    if start_date is not None:
        update_fields[f"stages.{stage_id}.start_date"] = start_date
    
    if end_date is not None:
        update_fields[f"stages.{stage_id}.end_date"] = end_date
    
    if notes is not None:
        update_fields[f"stages.{stage_id}.notes"] = notes
    
    await db.sdc_processes.update_one(
        {"sdc_id": sdc_id},
        {"$set": update_fields}
    )
    
    await create_audit_log(
        action=AuditAction.UPDATE,
        entity_type="sdc_processes",
        entity_id=sdc_id,
        user_id=user.user_id,
        user_email=user.email,
        changes=update_fields
    )
    
    return {"message": f"Stage {stage_id} updated successfully"}


@router.put("/{sdc_id}/process-status/deliverable/{deliverable_id}")
async def update_deliverable_status(
    sdc_id: str,
    deliverable_id: str,
    status: str,
    notes: str = None,
    user: User = Depends(require_ho_role)
):
    """Update a deliverable status for an SDC"""
    valid_deliverables = [d["deliverable_id"] for d in DELIVERABLES]
    if deliverable_id not in valid_deliverables:
        raise HTTPException(status_code=400, detail=f"Invalid deliverable_id. Must be one of: {valid_deliverables}")
    
    if status not in ["pending", "completed", "not_required"]:
        raise HTTPException(status_code=400, detail="Status must be: pending, completed, or not_required")
    
    process_data = await db.sdc_processes.find_one({"sdc_id": sdc_id})
    if not process_data:
        await get_sdc_process_status(sdc_id, user)
    
    update_fields = {
        f"deliverables.{deliverable_id}.status": status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if status == "completed":
        update_fields[f"deliverables.{deliverable_id}.completed_date"] = datetime.now(timezone.utc).isoformat()
    
    if notes is not None:
        update_fields[f"deliverables.{deliverable_id}.notes"] = notes
    
    await db.sdc_processes.update_one(
        {"sdc_id": sdc_id},
        {"$set": update_fields}
    )
    
    return {"message": f"Deliverable {deliverable_id} updated to {status}"}


@router.delete("/{sdc_id}")
async def delete_sdc(sdc_id: str, user: User = Depends(require_ho_role)):
    """Soft delete SDC (HO only) - Can be recovered within 30 days"""
    sdc = await db.sdcs.find_one({"sdc_id": sdc_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not sdc:
        raise HTTPException(status_code=404, detail="SDC not found")
    
    success = await soft_delete_document(
        collection_name="sdcs",
        query={"sdc_id": sdc_id},
        user_id=user.user_id,
        user_email=user.email
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete SDC")
    
    await db.work_orders.update_many(
        {"sdc_id": sdc_id},
        {"$set": {
            "is_deleted": True,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
            "deleted_by": user.user_id,
            "deleted_by_email": user.email
        }}
    )
    
    return {
        "message": "SDC deleted successfully. Can be recovered within 30 days.",
        "sdc_id": sdc_id,
        "recovery_days": 30
    }
