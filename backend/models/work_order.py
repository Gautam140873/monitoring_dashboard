"""
Work Order and related models for SkillFlow CRM
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
import uuid


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
    sessions_per_day: int = 8
    num_students: int
    cost_per_student: float
    total_contract_value: float = 0
    manager_email: Optional[str] = None
    start_date: Optional[str] = None
    calculated_end_date: Optional[str] = None
    manual_end_date: Optional[str] = None
    status: str = "active"
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
    status: str = "pending"
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
    order_value: float
    billing_value: float
    variance: float = 0
    variance_percent: float = 0
    payment_received: float = 0
    outstanding: float = 0
    status: str = "pending"
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
    sdc_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Alert(BaseModel):
    model_config = ConfigDict(extra="ignore")
    alert_id: str = Field(default_factory=lambda: f"alert_{uuid.uuid4().hex[:8]}")
    sdc_id: str
    sdc_name: str
    work_order_id: Optional[str] = None
    alert_type: str
    message: str
    severity: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
