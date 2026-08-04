from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import models
import datetime
from auth import get_current_user, check_permission, get_db
from services.ownership_service import check_and_release_expired_ownerships, check_candidate_lock, reset_ownership_timer

router = APIRouter()

# ─── SCHEMAS ─────────────────────────────────────────────────────────────────

class ExtensionRequestCreate(BaseModel):
    application_id: int
    reason_category: str
    custom_explanation: Optional[str] = None

class ResolveExtensionRequest(BaseModel):
    status: str  # APPROVED, REJECTED

class WaitingListCreate(BaseModel):
    candidate_id: int

# ─── HELPER FOR AUDIT LOGGING ────────────────────────────────────────────────

def log_audit(db: Session, user: models.User, action: str, target_type: str, target_id: Optional[int], details: dict, request: Optional[Request] = None):
    ip_addr = request.client.host if request and request.client else None
    audit = models.ImmutableAuditLog(
        user_id=user.id,
        user_name=user.full_name,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_addr
    )
    db.add(audit)
    db.commit()

# ─── ENDPOINTS ────────────────────────────────────────────────────────────────

@router.post("/extension-request", status_code=status.HTTP_201_CREATED)
def create_extension_request(
    data: ExtensionRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Hotel HR requests an extension for their candidate ownership."""
    app = db.query(models.Application).filter_by(id=data.application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Başvuru kaydı bulunamadı.")

    # Authorization Check: Must have access to the application's hotel
    if not current_user.hotel_access_ids or app.hotel_id not in current_user.hotel_access_ids:
        raise HTTPException(status_code=403, detail="Bu otelin adayı için uzatma talep edemezsiniz.")

    # Check maximum extensions count from dynamic configuration
    cfg_max = db.query(models.SystemConfiguration).filter_by(key="max_extensions_allowed").first()
    max_extensions = int(cfg_max.value) if cfg_max else 3
    if app.extension_count >= max_extensions:
        raise HTTPException(status_code=400, detail=f"Maksimum uzatma sınırına ulaşıldı (Maks: {max_extensions}).")

    # Create extension request
    req = models.CandidateExtensionRequest(
        application_id=data.application_id,
        requested_by_id=current_user.id,
        reason_category=data.reason_category,
        custom_explanation=data.custom_explanation,
        status="PENDING"
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    log_audit(db, current_user, "request_extension", "extension_request", req.id, data.dict(), request)

    # Notify Central HR users
    central_users = db.query(models.User).filter(
        models.User.role_id.in_(
            db.query(models.Role.id).filter(models.Role.code.in_(["SYSTEM_ADMIN", "CENTRAL_HR"]))
        )
    ).all()
    
    candidate = db.query(models.Candidate).filter_by(id=app.candidate_id).first()
    cand_name = candidate.name if candidate else "Bilinmeyen Aday"
    
    for u in central_users:
        notif = models.Notification(
            user_id=u.id,
            title="Yeni Sahiplik Uzatma Talebi",
            message=f"{current_user.full_name}, {cand_name} isimli aday için uzatma talep etti. Neden: {data.reason_category}"
        )
        db.add(notif)
    db.commit()

    return {
        "id": req.id,
        "status": req.status,
        "application_id": req.application_id,
        "reason_category": req.reason_category
    }


@router.get("/extension-requests")
def list_extension_requests(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Retrieve list of extension requests. Scoped by user hierarchy privileges."""
    # Central HR or Admin can view all
    is_central = current_user.data_visibility_scope == "GLOBAL"
    
    query = db.query(models.CandidateExtensionRequest).join(models.Application)
    
    if not is_central:
        # Hotel HR or Manager: Filter by their hotel accesses
        if not current_user.hotel_access_ids:
            return []
        query = query.filter(models.Application.hotel_id.in_(current_user.hotel_access_ids))
        
    requests = query.order_by(models.CandidateExtensionRequest.created_at.desc()).all()
    
    results = []
    for r in requests:
        app = db.query(models.Application).filter_by(id=r.application_id).first()
        candidate = db.query(models.Candidate).filter_by(id=app.candidate_id).first() if app else None
        hotel = db.query(models.Hotel).filter_by(id=app.hotel_id).first() if app else None
        requester = db.query(models.User).filter_by(id=r.requested_by_id).first()
        reviewer = db.query(models.User).filter_by(id=r.reviewed_by_id).first() if r.reviewed_by_id else None

        results.append({
            "id": r.id,
            "application_id": r.application_id,
            "candidate_name": candidate.name if candidate else "Bilinmeyen Aday",
            "hotel_name": hotel.name if hotel else "Bilinmeyen Otel",
            "reason_category": r.reason_category,
            "custom_explanation": r.custom_explanation,
            "status": r.status,
            "days_requested": r.days_requested,
            "requester_name": requester.full_name if requester else "Bilinmeyen İK",
            "reviewer_name": reviewer.full_name if reviewer else None,
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
            "created_at": r.created_at.isoformat()
        })
    return results


@router.put("/extension-requests/{id}/resolve")
def resolve_extension_request(
    id: int,
    data: ResolveExtensionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_permission("can_approve_offers"))  # Only approvers (Central HR / Admin) can approve
):
    """Central HR approves or rejects an ownership extension request."""
    req = db.query(models.CandidateExtensionRequest).filter_by(id=id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Talep bulunamadı.")
    
    if req.status != "PENDING":
        raise HTTPException(status_code=400, detail="Bu talep zaten sonuçlandırılmış.")

    req.status = data.status.upper()
    req.reviewed_by_id = current_user.id
    req.reviewed_at = datetime.datetime.utcnow()
    
    app = db.query(models.Application).filter_by(id=req.application_id).first()
    candidate = db.query(models.Candidate).filter_by(id=app.candidate_id).first() if app else None
    cand_name = candidate.name if candidate else "Bilinmeyen Aday"
    
    if req.status == "APPROVED" and app:
        # Extend ownership duration
        cfg_days = db.query(models.SystemConfiguration).filter_by(key="ownership_duration_days").first()
        days = int(cfg_days.value) if cfg_days else 10
        
        app.ownership_expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=days)
        app.extension_count += 1
        db.add(app)

        # Notify requester
        notif = models.Notification(
            user_id=req.requested_by_id,
            title="Sahiplik Talebi Onaylandı",
            message=f"{cand_name} isimli aday için uzatma talebiniz onaylandı. Yeni süre: +{days} gün."
        )
        db.add(notif)
    
    elif req.status == "REJECTED" and app:
        # Transfer to common pool instantly
        app.lock_status = 'UNLOCKED'
        app.status = models.ApplicationStatus.REJECTED
        history = app.status_history or []
        history.append({
            "status": "rejected",
            "changed_at": datetime.datetime.utcnow().isoformat(),
            "changed_by": current_user.full_name,
            "note": "Uzatma talebi reddedildi. Ortak havuza aktarıldı."
        })
        app.status_history = history
        db.add(app)

        # Notify requester
        notif = models.Notification(
            user_id=req.requested_by_id,
            title="Sahiplik Talebi Reddedildi",
            message=f"{cand_name} isimli aday için uzatma talebiniz reddedildi. Aday ortak havuza aktarıldı."
        )
        db.add(notif)

        # Notify waiting list recruiters
        waiting_entries = db.query(models.CandidateInterestWaitingList).filter_by(
            candidate_id=app.candidate_id,
            notified=False
        ).all()
        for entry in waiting_entries:
            wait_notif = models.Notification(
                user_id=entry.user_id,
                title="Aday Ortak Havuzda",
                message=f"Takip ettiğiniz {cand_name} isimli aday ortak havuza aktarıldı ve artık yeni işlemler için uygun."
            )
            db.add(wait_notif)
            entry.notified = True
            db.add(entry)

    db.commit()
    log_audit(db, current_user, f"resolve_extension_{req.status.lower()}", "extension_request", req.id, data.dict(), request)
    return {
        "id": req.id,
        "status": req.status,
        "extension_count": app.extension_count if app else 0
    }


