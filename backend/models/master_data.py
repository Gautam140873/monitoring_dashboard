"""
Master Data models for SkillFlow CRM
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid


class JobRoleMaster(BaseModel):
    """Master Data - Job Role Configuration (HO Only)"""
    model_config = ConfigDict(extra="ignore")
    job_role_id: str = Field(default_factory=lambda: f"jr_{uuid.uuid4().hex[:8]}")
    job_role_code: str
    job_role_name: str
    category: str
    rate_per_hour: float
    total_training_hours: int
    awarding_body: str
    scheme_name: str
    default_daily_hours: int = 8
    default_batch_size: int = 30
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MasterWorkOrder(BaseModel):
    """Master Data - Work Order with Multiple Job Roles and SDCs (HO Only)"""
    model_config = ConfigDict(extra="ignore")
    master_wo_id: str = Field(default_factory=lambda: f"mwo_{uuid.uuid4().hex[:8]}")
    work_order_number: str
    job_roles: List[dict] = []
    total_training_target: int = 0
    num_sdcs: int = 0
    sdc_districts: List[dict] = []
    total_contract_value: float = 0
    awarding_body: str = ""
    scheme_name: str = ""
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
