from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
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
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Google OAuth imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Google OAuth config
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']

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

# ==================== MASTER DATA MODELS ====================

class JobRoleMaster(BaseModel):
    """Master Data - Job Role Configuration (HO Only)"""
    model_config = ConfigDict(extra="ignore")
    job_role_id: str = Field(default_factory=lambda: f"jr_{uuid.uuid4().hex[:8]}")
    job_role_code: str  # e.g., CSC/Q0801
    job_role_name: str  # e.g., Field Technician Computing
    category: str  # "A", "B", or "custom"
    rate_per_hour: float  # Cat A: 46, Cat B: 42, or custom
    total_training_hours: int  # e.g., 400 hours
    awarding_body: str  # e.g., NSDC
    scheme_name: str  # e.g., PMKVY 4.0
    default_daily_hours: int = 8  # 4, 6, or 8
    default_batch_size: int = 30  # typical 25-30
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MasterWorkOrder(BaseModel):
    """Master Data - Work Order with Multiple Job Roles and SDCs (HO Only)"""
    model_config = ConfigDict(extra="ignore")
    master_wo_id: str = Field(default_factory=lambda: f"mwo_{uuid.uuid4().hex[:8]}")
    work_order_number: str  # e.g., WO/2025/001
    
    # Multiple Job Roles with individual targets
    job_roles: List[dict] = []  # [{job_role_id, job_role_code, job_role_name, category, rate_per_hour, hours, target}]
    
    # Training Targets
    total_training_target: int = 0  # Total target across all job roles
    
    # SDC Configuration
    num_sdcs: int = 0  # Number of SDCs/Districts
    sdc_districts: List[dict] = []  # [{district_name, sdc_name, target_allocation}]
    
    # Aggregated values (auto-calculated)
    total_contract_value: float = 0
    
    # Metadata
    awarding_body: str = ""
    scheme_name: str = ""
    status: str = "active"  # active, completed, cancelled
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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

# ==================== MASTER DATA REQUEST MODELS ====================

class JobRoleMasterCreate(BaseModel):
    """Create a new Job Role in Master Data"""
    job_role_code: str
    job_role_name: str
    category: str  # "A", "B", or "custom"
    rate_per_hour: Optional[float] = None  # Auto-set if category is A or B
    total_training_hours: int
    awarding_body: str
    scheme_name: str
    default_daily_hours: int = 8
    default_batch_size: int = 30

class JobRoleMasterUpdate(BaseModel):
    """Update Job Role in Master Data"""
    job_role_name: Optional[str] = None
    category: Optional[str] = None
    rate_per_hour: Optional[float] = None
    total_training_hours: Optional[int] = None
    awarding_body: Optional[str] = None
    scheme_name: Optional[str] = None
    default_daily_hours: Optional[int] = None
    default_batch_size: Optional[int] = None
    is_active: Optional[bool] = None

class MasterWorkOrderCreate(BaseModel):
    """Create Work Order from Master Data"""
    work_order_number: str
    job_role_id: str  # Reference to JobRoleMaster

class SDCFromMasterCreate(BaseModel):
    """Create SDC from Master Work Order"""
    master_wo_id: str  # Reference to MasterWorkOrder
    location: str  # SDC location/name
    target_students: int  # Target allocation for this SDC
    daily_hours: int = 8  # 4, 6, or 8
    manager_email: Optional[str] = None

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

# ==================== MASTER DATA ENDPOINTS (HO ONLY) ====================

# Category rate mapping
CATEGORY_RATES = {
    "A": 46.0,
    "B": 42.0
}

@api_router.get("/master/job-roles")
async def list_job_roles(user: User = Depends(require_ho_role)):
    """List all Job Roles from Master Data (HO only)"""
    job_roles = await db.job_role_master.find({}, {"_id": 0}).to_list(1000)
    return job_roles

