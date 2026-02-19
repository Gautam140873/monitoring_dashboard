"""
SkillFlow CRM API - Modular Backend Server
Refactored from monolithic structure to modular architecture
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
import os
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

# Internal imports
from database import db, client
from config import TRAINING_STAGES, PROCESS_STAGES, DELIVERABLES
from models.user import User
from models.schemas import (
    InvoiceCreate, PaymentUpdate, HolidayCreate,
    WorkOrderCreate, WorkOrderStartDate, RoadmapUpdate
)
from services.auth import get_current_user, require_ho_role
from services.utils import calculate_end_date, get_or_create_sdc, create_training_roadmap

# Import routers
from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.master_data import router as master_data_router
from routers.resources import router as resources_router
from routers.sdcs import router as sdcs_router
from routers.dashboard import router as dashboard_router

# Create the main app
app = FastAPI(title="SkillFlow CRM API", version="3.0.0")

# Create main API router
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== INVOICE & BILLING ENDPOINTS ====================

@api_router.post("/invoices")
async def create_invoice(invoice_data: InvoiceCreate, user: User = Depends(get_current_user)):
    """Create invoice with variance calculation"""
    if user.role not in ["ho", "admin"] and user.assigned_sdc_id != invoice_data.sdc_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    variance = invoice_data.order_value - invoice_data.billing_value
    variance_percent = round((variance / invoice_data.order_value * 100) if invoice_data.order_value > 0 else 0, 1)
    outstanding = invoice_data.billing_value
    
    invoice = {
        "invoice_id": f"inv_{uuid.uuid4().hex[:8]}",
        "sdc_id": invoice_data.sdc_id,
        "work_order_id": invoice_data.work_order_id,
        "invoice_number": invoice_data.invoice_number,
        "invoice_date": invoice_data.invoice_date,
        "order_value": invoice_data.order_value,
        "billing_value": invoice_data.billing_value,
        "variance": variance,
        "variance_percent": variance_percent,
        "payment_received": 0,
        "outstanding": outstanding,
        "status": "pending",
        "payment_date": None,
        "notes": invoice_data.notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.invoices.insert_one(invoice.copy())
    
    if abs(variance_percent) > 10:
        sdc = await db.sdcs.find_one({"sdc_id": invoice_data.sdc_id}, {"_id": 0})
        alert = {
            "alert_id": f"alert_{uuid.uuid4().hex[:8]}",
            "sdc_id": invoice_data.sdc_id,
            "sdc_name": sdc["name"] if sdc else invoice_data.sdc_id,
            "work_order_id": invoice_data.work_order_id,
            "alert_type": "variance",
            "message": f"Billing variance of {variance_percent}% detected on invoice {invoice_data.invoice_number}",
            "severity": "high" if abs(variance_percent) > 25 else "medium",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "resolved": False
        }
        await db.alerts.insert_one(alert.copy())
    
    return invoice


@api_router.get("/invoices")
async def list_invoices(sdc_id: Optional[str] = None, user: User = Depends(get_current_user)):
    """List invoices"""
    query = {}
    if user.role not in ["ho", "admin"]:
        if user.assigned_sdc_id:
            query["sdc_id"] = user.assigned_sdc_id
        else:
            return []
    elif sdc_id:
        query["sdc_id"] = sdc_id
    
    invoices = await db.invoices.find(query, {"_id": 0}).to_list(1000)
    return invoices


@api_router.put("/invoices/{invoice_id}/payment")
async def record_payment(invoice_id: str, payment: PaymentUpdate, user: User = Depends(get_current_user)):
    """Record payment received - triggers status update"""
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if user.role not in ["ho", "admin"] and user.assigned_sdc_id != invoice["sdc_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    new_payment = payment.payment_received
    new_outstanding = invoice["billing_value"] - new_payment
    
    if new_outstanding <= 0:
        new_status = "paid"
    elif new_payment > 0:
        new_status = "partial"
    else:
        new_status = "pending"
    
    await db.invoices.update_one(
        {"invoice_id": invoice_id},
        {"$set": {
            "payment_received": new_payment,
            "outstanding": max(0, new_outstanding),
            "status": new_status,
            "payment_date": payment.payment_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        }}
    )
    
    if new_status == "paid" and invoice.get("work_order_id"):
        await db.training_roadmaps.update_many(
            {"work_order_id": invoice["work_order_id"], "status": "completed"},
            {"$set": {"status": "paid", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        logger.info(f"Payment trigger: Marked roadmap stages as PAID for work order {invoice['work_order_id']}")
    
    return {
        "message": "Payment recorded",
        "new_status": new_status,
        "outstanding": max(0, new_outstanding)
    }


# ==================== HOLIDAY ENDPOINTS ====================

@api_router.get("/holidays")
async def list_holidays(year: Optional[int] = None, sdc_id: Optional[str] = None, user: User = Depends(get_current_user)):
    """List holidays"""
    query = {}
    if year:
        query["year"] = year
    if sdc_id:
        query["$or"] = [{"is_local": False}, {"sdc_id": sdc_id}]
    
    holidays = await db.holidays.find(query, {"_id": 0}).to_list(1000)
    return holidays


@api_router.post("/holidays")
async def create_holiday(holiday_data: HolidayCreate, user: User = Depends(get_current_user)):
    """Create holiday (HO for global, Local Manager for local)"""
    if holiday_data.is_local:
        if not holiday_data.sdc_id:
            raise HTTPException(status_code=400, detail="SDC ID required for local holiday")
        if user.role not in ["ho", "admin"] and user.assigned_sdc_id != holiday_data.sdc_id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        if user.role not in ["ho", "admin"]:
            raise HTTPException(status_code=403, detail="HO access required for global holidays")
    
    holiday = {
        "holiday_id": f"hol_{uuid.uuid4().hex[:8]}",
        "date": holiday_data.date,
        "name": holiday_data.name,
        "year": holiday_data.year,
        "is_local": holiday_data.is_local,
        "sdc_id": holiday_data.sdc_id if holiday_data.is_local else None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.holidays.insert_one(holiday.copy())
    return holiday


@api_router.delete("/holidays/{holiday_id}")
async def delete_holiday(holiday_id: str, user: User = Depends(get_current_user)):
    """Delete holiday"""
    holiday = await db.holidays.find_one({"holiday_id": holiday_id}, {"_id": 0})
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")
    
    if holiday.get("is_local"):
        if user.role not in ["ho", "admin"] and user.assigned_sdc_id != holiday.get("sdc_id"):
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        if user.role not in ["ho", "admin"]:
            raise HTTPException(status_code=403, detail="HO access required")
    
    await db.holidays.delete_one({"holiday_id": holiday_id})
    return {"message": "Holiday deleted"}


# ==================== WORK ORDER ENDPOINTS ====================

@api_router.post("/work-orders")
async def create_work_order(wo_data: WorkOrderCreate, user: User = Depends(require_ho_role)):
    """Create a new Work Order (Master Entry) - HO Only"""
    sdc = await get_or_create_sdc(wo_data.location, wo_data.manager_email)
    
    total_contract_value = wo_data.num_students * wo_data.cost_per_student
    
    work_order = {
        "work_order_id": f"wo_{uuid.uuid4().hex[:8]}",
        "work_order_number": wo_data.work_order_number,
        "sdc_id": sdc["sdc_id"],
        "location": wo_data.location,
        "job_role_code": wo_data.job_role_code,
        "job_role_name": wo_data.job_role_name,
        "awarding_body": wo_data.awarding_body,
        "scheme_name": wo_data.scheme_name,
        "total_training_hours": wo_data.total_training_hours,
        "sessions_per_day": wo_data.sessions_per_day,
        "num_students": wo_data.num_students,
        "cost_per_student": wo_data.cost_per_student,
        "total_contract_value": total_contract_value,
        "manager_email": wo_data.manager_email,
        "start_date": None,
        "calculated_end_date": None,
        "manual_end_date": None,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.user_id
    }
    
    await db.work_orders.insert_one(work_order.copy())
    await create_training_roadmap(work_order["work_order_id"], sdc["sdc_id"], wo_data.num_students)
    
    logger.info(f"Created Work Order: {wo_data.work_order_number} for {wo_data.location}")
    
    return {
        "work_order": work_order,
        "sdc": sdc,
        "message": "Work Order created with training roadmap"
    }


@api_router.get("/work-orders")
async def list_work_orders(sdc_id: Optional[str] = None, user: User = Depends(get_current_user)):
    """List work orders"""
    query = {"is_deleted": {"$ne": True}}
    if user.role not in ["ho", "admin"]:
        if user.assigned_sdc_id:
            query["sdc_id"] = user.assigned_sdc_id
        else:
            return []
    elif sdc_id:
        query["sdc_id"] = sdc_id
    
    work_orders = await db.work_orders.find(query, {"_id": 0}).to_list(1000)
    return work_orders


@api_router.get("/work-orders/{work_order_id}")
async def get_work_order(work_order_id: str, user: User = Depends(get_current_user)):
    """Get work order with roadmap"""
    work_order = await db.work_orders.find_one({"work_order_id": work_order_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not work_order:
        raise HTTPException(status_code=404, detail="Work Order not found")
    
    if user.role not in ["ho", "admin"] and user.assigned_sdc_id != work_order["sdc_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    roadmaps = await db.training_roadmaps.find({"work_order_id": work_order_id}, {"_id": 0}).to_list(100)
    roadmaps.sort(key=lambda x: x.get("stage_order", 0))
    
    return {**work_order, "roadmap": roadmaps}


@api_router.put("/work-orders/{work_order_id}/start-date")
async def set_start_date(work_order_id: str, date_data: WorkOrderStartDate, user: User = Depends(get_current_user)):
    """Set start date and calculate end date"""
    work_order = await db.work_orders.find_one({"work_order_id": work_order_id}, {"_id": 0})
    if not work_order:
        raise HTTPException(status_code=404, detail="Work Order not found")
    
    if user.role not in ["ho", "admin"] and user.assigned_sdc_id != work_order["sdc_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    calculated_end = await calculate_end_date(
        date_data.start_date,
        work_order["total_training_hours"],
        work_order["sessions_per_day"],
        work_order["sdc_id"]
    )
    
    await db.work_orders.update_one(
        {"work_order_id": work_order_id},
        {"$set": {
            "start_date": date_data.start_date,
            "calculated_end_date": calculated_end,
            "manual_end_date": date_data.manual_end_date
        }}
    )
    
    return {
        "start_date": date_data.start_date,
        "calculated_end_date": calculated_end,
        "manual_end_date": date_data.manual_end_date
    }


# ==================== TRAINING ROADMAP ENDPOINTS ====================

@api_router.get("/roadmaps/{work_order_id}")
async def get_roadmap(work_order_id: str, user: User = Depends(get_current_user)):
    """Get training roadmap for work order"""
    work_order = await db.work_orders.find_one({"work_order_id": work_order_id}, {"_id": 0})
    if not work_order:
        raise HTTPException(status_code=404, detail="Work Order not found")
    
    if user.role not in ["ho", "admin"] and user.assigned_sdc_id != work_order["sdc_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    roadmaps = await db.training_roadmaps.find({"work_order_id": work_order_id}, {"_id": 0}).to_list(100)
    roadmaps.sort(key=lambda x: x.get("stage_order", 0))
    
    return roadmaps


@api_router.put("/roadmaps/{roadmap_id}")
async def update_roadmap(roadmap_id: str, update: RoadmapUpdate, user: User = Depends(get_current_user)):
    """Update roadmap stage"""
    roadmap = await db.training_roadmaps.find_one({"roadmap_id": roadmap_id}, {"_id": 0})
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    
    work_order = await db.work_orders.find_one({"work_order_id": roadmap["work_order_id"]}, {"_id": 0})
    if user.role not in ["ho", "admin"] and user.assigned_sdc_id != work_order["sdc_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if update.completed_count is not None:
        update_data["completed_count"] = update.completed_count
    if update.status is not None:
        update_data["status"] = update.status
    if update.notes is not None:
        update_data["notes"] = update.notes
    
    await db.training_roadmaps.update_one({"roadmap_id": roadmap_id}, {"$set": update_data})
    
    return {"message": "Roadmap updated"}


@api_router.post("/roadmaps/batch-update")
async def batch_update_roadmap(updates: list, user: User = Depends(require_ho_role)):
    """Batch update multiple roadmap stages"""
    updated_count = 0
    for update in updates:
        roadmap_id = update.get("roadmap_id")
        if roadmap_id:
            update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
            if "completed_count" in update:
                update_data["completed_count"] = update["completed_count"]
            if "status" in update:
                update_data["status"] = update["status"]
            if "notes" in update:
                update_data["notes"] = update["notes"]
            
            result = await db.training_roadmaps.update_one({"roadmap_id": roadmap_id}, {"$set": update_data})
            if result.modified_count > 0:
                updated_count += 1
    
    return {"message": f"Updated {updated_count} roadmap stages"}


# ==================== UTILITY ENDPOINTS ====================

@api_router.post("/calculate-end-date")
async def api_calculate_end_date(
    start_date: str, 
    training_hours: int, 
    sessions_per_day: int = 8,
    sdc_id: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """Calculate training end date"""
    end_date = await calculate_end_date(start_date, training_hours, sessions_per_day, sdc_id)
    return {
        "start_date": start_date, 
        "end_date": end_date, 
        "training_hours": training_hours,
        "sessions_per_day": sessions_per_day
    }


@api_router.get("/training-stages")
async def get_training_stages():
    """Get list of training stages"""
    return TRAINING_STAGES


@api_router.get("/")
async def root():
    return {"message": "SkillFlow CRM API", "version": "3.0.0 (Modular)"}


# ==================== SEED DATA ENDPOINT ====================

@api_router.post("/seed-data")
async def seed_sample_data(user: User = Depends(require_ho_role)):
    """Seed sample data for demo purposes (HO only)"""
    await db.sdcs.delete_many({})
    await db.work_orders.delete_many({})
    await db.training_roadmaps.delete_many({})
    await db.invoices.delete_many({})
    await db.holidays.delete_many({})
    await db.alerts.delete_many({})
    
    holidays_data = [
        {"holiday_id": "hol_001", "date": "2025-01-26", "name": "Republic Day", "year": 2025, "is_local": False},
        {"holiday_id": "hol_002", "date": "2025-03-14", "name": "Holi", "year": 2025, "is_local": False},
        {"holiday_id": "hol_003", "date": "2025-08-15", "name": "Independence Day", "year": 2025, "is_local": False},
        {"holiday_id": "hol_004", "date": "2025-10-02", "name": "Gandhi Jayanti", "year": 2025, "is_local": False},
        {"holiday_id": "hol_005", "date": "2025-10-20", "name": "Dussehra", "year": 2025, "is_local": False},
        {"holiday_id": "hol_006", "date": "2025-11-01", "name": "Diwali", "year": 2025, "is_local": False}
    ]
    for hol in holidays_data:
        hol["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.holidays.insert_many(holidays_data)
    
    return {
        "message": "Sample data seeded successfully",
        "holidays": len(holidays_data)
    }


# ==================== INCLUDE MODULAR ROUTERS ====================

# Include all modular routers under /api prefix
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(master_data_router)
api_router.include_router(resources_router)
api_router.include_router(sdcs_router)
api_router.include_router(dashboard_router)

# Include main API router in app
app.include_router(api_router)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== DATABASE INITIALIZATION ====================

@app.on_event("startup")
async def startup_db_client():
    """Initialize database indexes and collections on startup"""
    try:
        # Create indexes for performance optimization
        await db.users.create_index("email", unique=True)
        await db.users.create_index("user_id", unique=True)
        await db.users.create_index("role")
        
        await db.sdcs.create_index("sdc_id", unique=True)
        await db.sdcs.create_index("is_deleted")
        await db.sdcs.create_index([("location", 1), ("is_deleted", 1)])
        
        await db.work_orders.create_index("work_order_id", unique=True)
        await db.work_orders.create_index("sdc_id")
        await db.work_orders.create_index("status")
        await db.work_orders.create_index("is_deleted")
        
        await db.master_work_orders.create_index("master_wo_id", unique=True)
        await db.master_work_orders.create_index("work_order_number")
        await db.master_work_orders.create_index("status")
        
        await db.trainers.create_index("trainer_id", unique=True)
        await db.trainers.create_index("email")
        await db.trainers.create_index("status")
        await db.trainers.create_index("is_deleted")
        
        await db.center_managers.create_index("manager_id", unique=True)
        await db.center_managers.create_index("email")
        await db.center_managers.create_index("status")
        
        await db.sdc_infrastructure.create_index("infra_id", unique=True)
        await db.sdc_infrastructure.create_index("district")
        await db.sdc_infrastructure.create_index("status")
        
        await db.job_role_master.create_index("job_role_id", unique=True)
        await db.job_role_master.create_index("job_role_code", unique=True)
        await db.job_role_master.create_index("is_active")
        
        await db.audit_logs.create_index("audit_id", unique=True)
        await db.audit_logs.create_index([("timestamp", -1)])
        await db.audit_logs.create_index("entity_type")
        await db.audit_logs.create_index("entity_id")
        await db.audit_logs.create_index("user_id")
        await db.audit_logs.create_index("action")
        
        await db.invoices.create_index("invoice_id", unique=True)
        await db.invoices.create_index("sdc_id")
        await db.invoices.create_index([("invoice_date", -1)])
        
        await db.user_sessions.create_index("session_token", unique=True)
        await db.user_sessions.create_index("user_id")
        await db.user_sessions.create_index("expires_at", expireAfterSeconds=0)
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating database indexes: {e}")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