@router.post("/waiting-list", status_code=status.HTTP_201_CREATED)
def subscribe_to_waiting_list(
    data: WaitingListCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Recruiter signs up to receive notification when locked candidate enters common pool."""
    # Check if recruiter already registered on waiting list
    existing = db.query(models.CandidateInterestWaitingList).filter_by(
        candidate_id=data.candidate_id,
        user_id=current_user.id,
        notified=False
    ).first()
    
    if existing:
        return {"message": "Zaten bekleme listesine kayıtlısınız."}

    # Fetch interested recruiter's active hotel
    user_hotel_id = current_user.hotel_access_ids[0] if current_user.hotel_access_ids else None
    if not user_hotel_id:
        raise HTTPException(status_code=400, detail="Bağlı olduğunuz bir otel kaydı bulunmuyor.")

    entry = models.CandidateInterestWaitingList(
        candidate_id=data.candidate_id,
        hotel_id=user_hotel_id,
        user_id=current_user.id,
        notified=False
    )
    db.add(entry)
    db.commit()

    log_audit(db, current_user, "join_waiting_list", "candidate", data.candidate_id, {"hotel_id": user_hotel_id}, request)
    return {"message": "Başarıyla bekleme listesine kaydoldunuz. Aday boşa çıktığında bilgilendirileceksiniz."}


@router.get("/candidate-lock-status/{candidate_id}")
def get_candidate_lock_details(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Query candidates locking information and details."""
    lock_details = check_candidate_lock(candidate_id, current_user, db)
    return lock_details


@router.post("/release-expired")
def run_release_expired(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_permission("can_access_settings"))  # Admin or settings privilege
):
    """Manually triggers checking and auto-release of expired ownerships."""
    released_count = check_and_release_expired_ownerships(db)
    return {
        "status": "success",
        "released_count": released_count
    }


@router.post("/release/{application_id}")
def force_release_application_lock(
    application_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_permission("can_access_settings"))  # Override permissions
):
    """Force release and unlock an active candidate application."""
    app = db.query(models.Application).filter_by(id=application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Başvuru bulunamadı.")
    
    app.lock_status = 'UNLOCKED'
    app.status = models.ApplicationStatus.REJECTED
    history = app.status_history or []
    history.append({
        "status": "rejected",
        "changed_at": datetime.datetime.utcnow().isoformat(),
        "changed_by": current_user.full_name,
        "note": "Yetkili kullanıcı tarafından kilit kaldırıldı. Ortak havuza aktarıldı."
    })
    app.status_history = history
    db.add(app)
    
    # Notify waiting list
    candidate = db.query(models.Candidate).filter_by(id=app.candidate_id).first()
    cand_name = candidate.name if candidate else "Bilinmeyen Aday"
    
    waiting_entries = db.query(models.CandidateInterestWaitingList).filter_by(
        candidate_id=app.candidate_id,
        notified=False
    ).all()
    for entry in waiting_entries:
        wait_notif = models.Notification(
            user_id=entry.user_id,
            title="Aday Ortak Havuzda",
            message=f"Kilit kaldırılan {cand_name} isimli aday artık yeni işlemler için uygun."
        )
        db.add(wait_notif)
        entry.notified = True
        db.add(entry)
        
    db.commit()
    log_audit(db, current_user, "force_release_lock", "application", app.id, {}, request)
    return {"message": "Adayın kilidi başarıyla kaldırıldı ve ortak havuza aktarıldı."}
