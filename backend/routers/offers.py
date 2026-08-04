from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone, timedelta
import json, os
import models, schemas, database
import auth
from config import settings
from services.salary_service import validate_offer_salary, create_offer_approval_flow

router = APIRouter()

@router.post("/", response_model=schemas.OfferOut, status_code=201)
def create_offer(data: schemas.OfferCreate, db: Session = Depends(database.get_db)):
    app = db.query(models.Application).options(
        joinedload(models.Application.position)
    ).filter(models.Application.id == data.application_id).first()
    if not app: raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
    existing = db.query(models.Offer).filter(models.Offer.application_id == data.application_id).first()
    if existing: raise HTTPException(status_code=400, detail="Bu başvuru için zaten teklif mevcut")
    
    # Validate proposed salary against SalaryPolicy
    val_res = validate_offer_salary(
        hotel_id=app.hotel_id,
        department_id=app.position.department_id if app.position else None,
        position_title=data.position_title or (app.position.title if app.position else ""),
        proposed_salary=data.proposed_salary,
        db=db
    )
    
    is_valid = val_res["is_valid"]
    approval_status = "APPROVED"
    
    if not is_valid:
        # Requires approval flow
        approval_status = "PENDING_APPROVAL"
        if not data.deviation_reason:
            raise HTTPException(status_code=400, detail="Maaş politikası sınırları dışındaki teklifler için sapma nedeni belirtilmelidir.")

    offer = models.Offer(
        application_id=data.application_id, 
        position_id=app.position_id if app else None,
        candidate_id=app.candidate_id if app else None,
        recruiter_id=1,
        offer_date=datetime.now(timezone.utc).isoformat(),
        offered_salary=float(data.proposed_salary or 0),
        status="draft",
        proposed_salary=data.proposed_salary, 
        currency=data.currency,
        start_date=data.start_date,
        position_title=data.position_title or (app.position.title if app.position else None),
        benefits=data.benefits, 
        notes=data.notes, 
        negotiation_history=[],
        deviation_reason=data.deviation_reason if not is_valid else None,
        deviation_explanation=data.deviation_explanation if not is_valid else None,
        approval_status=approval_status
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    
    # If pending approval, trigger the sequential approvals flow
    if approval_status == "PENDING_APPROVAL":
        create_offer_approval_flow(offer.id, db)
        
    app.status = "offer"
    h = app.status_history or []
    h.append({"status": "offer", "date": datetime.now(timezone.utc).isoformat(), "note": "Teklif oluşturuldu" + (" (Onay Bekliyor)" if approval_status == "PENDING_APPROVAL" else "")})
    app.status_history = h
    db.commit()
    return offer

@router.get("/application/{app_id}", response_model=schemas.OfferOut)
def get_offer(app_id: int, db: Session = Depends(database.get_db)):
    offer = db.query(models.Offer).filter(models.Offer.application_id == app_id).first()
    if not offer: raise HTTPException(status_code=404, detail="Teklif bulunamadı")
    return offer

@router.patch("/{offer_id}/status")
def update_offer_status(offer_id: int, status: str, db: Session = Depends(database.get_db)):
    offer = db.query(models.Offer).options(
        joinedload(models.Offer.application)
    ).filter(models.Offer.id == offer_id).first()
    if not offer: raise HTTPException(status_code=404, detail="Teklif bulunamadı")
    
    # Block submission if approval is pending or rejected
    if status == "sent" and offer.approval_status == "PENDING_APPROVAL":
        raise HTTPException(status_code=400, detail="Teklif henüz onaylanmadı. Gönderilemez.")
    if status == "sent" and offer.approval_status == "REJECTED":
        raise HTTPException(status_code=400, detail="Teklif onay sürecinde reddedildi. Gönderilemez.")
        
    offer.status = status
    offer.responded_at = datetime.now(timezone.utc)
    if status == "accepted":
        offer.final_salary = offer.proposed_salary
        if offer.application:
            offer.application.status = "hired"
            offer.application.hired_at = datetime.now(timezone.utc)
    elif status == "sent":
        offer.sent_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": offer.status}

@router.post("/{offer_id}/generate-letter")
def generate_letter(offer_id: int, db: Session = Depends(database.get_db)):
    """AI ile kişiselleştirilmiş teklif mektubu üret."""
    offer = db.query(models.Offer).options(
        joinedload(models.Offer.application).joinedload(models.Application.candidate),
        joinedload(models.Offer.application).joinedload(models.Application.position),
    ).filter(models.Offer.id == offer_id).first()
    if not offer: raise HTTPException(status_code=404, detail="Teklif bulunamadı")
    candidate = offer.application.candidate if offer.application else None
    position = offer.application.position if offer.application else None
    benefits_str = "\n".join([f"- {b}" for b in (offer.benefits or [])])
    start_str = offer.start_date.strftime("%d %B %Y") if offer.start_date else "Müzakere edilecek"
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        offer.letter_content = f"""Sayın {candidate.name if candidate else 'Aday'},\n\n{offer.position_title or 'Pozisyon'} pozisyonu için işe alım teklifimizi sunmaktan memnuniyet duyarız.\n\nAylık net maaş: {offer.proposed_salary:,} {offer.currency}\nBaşlangıç Tarihi: {start_str}\n\nSaygılarımızla,\nİK Departmanı"""
        db.commit()
        return {"letter": offer.letter_content}
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel(settings.GEMINI_MODEL, generation_config={"response_mime_type": "application/json"})
        prompt = f"""
Profesyonel, sıcak ve kurumsal bir iş teklifi mektubu yaz (Türkçe).

Aday: {candidate.name if candidate else 'Aday'}
Pozisyon: {offer.position_title or (position.title if position else 'Pozisyon')}
Maaş: {offer.proposed_salary:,} {offer.currency} / aylık net
Başlangıç: {start_str}
Yan Haklar: {benefits_str or "Belirtilmemiş"}
Notlar: {offer.notes or ""}

Mektupta: selamlama, pozisyon ve koşullar, maaş+yan haklar, başlangıç tarihi, kabul süresi (7 gün), profesyonel kapanış olsun.

JSON: {{"letter": "mektup metni"}}
"""
        resp = model.generate_content(prompt)
        result = json.loads(resp.text)
        offer.letter_content = result.get("letter", "")
    except Exception as e:
        offer.letter_content = f"Sayın {candidate.name if candidate else 'Aday'},\n\n{offer.position_title or 'Pozisyon'} için teklifimizi sunuyoruz.\n\nMaaş: {offer.proposed_salary:,} {offer.currency}/ay\nBaşlangıç: {start_str}\n\nSaygılarımızla,\nİK Departmanı"
    db.commit()
    return {"letter": offer.letter_content}


@router.get("/approvals/pending")
def get_pending_approvals(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    user_role_code = current_user.role  # SYSTEM_ADMIN, CENTRAL_HR, HOTEL_HR, etc.
    
    query = db.query(models.OfferApprovalRequest).join(models.Offer).join(models.Application).filter(
        models.OfferApprovalRequest.status == "PENDING"
    )
    
    # Scoping data visibility by hotel or department
    if current_user.data_visibility_scope == "HOTEL" and current_user.hotel_access_ids:
        query = query.filter(models.Application.hotel_id.in_(current_user.hotel_access_ids))
    elif current_user.data_visibility_scope == "DEPARTMENT" and current_user.department_access_ids:
        query = query.filter(models.Application.position.has(models.Position.department_id.in_(current_user.department_access_ids)))
        
    # Map roles to requested approval types
    if user_role_code == "HOTEL_HR":
        query = query.filter(models.OfferApprovalRequest.approver_role == "HOTEL_HR")
    elif user_role_code in ["CENTRAL_HR", "SYSTEM_ADMIN", "ADMIN"]:
        query = query.filter(models.OfferApprovalRequest.approver_role == "CENTRAL_HR")
    else:
        return []
        
    return query.options(
        joinedload(models.OfferApprovalRequest.offer).joinedload(models.Offer.application).joinedload(models.Application.candidate)
    ).all()


@router.post("/approvals/{request_id}/resolve")
def resolve_approval(request_id: int, payload: dict = Body(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    req = db.query(models.OfferApprovalRequest).filter_by(id=request_id, status="PENDING").first()
    if not req:
        raise HTTPException(status_code=404, detail="Onay isteği bulunamadı veya zaten çözülmüş")
        
    decision = payload.get("status") # APPROVED or REJECTED
    notes = payload.get("notes", "")
    
    if decision not in ["APPROVED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Geçersiz karar")
        
    req.status = decision
    req.decision_notes = notes
    req.resolved_by_id = current_user.id
    req.resolved_at = datetime.now(timezone.utc)
    
    offer = db.query(models.Offer).filter_by(id=req.offer_id).first()
    
    if decision == "REJECTED":
        offer.approval_status = "REJECTED"
        # Update other WAITING requests for this offer to REJECTED/CANCELLED
        db.query(models.OfferApprovalRequest).filter(
            models.OfferApprovalRequest.offer_id == req.offer_id,
            models.OfferApprovalRequest.id != req.id
        ).update({"status": "REJECTED"})
    else:
        # Find next WAITING request in sequence
        next_req = db.query(models.OfferApprovalRequest).filter(
            models.OfferApprovalRequest.offer_id == req.offer_id,
            models.OfferApprovalRequest.sequence_number > req.sequence_number,
            models.OfferApprovalRequest.status == "WAITING"
        ).order_by(models.OfferApprovalRequest.sequence_number).first()
        
        if next_req:
            next_req.status = "PENDING"
        else:
            offer.approval_status = "APPROVED"
            
    db.commit()
    
    # Audit log entry for approved actions
    from models import ImmutableAuditLog
    audit = ImmutableAuditLog(
        user_id=current_user.id,
        action="RESOLVE_OFFER_APPROVAL",
        details=f"Offer ID: {offer.id}, Decision: {decision}, Notes: {notes}"
    )
    db.add(audit)
    db.commit()
    
    return {"message": "Karar başarıyla kaydedildi"}

