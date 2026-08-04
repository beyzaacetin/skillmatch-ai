import datetime
from sqlalchemy.orm import Session
import models

def check_and_release_expired_ownerships(db: Session):
    """
    Checks active applications that have expired ownership, transitions them to
    unlocked (common pool) state, and notifies waiting recruiters.
    """
    now = datetime.datetime.utcnow()
    # Find active applications with expired ownership
    expired_apps = db.query(models.Application).filter(
        models.Application.lock_status == 'LOCKED',
        models.Application.ownership_expires_at != None,
        models.Application.ownership_expires_at <= now,
        models.Application.status.notin_(['hired', 'rejected', 'withdrawn'])
    ).all()

    released_count = 0
    for app in expired_apps:
        candidate = db.query(models.Candidate).filter_by(id=app.candidate_id).first()
        hotel = db.query(models.Hotel).filter_by(id=app.hotel_id).first()
        cand_name = candidate.name if candidate else "Bilinmeyen Aday"
        hotel_name = hotel.name if hotel else "Bilinmeyen Otel"

        # Update application state
        app.lock_status = 'UNLOCKED'
        app.status = "rejected"  # Close this application
        history = app.status_history or []
        history.append({
            "status": "rejected",
            "changed_at": now.isoformat(),
            "changed_by": "SYSTEM",
            "note": f"Sahiplik süresi doldu ({hotel_name}). Ortak havuza aktarıldı."
        })
        app.status_history = history
        db.add(app)

        # Create Immutable Audit Log
        audit = models.ImmutableAuditLog(
            user_id=0,
            user_name="SYSTEM",
            action="auto_release",
            target_type="application",
            target_id=app.id,
            details={
                "candidate_id": app.candidate_id,
                "candidate_name": cand_name,
                "owning_hotel_id": app.hotel_id,
                "owning_hotel_name": hotel_name,
                "expires_at": app.ownership_expires_at.isoformat() if app.ownership_expires_at else None
            }
        )
        db.add(audit)

        # Notify owning hotel recruiters
        hr_users = db.query(models.User).all()
        for u in hr_users:
            if app.hotel_id in (u.hotel_access_ids or []) and u.role in ["HOTEL_HR", "HR", "RECRUITER", "SYSTEM_ADMIN"]:
                notif = models.Notification(
                    user_id=u.id,
                    title="Sahiplik Süresi Doldu",
                    message=f"{cand_name} isimli adayın sahiplik süresi dolduğundan ortak havuza aktarıldı."
                )
                db.add(notif)

        # Notify waiting list recruiters
        waiting_entries = db.query(models.CandidateInterestWaitingList).filter_by(
            candidate_id=app.candidate_id,
            notified=False
        ).all()
        for entry in waiting_entries:
            notif = models.Notification(
                user_id=entry.user_id,
                title="Aday Ortak Havuzda",
                message=f"Takip ettiğiniz {cand_name} isimli aday ortak havuza aktarıldı ve artık yeni işlemler için uygun."
            )
            db.add(notif)
            entry.notified = True
            db.add(entry)

        released_count += 1
    
    if released_count > 0:
        db.commit()
    return released_count


def reset_ownership_timer(application_id: int, db: Session, action: str) -> bool:
    """
    Resets the application ownership expiration if the performed action
    is configured to trigger a timer reset.
    """
    # Fetch reset actions configuration
    cfg_actions = db.query(models.SystemConfiguration).filter_by(key="timer_reset_actions").first()
    reset_actions = cfg_actions.value if cfg_actions else ['interview_scheduled', 'phone_call_logged', 'interview_completed', 'offer_created', 'status_changed']
    
    if action not in reset_actions:
        return False

    app = db.query(models.Application).filter_by(id=application_id).first()
    if not app:
        return False

    # Fetch duration configuration
    cfg_days = db.query(models.SystemConfiguration).filter_by(key="ownership_duration_days").first()
    duration_days = int(cfg_days.value) if cfg_days else 10

    now = datetime.datetime.utcnow()
    app.ownership_started_at = now
    app.ownership_expires_at = now + datetime.timedelta(days=duration_days)
    app.lock_status = 'LOCKED'  # Re-lock if it was unlocked
    db.add(app)
    
    # Audit log
    candidate = db.query(models.Candidate).filter_by(id=app.candidate_id).first()
    audit = models.ImmutableAuditLog(
        user_id=0,
        user_name="SYSTEM",
        action="reset_timer",
        target_type="application",
        target_id=app.id,
        details={
            "action_trigger": action,
            "duration_days": duration_days,
            "expires_at": app.ownership_expires_at.isoformat(),
            "candidate_name": candidate.name if candidate else "Bilinmeyen Aday"
        }
    )
    db.add(audit)
    db.commit()
    return True


def check_candidate_lock(candidate_id: int, requesting_user: models.User, db: Session) -> dict:
    """
    Checks if a candidate is actively locked by another hotel.
    Allows access if the user has GLOBAL/REGION visibility or belongs to the owning hotel.
    """
    # Find active lock applications (not hired/rejected/withdrawn and lock_status == 'LOCKED')
    active_app = db.query(models.Application).filter(
        models.Application.candidate_id == candidate_id,
        models.Application.lock_status == 'LOCKED',
        models.Application.status.notin_(['hired', 'rejected', 'withdrawn'])
    ).first()

    if not active_app:
        return {"locked": False}

    # Bypassed if global access or requesting_user belongs to the owning hotel
    is_owner = requesting_user.hotel_access_ids and (active_app.hotel_id in requesting_user.hotel_access_ids)
    is_central = requesting_user.data_visibility_scope == "GLOBAL"

    if is_owner or is_central:
        return {"locked": False, "bypass_allowed": True, "owning_hotel_id": active_app.hotel_id, "application_id": active_app.id, "expires_at": active_app.ownership_expires_at.isoformat() if active_app.ownership_expires_at else None}

    # Locked for this user
    hotel = db.query(models.Hotel).filter_by(id=active_app.hotel_id).first()
    pos = db.query(models.Position).filter_by(id=active_app.position_id).first()
    
    return {
        "locked": True,
        "bypass_allowed": False,
        "owning_hotel_id": active_app.hotel_id,
        "application_id": active_app.id,
        "owning_hotel_name": hotel.name if hotel else "Bilinmeyen Otel",
        "position_title": pos.title if pos else "Bilinmeyen Pozisyon",
        "stage": active_app.status.value if hasattr(active_app.status, "value") else str(active_app.status),
        "expires_at": active_app.ownership_expires_at.isoformat() if active_app.ownership_expires_at else None
    }
