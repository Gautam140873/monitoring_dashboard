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

class UserSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    session_id: str
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SDC(BaseModel):
    model_config = ConfigDict(extra="ignore")
    sdc_id: str = Field(default_factory=lambda: f"sdc_{uuid.uuid4().hex[:8]}")
    name: str
    location: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class JobRole(BaseModel):
    model_config = ConfigDict(extra="ignore")
    job_role_id: str = Field(default_factory=lambda: f"jr_{uuid.uuid4().hex[:8]}")
    sdc_id: str
    job_role_code: str
    job_role_name: str
    awarding_body: str
    scheme_name: str
    training_hours: int
    cost_per_hour: float
    target_candidates: int
    total_value: float = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Batch(BaseModel):
    model_config = ConfigDict(extra="ignore")
    batch_id: str = Field(default_factory=lambda: f"batch_{uuid.uuid4().hex[:8]}")
    sdc_id: str
    job_role_id: str
    work_order_number: str
    start_date: str
    end_date: Optional[str] = None
    mobilized: int = 0
    in_training: int = 0
    assessed: int = 0
    placed: int = 0
    status: str = "active"  # active, completed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    invoice_id: str = Field(default_factory=lambda: f"inv_{uuid.uuid4().hex[:8]}")
    sdc_id: str
    batch_id: Optional[str] = None
    invoice_number: str
    invoice_date: str
    amount: float
    status: str = "pending"  # pending, paid
    payment_date: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Holiday(BaseModel):
    model_config = ConfigDict(extra="ignore")
    holiday_id: str = Field(default_factory=lambda: f"hol_{uuid.uuid4().hex[:8]}")
    date: str
    name: str
    year: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Alert(BaseModel):
    model_config = ConfigDict(extra="ignore")
    alert_id: str = Field(default_factory=lambda: f"alert_{uuid.uuid4().hex[:8]}")
    sdc_id: str
    sdc_name: str
    alert_type: str  # overdue, variance
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

class JobRoleCreate(BaseModel):
    sdc_id: str
    job_role_code: str
    job_role_name: str
    awarding_body: str
    scheme_name: str
    training_hours: int
    cost_per_hour: float
    target_candidates: int

class BatchCreate(BaseModel):
    sdc_id: str
    job_role_id: str
    work_order_number: str
    start_date: str
    mobilized: int = 0

class BatchUpdate(BaseModel):
    mobilized: Optional[int] = None
    in_training: Optional[int] = None
    assessed: Optional[int] = None
    placed: Optional[int] = None
    status: Optional[str] = None

class InvoiceCreate(BaseModel):
    sdc_id: str
    batch_id: Optional[str] = None
    invoice_number: str
    invoice_date: str
    amount: float

class InvoiceUpdate(BaseModel):
    status: Optional[str] = None
    payment_date: Optional[str] = None

class HolidayCreate(BaseModel):
    date: str
    name: str
    year: int

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
    
    # Find session
    session_doc = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Check expiry
    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Get user
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

