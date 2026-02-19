"""
Utility services for SkillFlow CRM
"""
import uuid
import logging
from datetime import datetime, timezone, timedelta

from database import db
from config import TRAINING_STAGES

logger = logging.getLogger(__name__)


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