@api_router.get("/master/job-roles/active")
async def list_active_job_roles(user: User = Depends(get_current_user)):
    """List active Job Roles (for dropdown selection)"""
    job_roles = await db.job_role_master.find({"is_active": True}, {"_id": 0}).to_list(1000)
    return job_roles

@api_router.post("/master/job-roles")
async def create_job_role(jr_data: JobRoleMasterCreate, user: User = Depends(require_ho_role)):
    """Create a new Job Role in Master Data (HO only)"""
    # Auto-set rate based on category
    rate = jr_data.rate_per_hour
    if rate is None:
        rate = CATEGORY_RATES.get(jr_data.category.upper(), 0)
    
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
    
    # Check for duplicate job role code
    existing = await db.job_role_master.find_one({"job_role_code": jr_data.job_role_code})
    if existing:
        raise HTTPException(status_code=400, detail=f"Job Role Code {jr_data.job_role_code} already exists")
    
    job_role_to_insert = job_role.copy()
    await db.job_role_master.insert_one(job_role_to_insert)
    
    logger.info(f"Created Job Role: {jr_data.job_role_code} - {jr_data.job_role_name}")
    return job_role

@api_router.get("/master/job-roles/{job_role_id}")
async def get_job_role(job_role_id: str, user: User = Depends(require_ho_role)):
    """Get Job Role details (HO only)"""
    job_role = await db.job_role_master.find_one({"job_role_id": job_role_id}, {"_id": 0})
    if not job_role:
        raise HTTPException(status_code=404, detail="Job Role not found")
    return job_role

@api_router.put("/master/job-roles/{job_role_id}")
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
        # Auto-update rate if category changed and no custom rate
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

