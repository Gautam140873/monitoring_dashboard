"""
Request/Response schemas for SkillFlow CRM
"""
from pydantic import BaseModel
from typing import Optional, List


class SessionRequest(BaseModel):
    session_id: str


class SDCCreate(BaseModel):
    name: str
    location: str
    manager_email: Optional[str] = None


class WorkOrderCreate(BaseModel):
    work_order_number: str
    location: str
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


# Master Data Request Models
class JobRoleMasterCreate(BaseModel):
    """Create a new Job Role in Master Data"""
    job_role_code: str
    job_role_name: str
    category: str
    rate_per_hour: Optional[float] = None
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


class JobRoleAllocation(BaseModel):
    """Job Role allocation within a Work Order"""
    job_role_id: str
    target: int


class SDCDistrictAllocation(BaseModel):
    """SDC/District allocation within a Work Order"""
    district_name: str
    sdc_count: int = 1


class MasterWorkOrderCreate(BaseModel):
    """Create Work Order with multiple job roles and SDC districts"""
    work_order_number: str
    awarding_body: str
    scheme_name: str
    total_training_target: int
    job_roles: List[JobRoleAllocation]
    sdc_districts: List[SDCDistrictAllocation]


class MasterWorkOrderUpdate(BaseModel):
    """Update Master Work Order"""
    awarding_body: Optional[str] = None
    scheme_name: Optional[str] = None
    total_training_target: Optional[int] = None
    status: Optional[str] = None


class SDCFromMasterCreate(BaseModel):
    """Create/Open SDC from Master Work Order"""
    master_wo_id: str
    district_name: str
    sdc_suffix: Optional[str] = None
    job_role_id: str
    target_students: int
    daily_hours: int = 8
    manager_email: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    # Resource assignments
    infra_id: Optional[str] = None
    manager_id: Optional[str] = None
    trainer_id: Optional[str] = None


# Resource Master Request Models
class TrainerCreate(BaseModel):
    """Create a new Trainer"""
    name: str
    email: str
    phone: str
    qualification: str
    specialization: str
    domain: Optional[str] = None
    experience_years: int = 0
    nsqf_level: Optional[int] = None
    certifications: List[str] = []
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None


class TrainerUpdate(BaseModel):
    """Update Trainer"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    domain: Optional[str] = None
    experience_years: Optional[int] = None
    nsqf_level: Optional[int] = None
    certifications: Optional[List[str]] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class CenterManagerCreate(BaseModel):
    """Create a new Center Manager"""
    name: str
    email: str
    phone: str
    qualification: Optional[str] = None
    experience_years: int = 0
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None


class CenterManagerUpdate(BaseModel):
    """Update Center Manager"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class SDCInfrastructureCreate(BaseModel):
    """Create SDC Infrastructure"""
    center_name: str
    center_code: str
    district: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    pincode: str
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    total_capacity: int = 30
    num_classrooms: int = 1
    num_computer_labs: int = 0
    has_projector: bool = True
    has_ac: bool = False
    has_library: bool = False
    has_biometric: bool = False
    has_internet: bool = False
    has_fire_safety: bool = False
    other_facilities: List[str] = []


class SDCInfrastructureUpdate(BaseModel):
    """Update SDC Infrastructure"""
    center_name: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    total_capacity: Optional[int] = None
    num_classrooms: Optional[int] = None
    num_computer_labs: Optional[int] = None
    has_projector: Optional[bool] = None
    has_ac: Optional[bool] = None
    has_library: Optional[bool] = None
    has_biometric: Optional[bool] = None
    has_internet: Optional[bool] = None
    has_fire_safety: Optional[bool] = None
    other_facilities: Optional[List[str]] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class StageUpdateRequest(BaseModel):
    """Update SDC process stage"""
    stage_id: str
    status: Optional[str] = None
    completed: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class DeliverableUpdateRequest(BaseModel):
    """Update SDC deliverable"""
    deliverable_id: str
    status: str  # "yes", "no", "not_required"
