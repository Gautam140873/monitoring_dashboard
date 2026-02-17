from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import httpx
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="SkillFlow CRM API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== TRAINING ROADMAP STAGES ====================
TRAINING_STAGES = [
    {"stage_id": "mobilization", "name": "Mobilization", "order": 1, "description": "Finding students"},
    {"stage_id": "dress_distribution", "name": "Dress Distribution", "order": 2, "description": "Uniform distribution"},
    {"stage_id": "study_material", "name": "Study Material Distribution", "order": 3, "description": "Books and materials"},
    {"stage_id": "classroom_training", "name": "Classroom Training", "order": 4, "description": "Main training phase"},
    {"stage_id": "assessment", "name": "Assessment", "order": 5, "description": "Evaluation and certification"},
    {"stage_id": "ojt", "name": "OJT (On-the-Job Training)", "order": 6, "description": "Practical work experience"},
    {"stage_id": "placement", "name": "Placement", "order": 7, "description": "Job placement"}
]

# ==================== MODELS ====================

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    role: str = "sdc"  # "sdc" or "ho"
    assigned_sdc_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SDC(BaseModel):
    model_config = ConfigDict(extra="ignore")
    sdc_id: str = Field(default_factory=lambda: f"sdc_{uuid.uuid4().hex[:8]}")
    name: str
    location: str
    manager_email: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WorkOrder(BaseModel):
    """Master Entry - Work Order from HO"""
    model_config = ConfigDict(extra="ignore")
    work_order_id: str = Field(default_factory=lambda: f"wo_{uuid.uuid4().hex[:8]}")
    work_order_number: str
    sdc_id: str
    location: str
    job_role_code: str
    job_role_name: str
    awarding_body: str
    scheme_name: str
    total_training_hours: int
    sessions_per_day: int = 8  # hours per day
    num_students: int
    cost_per_student: float
    total_contract_value: float = 0  # Auto-calculated
    manager_email: Optional[str] = None
    start_date: Optional[str] = None  # Set by local manager
    calculated_end_date: Optional[str] = None  # Auto-calculated
    manual_end_date: Optional[str] = None  # Override by local manager
    status: str = "active"  # active, completed, cancelled
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None

class TrainingRoadmap(BaseModel):
    """Training stages for a work order"""
    model_config = ConfigDict(extra="ignore")
    roadmap_id: str = Field(default_factory=lambda: f"rm_{uuid.uuid4().hex[:8]}")
    work_order_id: str
    sdc_id: str
    stage_id: str
    stage_name: str
    stage_order: int
    target_count: int = 0
    completed_count: int = 0
    status: str = "pending"  # pending, in_progress, completed, paid
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    notes: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    invoice_id: str = Field(default_factory=lambda: f"inv_{uuid.uuid4().hex[:8]}")
    sdc_id: str
    work_order_id: Optional[str] = None
    invoice_number: str
    invoice_date: str
    order_value: float  # What was contracted
    billing_value: float  # What we actually billed
    variance: float = 0  # Auto-calculated: order_value - billing_value
    variance_percent: float = 0
    payment_received: float = 0
    outstanding: float = 0  # Auto-calculated: billing_value - payment_received
    status: str = "pending"  # pending, partial, paid
    payment_date: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Holiday(BaseModel):
    model_config = ConfigDict(extra="ignore")
    holiday_id: str = Field(default_factory=lambda: f"hol_{uuid.uuid4().hex[:8]}")
    date: str
    name: str
    year: int
    is_local: bool = False
    sdc_id: Optional[str] = None  # If local holiday
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Alert(BaseModel):
    model_config = ConfigDict(extra="ignore")
    alert_id: str = Field(default_factory=lambda: f"alert_{uuid.uuid4().hex[:8]}")
    sdc_id: str
    sdc_name: str
    work_order_id: Optional[str] = None
    alert_type: str  # overdue, variance, blocker
    message: str
    severity: str  # high, medium, low
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False

# ==================== REQUEST/RESPONSE MODELS ====================

class SessionRequest(BaseModel):
    session_id: str

class SDCCreate(BaseModel):
    name: str
    location: str
    manager_email: Optional[str] = None

class WorkOrderCreate(BaseModel):
    work_order_number: str
    location: str  # Used to auto-create SDC if not exists
    job_role_code: str
    job_role_name: str
    awarding_body: str
    scheme_name: str
    total_training_hours: int
    sessions_per_day: int = 8
    num_students: int
    cost_per_student: float
    manager_email: Optional[str] = None