@api_router.delete("/master/job-roles/{job_role_id}")
async def delete_job_role(job_role_id: str, user: User = Depends(require_ho_role)):
    """Delete (deactivate) Job Role from Master Data (HO only)"""
    result = await db.job_role_master.update_one(
        {"job_role_id": job_role_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Job Role not found")
    return {"message": "Job Role deactivated successfully"}

# ==================== MASTER WORK ORDER ENDPOINTS ====================

@api_router.get("/master/work-orders")
async def list_master_work_orders(user: User = Depends(require_ho_role)):
    """List all Master Work Orders (HO only)"""
    work_orders = await db.master_work_orders.find({}, {"_id": 0}).to_list(1000)
    
    # Enrich with SDC count and totals
    for wo in work_orders:
        sdcs = await db.sdcs.find({"master_wo_id": wo["master_wo_id"]}, {"_id": 0}).to_list(100)
        wo["sdc_count"] = len(sdcs)
        wo["sdcs"] = sdcs
    
    return work_orders

@api_router.post("/master/work-orders")
async def create_master_work_order(mwo_data: MasterWorkOrderCreate, user: User = Depends(require_ho_role)):
    """Create a Master Work Order from Job Role (HO only)"""
    # Get Job Role details
    job_role = await db.job_role_master.find_one({"job_role_id": mwo_data.job_role_id}, {"_id": 0})
    if not job_role:
        raise HTTPException(status_code=404, detail="Job Role not found in Master Data")
    
    if not job_role.get("is_active", True):
        raise HTTPException(status_code=400, detail="Job Role is not active")
    
    # Check for duplicate work order number
    existing = await db.master_work_orders.find_one({"work_order_number": mwo_data.work_order_number})
    if existing:
        raise HTTPException(status_code=400, detail=f"Work Order {mwo_data.work_order_number} already exists")
    
    master_wo = {
        "master_wo_id": f"mwo_{uuid.uuid4().hex[:8]}",
        "work_order_number": mwo_data.work_order_number,
        "job_role_id": job_role["job_role_id"],
        "job_role_code": job_role["job_role_code"],
        "job_role_name": job_role["job_role_name"],
        "category": job_role["category"],
        "rate_per_hour": job_role["rate_per_hour"],
        "total_training_hours": job_role["total_training_hours"],
        "awarding_body": job_role["awarding_body"],
        "scheme_name": job_role["scheme_name"],
        "total_target_students": 0,
        "total_contract_value": 0,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.user_id,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    master_wo_to_insert = master_wo.copy()
    await db.master_work_orders.insert_one(master_wo_to_insert)
    
    logger.info(f"Created Master Work Order: {mwo_data.work_order_number}")
    return master_wo

@api_router.get("/master/work-orders/{master_wo_id}")
async def get_master_work_order(master_wo_id: str, user: User = Depends(require_ho_role)):
    """Get Master Work Order with all linked SDCs (HO only)"""
    master_wo = await db.master_work_orders.find_one({"master_wo_id": master_wo_id}, {"_id": 0})
    if not master_wo:
        raise HTTPException(status_code=404, detail="Master Work Order not found")
    
    # Get all SDCs linked to this Master Work Order
    sdcs = await db.sdcs.find({"master_wo_id": master_wo_id}, {"_id": 0}).to_list(100)
    
    # Get work orders (batches) for each SDC
    for sdc in sdcs:
        work_orders = await db.work_orders.find(
            {"sdc_id": sdc["sdc_id"], "master_wo_id": master_wo_id}, 
            {"_id": 0}
        ).to_list(100)
        sdc["work_orders"] = work_orders
        sdc["batch_count"] = len(work_orders)
        sdc["total_students"] = sum(wo.get("num_students", 0) for wo in work_orders)
        sdc["total_value"] = sum(wo.get("total_contract_value", 0) for wo in work_orders)
    
    master_wo["sdcs"] = sdcs
    master_wo["sdc_count"] = len(sdcs)
    
    return master_wo

@api_router.post("/master/work-orders/{master_wo_id}/sdcs")
async def create_sdc_from_master(master_wo_id: str, sdc_data: SDCFromMasterCreate, user: User = Depends(require_ho_role)):
    """Create SDC from Master Work Order (HO only)
    This creates the SDC and initial work order/batch automatically
    """
    # Get Master Work Order
    master_wo = await db.master_work_orders.find_one({"master_wo_id": master_wo_id}, {"_id": 0})
    if not master_wo:
        raise HTTPException(status_code=404, detail="Master Work Order not found")
    
    # Create or get SDC
    location_key = sdc_data.location.lower().replace(" ", "_").replace(",", "")
    sdc_id = f"sdc_{location_key}"
    
    existing_sdc = await db.sdcs.find_one({"sdc_id": sdc_id}, {"_id": 0})
    
    if existing_sdc:
        # Update existing SDC with master_wo_id if not set
        if not existing_sdc.get("master_wo_id"):
            await db.sdcs.update_one(
                {"sdc_id": sdc_id},
                {"$set": {
                    "master_wo_id": master_wo_id,
                    "target_students": sdc_data.target_students,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }}
            )
        sdc = existing_sdc
        sdc["master_wo_id"] = master_wo_id
        sdc["target_students"] = sdc_data.target_students
    else:
        # Create new SDC
        sdc = {
            "sdc_id": sdc_id,
            "name": f"SDC {sdc_data.location.title()}",
            "location": sdc_data.location,
            "master_wo_id": master_wo_id,
            "target_students": sdc_data.target_students,
            "manager_email": sdc_data.manager_email,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        sdc_to_insert = sdc.copy()
        await db.sdcs.insert_one(sdc_to_insert)
    
    # Calculate contract value: Students × Hours × Rate
    contract_value = sdc_data.target_students * master_wo["total_training_hours"] * master_wo["rate_per_hour"]
    
    # Create Work Order (Batch) for this SDC
    work_order = {
        "work_order_id": f"wo_{uuid.uuid4().hex[:8]}",
        "work_order_number": f"{master_wo['work_order_number']}/{sdc_data.location.upper()[:3]}",
        "master_wo_id": master_wo_id,
        "sdc_id": sdc_id,
        "location": sdc_data.location,
        "job_role_code": master_wo["job_role_code"],
        "job_role_name": master_wo["job_role_name"],
        "awarding_body": master_wo["awarding_body"],
        "scheme_name": master_wo["scheme_name"],
        "total_training_hours": master_wo["total_training_hours"],
        "sessions_per_day": sdc_data.daily_hours,
        "num_students": sdc_data.target_students,
        "rate_per_hour": master_wo["rate_per_hour"],
        "cost_per_student": master_wo["total_training_hours"] * master_wo["rate_per_hour"],
        "total_contract_value": contract_value,
        "manager_email": sdc_data.manager_email,
        "start_date": None,
        "calculated_end_date": None,
        "manual_end_date": None,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.user_id
    }
    
    work_order_to_insert = work_order.copy()
    await db.work_orders.insert_one(work_order_to_insert)
    
    # Create Training Roadmap for this work order
    await create_training_roadmap(work_order["work_order_id"], sdc_id, sdc_data.target_students)
    
    # Update Master Work Order totals
    all_sdcs = await db.sdcs.find({"master_wo_id": master_wo_id}, {"_id": 0}).to_list(100)
    total_students = sum(s.get("target_students", 0) for s in all_sdcs)
    total_value = total_students * master_wo["total_training_hours"] * master_wo["rate_per_hour"]
    
    await db.master_work_orders.update_one(
        {"master_wo_id": master_wo_id},
        {"$set": {
            "total_target_students": total_students,
            "total_contract_value": total_value,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logger.info(f"Created SDC {sdc_data.location} for Master WO {master_wo['work_order_number']}")
    
    return {
        "message": "SDC created successfully from Master Data",
        "sdc": sdc,
        "work_order": work_order,
        "contract_value": contract_value,
        "calculation": f"{sdc_data.target_students} students × {master_wo['total_training_hours']} hrs × ₹{master_wo['rate_per_hour']}/hr"
    }

@api_router.get("/master/summary")
async def get_master_summary(user: User = Depends(require_ho_role)):
    """Get Master Data Summary with all aggregations (HO only)"""
    # Get all job roles
    job_roles = await db.job_role_master.find({"is_active": True}, {"_id": 0}).to_list(1000)
    
    # Get all master work orders
    master_wos = await db.master_work_orders.find({}, {"_id": 0}).to_list(1000)
    
    # Calculate totals
    total_contract_value = sum(wo.get("total_contract_value", 0) for wo in master_wos)
    total_students = sum(wo.get("total_target_students", 0) for wo in master_wos)
    
    # Get SDC count
    sdc_count = await db.sdcs.count_documents({})
    
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
        "sdcs": {
            "total": sdc_count
        }
    }

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

class BatchProgressUpdate(BaseModel):
    """Batch update for multiple roadmap stages"""
    updates: List[dict]  # [{"roadmap_id": "...", "completed_count": 10, "status": "in_progress"}]

@api_router.put("/roadmaps/batch-update")
async def batch_update_roadmap(
    batch_data: BatchProgressUpdate,
    user: User = Depends(get_current_user)
):
    """Batch update multiple roadmap stages at once"""
    updated_count = 0
    errors = []
    
    for update in batch_data.updates:
        roadmap_id = update.get("roadmap_id")
        if not roadmap_id:
            continue
            
        roadmap = await db.training_roadmaps.find_one({"roadmap_id": roadmap_id}, {"_id": 0})
        if not roadmap:
            errors.append(f"Roadmap {roadmap_id} not found")
            continue
        
        if user.role != "ho" and user.assigned_sdc_id != roadmap["sdc_id"]:
            errors.append(f"Access denied for {roadmap_id}")
            continue
        
        update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if "completed_count" in update:
            update_data["completed_count"] = update["completed_count"]
        if "status" in update:
            update_data["status"] = update["status"]
        if "notes" in update:
            update_data["notes"] = update["notes"]
        
        await db.training_roadmaps.update_one(
            {"roadmap_id": roadmap_id},
            {"$set": update_data}
        )
        updated_count += 1
    
    return {
        "message": f"Updated {updated_count} stages",
        "updated": updated_count,
        "errors": errors
    }

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

# ==================== EXPORT ENDPOINTS ====================

from fastapi.responses import StreamingResponse
import csv
import io

@api_router.get("/export/financial-summary")
async def export_financial_summary(user: User = Depends(require_ho_role)):
    """Export financial summary as CSV (HO only)"""
    sdcs = await db.sdcs.find({}, {"_id": 0}).to_list(1000)
    work_orders = await db.work_orders.find({}, {"_id": 0}).to_list(1000)
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(1000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "SDC Name", "Location", "Work Orders", "Total Contract", 
        "Total Billed", "Total Paid", "Outstanding", "Variance", "Variance %"
    ])
    
    for sdc in sdcs:
        sdc_id = sdc["sdc_id"]
        sdc_wos = [wo for wo in work_orders if wo.get("sdc_id") == sdc_id]
        sdc_invs = [inv for inv in invoices if inv.get("sdc_id") == sdc_id]
        
        total_contract = sum(wo.get("total_contract_value", 0) for wo in sdc_wos)
        total_billed = sum(inv.get("billing_value", 0) for inv in sdc_invs)
        total_paid = sum(inv.get("payment_received", 0) for inv in sdc_invs)
        outstanding = sum(inv.get("outstanding", 0) for inv in sdc_invs)
        variance = total_contract - total_billed
        variance_pct = round((variance / total_contract * 100) if total_contract > 0 else 0, 1)
        
        writer.writerow([
            sdc["name"], sdc["location"], len(sdc_wos), total_contract,
            total_billed, total_paid, outstanding, variance, f"{variance_pct}%"
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=financial_summary.csv"}
    )

@api_router.get("/export/work-orders")
async def export_work_orders(sdc_id: Optional[str] = None, user: User = Depends(get_current_user)):
    """Export work orders as CSV"""
    query = {}
    if user.role != "ho":
        if user.assigned_sdc_id:
            query["sdc_id"] = user.assigned_sdc_id
        else:
            raise HTTPException(status_code=403, detail="No SDC assigned")
    elif sdc_id:
        query["sdc_id"] = sdc_id
    
    work_orders = await db.work_orders.find(query, {"_id": 0}).to_list(1000)
    sdcs = await db.sdcs.find({}, {"_id": 0}).to_list(1000)
    sdc_map = {s["sdc_id"]: s["name"] for s in sdcs}
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Work Order #", "SDC", "Location", "Job Role Code", "Job Role Name",
        "Scheme", "Students", "Training Hours", "Start Date", "End Date",
        "Contract Value", "Status"
    ])
    
    for wo in work_orders:
        writer.writerow([
            wo["work_order_number"],
            sdc_map.get(wo["sdc_id"], wo["sdc_id"]),
            wo["location"],
            wo["job_role_code"],
            wo["job_role_name"],
            wo["scheme_name"],
            wo["num_students"],
            wo["total_training_hours"],
            wo.get("start_date", "Not Set"),
            wo.get("manual_end_date") or wo.get("calculated_end_date", "Not Set"),
            wo["total_contract_value"],
            wo["status"]
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=work_orders.csv"}
    )

@api_router.get("/export/training-progress")
async def export_training_progress(sdc_id: Optional[str] = None, user: User = Depends(get_current_user)):
    """Export training progress as CSV"""
    query = {}
    if user.role != "ho":
        if user.assigned_sdc_id:
            query["sdc_id"] = user.assigned_sdc_id
        else:
            raise HTTPException(status_code=403, detail="No SDC assigned")
    elif sdc_id:
        query["sdc_id"] = sdc_id
    
    roadmaps = await db.training_roadmaps.find(query, {"_id": 0}).to_list(10000)
    work_orders = await db.work_orders.find(query, {"_id": 0}).to_list(1000)
    wo_map = {wo["work_order_id"]: wo["work_order_number"] for wo in work_orders}
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Work Order #", "Stage", "Target", "Completed", "Progress %", "Status", "Notes"
    ])
    
    for rm in sorted(roadmaps, key=lambda x: (x["work_order_id"], x["stage_order"])):
        progress = round((rm["completed_count"] / rm["target_count"] * 100) if rm["target_count"] > 0 else 0, 1)
        writer.writerow([
            wo_map.get(rm["work_order_id"], rm["work_order_id"]),
            rm["stage_name"],
            rm["target_count"],
            rm["completed_count"],
            f"{progress}%",
            rm["status"],
            rm.get("notes", "")
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=training_progress.csv"}
    )

@api_router.get("/export/invoices")
async def export_invoices(sdc_id: Optional[str] = None, user: User = Depends(get_current_user)):
    """Export invoices as CSV"""
    query = {}
    if user.role != "ho":
        if user.assigned_sdc_id:
            query["sdc_id"] = user.assigned_sdc_id
        else:
            raise HTTPException(status_code=403, detail="No SDC assigned")
    elif sdc_id:
        query["sdc_id"] = sdc_id
    
    invoices = await db.invoices.find(query, {"_id": 0}).to_list(1000)
    sdcs = await db.sdcs.find({}, {"_id": 0}).to_list(1000)
    sdc_map = {s["sdc_id"]: s["name"] for s in sdcs}
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Invoice #", "SDC", "Date", "Order Value", "Billed Amount",
        "Variance", "Variance %", "Payment Received", "Outstanding", "Status", "Payment Date"
    ])
    
    for inv in invoices:
        writer.writerow([
            inv["invoice_number"],
            sdc_map.get(inv["sdc_id"], inv["sdc_id"]),
            inv["invoice_date"],
            inv["order_value"],
            inv["billing_value"],
            inv["variance"],
            f"{inv['variance_percent']}%",
            inv["payment_received"],
            inv["outstanding"],
            inv["status"],
            inv.get("payment_date", "")
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=invoices.csv"}
    )

# ==================== GMAIL API INTEGRATION ====================

def get_gmail_flow(redirect_uri: str):
    """Create OAuth flow for Gmail"""
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }
    flow = Flow.from_client_config(client_config, scopes=GMAIL_SCOPES)
    flow.redirect_uri = redirect_uri
    return flow

@api_router.get("/gmail/auth")
async def gmail_auth_start(request: Request, user: User = Depends(require_ho_role)):
    """Start Gmail OAuth flow (HO only)"""
    # Get the frontend URL for redirect
    frontend_url = request.headers.get("origin", "https://skill-tracker-99.preview.emergentagent.com")
    redirect_uri = f"{frontend_url}/api/gmail/callback"
    
    # Use backend URL for callback
    backend_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{backend_url}api/gmail/callback"
    
    flow = get_gmail_flow(redirect_uri)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    # Store state in DB for verification
    await db.oauth_states.insert_one({
        "state": state,
        "user_id": user.user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"authorization_url": authorization_url, "state": state}

@api_router.get("/gmail/callback")
async def gmail_callback(code: str, state: str, request: Request):
    """Handle Gmail OAuth callback"""
    # Verify state
    state_doc = await db.oauth_states.find_one({"state": state})
    if not state_doc:
        raise HTTPException(status_code=400, detail="Invalid state")
    
    user_id = state_doc["user_id"]
    await db.oauth_states.delete_one({"state": state})
    
    # Get the redirect URI
    backend_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{backend_url}api/gmail/callback"
    
    try:
        flow = get_gmail_flow(redirect_uri)
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Store credentials in DB
        creds_data = {
            "user_id": user_id,
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": list(credentials.scopes),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.gmail_credentials.update_one(
            {"user_id": user_id},
            {"$set": creds_data},
            upsert=True
        )
        
        # Redirect to settings page
        frontend_url = os.environ.get("FRONTEND_URL", "https://skill-tracker-99.preview.emergentagent.com")
        return RedirectResponse(url=f"{frontend_url}/settings?gmail=connected")
        
    except Exception as e:
        logger.error(f"Gmail OAuth error: {e}")
        frontend_url = os.environ.get("FRONTEND_URL", "https://skill-tracker-99.preview.emergentagent.com")
        return RedirectResponse(url=f"{frontend_url}/settings?gmail=error")

@api_router.get("/gmail/status")
async def gmail_status(user: User = Depends(require_ho_role)):
    """Check Gmail connection status"""
    creds = await db.gmail_credentials.find_one({"user_id": user.user_id}, {"_id": 0})
    if creds and creds.get("token"):
        return {"connected": True, "updated_at": creds.get("updated_at")}
    return {"connected": False}

async def get_gmail_service(user_id: str):
    """Get Gmail service for sending emails"""
    creds_doc = await db.gmail_credentials.find_one({"user_id": user_id}, {"_id": 0})
    if not creds_doc:
        return None
    
    credentials = Credentials(
        token=creds_doc["token"],
        refresh_token=creds_doc.get("refresh_token"),
        token_uri=creds_doc["token_uri"],
        client_id=creds_doc["client_id"],
        client_secret=creds_doc["client_secret"],
        scopes=creds_doc["scopes"]
    )
    
    # Refresh if expired
    if credentials.expired and credentials.refresh_token:
        from google.auth.transport.requests import Request as GoogleRequest
        credentials.refresh(GoogleRequest())
        
        # Update stored credentials
        await db.gmail_credentials.update_one(
            {"user_id": user_id},
            {"$set": {"token": credentials.token, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return build('gmail', 'v1', credentials=credentials)

def create_risk_summary_email(alerts: List[dict], dashboard_data: dict, recipient_email: str) -> MIMEMultipart:
    """Create HTML email for Risk Summary"""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🚨 SkillFlow Risk Summary - {datetime.now().strftime('%d %b %Y')}"
    msg['To'] = recipient_email
    
    # Get commercial health data
    health = dashboard_data.get("commercial_health", {})
    
    # Build alerts HTML
    alerts_html = ""
    for alert in alerts:
        severity_color = "#dc2626" if alert["severity"] == "high" else "#f59e0b"
        alerts_html += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                <span style="display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; 
                    background-color: {severity_color}20; color: {severity_color}; font-weight: 600;">
                    {alert['severity'].upper()}
                </span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; font-weight: 500;">{alert['sdc_name']}</td>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{alert['alert_type'].title()}</td>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{alert['message']}</td>
        </tr>
        """
    
    # Format currency
    def fmt_currency(val):
        return f"₹{val:,.0f}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #1f2937; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #1e293b; color: white; padding: 24px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #ffffff; padding: 24px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px; }}
            .metric-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 20px 0; }}
            .metric {{ background: #f8fafc; padding: 16px; border-radius: 8px; text-align: center; }}
            .metric-value {{ font-size: 24px; font-weight: 700; color: #1e293b; }}
            .metric-label {{ font-size: 12px; color: #64748b; margin-top: 4px; }}
            .alert-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .alert-table th {{ background: #f1f5f9; padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; }}
            .footer {{ margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #64748b; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0; font-size: 24px;">🚨 Risk Summary Report</h1>
                <p style="margin: 8px 0 0 0; opacity: 0.8;">SkillFlow CRM - {datetime.now().strftime('%d %B %Y, %I:%M %p')}</p>
            </div>
            <div class="content">
                <h2 style="margin-top: 0;">Commercial Health Overview</h2>
                <div class="metric-grid">
                    <div class="metric">
                        <div class="metric-value">{fmt_currency(health.get('total_portfolio', 0))}</div>
                        <div class="metric-label">Total Portfolio</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{fmt_currency(health.get('actual_billed', 0))}</div>
                        <div class="metric-label">Actual Billed</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" style="color: #10b981;">{fmt_currency(health.get('collected', 0))}</div>
                        <div class="metric-label">Collected</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" style="color: #dc2626;">{fmt_currency(health.get('outstanding', 0))}</div>
                        <div class="metric-label">Outstanding</div>
                    </div>
                </div>
                
                <h2>Active Alerts ({len(alerts)})</h2>
                {'<p style="color: #64748b;">No active alerts at this time.</p>' if not alerts else f'''
                <table class="alert-table">
                    <thead>
                        <tr>
                            <th>Severity</th>
                            <th>SDC</th>
                            <th>Type</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {alerts_html}
                    </tbody>
                </table>
                '''}
                
                <div class="footer">
                    <p>This is an automated report from SkillFlow CRM. <a href="https://skill-tracker-99.preview.emergentagent.com/dashboard">View Dashboard</a></p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    plain_text = f"""
    SkillFlow Risk Summary Report - {datetime.now().strftime('%d %B %Y')}
    
    COMMERCIAL HEALTH
    - Total Portfolio: {fmt_currency(health.get('total_portfolio', 0))}
    - Actual Billed: {fmt_currency(health.get('actual_billed', 0))}
    - Collected: {fmt_currency(health.get('collected', 0))}
    - Outstanding: {fmt_currency(health.get('outstanding', 0))}
    
    ACTIVE ALERTS ({len(alerts)})
    """ + "\n".join([f"- [{a['severity'].upper()}] {a['sdc_name']}: {a['message']}" for a in alerts])
    
    msg.attach(MIMEText(plain_text, 'plain'))
    msg.attach(MIMEText(html, 'html'))
    
    return msg

class EmailRecipient(BaseModel):
    email: str

@api_router.post("/gmail/send-risk-summary")
async def send_risk_summary_email(recipient: EmailRecipient, user: User = Depends(require_ho_role)):
    """Send Risk Summary email to specified recipient (HO only)"""
    # Get Gmail service
    service = await get_gmail_service(user.user_id)
    if not service:
        raise HTTPException(status_code=400, detail="Gmail not connected. Please authorize Gmail access first.")
    
    # Get alerts and dashboard data
    alerts = await db.alerts.find({"resolved": False}, {"_id": 0}).to_list(1000)
    
    # Get dashboard overview
    work_orders = await db.work_orders.find({}, {"_id": 0}).to_list(1000)
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(1000)
    
    total_portfolio = sum(wo.get("total_contract_value", 0) for wo in work_orders)
    total_billed = sum(inv.get("billing_value", 0) for inv in invoices)
    total_paid = sum(inv.get("payment_received", 0) for inv in invoices)
    outstanding = sum(inv.get("outstanding", 0) for inv in invoices)
    
    dashboard_data = {
        "commercial_health": {
            "total_portfolio": total_portfolio,
            "actual_billed": total_billed,
            "collected": total_paid,
            "outstanding": outstanding,
            "variance": total_portfolio - total_billed
        }
    }
    
    # Create email
    message = create_risk_summary_email(alerts, dashboard_data, recipient.email)
    
    try:
        # Get sender's email
        profile = service.users().getProfile(userId='me').execute()
        sender_email = profile['emailAddress']
        message['From'] = sender_email
        
        # Encode and send
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_result = service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()
        
        logger.info(f"Risk summary email sent to {recipient.email}, message ID: {send_result['id']}")
        
        # Log the email
        await db.email_logs.insert_one({
            "email_id": send_result['id'],
            "recipient": recipient.email,
            "sender": sender_email,
            "subject": message['Subject'],
            "type": "risk_summary",
            "alerts_count": len(alerts),
            "sent_by": user.user_id,
            "sent_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "message": "Risk summary email sent successfully",
            "email_id": send_result['id'],
            "recipient": recipient.email,
            "alerts_count": len(alerts)
        }
        
    except HttpError as e:
        logger.error(f"Gmail API error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@api_router.get("/email-logs")
async def get_email_logs(user: User = Depends(require_ho_role)):
    """Get email sending history (HO only)"""
    logs = await db.email_logs.find({}, {"_id": 0}).sort("sent_at", -1).to_list(100)
    return logs

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
