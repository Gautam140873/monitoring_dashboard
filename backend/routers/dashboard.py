"""
Dashboard router for SkillFlow CRM
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone
import uuid

from ..database import db
from ..models.user import User
from ..services.auth import get_current_user, require_ho_role
from ..config import TRAINING_STAGES

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview")
async def get_dashboard_overview(user: User = Depends(get_current_user)):
    """Get dashboard overview with commercial health metrics"""
    sdc_query = {}
    if user.role not in ["ho", "admin"] and user.assigned_sdc_id:
        sdc_query["sdc_id"] = user.assigned_sdc_id
    
    sdcs = await db.sdcs.find(sdc_query, {"_id": 0}).to_list(1000)
    work_orders = await db.work_orders.find(sdc_query, {"_id": 0}).to_list(1000)
    total_portfolio = sum(wo.get("total_contract_value", 0) for wo in work_orders)
    
    invoices = await db.invoices.find(sdc_query, {"_id": 0}).to_list(1000)
    total_billed = sum(inv.get("billing_value", 0) for inv in invoices)
    total_paid = sum(inv.get("payment_received", 0) for inv in invoices)
    outstanding = sum(inv.get("outstanding", 0) for inv in invoices)
    
    roadmaps = await db.training_roadmaps.find(sdc_query, {"_id": 0}).to_list(1000)
    
    stage_totals = {}
    for stage in TRAINING_STAGES:
        stage_roadmaps = [r for r in roadmaps if r["stage_id"] == stage["stage_id"]]
        stage_totals[stage["stage_id"]] = {
            "name": stage["name"],
            "target": sum(r.get("target_count", 0) for r in stage_roadmaps),
            "completed": sum(r.get("completed_count", 0) for r in stage_roadmaps)
        }
    
    variance = total_portfolio - total_billed
    variance_percent = round((variance / total_portfolio * 100) if total_portfolio > 0 else 0, 1)
    
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
        
        sdc_stage_progress = {}
        for stage in TRAINING_STAGES:
            stage_rms = [r for r in sdc_roadmaps if r["stage_id"] == stage["stage_id"]]
            sdc_stage_progress[stage["stage_id"]] = {
                "target": sum(r.get("target_count", 0) for r in stage_rms),
                "completed": sum(r.get("completed_count", 0) for r in stage_rms)
            }
        
        overdue_count = sum(1 for wo in sdc_work_orders 
                          if wo.get("calculated_end_date") and wo["calculated_end_date"] < today 
                          and wo.get("status") == "active")
        
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
            "blockers": blockers[:3]
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


# Alerts endpoints
@router.get("/alerts")
async def get_alerts(user: User = Depends(get_current_user)):
    """Get risk alerts"""
    query = {"resolved": False}
    if user.role not in ["ho", "admin"] and user.assigned_sdc_id:
        query["sdc_id"] = user.assigned_sdc_id
    
    alerts = await db.alerts.find(query, {"_id": 0}).to_list(1000)
    return alerts


@router.post("/alerts/generate")
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


@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, user: User = Depends(require_ho_role)):
    """Resolve an alert (HO only)"""
    result = await db.alerts.update_one({"alert_id": alert_id}, {"$set": {"resolved": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert resolved"}
