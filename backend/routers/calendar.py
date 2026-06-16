from fastapi import APIRouter, Depends, HTTPException, Body, Response
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas, database, auth
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=List[schemas.CalendarEventOut])
def get_calendar_events(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Fetch all calendar events."""
    return db.query(models.CalendarEvent).all()

@router.post("/", response_model=schemas.CalendarEventOut, status_code=201)
def create_calendar_event(
    event_in: schemas.CalendarEventCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Create a new calendar event."""
    user_role_upper = current_user.role.upper() if current_user.role else ""
    if user_role_upper == "VIEWER":
        raise HTTPException(status_code=403, detail="İzleyici (Viewer) rolü takvim etkinliği oluşturamaz.")
        
    event = models.CalendarEvent(
        title=event_in.title,
        description=event_in.description,
        event_type=event_in.event_type,
        start_time=event_in.start_time,
        end_time=event_in.end_time,
        candidate_id=event_in.candidate_id,
        position_id=event_in.position_id,
        application_id=event_in.application_id,
        interview_id=event_in.interview_id,
        task_id=event_in.task_id
    )
    
    # If it is an interview event type and interview_id is not set, create a models.Interview as well
    if event_in.event_type == "interview" and not event_in.interview_id and event_in.application_id:
        # Check if application exists
        app = db.query(models.Application).filter(models.Application.id == event_in.application_id).first()
        if app:
            new_interview = models.Interview(
                application_id=event_in.application_id,
                interview_type="hr",
                status="scheduled",
                scheduled_at=event_in.start_time,
                interviewer_name=current_user.full_name
            )
            db.add(new_interview)
            db.commit()
            db.refresh(new_interview)
            event.interview_id = new_interview.id
            
            # Log candidate activity
            activity = models.CandidateActivity(
                candidate_id=app.candidate_id,
                application_id=app.id,
                activity_type="interview_scheduled",
                note=f"Mülakat planlandı: {event_in.title} ({event_in.start_time.strftime('%d.%m.%Y %H:%M')})",
                created_by=current_user.full_name
            )
            db.add(activity)

    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@router.patch("/{id}", response_model=schemas.CalendarEventOut)
def update_calendar_event(
    id: int,
    payload: dict = Body(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Update a calendar event."""
    user_role_upper = current_user.role.upper() if current_user.role else ""
    if user_role_upper == "VIEWER":
        raise HTTPException(status_code=403, detail="İzleyici (Viewer) rolü takvim etkinliği güncelleyemez.")
        
    event = db.query(models.CalendarEvent).filter(models.CalendarEvent.id == id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadı.")
        
    if "title" in payload: event.title = payload["title"]
    if "description" in payload: event.description = payload["description"]
    if "event_type" in payload: event.event_type = payload["event_type"]
    if "start_time" in payload:
        event.start_time = datetime.fromisoformat(payload["start_time"].replace("Z", "+00:00"))
        # Sync with linked interview if exists
        if event.interview_id:
            iv = db.query(models.Interview).filter(models.Interview.id == event.interview_id).first()
            if iv:
                iv.scheduled_at = event.start_time
    if "end_time" in payload:
        if payload["end_time"]:
            event.end_time = datetime.fromisoformat(payload["end_time"].replace("Z", "+00:00"))
        else:
            event.end_time = None
            
    db.commit()
    db.refresh(event)
    return event

@router.delete("/{id}", status_code=204)
def delete_calendar_event(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Delete a calendar event."""
    user_role_upper = current_user.role.upper() if current_user.role else ""
    if user_role_upper == "VIEWER":
        raise HTTPException(status_code=403, detail="İzleyici (Viewer) rolü takvim etkinliği silemez.")
        
    event = db.query(models.CalendarEvent).filter(models.CalendarEvent.id == id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadı.")
        
    # If there is a linked interview, delete it as well or set status to cancelled
    if event.interview_id:
        iv = db.query(models.Interview).filter(models.Interview.id == event.interview_id).first()
        if iv:
            db.delete(iv)
            
    db.delete(event)
    db.commit()
    return Response(status_code=204)
