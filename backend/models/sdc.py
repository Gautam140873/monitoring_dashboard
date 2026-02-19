"""
SDC model for SkillFlow CRM
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
import uuid


class SDC(BaseModel):
    model_config = ConfigDict(extra="ignore")
    sdc_id: str = Field(default_factory=lambda: f"sdc_{uuid.uuid4().hex[:8]}")
    name: str
    location: str
    manager_email: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
