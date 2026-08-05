"""
Candidate Portal Router — Aday Kendi Başvurusunu Takip Eder
Token ile güvenli erişim — e-posta ile gönderilen link aracılığıyla.

GET  /api/portal/me                — Aday profili
GET  /api/portal/applications      — Aday başvuruları
GET  /api/portal/applications/{id} — Başvuru detayı (mülakat, teklif)
POST /api/portal/offer/{id}/accept — Teklifi kabul et
POST /api/portal/offer/{id}/reject — Teklifi reddet
GET  /api/portal/notifications     — Bildirimler
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

import models, schemas
from database import get_db
from auth import get_candidate_from_token, get_current_user

router = APIRouter()


def _get_portal_user(
    token: str = Query(..., description="Portal erişim tokenı"),
    db: Session = Depends(get_db),
) -> models.User:
    return get_candidate_from_token(token, db)


@router.get("/me")
def get_portal_profile(
    db: Session = Depends(get_db),
    portal_user: models.User = Depends(_get_portal_user),
):
    """Aday kendi profil bilgisini görür."""
    candidate = db.query(models.Candidate).filter(
        models.Candidate.user_id == portal_user.id
    ).first()

    return {
        "user": {
            "id": portal_user.id,
            "full_name": portal_user.full_name,
            "email": portal_user.email,
        },
        "candidate": {
            "id": candidate.id if candidate else None,
            "name": candidate.name if candidate else portal_user.full_name,
            "skills": candidate.skills if candidate else [],
            "seniority_level": candidate.seniority_level if candidate else None,
        } if candidate else None,
    }


@router.get("/applications")
def get_portal_applications(
    db: Session = Depends(get_db),
    portal_user: models.User = Depends(_get_portal_user),
):
    """Aday tüm başvurularını görür."""
    candidate = db.query(models.Candidate).filter(
        models.Candidate.user_id == portal_user.id
    ).first()

    if not candidate:
        return []

    applications = db.query(models.Application).options(
        joinedload(models.Application.position),
        joinedload(models.Application.interviews),
        joinedload(models.Application.offer),
    ).filter(
        models.Application.candidate_id == candidate.id
    ).order_by(models.Application.applied_at.desc()).all()

    result = []
    for app in applications:
        # Adaya gösterilen bilgileri filtrele (iç notları gizle)
        interviews_data = []
        for iv in app.interviews:
            interviews_data.append({
                "id": iv.id,
                "interview_type": iv.interview_type.value,
                "status": iv.status.value,
                "round_number": iv.round_number,
                "scheduled_at": iv.scheduled_at.isoformat() if iv.scheduled_at else None,
                "duration_minutes": iv.duration_minutes,
                "meeting_link": iv.meeting_link if iv.status.value == "scheduled" else None,
                "location": iv.location if iv.status.value == "scheduled" else None,
            })

        offer_data = None
        if app.offer and app.offer.status != models.OfferStatus.DRAFT:
            offer_data = {
                "id": app.offer.id,
                "status": app.offer.status.value,
                "proposed_salary": app.offer.proposed_salary,
                "currency": app.offer.currency,
                "start_date": app.offer.start_date.isoformat() if app.offer.start_date else None,
                "benefits": app.offer.benefits,
                "letter_content": app.offer.letter_content,
                "expires_at": app.offer.expires_at.isoformat() if app.offer.expires_at else None,
            }

        result.append({
            "id": app.id,
            "status": app.status.value,
            "applied_at": app.applied_at.isoformat(),
            "position": {
                "id": app.position.id if app.position else None,
                "title": app.position.title if app.position else None,
                "department": app.position.department if app.position else None,
                "location": app.position.location if app.position else None,
            } if app.position else None,
            "status_history": [
                {
                    "status": h.get("status"),
                    "changed_at": h.get("changed_at"),
                    "note": h.get("note"),
                }
                for h in (app.status_history or [])
                if h.get("status") not in ["screening"]  # Bazı iç durumları gizle
            ],
            "interviews": interviews_data,
            "offer": offer_data,
        })

    return result


@router.post("/offer/{offer_id}/accept")
def accept_offer(
    offer_id: int,
    db: Session = Depends(get_db),
    portal_user: models.User = Depends(_get_portal_user),
):
    """Aday teklifi kabul eder."""
    offer = db.query(models.Offer).options(
        joinedload(models.Offer.application).joinedload(models.Application.candidate)
    ).filter(models.Offer.id == offer_id).first()

    if not offer:
        raise HTTPException(status_code=404, detail="Teklif bulunamadı")

    # Teklif bu adaya mı ait?
    candidate = db.query(models.Candidate).filter(
        models.Candidate.user_id == portal_user.id
    ).first()
    if not candidate or offer.application.candidate_id != candidate.id:
        raise HTTPException(status_code=403, detail="Bu teklife erişim yetkiniz yok")

    if offer.status not in [models.OfferStatus.SENT, models.OfferStatus.NEGOTIATING]:
        raise HTTPException(status_code=400, detail="Bu teklif kabul edilebilir durumda değil")

    from datetime import timezone
    from datetime import datetime
    offer.status = models.OfferStatus.ACCEPTED
    offer.responded_at = datetime.now(timezone.utc)
    offer.final_salary = offer.proposed_salary

    if offer.application:
        offer.application.status = models.ApplicationStatus.HIRED
        offer.application.hired_at = datetime.now(timezone.utc)
        history = offer.application.status_history or []
        history.append({
            "status": "hired",
            "changed_at": datetime.now(timezone.utc).isoformat(),
            "changed_by": candidate.name,
            "note": "Aday teklifi kabul etti",
        })
        offer.application.status_history = history

    db.commit()
    return {"message": "Teklif kabul edildi. Sizi ekibimizde görmekten heyecan duyuyoruz!"}


@router.post("/offer/{offer_id}/reject")
def reject_offer(
    offer_id: int,
    reason: str = Query(default=""),
    db: Session = Depends(get_db),
    portal_user: models.User = Depends(_get_portal_user),
):
    """Aday teklifi reddeder."""
    offer = db.query(models.Offer).options(
        joinedload(models.Offer.application).joinedload(models.Application.candidate)
    ).filter(models.Offer.id == offer_id).first()

    if not offer:
        raise HTTPException(status_code=404, detail="Teklif bulunamadı")

    candidate = db.query(models.Candidate).filter(
        models.Candidate.user_id == portal_user.id
    ).first()
    if not candidate or offer.application.candidate_id != candidate.id:
        raise HTTPException(status_code=403, detail="Bu teklife erişim yetkiniz yok")

    from datetime import timezone, datetime
    offer.status = models.OfferStatus.REJECTED
    offer.responded_at = datetime.now(timezone.utc)
    if reason:
        offer.notes = f"{offer.notes or ''}\nRed gerekçesi: {reason}"

    if offer.application:
        offer.application.status = models.ApplicationStatus.OFFER_REJECTED

    db.commit()
    return {"message": "Teklif reddedildi"}


@router.get("/notifications")
def get_notifications(
    db: Session = Depends(get_db),
    portal_user: models.User = Depends(_get_portal_user),
):
    """Aday bildirimlerini görür."""
    notifications = db.query(models.Notification).filter(
        models.Notification.user_id == portal_user.id
    ).order_by(models.Notification.created_at.desc()).limit(20).all()

    # Okunmamışları okundu yap
    for n in notifications:
        if not n.is_read:
            n.is_read = True
    db.commit()

    return [schemas.NotificationOut.model_validate(n) for n in notifications]


# ─── PUBLIC PORTAL ENDPOINTS (Phase 3) ────────────────────────────────────────

from fastapi import UploadFile, File, Form
from datetime import datetime, timezone, timedelta
import os, re, base64
from services import pdf_parser, ai_analyzer
from services.budget_service import check_headcount_budget, trigger_scoped_routing

@router.get("/public/positions")
def get_public_positions(db: Session = Depends(get_db)):
    """Public access to list of active job postings."""
    positions = db.query(models.Position).filter(models.Position.is_active == True).all()
    return [{
        "id": p.id,
        "title": p.title,
        "department": p.department,
        "description": p.description,
        "location": p.location,
        "required_skills": p.required_skills,
        "hotel_id": p.hotel_id
    } for p in positions]


@router.get("/public/positions/{pos_id}")
def get_public_position_details(pos_id: int, db: Session = Depends(get_db)):
    """Public access to specific job posting details."""
    p = db.query(models.Position).filter(models.Position.id == pos_id, models.Position.is_active == True).first()
    if not p:
        raise HTTPException(status_code=404, detail="Pozisyon bulunamadı")
    return {
        "id": p.id,
        "title": p.title,
        "department": p.department,
        "description": p.description,
        "location": p.location,
        "required_skills": p.required_skills,
        "hotel_id": p.hotel_id
    }


@router.get("/job/{pos_id}")
def get_public_position_details_alias(pos_id: int, db: Session = Depends(get_db)):
    return get_public_position_details(pos_id, db)


@router.post("/job/{pos_id}/apply")
async def apply_public_position_alias(
    pos_id: int,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    cover_letter: str = Form(default=""),
    cv_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    utm_source: Optional[str] = Query(None),
    utm_medium: Optional[str] = Query(None),
    utm_campaign: Optional[str] = Query(None),
    utm_content: Optional[str] = Query(None)
):
    return await apply_public_position(
        pos_id=pos_id,
        name=name,
        email=email,
        phone=phone,
        cover_letter=cover_letter,
        cv_file=cv_file,
        db=db,
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        utm_content=utm_content
    )


@router.post("/public/positions/{pos_id}/apply")
async def apply_public_position(
    pos_id: int,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    cover_letter: str = Form(default=""),
    cv_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    utm_source: Optional[str] = Query(None),
    utm_medium: Optional[str] = Query(None),
    utm_campaign: Optional[str] = Query(None),
    utm_content: Optional[str] = Query(None)
):
    """Public candidate apply endpoint for shareable job posting links."""
    position = db.query(models.Position).filter(models.Position.id == pos_id, models.Position.is_active == True).first()
    if not position:
        raise HTTPException(status_code=404, detail="Pozisyon bulunamadı")

    cfg_simul = db.query(models.SystemConfiguration).filter_by(key="simultaneous_applications_allowed").first()
    simultaneous_allowed = cfg_simul.value if cfg_simul else False

    if not simultaneous_allowed:
        active_app = db.query(models.Application).filter(
            models.Application.lock_status == 'LOCKED',
            models.Application.status.notin_(['hired', 'rejected', 'withdrawn'])
        ).join(models.Candidate).filter(
            (models.Candidate.email == email) | (models.Candidate.phone == phone)
        ).first()
        if active_app and active_app.hotel_id != position.hotel_id:
            raise HTTPException(
                status_code=400,
                detail="Bu adayın başka bir otelde kilitli aktif başvurusu bulunmaktadır. Süreç başlatılamaz."
            )

    content = await cv_file.read()
    text = pdf_parser.extract_text_from_pdf(content)
    analysis = {}
    if text and text.strip():
        try:
            analysis = ai_analyzer.analyze_cv(text)
        except Exception:
            pass

    bl = db.query(models.Candidate).filter(
        ((models.Candidate.email == email) & (models.Candidate.is_blacklisted == True)) |
        ((models.Candidate.phone == phone) & (models.Candidate.is_blacklisted == True))
    ).first()
    if bl:
        raise HTTPException(status_code=403, detail=f"Aday kara listededir: {bl.blacklist_reason or 'Sebep belirtilmemiş'}")

    candidate = db.query(models.Candidate).filter(
        (models.Candidate.email == email) | (models.Candidate.phone == phone)
    ).first()

    if not candidate:
        candidate = models.Candidate(
            name=name,
            full_name=name,
            email=email,
            phone=phone,
            position_id=position.id,
            tenant_id=1,
            summary=analysis.get("summary", ""),
            skills=analysis.get("skills", []),
            experience=analysis.get("experience", []),
            education=analysis.get("education", []),
            certifications=analysis.get("certifications", []),
            projects=analysis.get("projects", []),
            seniority_level=analysis.get("seniority_level"),
            seniority_score=analysis.get("seniority_score"),
            strengths=analysis.get("strengths", []),
            areas_for_improvement=analysis.get("areas_for_improvement", [])
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

        try:
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            upload_dir = os.path.join(BASE_DIR, "static", "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', cv_file.filename)
            dest_filename = f"{candidate.id}_{safe_filename}"
            file_path = os.path.join(upload_dir, dest_filename)
            with open(file_path, "wb") as f:
                f.write(content)
            candidate.cv_file_data = base64.b64encode(content).decode('utf-8')
            candidate.cv_file_path = f"/static/uploads/{dest_filename}"
            db.commit()
            db.refresh(candidate)
        except Exception:
            pass

    existing_app = db.query(models.Application).filter_by(candidate_id=candidate.id, position_id=position.id).first()
    if existing_app:
        raise HTTPException(status_code=400, detail="Bu pozisyona daha önce başvuruda bulundunuz.")

    cfg_days = db.query(models.SystemConfiguration).filter_by(key="ownership_duration_days").first()
    days = int(cfg_days.value) if cfg_days else 10

    now_utc = datetime.now(timezone.utc)
    app = models.Application(
        candidate_id=candidate.id,
        position_id=position.id,
        status="applied",
        status_history=[{"status": "applied", "date": now_utc.isoformat(), "note": "Başvuru oluşturuldu"}],
        cover_letter=cover_letter,
        source=utm_source or "Public Link",
        hotel_id=position.hotel_id,
        ownership_started_at=now_utc,
        ownership_expires_at=now_utc + timedelta(days=days),
        lock_status='LOCKED',
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        utm_content=utm_content
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    budget_status = check_headcount_budget(position.hotel_id, position.department_id, position.title, db)
    if budget_status["violates"]:
        audit = models.ImmutableAuditLog(
            user_id=0,
            user_name="SYSTEM",
            action="budget_violation_warning",
            target_type="application",
            target_id=app.id,
            details={
                "message": f"{position.title} pozisyonunda bütçe sınırı ({budget_status['budget']}) aşılmıştır. Mevcut aktif aday sayısı: {budget_status['active_count']}.",
                "hotel_id": position.hotel_id,
                "position_title": position.title
            }
        )
        db.add(audit)
        db.commit()
        trigger_scoped_routing(candidate.id, position.hotel_id, position.title, db)

    return {"message": "Başvurunuz başarıyla alındı.", "application_id": app.id}


@router.get("/public/walk-in/hotel/{hotel_id}")
def get_walkin_hotel_branding(hotel_id: int, db: Session = Depends(get_db)):
    """Fetch branding and department mapping info for walk-in QR application form."""
    hotel = db.query(models.Hotel).filter_by(id=hotel_id, is_active=True).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Otel bulunamadı")
    
    positions = db.query(models.Position).filter(models.Position.hotel_id == hotel_id, models.Position.is_active == True).all()
    titles = list(set([p.title for p in positions]))

    return {
        "hotel_name": hotel.name,
        "branding_settings": hotel.branding_settings or {},
        "active_position_titles": titles
    }


@router.post("/public/walk-in/hotel/{hotel_id}/apply")
async def apply_walkin_qr(
    hotel_id: int,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    position_title: str = Form(...),
    kvkk_consent: bool = Form(...),
    cv_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Submit walk-in application from hotel QR code form."""
    if not kvkk_consent:
        raise HTTPException(status_code=400, detail="KVKK rıza onay metnini kabul etmeniz zorunludur.")

    hotel = db.query(models.Hotel).filter_by(id=hotel_id, is_active=True).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Otel bulunamadı")

    position = db.query(models.Position).filter(
        models.Position.hotel_id == hotel_id,
        func.lower(models.Position.title) == func.lower(position_title),
        models.Position.is_active == True
    ).first()

    if not position:
        position = db.query(models.Position).filter(
            models.Position.hotel_id == hotel_id,
            models.Position.is_active == True
        ).first()
        if not position:
            raise HTTPException(status_code=400, detail="Otelde aktif iş ilanı bulunmuyor.")

    content = await cv_file.read()
    text = pdf_parser.extract_text_from_pdf(content)
    analysis = {}
    if text and text.strip():
        try:
            analysis = ai_analyzer.analyze_cv(text)
        except Exception:
            pass

    bl = db.query(models.Candidate).filter(
        ((models.Candidate.email == email) & (models.Candidate.is_blacklisted == True)) |
        ((models.Candidate.phone == phone) & (models.Candidate.is_blacklisted == True))
    ).first()
    if bl:
        raise HTTPException(status_code=403, detail=f"Aday kara listededir: {bl.blacklist_reason or 'Sebep belirtilmemiş'}")

    candidate = db.query(models.Candidate).filter(
        (models.Candidate.email == email) | (models.Candidate.phone == phone)
    ).first()

    if not candidate:
        candidate = models.Candidate(
            name=name,
            full_name=name,
            email=email,
            phone=phone,
            position_id=position.id,
            tenant_id=1,
            summary=analysis.get("summary", ""),
            skills=analysis.get("skills", []),
            experience=analysis.get("experience", []),
            education=analysis.get("education", []),
            certifications=analysis.get("certifications", []),
            projects=analysis.get("projects", []),
            seniority_level=analysis.get("seniority_level"),
            seniority_score=analysis.get("seniority_score"),
            strengths=analysis.get("strengths", []),
            areas_for_improvement=analysis.get("areas_for_improvement", [])
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

        try:
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            upload_dir = os.path.join(BASE_DIR, "static", "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', cv_file.filename)
            dest_filename = f"{candidate.id}_{safe_filename}"
            file_path = os.path.join(upload_dir, dest_filename)
            with open(file_path, "wb") as f:
                f.write(content)
            candidate.cv_file_data = base64.b64encode(content).decode('utf-8')
            candidate.cv_file_path = f"/static/uploads/{dest_filename}"
            db.commit()
            db.refresh(candidate)
        except Exception:
            pass

    existing_app = db.query(models.Application).filter_by(candidate_id=candidate.id, position_id=position.id).first()
    if existing_app:
        raise HTTPException(status_code=400, detail="Bu pozisyona daha önce başvuruda bulundunuz.")

    cfg_days = db.query(models.SystemConfiguration).filter_by(key="ownership_duration_days").first()
    days = int(cfg_days.value) if cfg_days else 10

    now_utc = datetime.now(timezone.utc)
    app = models.Application(
        candidate_id=candidate.id,
        position_id=position.id,
        status="applied",
        status_history=[{"status": "applied", "date": now_utc.isoformat(), "note": "Başvuru oluşturuldu"}],
        source="QR Walk-In",
        hotel_id=hotel_id,
        ownership_started_at=now_utc,
        ownership_expires_at=now_utc + timedelta(days=days),
        lock_status='LOCKED'
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    budget_status = check_headcount_budget(hotel_id, position.department_id, position_title, db)
    if budget_status["violates"]:
        audit = models.ImmutableAuditLog(
            user_id=0,
            user_name="SYSTEM",
            action="budget_violation_warning",
            target_type="application",
            target_id=app.id,
            details={
                "message": f"{position_title} pozisyonunda bütçe sınırı ({budget_status['budget']}) aşılmıştır. Mevcut aktif aday sayısı: {budget_status['active_count']}.",
                "hotel_id": hotel_id,
                "position_title": position_title
            }
        )
        db.add(audit)
        db.commit()
        trigger_scoped_routing(candidate.id, hotel_id, position_title, db)

    return {"message": "Walk-in başvurunuz başarıyla alındı.", "application_id": app.id}