class WorkOrderStartDate(BaseModel):
    start_date: str
    manual_end_date: Optional[str] = None

class RoadmapUpdate(BaseModel):
    completed_count: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class InvoiceCreate(BaseModel):
    sdc_id: str
    work_order_id: Optional[str] = None
    invoice_number: str
    invoice_date: str
    order_value: float
    billing_value: float
    notes: Optional[str] = None

class PaymentUpdate(BaseModel):
    payment_received: float
    payment_date: Optional[str] = None

class HolidayCreate(BaseModel):
    date: str
    name: str
    year: int
    is_local: bool = False
    sdc_id: Optional[str] = None

class UserRoleUpdate(BaseModel):
    role: str
    assigned_sdc_id: Optional[str] = None

# ==================== AUTH HELPERS ====================

async def get_current_user(request: Request) -> User:
    """Get current authenticated user from session token"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_doc = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    user_doc = await db.users.find_one({"user_id": session_doc["user_id"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user_doc)

async def require_ho_role(user: User = Depends(get_current_user)) -> User:
    """Require HO (Head Office) role"""
    if user.role != "ho":
        raise HTTPException(status_code=403, detail="HO access required")
    return user

# ==================== DATE CALCULATION ====================

async def calculate_end_date(start_date: str, training_hours: int, sessions_per_day: int = 8, sdc_id: str = None) -> str:
    """Calculate training end date skipping Sundays and holidays"""
    # Get all holidays
    holiday_query = {"$or": [{"is_local": False}]}
    if sdc_id:
        holiday_query["$or"].append({"sdc_id": sdc_id, "is_local": True})
    
    holidays_docs = await db.holidays.find(holiday_query, {"_id": 0}).to_list(1000)
    holidays = [h["date"] for h in holidays_docs]
    
    start = datetime.strptime(start_date, "%Y-%m-%d")
    training_days = (training_hours + sessions_per_day - 1) // sessions_per_day  # Ceil division
    
    current_date = start
    days_counted = 0
    
    while days_counted < training_days:
        # Skip Sundays (weekday 6)
        if current_date.weekday() != 6:
            # Skip holidays
            if current_date.strftime("%Y-%m-%d") not in holidays:
                days_counted += 1
        
        if days_counted < training_days:
            current_date += timedelta(days=1)
    
    return current_date.strftime("%Y-%m-%d")

# ==================== AUTO SDC CREATION ====================

async def get_or_create_sdc(location: str, manager_email: str = None) -> dict:
    """Get existing SDC or create new one based on location"""
    # Normalize location for matching
    location_key = location.lower().replace(" ", "_").replace(",", "")
    sdc_id = f"sdc_{location_key}"
    
    existing = await db.sdcs.find_one({"sdc_id": sdc_id}, {"_id": 0})
    if existing:
        return existing
    
    # Create new SDC
    sdc_name = f"SDC {location.title()}"
    sdc = {
        "sdc_id": sdc_id,
        "name": sdc_name,
        "location": location,
        "manager_email": manager_email,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    # Make a copy before insert to avoid _id mutation
    sdc_to_insert = sdc.copy()
    await db.sdcs.insert_one(sdc_to_insert)
    logger.info(f"Auto-created SDC: {sdc_name} for location: {location}")
    
    return sdc

async def create_training_roadmap(work_order_id: str, sdc_id: str, num_students: int):
    """Create training roadmap stages for a work order"""
    roadmaps = []
    for stage in TRAINING_STAGES:
        roadmap = {
            "roadmap_id": f"rm_{uuid.uuid4().hex[:8]}",
            "work_order_id": work_order_id,
            "sdc_id": sdc_id,
            "stage_id": stage["stage_id"],
            "stage_name": stage["name"],
            "stage_order": stage["order"],
            "target_count": num_students,
            "completed_count": 0,
            "status": "pending",
            "start_date": None,
            "end_date": None,
            "notes": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        roadmaps.append(roadmap)
    
    if roadmaps:
        await db.training_roadmaps.insert_many(roadmaps)
    
    return roadmaps

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/session")
async def process_session(req: SessionRequest, response: Response):
    """Process session_id from Emergent Auth"""
    try:
        async with httpx.AsyncClient() as client:
            auth_response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": req.session_id}
            )
            
            if auth_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session ID")
            
            auth_data = auth_response.json()
    except httpx.RequestError as e:
        logger.error(f"Auth request failed: {e}")
        raise HTTPException(status_code=500, detail="Authentication service unavailable")
    
    email = auth_data.get("email")
    name = auth_data.get("name")
    picture = auth_data.get("picture")
    session_token = auth_data.get("session_token")
    
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": name, "picture": picture}}
        )
        role = existing_user.get("role", "sdc")
        assigned_sdc_id = existing_user.get("assigned_sdc_id")
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        new_user = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "role": "sdc",
            "assigned_sdc_id": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(new_user)
        role = "sdc"
        assigned_sdc_id = None
    
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    session_doc = {
        "session_id": req.session_id,
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.user_sessions.delete_many({"user_id": user_id})
    await db.user_sessions.insert_one(session_doc)
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    return {
        "user_id": user_id,
        "email": email,
        "name": name,
        "picture": picture,
        "role": role,
        "assigned_sdc_id": assigned_sdc_id
    }

@api_router.get("/auth/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get current user info"""
    return {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "role": user.role,
        "assigned_sdc_id": user.assigned_sdc_id
    }

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user"""
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_many({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out successfully"}

# ==================== USER MANAGEMENT (HO ONLY) ====================

@api_router.get("/users")
async def list_users(user: User = Depends(require_ho_role)):
    """List all users (HO only)"""
    users = await db.users.find({}, {"_id": 0}).to_list(1000)
    return users

@api_router.put("/users/{user_id}/role")
async def update_user_role(user_id: str, role_update: UserRoleUpdate, user: User = Depends(require_ho_role)):
    """Update user role (HO only)"""
    result = await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"role": role_update.role, "assigned_sdc_id": role_update.assigned_sdc_id}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Role updated successfully"}

# ==================== WORK ORDER ENDPOINTS (MASTER ENTRY) ====================

@api_router.post("/work-orders")
async def create_work_order(wo_data: WorkOrderCreate, user: User = Depends(require_ho_role)):
    """Create a new Work Order (Master Entry) - HO Only
    This automatically creates SDC if not exists and creates training roadmap
    """
    # Step 1: Get or create SDC based on location
    sdc = await get_or_create_sdc(wo_data.location, wo_data.manager_email)
    
    # Step 2: Calculate total contract value
    total_contract_value = wo_data.num_students * wo_data.cost_per_student
    
    # Step 3: Create Work Order
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
    
    # Make a copy before insert to avoid _id mutation
    work_order_to_insert = work_order.copy()
    await db.work_orders.insert_one(work_order_to_insert)
    
    # Step 4: Auto-create Training Roadmap
    roadmaps = await create_training_roadmap(
        work_order["work_order_id"], 
        sdc["sdc_id"], 
        wo_data.num_students
    )
    
    logger.info(f"Created Work Order {wo_data.work_order_number} for {wo_data.location}")
    
    # Return clean response without MongoDB _id
    sdc_clean = {k: v for k, v in sdc.items() if k != "_id"}
    
    return {
        "message": "Work Order created successfully",
        "work_order": work_order,
        "sdc": sdc_clean,
        "roadmap_stages": len(roadmaps)
    }

@api_router.get("/work-orders")
async def list_work_orders(user: User = Depends(get_current_user)):
    """List work orders (filtered by role)"""
    query = {}
    if user.role != "ho" and user.assigned_sdc_id:
        query["sdc_id"] = user.assigned_sdc_id
    
    work_orders = await db.work_orders.find(query, {"_id": 0}).to_list(1000)
    return work_orders

@api_router.get("/work-orders/{work_order_id}")
async def get_work_order(work_order_id: str, user: User = Depends(get_current_user)):
    """Get work order details with roadmap"""
    work_order = await db.work_orders.find_one({"work_order_id": work_order_id}, {"_id": 0})
    if not work_order:
        raise HTTPException(status_code=404, detail="Work Order not found")
    
    # Check access
    if user.role != "ho" and user.assigned_sdc_id != work_order["sdc_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get roadmap
    roadmap = await db.training_roadmaps.find(
        {"work_order_id": work_order_id}, 
        {"_id": 0}
    ).sort("stage_order", 1).to_list(100)
    
    # Get invoices
    invoices = await db.invoices.find(
        {"work_order_id": work_order_id}, 
        {"_id": 0}
    ).to_list(100)
    
    return {
        **work_order,
        "roadmap": roadmap,
        "invoices": invoices
    }

@api_router.put("/work-orders/{work_order_id}/start-date")
async def set_work_order_start_date(
    work_order_id: str, 
    date_data: WorkOrderStartDate, 
    user: User = Depends(get_current_user)
):
    """Set start date for work order (Local Manager)
    This auto-calculates end date based on training hours and holidays
    """
    work_order = await db.work_orders.find_one({"work_order_id": work_order_id}, {"_id": 0})
    if not work_order:
        raise HTTPException(status_code=404, detail="Work Order not found")
    
    # Check access
    if user.role != "ho" and user.assigned_sdc_id != work_order["sdc_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Calculate end date
    calculated_end_date = await calculate_end_date(
        date_data.start_date,
        work_order["total_training_hours"],
        work_order.get("sessions_per_day", 8),
        work_order["sdc_id"]
    )
    
    update_data = {
        "start_date": date_data.start_date,
        "calculated_end_date": calculated_end_date
    }
    
    # Allow manual override
    if date_data.manual_end_date:
        update_data["manual_end_date"] = date_data.manual_end_date
    
    await db.work_orders.update_one(
        {"work_order_id": work_order_id},
        {"$set": update_data}
    )
    
    # Update first roadmap stage
    await db.training_roadmaps.update_one(
        {"work_order_id": work_order_id, "stage_order": 1},
        {"$set": {"status": "in_progress", "start_date": date_data.start_date}}
    )
    
    return {
        "message": "Start date set successfully",
        "start_date": date_data.start_date,
        "calculated_end_date": calculated_end_date,
        "manual_end_date": date_data.manual_end_date
    }

# ==================== TRAINING ROADMAP ENDPOINTS ====================

@api_router.get("/roadmap/{work_order_id}")
async def get_roadmap(work_order_id: str, user: User = Depends(get_current_user)):
    """Get training roadmap for a work order"""
    work_order = await db.work_orders.find_one({"work_order_id": work_order_id}, {"_id": 0})
    if not work_order:
        raise HTTPException(status_code=404, detail="Work Order not found")
    
    if user.role != "ho" and user.assigned_sdc_id != work_order["sdc_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    roadmap = await db.training_roadmaps.find(
        {"work_order_id": work_order_id}, 
        {"_id": 0}
    ).sort("stage_order", 1).to_list(100)
    
    return roadmap

@api_router.put("/roadmap/{roadmap_id}")
async def update_roadmap_stage(
    roadmap_id: str, 
    update: RoadmapUpdate, 
    user: User = Depends(get_current_user)
):
    """Update a roadmap stage"""
    roadmap = await db.training_roadmaps.find_one({"roadmap_id": roadmap_id}, {"_id": 0})
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap stage not found")
    
    if user.role != "ho" and user.assigned_sdc_id != roadmap["sdc_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if update.completed_count is not None:
        update_data["completed_count"] = update.completed_count
    if update.status:
        update_data["status"] = update.status
    if update.notes:
        update_data["notes"] = update.notes
    
    await db.training_roadmaps.update_one(
        {"roadmap_id": roadmap_id},
        {"$set": update_data}
    )
    
    return {"message": "Roadmap stage updated"}

# ==================== SDC ENDPOINTS ====================

@api_router.get("/sdcs")
async def list_sdcs(user: User = Depends(get_current_user)):
    """List SDCs (filtered by role)"""
    if user.role == "ho":
        sdcs = await db.sdcs.find({}, {"_id": 0}).to_list(1000)
    else:
        if user.assigned_sdc_id:
            sdcs = await db.sdcs.find({"sdc_id": user.assigned_sdc_id}, {"_id": 0}).to_list(1000)
        else:
            sdcs = []
    return sdcs

@api_router.post("/sdcs")
async def create_sdc(sdc_data: SDCCreate, user: User = Depends(require_ho_role)):
    """Create new SDC (HO only)"""
    sdc = await get_or_create_sdc(sdc_data.location, sdc_data.manager_email)
    # Update name if different
    if sdc_data.name != sdc["name"]:
        await db.sdcs.update_one(
            {"sdc_id": sdc["sdc_id"]},
            {"$set": {"name": sdc_data.name}}
        )
        sdc["name"] = sdc_data.name
    return sdc

@api_router.get("/sdcs/{sdc_id}")
async def get_sdc(sdc_id: str, user: User = Depends(get_current_user)):
    """Get SDC details with work orders and progress"""
    if user.role != "ho" and user.assigned_sdc_id != sdc_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    sdc = await db.sdcs.find_one({"sdc_id": sdc_id}, {"_id": 0})
    if not sdc:
        raise HTTPException(status_code=404, detail="SDC not found")
    
    # Get work orders
    work_orders = await db.work_orders.find({"sdc_id": sdc_id}, {"_id": 0}).to_list(1000)
    
    # Calculate overall progress from roadmaps
    roadmaps = await db.training_roadmaps.find({"sdc_id": sdc_id}, {"_id": 0}).to_list(1000)
    
    # Group by stage
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
    
    # Get invoices
    invoices = await db.invoices.find({"sdc_id": sdc_id}, {"_id": 0}).to_list(1000)
    total_order_value = sum(inv.get("order_value", 0) for inv in invoices)
    total_billed = sum(inv.get("billing_value", 0) for inv in invoices)
    total_paid = sum(inv.get("payment_received", 0) for inv in invoices)
    total_outstanding = sum(inv.get("outstanding", 0) for inv in invoices)
    
    # Contract values from work orders
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

@api_router.delete("/sdcs/{sdc_id}")
async def delete_sdc(sdc_id: str, user: User = Depends(require_ho_role)):
    """Delete SDC (HO only)"""
    result = await db.sdcs.delete_one({"sdc_id": sdc_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="SDC not found")
    
    # Delete related data
    await db.work_orders.delete_many({"sdc_id": sdc_id})
    await db.training_roadmaps.delete_many({"sdc_id": sdc_id})
    await db.invoices.delete_many({"sdc_id": sdc_id})
    
    return {"message": "SDC deleted successfully"}

# ==================== INVOICE & BILLING ENDPOINTS ====================

@api_router.post("/invoices")
async def create_invoice(invoice_data: InvoiceCreate, user: User = Depends(get_current_user)):
    """Create invoice with variance calculation"""
    if user.role != "ho" and user.assigned_sdc_id != invoice_data.sdc_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Calculate variance and outstanding
    variance = invoice_data.order_value - invoice_data.billing_value
    variance_percent = round((variance / invoice_data.order_value * 100) if invoice_data.order_value > 0 else 0, 1)
    outstanding = invoice_data.billing_value  # Initially, all billed is outstanding
    
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
    
    # Make a copy before insert to avoid _id mutation
    invoice_to_insert = invoice.copy()
    await db.invoices.insert_one(invoice_to_insert)
    
    # Check if variance is significant (>10%)
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
        alert_to_insert = alert.copy()
        await db.alerts.insert_one(alert_to_insert)
    
    return invoice

@api_router.get("/invoices")
async def list_invoices(sdc_id: Optional[str] = None, user: User = Depends(get_current_user)):
    """List invoices"""
    query = {}
    if user.role != "ho":
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
    
    if user.role != "ho" and user.assigned_sdc_id != invoice["sdc_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Calculate new outstanding
    new_payment = payment.payment_received
    new_outstanding = invoice["billing_value"] - new_payment
    
    # Determine status
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
    
    # PAYMENT TRIGGER: If fully paid, mark related roadmap stages as PAID
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
        # Local holiday - check SDC access
        if not holiday_data.sdc_id:
            raise HTTPException(status_code=400, detail="SDC ID required for local holiday")
        if user.role != "ho" and user.assigned_sdc_id != holiday_data.sdc_id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        # Global holiday - HO only
        if user.role != "ho":
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
    
    await db.holidays.insert_one(holiday)
    return holiday

@api_router.delete("/holidays/{holiday_id}")
async def delete_holiday(holiday_id: str, user: User = Depends(get_current_user)):
    """Delete holiday"""
    holiday = await db.holidays.find_one({"holiday_id": holiday_id}, {"_id": 0})
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")
    
    # Check access
    if holiday.get("is_local"):
        if user.role != "ho" and user.assigned_sdc_id != holiday.get("sdc_id"):
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        if user.role != "ho":
            raise HTTPException(status_code=403, detail="HO access required")
    
    await db.holidays.delete_one({"holiday_id": holiday_id})
    return {"message": "Holiday deleted"}

# ==================== DASHBOARD ENDPOINTS ====================

@api_router.get("/dashboard/overview")
async def get_dashboard_overview(user: User = Depends(get_current_user)):
    """Get dashboard overview with commercial health metrics"""
    sdc_query = {}
    if user.role != "ho" and user.assigned_sdc_id:
        sdc_query["sdc_id"] = user.assigned_sdc_id
    
    # Get all SDCs
    sdcs = await db.sdcs.find(sdc_query, {"_id": 0}).to_list(1000)
    
    # Get work orders for total portfolio
    work_orders = await db.work_orders.find(sdc_query, {"_id": 0}).to_list(1000)
    total_portfolio = sum(wo.get("total_contract_value", 0) for wo in work_orders)
    
    # Get all invoices
    invoices = await db.invoices.find(sdc_query, {"_id": 0}).to_list(1000)
    total_billed = sum(inv.get("billing_value", 0) for inv in invoices)
    total_paid = sum(inv.get("payment_received", 0) for inv in invoices)
    outstanding = sum(inv.get("outstanding", 0) for inv in invoices)
    
    # Get all roadmaps for progress
    roadmaps = await db.training_roadmaps.find(sdc_query, {"_id": 0}).to_list(1000)
    
    # Calculate stage totals
    stage_totals = {}
    for stage in TRAINING_STAGES:
        stage_roadmaps = [r for r in roadmaps if r["stage_id"] == stage["stage_id"]]
        stage_totals[stage["stage_id"]] = {
            "name": stage["name"],
            "target": sum(r.get("target_count", 0) for r in stage_roadmaps),
            "completed": sum(r.get("completed_count", 0) for r in stage_roadmaps)
        }
    
    # Calculate variance
    variance = total_portfolio - total_billed
    variance_percent = round((variance / total_portfolio * 100) if total_portfolio > 0 else 0, 1)
    
    # Build SDC summaries
    sdc_summaries = []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    for sdc in sdcs:
        sdc_id = sdc["sdc_id"]
        sdc_work_orders = [wo for wo in work_orders if wo.get("sdc_id") == sdc_id]
        sdc_invoices = [inv for inv in invoices if inv.get("sdc_id") == sdc_id]
        sdc_roadmaps = [r for r in roadmaps if r.get("sdc_id") == sdc_id]
        
        sdc_portfolio = sum(wo.get("total_contract_value", 0) for wo in sdc_work_orders)
        sdc_billed = sum(inv.get("billing_value", 0) for inv in sdc_invoices)
        sdc_paid = sum(inv.get("payment_received", 0) for inv in sdc_invoices)
        sdc_outstanding = sum(inv.get("outstanding", 0) for inv in sdc_invoices)
        
        # Stage progress for this SDC
        sdc_stage_progress = {}
        for stage in TRAINING_STAGES:
            stage_rms = [r for r in sdc_roadmaps if r["stage_id"] == stage["stage_id"]]
            sdc_stage_progress[stage["stage_id"]] = {
                "target": sum(r.get("target_count", 0) for r in stage_rms),
                "completed": sum(r.get("completed_count", 0) for r in stage_rms)
            }
        
        # Check for overdue work orders
        overdue_count = sum(1 for wo in sdc_work_orders 
                          if wo.get("calculated_end_date") and wo["calculated_end_date"] < today 
                          and wo.get("status") == "active")
        
        # Check for blockers (incomplete stages with notes)
        blockers = [r.get("notes") for r in sdc_roadmaps 
                   if r.get("notes") and r.get("status") not in ["completed", "paid"]]
        
        sdc_summaries.append({
            "sdc_id": sdc_id,
            "name": sdc["name"],
            "location": sdc["location"],
            "manager_email": sdc.get("manager_email"),
            "progress": sdc_stage_progress,
            "financial": {
                "portfolio": sdc_portfolio,
                "billed": sdc_billed,
                "paid": sdc_paid,
                "outstanding": sdc_outstanding,
                "variance": sdc_portfolio - sdc_billed
            },
            "work_orders_count": len(sdc_work_orders),
            "overdue_count": overdue_count,
            "blockers": blockers[:3]  # Top 3 blockers
        })
    
    return {
        "commercial_health": {
            "total_portfolio": total_portfolio,
            "actual_billed": total_billed,
            "outstanding": outstanding,
            "collected": total_paid,
            "variance": variance,
            "variance_percent": variance_percent
        },
        "stage_progress": stage_totals,
        "sdc_count": len(sdcs),
        "sdc_summaries": sdc_summaries,
        "work_orders_count": len(work_orders)
    }

# ==================== ALERTS ENDPOINTS ====================

@api_router.get("/alerts")
async def get_alerts(user: User = Depends(get_current_user)):
    """Get risk alerts"""
    query = {"resolved": False}
    if user.role != "ho" and user.assigned_sdc_id:
        query["sdc_id"] = user.assigned_sdc_id
    
    alerts = await db.alerts.find(query, {"_id": 0}).to_list(1000)
    return alerts

@api_router.post("/alerts/generate")
async def generate_alerts(user: User = Depends(require_ho_role)):
    """Generate risk alerts based on current data (HO only)"""
    await db.alerts.delete_many({"resolved": False})
    
    sdcs = await db.sdcs.find({}, {"_id": 0}).to_list(1000)
    work_orders = await db.work_orders.find({}, {"_id": 0}).to_list(1000)
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(1000)
    roadmaps = await db.training_roadmaps.find({}, {"_id": 0}).to_list(1000)
    
    new_alerts = []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    for sdc in sdcs:
        sdc_id = sdc["sdc_id"]
        sdc_name = sdc["name"]
        
        # Check for overdue work orders
        sdc_work_orders = [wo for wo in work_orders if wo.get("sdc_id") == sdc_id]
        for wo in sdc_work_orders:
            end_date = wo.get("manual_end_date") or wo.get("calculated_end_date")
            if end_date and end_date < today and wo.get("status") == "active":
                alert = {
                    "alert_id": f"alert_{uuid.uuid4().hex[:8]}",
                    "sdc_id": sdc_id,
                    "sdc_name": sdc_name,
                    "work_order_id": wo["work_order_id"],
                    "alert_type": "overdue",
                    "message": f"Work Order {wo['work_order_number']} is overdue (End: {end_date})",
                    "severity": "high",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "resolved": False
                }
                new_alerts.append(alert)
        
        # Check for billing variance > 10%
        sdc_invoices = [inv for inv in invoices if inv.get("sdc_id") == sdc_id]
        for inv in sdc_invoices:
            if abs(inv.get("variance_percent", 0)) > 10:
                alert = {
                    "alert_id": f"alert_{uuid.uuid4().hex[:8]}",
                    "sdc_id": sdc_id,
                    "sdc_name": sdc_name,
                    "work_order_id": inv.get("work_order_id"),
                    "alert_type": "variance",
                    "message": f"Invoice {inv['invoice_number']} has {inv['variance_percent']}% variance",
                    "severity": "high" if abs(inv.get("variance_percent", 0)) > 25 else "medium",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "resolved": False
                }
                new_alerts.append(alert)
        
        # Check for blockers (stages with notes that are stuck)
        sdc_roadmaps = [r for r in roadmaps if r.get("sdc_id") == sdc_id]
        for rm in sdc_roadmaps:
            if rm.get("notes") and rm.get("status") == "in_progress":
                alert = {
                    "alert_id": f"alert_{uuid.uuid4().hex[:8]}",
                    "sdc_id": sdc_id,
                    "sdc_name": sdc_name,
                    "work_order_id": rm.get("work_order_id"),
                    "alert_type": "blocker",
                    "message": f"{rm['stage_name']}: {rm['notes']}",
                    "severity": "medium",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "resolved": False
                }
                new_alerts.append(alert)
    
    if new_alerts:
        await db.alerts.insert_many(new_alerts)
    
    return {"message": f"Generated {len(new_alerts)} alerts", "alerts": new_alerts}

@api_router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, user: User = Depends(require_ho_role)):
    """Resolve an alert (HO only)"""
    result = await db.alerts.update_one({"alert_id": alert_id}, {"$set": {"resolved": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert resolved"}

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
    return {"message": "SkillFlow CRM API", "version": "2.0.0"}

# ==================== SEED DATA ENDPOINT ====================

@api_router.post("/seed-data")
async def seed_sample_data(user: User = Depends(require_ho_role)):
    """Seed sample data for demo purposes (HO only)"""
    # Clear existing data
    await db.sdcs.delete_many({})
    await db.work_orders.delete_many({})
    await db.training_roadmaps.delete_many({})
    await db.invoices.delete_many({})
    await db.holidays.delete_many({})
    await db.alerts.delete_many({})
    
    # Create holidays first
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
    
    # Create Work Orders (which auto-creates SDCs and roadmaps)
    work_orders_data = [
        {
            "work_order_number": "WO/2025/001",
            "location": "Gurugram",
            "job_role_code": "CSC/Q0801",
            "job_role_name": "Field Technician Computing",
            "awarding_body": "NSDC PMKVY",
            "scheme_name": "PMKVY 4.0",
            "total_training_hours": 200,
            "sessions_per_day": 8,
            "num_students": 50,
            "cost_per_student": 10000,
            "manager_email": "gurugram.manager@skillflow.com"
        },
        {
            "work_order_number": "WO/2025/002",
            "location": "Jaipur",
            "job_role_code": "ASC/Q1401",
            "job_role_name": "Domestic Data Entry Operator",
            "awarding_body": "RSLDC",
            "scheme_name": "RAJKIVK",
            "total_training_hours": 180,
            "sessions_per_day": 8,
            "num_students": 60,
            "cost_per_student": 7200,
            "manager_email": "jaipur.manager@skillflow.com"
        },
        {
            "work_order_number": "WO/2025/003",
            "location": "Delhi",
            "job_role_code": "TEL/Q2201",
            "job_role_name": "CRM Domestic Voice",
            "awarding_body": "State Govt",
            "scheme_name": "DDUGKY",
            "total_training_hours": 300,
            "sessions_per_day": 8,
            "num_students": 45,
            "cost_per_student": 18000,
            "manager_email": "delhi.manager@skillflow.com"
        }
    ]
    
    created_sdcs = set()
    for wo_data in work_orders_data:
        # Create SDC
        sdc = await get_or_create_sdc(wo_data["location"], wo_data["manager_email"])
        created_sdcs.add(sdc["sdc_id"])
        
        # Calculate contract value
        total_contract_value = wo_data["num_students"] * wo_data["cost_per_student"]
        
        # Create Work Order
        work_order = {
            "work_order_id": f"wo_{uuid.uuid4().hex[:8]}",
            "work_order_number": wo_data["work_order_number"],
            "sdc_id": sdc["sdc_id"],
            "location": wo_data["location"],
            "job_role_code": wo_data["job_role_code"],
            "job_role_name": wo_data["job_role_name"],
            "awarding_body": wo_data["awarding_body"],
            "scheme_name": wo_data["scheme_name"],
            "total_training_hours": wo_data["total_training_hours"],
            "sessions_per_day": wo_data["sessions_per_day"],
            "num_students": wo_data["num_students"],
            "cost_per_student": wo_data["cost_per_student"],
            "total_contract_value": total_contract_value,
            "manager_email": wo_data["manager_email"],
            "start_date": "2025-01-15",
            "calculated_end_date": await calculate_end_date("2025-01-15", wo_data["total_training_hours"], wo_data["sessions_per_day"], sdc["sdc_id"]),
            "manual_end_date": None,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user.user_id
        }
        
        await db.work_orders.insert_one(work_order)
        
        # Create roadmap with some progress
        for i, stage in enumerate(TRAINING_STAGES):
            progress = wo_data["num_students"] if i < 2 else (wo_data["num_students"] * (0.8 - i * 0.1) if i < 5 else wo_data["num_students"] * 0.2)
            status = "completed" if i < 2 else ("in_progress" if i == 2 else "pending")
            
            roadmap = {
                "roadmap_id": f"rm_{uuid.uuid4().hex[:8]}",
                "work_order_id": work_order["work_order_id"],
                "sdc_id": sdc["sdc_id"],
                "stage_id": stage["stage_id"],
                "stage_name": stage["name"],
                "stage_order": stage["order"],
                "target_count": wo_data["num_students"],
                "completed_count": int(progress),
                "status": status,
                "start_date": "2025-01-15" if i < 3 else None,
                "end_date": None,
                "notes": "Waiting for attendance upload" if i == 2 and wo_data["location"] == "Jaipur" else None,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await db.training_roadmaps.insert_one(roadmap)
        
        # Create invoice
        billing_value = total_contract_value * 0.7  # 70% billed
        payment_received = billing_value * 0.6  # 60% of billed received
        
        invoice = {
            "invoice_id": f"inv_{uuid.uuid4().hex[:8]}",
            "sdc_id": sdc["sdc_id"],
            "work_order_id": work_order["work_order_id"],
            "invoice_number": f"INV/{wo_data['work_order_number'].split('/')[-1]}",
            "invoice_date": "2025-02-01",
            "order_value": total_contract_value,
            "billing_value": billing_value,
            "variance": total_contract_value - billing_value,
            "variance_percent": round(((total_contract_value - billing_value) / total_contract_value * 100), 1),
            "payment_received": payment_received,
            "outstanding": billing_value - payment_received,
            "status": "partial",
            "payment_date": "2025-02-15",
            "notes": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.invoices.insert_one(invoice)
    
    return {
        "message": "Sample data seeded successfully",
        "sdcs": len(created_sdcs),
        "work_orders": len(work_orders_data),
        "holidays": len(holidays_data)
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
