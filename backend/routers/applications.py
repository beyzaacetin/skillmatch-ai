from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, timezone
import json
import logging
import models, schemas, database
import auth
from services.matcher import matcher_service

from services.llm_matcher import llm_matcher_service

logger = logging.getLogger(__name__)
router = APIRouter()

def _push_history(app, status, note=None):
    h = app.status_history or []
    h.append({"status": status, "date": datetime.now(timezone.utc).isoformat(), "note": note})
    app.status_history = h
    app.status = status

@router.post("/", response_model=schemas.ApplicationOut, status_code=201)
def create_application(data: schemas.ApplicationCreate, db: Session = Depends(database.get_db)):
    exists = db.query(models.Application).filter(
        models.Application.candidate_id == data.candidate_id,
        models.Application.position_id == data.position_id
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Bu aday bu pozisyona zaten eklenmiş.")
    candidate = db.query(models.Candidate).filter(models.Candidate.id == data.candidate_id, models.Candidate.is_deleted == False).first()
    position = db.query(models.Position).filter(models.Position.id == data.position_id).first()
    if not candidate or not position:
        raise HTTPException(status_code=404, detail="Aday veya pozisyon bulunamadı")
    
    # Compute AI match score using LLM Matcher Service
    score_val = None
    semantic_val = None
    keyword_val = None
    skills_val = []
    
    try:
        match_score_obj = llm_matcher_service.match_candidate_position(data.candidate_id, data.position_id, db)
        score_val = match_score_obj.overall_score
        semantic_val = match_score_obj.domain_fit_score
        keyword_val = match_score_obj.required_skill_score
        skills_val = match_score_obj.matching_skills or []
    except Exception as match_err:
        logger.error(f"Error calling llm_matcher_service: {match_err}")
        # fallback to old matcher
        try:
            matches = matcher_service.match_candidates(data.position_id, db)
            score_data = next((m for m in matches if m["candidate"].id == data.candidate_id), None)
            if score_data:
                score_val = score_data["score"]
                semantic_val = score_data.get("semantic_score")
                keyword_val = score_data.get("keyword_score")
                skills_val = score_data.get("matching_skills", [])
        except Exception as fallback_err:
            logger.error(f"Fallback matcher failed: {fallback_err}")

    app = models.Application(
        candidate_id=data.candidate_id, position_id=data.position_id,
        status="applied",
        status_history=[{"status": "applied", "date": datetime.now(timezone.utc).isoformat(), "note": "Başvuru oluşturuldu"}],
        cover_letter=data.cover_letter, source=data.source,
        match_score=score_val,
        semantic_score=semantic_val,
        keyword_score=keyword_val,
        matching_skills=skills_val,
    )
    try:
        db.add(app)
        db.commit()
        db.refresh(app)
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating application: {e}")
        raise HTTPException(status_code=500, detail=f"Başvuru oluşturulurken hata oluştu: {str(e)}")
        
    return _load(app.id, db)

@router.get("/", response_model=List[schemas.ApplicationOut])
def list_applications(position_id: Optional[int]=None, status: Optional[str]=None, db: Session = Depends(database.get_db)):
    q = db.query(models.Application).join(models.Candidate).filter(models.Candidate.is_deleted == False).options(joinedload(models.Application.candidate), joinedload(models.Application.position))
    if position_id: q = q.filter(models.Application.position_id == position_id)
    if status: q = q.filter(models.Application.status == status)
    return q.order_by(models.Application.applied_at.desc()).all()

@router.post("/bulk-update")
def bulk_update(data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    app_ids = data.get("application_ids", [])
    action = data.get("action")
    stage = data.get("stage")
    note = data.get("note", "")
    tag = data.get("tag")
    
    if not app_ids:
        raise HTTPException(status_code=400, detail="Hiçbir başvuru seçilmedi.")
        
    apps = db.query(models.Application).filter(models.Application.id.in_(app_ids)).all()
    for app in apps:
        old_val = app.status
        if action == "change_stage" and stage:
            _push_history(app, stage, note)
            activity = models.CandidateActivity(
                candidate_id=app.candidate_id,
                application_id=app.id,
                activity_type="stage_changed",
                old_value=old_val,
                new_value=stage,
                note=note or "Toplu işlem ile aşama güncellendi.",
                created_by=current_user.full_name
            )
            db.add(activity)
            
        elif action == "reject":
            _push_history(app, "rejected", note)
            activity = models.CandidateActivity(
                candidate_id=app.candidate_id,
                application_id=app.id,
                activity_type="rejected",
                old_value=old_val,
                new_value="rejected",
                note=note or "Toplu işlem ile elendi.",
                created_by=current_user.full_name
            )
            db.add(activity)
            
        elif action == "add_tag" and tag:
            candidate = db.query(models.Candidate).filter(models.Candidate.id == app.candidate_id).first()
            if candidate:
                tags = candidate.tags or []
                if tag not in tags:
                    tags.append(tag)
                    candidate.tags = tags
                    activity = models.CandidateActivity(
                        candidate_id=app.candidate_id,
                        application_id=app.id,
                        activity_type="note_added",
                        note=f"Etiket eklendi: {tag}",
                        created_by=current_user.full_name
                    )
                    db.add(activity)
                    
        elif action == "add_note" and note:
            app.hr_notes = (app.hr_notes or "") + f"\n[{datetime.now(timezone.utc).strftime('%d %b %H:%M')} - {current_user.full_name}]: {note}"
            activity = models.CandidateActivity(
                candidate_id=app.candidate_id,
                application_id=app.id,
                activity_type="note_added",
                note=note,
                created_by=current_user.full_name
            )
            db.add(activity)
            
    db.commit()
    return {"message": "Toplu işlem başarıyla tamamlandı.", "updated_count": len(apps)}

@router.get("/pipeline")
def get_pipeline(position_id: Optional[int]=None, db: Session = Depends(database.get_db)):
    q = db.query(models.Application).join(models.Candidate).filter(models.Candidate.is_deleted == False).options(joinedload(models.Application.candidate), joinedload(models.Application.position))
    if position_id: q = q.filter(models.Application.position_id == position_id)
    apps = q.order_by(models.Application.match_score.desc().nullslast()).all()
    stages = ["applied", "screening", "hr_interview", "tech_interview", "manager_interview", "reference_check", "offer", "hired", "rejected", "hold"]
    labels = {
        "applied": "Başvurdu",
        "screening": "Değerlendirme",
        "hr_interview": "İK Mülakatı",
        "tech_interview": "Teknik Mülakat",
        "manager_interview": "Yönetici Mülakatı",
        "reference_check": "Referans Kontrolü",
        "offer": "Teklif",
        "hired": "İşe Alındı",
        "rejected": "Elendi",
        "hold": "Beklemede"
    }
    cols = []
    for s in stages:
        group = [_app_dict(a) for a in apps if a.status == s]
        cols.append({"status": s, "label": labels[s], "count": len(group), "applications": group})
    return {"columns": cols, "total": len(apps)}


def _load(app_id, db):
    return db.query(models.Application).options(
        joinedload(models.Application.candidate), joinedload(models.Application.position)
    ).filter(models.Application.id == app_id).first()

def _app_dict(a):
    c = a.candidate
    p = a.position
    return {
        "id": a.id, "status": a.status, "match_score": a.match_score,
        "semantic_score": a.semantic_score, "keyword_score": a.keyword_score,
        "matching_skills": a.matching_skills or [], "hr_notes": a.hr_notes,
        "applied_at": a.applied_at.isoformat() if a.applied_at else None,
        "source": a.source,
        "candidate": {"id": c.id, "name": c.name, "email": c.email, "seniority_level": c.seniority_level,
                      "skills": c.skills or [], "rating": c.rating, "is_favorite": c.is_favorite,
                      "summary": c.summary, "original_filename": c.original_filename} if c else None,
        "position": {"id": p.id, "title": p.title, "department": p.department} if p else None,
    }

@router.get("/{app_id}", response_model=schemas.ApplicationOut)
def get_application(app_id: int, db: Session = Depends(database.get_db)):
    a = _load(app_id, db)
    if not a or (a.candidate and a.candidate.is_deleted): raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
    return a

@router.patch("/{app_id}/status")
def update_status(app_id: int, data: schemas.ApplicationStatusUpdate, db: Session = Depends(database.get_db)):
    a = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not a: raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
    old_status = a.status
    _push_history(a, data.status, data.note)
    if data.status == "hired": a.hired_at = datetime.now(timezone.utc)
    db.commit()
    
    # Log the transition
    from routers.candidates import _log
    _log(db, "status_changed", "application", a.id, {"from": old_status, "to": a.status, "candidate_id": a.candidate_id})
    
    return {"status": a.status}

@router.put("/{app_id}/notes")
def update_hr_notes(app_id: int, notes: str, db: Session = Depends(database.get_db)):
    a = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not a: raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
    a.hr_notes = notes
    db.commit()
    return {"ok": True}

@router.delete("/{app_id}", status_code=204)
def delete_application(app_id: int, db: Session = Depends(database.get_db)):
    a = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not a: raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
    db.delete(a)
    db.commit()

@router.get("/{app_id}/match-score", response_model=schemas.MatchScoreOut)
def get_application_match_score(app_id: int, db: Session = Depends(database.get_db)):
    app = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
    
    # Check if MatchScore exists
    ms = db.query(models.MatchScore).filter(
        models.MatchScore.candidate_id == app.candidate_id,
        models.MatchScore.position_id == app.position_id
    ).first()
    
    if not ms:
        from services.llm_matcher import llm_matcher_service
        try:
            ms = llm_matcher_service.match_candidate_position(app.candidate_id, app.position_id, db)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Eşleşme skoru hesaplanırken hata oluştu: {str(e)}")
            
    return ms