def calculate_end_date(start_date: str, training_hours: int, hours_per_day: int = 8, holidays: List[str] = None) -> str:
    """Calculate training end date skipping Sundays and holidays"""
    if holidays is None:
        holidays = []
    
    start = datetime.strptime(start_date, "%Y-%m-%d")
    training_days = (training_hours + hours_per_day - 1) // hours_per_day  # Ceil division
    
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
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        # Update user info
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": name, "picture": picture}}
        )
        role = existing_user.get("role", "sdc")
        assigned_sdc_id = existing_user.get("assigned_sdc_id")
    else:
        # Create new user
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        new_user = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "role": "sdc",  # Default role
            "assigned_sdc_id": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(new_user)
        role = "sdc"
        assigned_sdc_id = None
    
    # Create session
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    session_doc = {
        "session_id": req.session_id,
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Delete old sessions for this user
    await db.user_sessions.delete_many({"user_id": user_id})
    await db.user_sessions.insert_one(session_doc)
    
    # Set cookie
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
    sdc = SDC(**sdc_data.model_dump())
    sdc_dict = sdc.model_dump()
    sdc_dict["created_at"] = sdc_dict["created_at"].isoformat()
    sdc_dict["last_updated"] = sdc_dict["last_updated"].isoformat()
    await db.sdcs.insert_one(sdc_dict)
    return sdc_dict

@api_router.get("/sdcs/{sdc_id}")
async def get_sdc(sdc_id: str, user: User = Depends(get_current_user)):
    """Get SDC details with progress"""
    # Check access
    if user.role != "ho" and user.assigned_sdc_id != sdc_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    sdc = await db.sdcs.find_one({"sdc_id": sdc_id}, {"_id": 0})
    if not sdc:
        raise HTTPException(status_code=404, detail="SDC not found")
    
    # Get batches for this SDC
    batches = await db.batches.find({"sdc_id": sdc_id}, {"_id": 0}).to_list(1000)
    
    # Calculate progress
    total_mobilized = sum(b.get("mobilized", 0) for b in batches)
    total_in_training = sum(b.get("in_training", 0) for b in batches)
    total_assessed = sum(b.get("assessed", 0) for b in batches)
    total_placed = sum(b.get("placed", 0) for b in batches)
    
    # Get job roles
    job_roles = await db.job_roles.find({"sdc_id": sdc_id}, {"_id": 0}).to_list(1000)
    
    # Get invoices
    invoices = await db.invoices.find({"sdc_id": sdc_id}, {"_id": 0}).to_list(1000)
    total_billed = sum(inv.get("amount", 0) for inv in invoices)
    total_paid = sum(inv.get("amount", 0) for inv in invoices if inv.get("status") == "paid")
    outstanding = total_billed - total_paid
    
    return {
        **sdc,
        "progress": {
            "mobilized": total_mobilized,
            "in_training": total_in_training,
            "assessed": total_assessed,
            "placed": total_placed,
            "placement_percent": round((total_placed / total_mobilized * 100) if total_mobilized > 0 else 0, 1)
        },
        "financial": {
            "total_billed": total_billed,
            "total_paid": total_paid,
            "outstanding": outstanding
        },
        "job_roles": job_roles,
        "batches": batches,
        "invoices": invoices
    }

@api_router.delete("/sdcs/{sdc_id}")
async def delete_sdc(sdc_id: str, user: User = Depends(require_ho_role)):
    """Delete SDC (HO only)"""
    result = await db.sdcs.delete_one({"sdc_id": sdc_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="SDC not found")
    
    # Delete related data
    await db.job_roles.delete_many({"sdc_id": sdc_id})
    await db.batches.delete_many({"sdc_id": sdc_id})
    await db.invoices.delete_many({"sdc_id": sdc_id})
    
    return {"message": "SDC deleted successfully"}

# ==================== JOB ROLE ENDPOINTS ====================

@api_router.get("/job-roles")
async def list_job_roles(sdc_id: Optional[str] = None, user: User = Depends(get_current_user)):
    """List job roles"""
    query = {}
    if user.role != "ho":
        if user.assigned_sdc_id:
            query["sdc_id"] = user.assigned_sdc_id
        else:
            return []
    elif sdc_id:
        query["sdc_id"] = sdc_id
    
    job_roles = await db.job_roles.find(query, {"_id": 0}).to_list(1000)
    return job_roles

@api_router.post("/job-roles")
async def create_job_role(job_role_data: JobRoleCreate, user: User = Depends(require_ho_role)):
    """Create job role (HO only)"""
    job_role = JobRole(**job_role_data.model_dump())
    job_role.total_value = job_role.training_hours * job_role.cost_per_hour * job_role.target_candidates
    
    job_role_dict = job_role.model_dump()
    job_role_dict["created_at"] = job_role_dict["created_at"].isoformat()
    await db.job_roles.insert_one(job_role_dict)
    return job_role_dict

# ==================== BATCH ENDPOINTS ====================

@api_router.get("/batches")
async def list_batches(sdc_id: Optional[str] = None, user: User = Depends(get_current_user)):
    """List batches"""
    query = {}
    if user.role != "ho":
        if user.assigned_sdc_id:
            query["sdc_id"] = user.assigned_sdc_id
        else:
            return []
    elif sdc_id:
        query["sdc_id"] = sdc_id
    
    batches = await db.batches.find(query, {"_id": 0}).to_list(1000)
    return batches

@api_router.post("/batches")
async def create_batch(batch_data: BatchCreate, user: User = Depends(get_current_user)):
    """Create batch"""
    # Check access
    if user.role != "ho" and user.assigned_sdc_id != batch_data.sdc_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get job role for training hours
    job_role = await db.job_roles.find_one({"job_role_id": batch_data.job_role_id}, {"_id": 0})
    if not job_role:
        raise HTTPException(status_code=404, detail="Job role not found")
    
    # Get holidays
    holidays_docs = await db.holidays.find({}, {"_id": 0}).to_list(1000)
    holidays = [h["date"] for h in holidays_docs]
    
    # Calculate end date
    end_date = calculate_end_date(batch_data.start_date, job_role["training_hours"], holidays=holidays)
    
    batch = Batch(**batch_data.model_dump())
    batch.end_date = end_date
    
    batch_dict = batch.model_dump()
    batch_dict["created_at"] = batch_dict["created_at"].isoformat()
    await db.batches.insert_one(batch_dict)
    return batch_dict

@api_router.put("/batches/{batch_id}")
async def update_batch(batch_id: str, batch_update: BatchUpdate, user: User = Depends(get_current_user)):
    """Update batch progress"""
    batch = await db.batches.find_one({"batch_id": batch_id}, {"_id": 0})
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Check access
    if user.role != "ho" and user.assigned_sdc_id != batch["sdc_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = {k: v for k, v in batch_update.model_dump().items() if v is not None}
    if update_data:
        await db.batches.update_one({"batch_id": batch_id}, {"$set": update_data})
    
    updated_batch = await db.batches.find_one({"batch_id": batch_id}, {"_id": 0})
    return updated_batch

# ==================== INVOICE ENDPOINTS ====================

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

@api_router.post("/invoices")
async def create_invoice(invoice_data: InvoiceCreate, user: User = Depends(get_current_user)):
    """Create invoice"""
    # Check access
    if user.role != "ho" and user.assigned_sdc_id != invoice_data.sdc_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    invoice = Invoice(**invoice_data.model_dump())
    invoice_dict = invoice.model_dump()
    invoice_dict["created_at"] = invoice_dict["created_at"].isoformat()
    await db.invoices.insert_one(invoice_dict)
    return invoice_dict

@api_router.put("/invoices/{invoice_id}")
async def update_invoice(invoice_id: str, invoice_update: InvoiceUpdate, user: User = Depends(get_current_user)):
    """Update invoice status"""
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check access
    if user.role != "ho" and user.assigned_sdc_id != invoice["sdc_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = {k: v for k, v in invoice_update.model_dump().items() if v is not None}
    if update_data:
        await db.invoices.update_one({"invoice_id": invoice_id}, {"$set": update_data})
    
    updated_invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    return updated_invoice

# ==================== HOLIDAY ENDPOINTS ====================

@api_router.get("/holidays")
async def list_holidays(year: Optional[int] = None, user: User = Depends(get_current_user)):
    """List holidays"""
    query = {}
    if year:
        query["year"] = year
    holidays = await db.holidays.find(query, {"_id": 0}).to_list(1000)
    return holidays

@api_router.post("/holidays")
async def create_holiday(holiday_data: HolidayCreate, user: User = Depends(require_ho_role)):
    """Create holiday (HO only)"""
    holiday = Holiday(**holiday_data.model_dump())
    holiday_dict = holiday.model_dump()
    holiday_dict["created_at"] = holiday_dict["created_at"].isoformat()
    await db.holidays.insert_one(holiday_dict)
    return holiday_dict

@api_router.delete("/holidays/{holiday_id}")
async def delete_holiday(holiday_id: str, user: User = Depends(require_ho_role)):
    """Delete holiday (HO only)"""
    result = await db.holidays.delete_one({"holiday_id": holiday_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Holiday not found")
    return {"message": "Holiday deleted successfully"}

# ==================== DASHBOARD ENDPOINTS ====================

@api_router.get("/dashboard/overview")
async def get_dashboard_overview(user: User = Depends(get_current_user)):
    """Get dashboard overview with commercial health metrics"""
    # Build query based on role
    sdc_query = {}
    if user.role != "ho" and user.assigned_sdc_id:
        sdc_query["sdc_id"] = user.assigned_sdc_id
    
    # Get all SDCs
    sdcs = await db.sdcs.find(sdc_query, {"_id": 0}).to_list(1000)
    
    # Get all job roles for total portfolio
    job_roles = await db.job_roles.find(sdc_query, {"_id": 0}).to_list(1000)
    total_portfolio = sum(jr.get("total_value", 0) for jr in job_roles)
    
    # Get all invoices
    invoices = await db.invoices.find(sdc_query, {"_id": 0}).to_list(1000)
    total_billed = sum(inv.get("amount", 0) for inv in invoices)
    total_paid = sum(inv.get("amount", 0) for inv in invoices if inv.get("status") == "paid")
    outstanding = total_billed - total_paid
    
    # Get all batches for progress
    batches = await db.batches.find(sdc_query, {"_id": 0}).to_list(1000)
    total_mobilized = sum(b.get("mobilized", 0) for b in batches)
    total_in_training = sum(b.get("in_training", 0) for b in batches)
    total_assessed = sum(b.get("assessed", 0) for b in batches)
    total_placed = sum(b.get("placed", 0) for b in batches)
    
    # Calculate variance
    variance = total_portfolio - total_billed
    variance_percent = round((variance / total_portfolio * 100) if total_portfolio > 0 else 0, 1)
    
    # Build SDC summaries
    sdc_summaries = []
    for sdc in sdcs:
        sdc_batches = [b for b in batches if b.get("sdc_id") == sdc["sdc_id"]]
        sdc_invoices = [inv for inv in invoices if inv.get("sdc_id") == sdc["sdc_id"]]
        sdc_job_roles = [jr for jr in job_roles if jr.get("sdc_id") == sdc["sdc_id"]]
        
        sdc_mobilized = sum(b.get("mobilized", 0) for b in sdc_batches)
        sdc_in_training = sum(b.get("in_training", 0) for b in sdc_batches)
        sdc_assessed = sum(b.get("assessed", 0) for b in sdc_batches)
        sdc_placed = sum(b.get("placed", 0) for b in sdc_batches)
        sdc_billed = sum(inv.get("amount", 0) for inv in sdc_invoices)
        sdc_paid = sum(inv.get("amount", 0) for inv in sdc_invoices if inv.get("status") == "paid")
        sdc_portfolio = sum(jr.get("total_value", 0) for jr in sdc_job_roles)
        
        sdc_summaries.append({
            "sdc_id": sdc["sdc_id"],
            "name": sdc["name"],
            "location": sdc["location"],
            "progress": {
                "mobilized": sdc_mobilized,
                "in_training": sdc_in_training,
                "assessed": sdc_assessed,
                "placed": sdc_placed,
                "total": sdc_mobilized,
                "placement_percent": round((sdc_placed / sdc_mobilized * 100) if sdc_mobilized > 0 else 0, 1)
            },
            "financial": {
                "portfolio": sdc_portfolio,
                "billed": sdc_billed,
                "paid": sdc_paid,
                "outstanding": sdc_billed - sdc_paid,
                "variance": sdc_portfolio - sdc_billed
            }
        })
    
    return {
        "commercial_health": {
            "total_portfolio": total_portfolio,
            "actual_billed": total_billed,
            "outstanding": outstanding,
            "variance": variance,
            "variance_percent": variance_percent
        },
        "progress": {
            "mobilized": total_mobilized,
            "in_training": total_in_training,
            "assessed": total_assessed,
            "placed": total_placed,
            "placement_percent": round((total_placed / total_mobilized * 100) if total_mobilized > 0 else 0, 1)
        },
        "sdc_count": len(sdcs),
        "sdc_summaries": sdc_summaries
    }

# ==================== ALERTS ENDPOINTS ====================

@api_router.get("/alerts")
async def get_alerts(user: User = Depends(get_current_user)):
    """Get risk alerts"""
    # Build query based on role
    query = {"resolved": False}
    if user.role != "ho" and user.assigned_sdc_id:
        query["sdc_id"] = user.assigned_sdc_id
    
    alerts = await db.alerts.find(query, {"_id": 0}).to_list(1000)
    return alerts

@api_router.post("/alerts/generate")
async def generate_alerts(user: User = Depends(require_ho_role)):
    """Generate risk alerts based on current data (HO only)"""
    # Clear old unresolved alerts
    await db.alerts.delete_many({"resolved": False})
    
    # Get all SDCs
    sdcs = await db.sdcs.find({}, {"_id": 0}).to_list(1000)
    
    new_alerts = []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    for sdc in sdcs:
        sdc_id = sdc["sdc_id"]
        sdc_name = sdc["name"]
        
        # Check for overdue batches
        batches = await db.batches.find({"sdc_id": sdc_id, "status": "active"}, {"_id": 0}).to_list(1000)
        for batch in batches:
            if batch.get("end_date") and batch["end_date"] < today:
                alert = Alert(
                    sdc_id=sdc_id,
                    sdc_name=sdc_name,
                    alert_type="overdue",
                    message=f"Batch {batch['work_order_number']} is overdue (End: {batch['end_date']})",
                    severity="high"
                )
                alert_dict = alert.model_dump()
                alert_dict["created_at"] = alert_dict["created_at"].isoformat()
                new_alerts.append(alert_dict)
        
        # Check for billing variance > 10%
        job_roles = await db.job_roles.find({"sdc_id": sdc_id}, {"_id": 0}).to_list(1000)
        invoices = await db.invoices.find({"sdc_id": sdc_id}, {"_id": 0}).to_list(1000)
        
        total_portfolio = sum(jr.get("total_value", 0) for jr in job_roles)
        total_billed = sum(inv.get("amount", 0) for inv in invoices)
        
        if total_portfolio > 0:
            variance_percent = ((total_portfolio - total_billed) / total_portfolio) * 100
            if variance_percent > 10:
                alert = Alert(
                    sdc_id=sdc_id,
                    sdc_name=sdc_name,
                    alert_type="variance",
                    message=f"Billing variance is {variance_percent:.1f}% (Portfolio: ₹{total_portfolio:,.0f}, Billed: ₹{total_billed:,.0f})",
                    severity="medium" if variance_percent < 25 else "high"
                )
                alert_dict = alert.model_dump()
                alert_dict["created_at"] = alert_dict["created_at"].isoformat()
                new_alerts.append(alert_dict)
    
    # Insert new alerts
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
async def api_calculate_end_date(start_date: str, training_hours: int, user: User = Depends(get_current_user)):
    """Calculate training end date"""
    holidays_docs = await db.holidays.find({}, {"_id": 0}).to_list(1000)
    holidays = [h["date"] for h in holidays_docs]
    
    end_date = calculate_end_date(start_date, training_hours, holidays=holidays)
    return {"start_date": start_date, "end_date": end_date, "training_hours": training_hours}

@api_router.get("/")
async def root():
    return {"message": "SkillFlow CRM API", "version": "1.0.0"}

# ==================== SEED DATA ENDPOINT ====================

@api_router.post("/seed-data")
async def seed_sample_data(user: User = Depends(require_ho_role)):
    """Seed sample data for demo purposes (HO only)"""
    # Clear existing data
    await db.sdcs.delete_many({})
    await db.job_roles.delete_many({})
    await db.batches.delete_many({})
    await db.invoices.delete_many({})
    await db.holidays.delete_many({})
    await db.alerts.delete_many({})
    
    # Create SDCs
    sdcs_data = [
        {"sdc_id": "sdc_gurugram", "name": "SDC Gurugram", "location": "Gurugram, Haryana"},
        {"sdc_id": "sdc_jaipur", "name": "SDC Jaipur", "location": "Jaipur, Rajasthan"},
        {"sdc_id": "sdc_delhi", "name": "SDC Delhi", "location": "New Delhi"}
    ]
    for sdc in sdcs_data:
        sdc["created_at"] = datetime.now(timezone.utc).isoformat()
        sdc["last_updated"] = datetime.now(timezone.utc).isoformat()
    await db.sdcs.insert_many(sdcs_data)
    
    # Create Job Roles
    job_roles_data = [
        {"job_role_id": "jr_001", "sdc_id": "sdc_gurugram", "job_role_code": "CSC/Q0801", "job_role_name": "Field Technician Computing", "awarding_body": "NSDC PMKVY", "scheme_name": "PMKVY 4.0", "training_hours": 200, "cost_per_hour": 50, "target_candidates": 50, "total_value": 500000},
        {"job_role_id": "jr_002", "sdc_id": "sdc_gurugram", "job_role_code": "SSC/Q2212", "job_role_name": "Retail Sales Associate", "awarding_body": "NSDC PMKVY", "scheme_name": "PMKVY 4.0", "training_hours": 150, "cost_per_hour": 45, "target_candidates": 40, "total_value": 270000},
        {"job_role_id": "jr_003", "sdc_id": "sdc_jaipur", "job_role_code": "ASC/Q1401", "job_role_name": "Domestic Data Entry Operator", "awarding_body": "RSLDC", "scheme_name": "RAJKIVK", "training_hours": 180, "cost_per_hour": 40, "target_candidates": 60, "total_value": 432000},
        {"job_role_id": "jr_004", "sdc_id": "sdc_jaipur", "job_role_code": "ITC/Q7201", "job_role_name": "Plumber General", "awarding_body": "RSLDC", "scheme_name": "RAJKIVK", "training_hours": 250, "cost_per_hour": 55, "target_candidates": 30, "total_value": 412500},
        {"job_role_id": "jr_005", "sdc_id": "sdc_delhi", "job_role_code": "TEL/Q2201", "job_role_name": "CRM Domestic Voice", "awarding_body": "State Govt", "scheme_name": "DDUGKY", "training_hours": 300, "cost_per_hour": 60, "target_candidates": 45, "total_value": 810000},
        {"job_role_id": "jr_006", "sdc_id": "sdc_delhi", "job_role_code": "AMH/Q1947", "job_role_name": "Sewing Machine Operator", "awarding_body": "State Govt", "scheme_name": "DDUGKY", "training_hours": 200, "cost_per_hour": 35, "target_candidates": 55, "total_value": 385000}
    ]
    for jr in job_roles_data:
        jr["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.job_roles.insert_many(job_roles_data)
    
    # Create Batches
    batches_data = [
        {"batch_id": "batch_001", "sdc_id": "sdc_gurugram", "job_role_id": "jr_001", "work_order_number": "WO/2025/001", "start_date": "2025-01-15", "end_date": "2025-02-28", "mobilized": 50, "in_training": 35, "assessed": 10, "placed": 5, "status": "active"},
        {"batch_id": "batch_002", "sdc_id": "sdc_gurugram", "job_role_id": "jr_002", "work_order_number": "WO/2025/002", "start_date": "2025-01-20", "end_date": "2025-03-05", "mobilized": 40, "in_training": 30, "assessed": 5, "placed": 2, "status": "active"},
        {"batch_id": "batch_003", "sdc_id": "sdc_jaipur", "job_role_id": "jr_003", "work_order_number": "WO/2025/003", "start_date": "2025-01-10", "end_date": "2025-02-20", "mobilized": 60, "in_training": 40, "assessed": 15, "placed": 8, "status": "active"},
        {"batch_id": "batch_004", "sdc_id": "sdc_jaipur", "job_role_id": "jr_004", "work_order_number": "WO/2025/004", "start_date": "2025-02-01", "end_date": "2025-04-15", "mobilized": 30, "in_training": 25, "assessed": 0, "placed": 0, "status": "active"},
        {"batch_id": "batch_005", "sdc_id": "sdc_delhi", "job_role_id": "jr_005", "work_order_number": "WO/2025/005", "start_date": "2025-01-05", "end_date": "2025-03-20", "mobilized": 45, "in_training": 38, "assessed": 20, "placed": 12, "status": "active"},
        {"batch_id": "batch_006", "sdc_id": "sdc_delhi", "job_role_id": "jr_006", "work_order_number": "WO/2025/006", "start_date": "2025-01-25", "end_date": "2025-03-10", "mobilized": 55, "in_training": 45, "assessed": 8, "placed": 3, "status": "active"}
    ]
    for batch in batches_data:
        batch["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.batches.insert_many(batches_data)
    
    # Create Invoices
    invoices_data = [
        {"invoice_id": "inv_001", "sdc_id": "sdc_gurugram", "batch_id": "batch_001", "invoice_number": "INV/2025/001", "invoice_date": "2025-01-20", "amount": 200000, "status": "paid", "payment_date": "2025-01-25"},
        {"invoice_id": "inv_002", "sdc_id": "sdc_gurugram", "batch_id": "batch_001", "invoice_number": "INV/2025/002", "invoice_date": "2025-02-01", "amount": 150000, "status": "pending", "payment_date": None},
        {"invoice_id": "inv_003", "sdc_id": "sdc_jaipur", "batch_id": "batch_003", "invoice_number": "INV/2025/003", "invoice_date": "2025-01-15", "amount": 180000, "status": "paid", "payment_date": "2025-01-22"},
        {"invoice_id": "inv_004", "sdc_id": "sdc_jaipur", "batch_id": "batch_003", "invoice_number": "INV/2025/004", "invoice_date": "2025-02-05", "amount": 120000, "status": "pending", "payment_date": None},
        {"invoice_id": "inv_005", "sdc_id": "sdc_delhi", "batch_id": "batch_005", "invoice_number": "INV/2025/005", "invoice_date": "2025-01-10", "amount": 300000, "status": "paid", "payment_date": "2025-01-18"},
        {"invoice_id": "inv_006", "sdc_id": "sdc_delhi", "batch_id": "batch_006", "invoice_number": "INV/2025/006", "invoice_date": "2025-02-10", "amount": 100000, "status": "pending", "payment_date": None}
    ]
    for inv in invoices_data:
        inv["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.invoices.insert_many(invoices_data)
    
    # Create Holidays
    holidays_data = [
        {"holiday_id": "hol_001", "date": "2025-01-26", "name": "Republic Day", "year": 2025},
        {"holiday_id": "hol_002", "date": "2025-03-14", "name": "Holi", "year": 2025},
        {"holiday_id": "hol_003", "date": "2025-08-15", "name": "Independence Day", "year": 2025},
        {"holiday_id": "hol_004", "date": "2025-10-02", "name": "Gandhi Jayanti", "year": 2025},
        {"holiday_id": "hol_005", "date": "2025-10-20", "name": "Dussehra", "year": 2025},
        {"holiday_id": "hol_006", "date": "2025-11-01", "name": "Diwali", "year": 2025}
    ]
    for hol in holidays_data:
        hol["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.holidays.insert_many(holidays_data)
    
    return {"message": "Sample data seeded successfully", "sdcs": 3, "job_roles": 6, "batches": 6, "invoices": 6, "holidays": 6}

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
