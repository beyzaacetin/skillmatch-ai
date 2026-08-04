import datetime
from sqlalchemy.orm import Session
import models
import logging

logger = logging.getLogger(__name__)

def check_headcount_budget(hotel_id: int, department_id: int, position_title: str, db: Session) -> dict:
    """
    Checks the active hiring + active offer count against the headcount budget.
    Returns a dict with:
      - 'allowed': bool (True if within budget or if no budget is configured)
      - 'budget': int (configured budget, or None)
      - 'active_count': int (current active hires + active offers)
      - 'violates': bool (True if active_count >= budget)
    """
    # 1. Fetch budget config
    budget_entry = db.query(models.WorkforceHeadcountBudget).filter(
        models.WorkforceHeadcountBudget.hotel_id == hotel_id,
        models.WorkforceHeadcountBudget.department_id == department_id,
        models.WorkforceHeadcountBudget.position_title.collate("NOCASE") == position_title
    ).first()

    # 2. Count active hired or offered candidates for this position title in the hotel/department
    active_count = db.query(models.Application).join(models.Position).filter(
        models.Position.hotel_id == hotel_id,
        models.Position.department_id == department_id,
        models.Position.title.collate("NOCASE") == position_title,
        models.Application.status.in_(["hired", "offer"])
    ).count()

    if not budget_entry:
        # No budget configured -> allow by default but indicate None
        return {
            "allowed": True,
            "budget": None,
            "active_count": active_count,
            "violates": False
        }

    violates = active_count >= budget_entry.headcount_budget
    return {
        "allowed": not violates,
        "budget": budget_entry.headcount_budget,
        "active_count": active_count,
        "violates": violates
    }


def trigger_scoped_routing(candidate_id: int, source_hotel_id: int, position_title: str, db: Session):
    """
    Applies the Priority Scoped Routing rules:
      1. Other active hotels in the same Region
      2. Other active hotels in the same City
      3. Central HR
    And creates CandidateRoutingSuggestion records.
    """
    candidate = db.query(models.Candidate).filter_by(id=candidate_id).first()
    cand_name = candidate.name if candidate else "Bilinmeyen Aday"
    
    source_hotel = db.query(models.Hotel).filter_by(id=source_hotel_id).first()
    if not source_hotel:
        return

    routed_hotel_ids = set()

    # Priority 1: Same Region
    if source_hotel.region_id:
        region_hotels = db.query(models.Hotel).filter(
            models.Hotel.region_id == source_hotel.region_id,
            models.Hotel.id != source_hotel_id,
            models.Hotel.is_active == True
        ).all()
        for h in region_hotels:
            if h.id not in routed_hotel_ids:
                # Check if this target hotel has available budget
                # For simplicity, we create suggestion and let them review
                routed_hotel_ids.add(h.id)
                _create_routing_suggestion(db, candidate_id, source_hotel_id, h.id, position_title, cand_name, source_hotel.name)

    # Priority 2: Same City
    if source_hotel.city_id:
        city_hotels = db.query(models.Hotel).filter(
            models.Hotel.city_id == source_hotel.city_id,
            models.Hotel.id != source_hotel_id,
            models.Hotel.is_active == True
        ).all()
        for h in city_hotels:
            if h.id not in routed_hotel_ids:
                routed_hotel_ids.add(h.id)
                _create_routing_suggestion(db, candidate_id, source_hotel_id, h.id, position_title, cand_name, source_hotel.name)

    # Priority 3: Central HR Users
    central_users = db.query(models.User).filter(
        models.User.role.in_(["ADMIN", "SYSTEM_ADMIN", "CENTRAL_HR"]),
        models.User.is_active == True
    ).all()
    for u in central_users:
        # Create a notification directly for Central HR users
        notif = models.Notification(
            user_id=u.id,
            title="Aday Yönlendirmesi (Bütçe Aşımı)",
            message=f"{source_hotel.name} otelindeki bütçe aşımı nedeniyle {cand_name} ({position_title}) adayı yönlendirildi."
        )
        db.add(notif)
    
    db.commit()


def _create_routing_suggestion(db: Session, candidate_id: int, source_hotel_id: int, target_hotel_id: int, position_title: str, cand_name: str, source_hotel_name: str):
    # Check if duplicate routing already exists
    exists = db.query(models.CandidateRoutingSuggestion).filter_by(
        candidate_id=candidate_id,
        source_hotel_id=source_hotel_id,
        target_hotel_id=target_hotel_id,
        position_title=position_title
    ).first()
    if exists:
        return

    suggestion = models.CandidateRoutingSuggestion(
        candidate_id=candidate_id,
        source_hotel_id=source_hotel_id,
        target_hotel_id=target_hotel_id,
        position_title=position_title,
        status="PENDING"
    )
    db.add(suggestion)
    db.flush()

    # Notify recruiters of target hotel
    target_recruiters = db.query(models.User).filter(
        models.User.role.in_(["RECRUITER", "HOTEL_HR"]),
        models.User.is_active == True
    ).all()
    for u in target_recruiters:
        if u.hotel_access_ids and (target_hotel_id in u.hotel_access_ids):
            notif = models.Notification(
                user_id=u.id,
                title="Aday Yönlendirmesi (Kardeş Otel)",
                message=f"{source_hotel_name} otelindeki bütçe aşımı nedeniyle {cand_name} ({position_title}) adayı otelinize yönlendirildi."
            )
            db.add(notif)
