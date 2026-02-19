"""
Resources router for SkillFlow CRM - Trainers, Managers, Infrastructure
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone
import uuid
import logging

from ..database import db
from ..models.user import User
from ..models.schemas import (
    TrainerCreate, TrainerUpdate,
    CenterManagerCreate, CenterManagerUpdate,
    SDCInfrastructureCreate, SDCInfrastructureUpdate
)
from ..services.auth import get_current_user, require_ho_role

router = APIRouter(prefix="/resources", tags=["Resources"])
logger = logging.getLogger(__name__)


# --- TRAINERS ---
@router.get("/trainers")
async def list_trainers(status: Optional[str] = None, user: User = Depends(require_ho_role)):
    """List all trainers (HO only)"""
    query = {"is_active": True}
    if status:
        query["status"] = status
    trainers = await db.trainers.find(query, {"_id": 0}).to_list(1000)
    return trainers


@router.get("/trainers/available")
async def list_available_trainers(user: User = Depends(get_current_user)):
    """List available trainers for dropdown"""
    trainers = await db.trainers.find({"is_active": True, "status": "available"}, {"_id": 0}).to_list(1000)
    return trainers


@router.post("/trainers")
async def create_trainer(data: TrainerCreate, user: User = Depends(require_ho_role)):
    """Create a new trainer (HO only)"""
    existing = await db.trainers.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail=f"Trainer with email {data.email} already exists")
    
    trainer = {
        "trainer_id": f"tr_{uuid.uuid4().hex[:8]}",
        "name": data.name,
        "email": data.email,
        "phone": data.phone,
        "qualification": data.qualification,
        "specialization": data.specialization,
        "domain": data.domain,
        "experience_years": data.experience_years,
        "nsqf_level": data.nsqf_level,
        "certifications": data.certifications,
        "status": "available",
        "assigned_sdc_id": None,
        "assigned_work_order_id": None,
        "address": data.address,
        "city": data.city,
        "state": data.state,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    trainer_to_insert = trainer.copy()
    await db.trainers.insert_one(trainer_to_insert)
    logger.info(f"Created trainer: {data.name}")
    return trainer


@router.put("/trainers/{trainer_id}")
async def update_trainer(trainer_id: str, data: TrainerUpdate, user: User = Depends(require_ho_role)):
    """Update trainer (HO only)"""
    trainer = await db.trainers.find_one({"trainer_id": trainer_id})
    if not trainer:
        raise HTTPException(status_code=404, detail="Trainer not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    for field in ["name", "email", "phone", "qualification", "specialization", "domain",
                  "experience_years", "nsqf_level", "certifications", "address", "city", "state", "status", "is_active"]:
        value = getattr(data, field, None)
        if value is not None:
            update_data[field] = value
    
    await db.trainers.update_one({"trainer_id": trainer_id}, {"$set": update_data})
    return {"message": "Trainer updated successfully"}


@router.post("/trainers/{trainer_id}/assign")
async def assign_trainer(trainer_id: str, sdc_id: str, work_order_id: str, user: User = Depends(require_ho_role)):
    """Assign trainer to SDC/Work Order (HO only)"""
    trainer = await db.trainers.find_one({"trainer_id": trainer_id})
    if not trainer:
        raise HTTPException(status_code=404, detail="Trainer not found")
    
    if trainer.get("status") != "available":
        raise HTTPException(status_code=400, detail="Trainer is not available")
    
    await db.trainers.update_one(
        {"trainer_id": trainer_id},
        {"$set": {
            "status": "assigned",
            "assigned_sdc_id": sdc_id,
            "assigned_work_order_id": work_order_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"message": f"Trainer assigned to SDC {sdc_id}"}


@router.post("/trainers/{trainer_id}/release")
async def release_trainer(trainer_id: str, user: User = Depends(require_ho_role)):
    """Release trainer (mark as available) (HO only)"""
    await db.trainers.update_one(
        {"trainer_id": trainer_id},
        {"$set": {
            "status": "available",
            "assigned_sdc_id": None,
            "assigned_work_order_id": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"message": "Trainer released and now available"}


# --- CENTER MANAGERS ---
@router.get("/managers")
async def list_managers(status: Optional[str] = None, user: User = Depends(require_ho_role)):
    """List all center managers (HO only)"""
    query = {"is_active": True}
    if status:
        query["status"] = status
    managers = await db.center_managers.find(query, {"_id": 0}).to_list(1000)
    return managers


@router.get("/managers/available")
async def list_available_managers(user: User = Depends(get_current_user)):
    """List available managers for dropdown"""
    managers = await db.center_managers.find({"is_active": True, "status": "available"}, {"_id": 0}).to_list(1000)
    return managers


@router.post("/managers")
async def create_manager(data: CenterManagerCreate, user: User = Depends(require_ho_role)):
    """Create a new center manager (HO only)"""
    existing = await db.center_managers.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail=f"Manager with email {data.email} already exists")
    
    manager = {
        "manager_id": f"cm_{uuid.uuid4().hex[:8]}",
        "name": data.name,
        "email": data.email,
        "phone": data.phone,
        "qualification": data.qualification,
        "experience_years": data.experience_years,
        "status": "available",
        "assigned_sdc_id": None,
        "address": data.address,
        "city": data.city,
        "state": data.state,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    manager_to_insert = manager.copy()
    await db.center_managers.insert_one(manager_to_insert)
    logger.info(f"Created center manager: {data.name}")
    return manager


@router.put("/managers/{manager_id}")
async def update_manager(manager_id: str, data: CenterManagerUpdate, user: User = Depends(require_ho_role)):
    """Update center manager (HO only)"""
    manager = await db.center_managers.find_one({"manager_id": manager_id})
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    for field in ["name", "email", "phone", "qualification", "experience_years", 
                  "address", "city", "state", "status", "is_active"]:
        value = getattr(data, field, None)
        if value is not None:
            update_data[field] = value
    
    await db.center_managers.update_one({"manager_id": manager_id}, {"$set": update_data})
    return {"message": "Manager updated successfully"}


@router.post("/managers/{manager_id}/assign")
async def assign_manager(manager_id: str, sdc_id: str, user: User = Depends(require_ho_role)):
    """Assign manager to SDC (HO only)"""
    manager = await db.center_managers.find_one({"manager_id": manager_id})
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    
    if manager.get("status") != "available":
        raise HTTPException(status_code=400, detail="Manager is not available")
    
    await db.center_managers.update_one(
        {"manager_id": manager_id},
        {"$set": {
            "status": "assigned",
            "assigned_sdc_id": sdc_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"message": f"Manager assigned to SDC {sdc_id}"}


@router.post("/managers/{manager_id}/release")
async def release_manager(manager_id: str, user: User = Depends(require_ho_role)):
    """Release manager (mark as available) (HO only)"""
    await db.center_managers.update_one(
        {"manager_id": manager_id},
        {"$set": {
            "status": "available",
            "assigned_sdc_id": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"message": "Manager released and now available"}


# --- SDC INFRASTRUCTURE ---
@router.get("/infrastructure")
async def list_infrastructure(status: Optional[str] = None, user: User = Depends(require_ho_role)):
    """List all SDC infrastructure (HO only)"""
    query = {"is_active": True}
    if status:
        query["status"] = status
    infrastructure = await db.sdc_infrastructure.find(query, {"_id": 0}).to_list(1000)
    return infrastructure


@router.get("/infrastructure/available")
async def list_available_infrastructure(user: User = Depends(get_current_user)):
    """List available infrastructure for dropdown"""
    infrastructure = await db.sdc_infrastructure.find(
        {"is_active": True, "status": "available"}, 
        {"_id": 0}
    ).to_list(1000)
    return infrastructure


@router.post("/infrastructure")
async def create_infrastructure(data: SDCInfrastructureCreate, user: User = Depends(require_ho_role)):
    """Create SDC infrastructure (HO only)"""
    existing = await db.sdc_infrastructure.find_one({"center_code": data.center_code})
    if existing:
        raise HTTPException(status_code=400, detail=f"Infrastructure with code {data.center_code} already exists")
    
    infra = {
        "infra_id": f"infra_{uuid.uuid4().hex[:8]}",
        "center_name": data.center_name,
        "center_code": data.center_code,
        "district": data.district,
        "address_line1": data.address_line1,
        "address_line2": data.address_line2,
        "city": data.city,
        "state": data.state,
        "pincode": data.pincode,
        "contact_phone": data.contact_phone,
        "contact_email": data.contact_email,
        "total_capacity": data.total_capacity,
        "num_classrooms": data.num_classrooms,
        "num_computer_labs": data.num_computer_labs,
        "has_projector": data.has_projector,
        "has_ac": data.has_ac,
        "has_library": data.has_library,
        "has_biometric": data.has_biometric,
        "has_internet": data.has_internet,
        "has_fire_safety": data.has_fire_safety,
        "other_facilities": data.other_facilities,
        "status": "available",
        "assigned_work_order_id": None,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    infra_to_insert = infra.copy()
    await db.sdc_infrastructure.insert_one(infra_to_insert)
    logger.info(f"Created SDC infrastructure: {data.center_name}")
    return infra


@router.put("/infrastructure/{infra_id}")
async def update_infrastructure(infra_id: str, data: SDCInfrastructureUpdate, user: User = Depends(require_ho_role)):
    """Update SDC infrastructure (HO only)"""
    infra = await db.sdc_infrastructure.find_one({"infra_id": infra_id})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastructure not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    for field in ["center_name", "address_line1", "address_line2", "city", "state", "pincode",
                  "contact_phone", "contact_email", "total_capacity", "num_classrooms", 
                  "num_computer_labs", "has_projector", "has_ac", "has_library", 
                  "has_biometric", "has_internet", "has_fire_safety",
                  "other_facilities", "status", "is_active"]:
        value = getattr(data, field, None)
        if value is not None:
            update_data[field] = value
    
    await db.sdc_infrastructure.update_one({"infra_id": infra_id}, {"$set": update_data})
    return {"message": "Infrastructure updated successfully"}


@router.post("/infrastructure/{infra_id}/assign")
async def assign_infrastructure(infra_id: str, work_order_id: str, user: User = Depends(require_ho_role)):
    """Assign infrastructure to work order (HO only)"""
    infra = await db.sdc_infrastructure.find_one({"infra_id": infra_id})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastructure not found")
    
    if infra.get("status") != "available":
        raise HTTPException(status_code=400, detail="Infrastructure is not available")
    
    await db.sdc_infrastructure.update_one(
        {"infra_id": infra_id},
        {"$set": {
            "status": "in_use",
            "assigned_work_order_id": work_order_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"message": f"Infrastructure assigned to work order {work_order_id}"}


@router.post("/infrastructure/{infra_id}/release")
async def release_infrastructure(infra_id: str, user: User = Depends(require_ho_role)):
    """Release infrastructure (mark as available) (HO only)"""
    await db.sdc_infrastructure.update_one(
        {"infra_id": infra_id},
        {"$set": {
            "status": "available",
            "assigned_work_order_id": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"message": "Infrastructure released and now available"}


# --- RESOURCE SUMMARY ---
@router.get("/summary")
async def get_resources_summary(user: User = Depends(require_ho_role)):
    """Get summary of all resources (HO only)"""
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
