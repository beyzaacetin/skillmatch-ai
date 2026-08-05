from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
import models, database, auth
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi.responses import StreamingResponse
import io
import csv

router = APIRouter()

@router.post("/custom")
def generate_custom_report(
    payload: dict = Body(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    hotel_ids = payload.get("hotel_ids", [])
    date_range = payload.get("date_range") # e.g., '30d', '90d', 'all'
    departments = payload.get("departments", [])
    metrics = payload.get("metrics", [])
    
    app_query = db.query(models.Application).join(models.Position)
    
    if hotel_ids:
        app_query = app_query.filter(models.Position.hotel_id.in_(hotel_ids))
        
    if departments:
        app_query = app_query.filter(models.Position.department.in_(departments))
        
    if date_range and date_range != "all":
        days = 30
        if date_range == "7d": days = 7
        elif date_range == "90d": days = 90
        cutoff = datetime.utcnow() - timedelta(days=days)
        app_query = app_query.filter(models.Application.applied_at >= cutoff)
        
    results = {}
    
    if "candidate_count" in metrics or not metrics:
        results["candidate_count"] = app_query.distinct(models.Application.candidate_id).count()
        
    if "application_count" in metrics or not metrics:
        results["application_count"] = app_query.count()
        
    if "interview_count" in metrics or not metrics:
        results["interview_count"] = app_query.filter(models.Application.status.in_(["hr_interview", "tech_interview", "manager_interview"])).count()
        
    if "offer_count" in metrics or not metrics:
        results["offer_count"] = app_query.filter(models.Application.status == "offer").count()
        
    if "hire_count" in metrics or not metrics:
        results["hire_count"] = app_query.filter(models.Application.status == "hired").count()
        
    if "avg_match_score" in metrics or not metrics:
        scores = [a.match_score for a in app_query.all() if a.match_score is not None]
        results["avg_match_score"] = round(sum(scores) / len(scores), 1) if scores else 0.0
        
    if "avg_time_to_hire" in metrics or not metrics:
        hired_apps = app_query.filter(models.Application.status == "hired", models.Application.hired_at != None).all()
        if hired_apps:
            total_days = sum(max(1, (app.hired_at - app.applied_at).days) for app in hired_apps)
            results["avg_time_to_hire"] = round(total_days / len(hired_apps), 1)
        else:
            results["avg_time_to_hire"] = 0.0
            
    return results

@router.get("/custom/export")
def export_custom_report(
    hotel_ids: str = None, # comma separated
    date_range: str = "30d",
    departments: str = None, # comma separated
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    app_query = db.query(models.Application).join(models.Position)
    
    if hotel_ids:
        ids = [int(x) for x in hotel_ids.split(",")]
        app_query = app_query.filter(models.Position.hotel_id.in_(ids))
        
    if departments:
        depts = departments.split(",")
        app_query = app_query.filter(models.Position.department.in_(depts))
        
    if date_range and date_range != "all":
        days = 30
        if date_range == "7d": days = 7
        elif date_range == "90d": days = 90
        cutoff = datetime.utcnow() - timedelta(days=days)
        app_query = app_query.filter(models.Application.applied_at >= cutoff)
        
    apps = app_query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Application ID", "Candidate ID", "Position ID", "Status", "Match Score", "Applied At", "Hired At"])
    
    for app in apps:
        writer.writerow([
            app.id,
            app.candidate_id,
            app.position_id,
            app.status,
            app.match_score,
            app.applied_at.isoformat() if app.applied_at else "",
            app.hired_at.isoformat() if app.hired_at else ""
        ])
        
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=custom_report.csv"}
    )
