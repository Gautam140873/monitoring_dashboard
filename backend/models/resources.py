"""
Resource Master models for SkillFlow CRM
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid


class TrainerMaster(BaseModel):
    """Master Data - Trainer Details"""
    model_config = ConfigDict(extra="ignore")
    trainer_id: str = Field(default_factory=lambda: f"tr_{uuid.uuid4().hex[:8]}")
    name: str
    email: str
    phone: str
    qualification: str
    specialization: str
    domain: Optional[str] = None
    experience_years: int = 0
    nsqf_level: Optional[int] = None
    certifications: List[str] = []
    status: str = "available"
    assigned_sdc_id: Optional[str] = None
    assigned_work_order_id: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CenterManagerMaster(BaseModel):
    """Master Data - Center Manager Details"""
    model_config = ConfigDict(extra="ignore")
    manager_id: str = Field(default_factory=lambda: f"cm_{uuid.uuid4().hex[:8]}")
    name: str
    email: str
    phone: str
    qualification: Optional[str] = None
    experience_years: int = 0
    status: str = "available"
    assigned_sdc_id: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SDCInfrastructureMaster(BaseModel):
    """Master Data - SDC/Center Infrastructure Details"""
    model_config = ConfigDict(extra="ignore")
    infra_id: str = Field(default_factory=lambda: f"infra_{uuid.uuid4().hex[:8]}")
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
    status: str = "available"
    assigned_work_order_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
