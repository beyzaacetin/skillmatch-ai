from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
import json
import models, schemas, database
from services import pdf_parser, ai_analyzer

router = APIRouter()

def _log(db: Session, action: str, target_type: str, target_id: int, details: dict = {}):
    log = models.Log(action=action, target_type=target_type, target_id=target_id, details=details)
    db.add(log)
    db.commit()

@router.post("/upload", response_model=schemas.Candidate)
async def upload_cv(file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    content = await file.read()
    text = pdf_parser.extract_text_from_pdf(content)
    
    if not text or not text.strip():
        # Fallback logic / Error logging
        print(f"[Upload] CV {file.filename} parse failed. Text is empty.")
        raise HTTPException(status_code=400, detail="CV içeriği okunamadı veya dosya boş/sadece resimden oluşuyor.")
        
    analysis = ai_analyzer.analyze_cv(text)
    
    email = analysis.get("email")
    phone = analysis.get("phone")
    
    # Blacklist check
    if email or phone:
        bl = db.query(models.Candidate).filter(
            ((models.Candidate.email == email) & (models.Candidate.is_blacklisted == True)) |
            ((models.Candidate.phone == phone) & (models.Candidate.is_blacklisted == True))
        ).first()
        if bl:
            raise HTTPException(status_code=403, detail=f"Aday kara listededir: {bl.blacklist_reason or 'Sebep belirtilmemiş'}")

    db_candidate = models.Candidate(
        name=analysis.get("name", "Bilinmiyor"),
        original_filename=file.filename,
        upload_status="Completed",
        email=email,
        phone=phone,
        summary=analysis.get("summary"),
        skills=analysis.get("skills", []),
        experience=analysis.get("experience", []),
        education=analysis.get("education", []),
        certifications=analysis.get("certifications", []),
        projects=analysis.get("projects", []),
        seniority_level=analysis.get("seniority_level"),
        seniority_score=analysis.get("seniority_score"),
        strengths=analysis.get("strengths", []),
        areas_for_improvement=analysis.get("areas_for_improvement", []),
    )
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    
    _log(db, "candidate_added", "candidate", db_candidate.id, {"name": db_candidate.name})
    
    return db_candidate

@router.get("/", response_model=List[schemas.Candidate])
def read_candidates(skip: int = 0, limit: int = 200, db: Session = Depends(database.get_db)):
    from sqlalchemy.orm import joinedload
    return db.query(models.Candidate).options(joinedload(models.Candidate.applications).joinedload(models.Application.position)).offset(skip).limit(limit).all()

@router.get("/{candidate_id}", response_model=schemas.Candidate)
def read_candidate(candidate_id: int, db: Session = Depends(database.get_db)):
    from sqlalchemy.orm import joinedload
    c = db.query(models.Candidate).options(joinedload(models.Candidate.applications).joinedload(models.Application.position)).filter(models.Candidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Aday bulunamadı")
    return c

@router.patch("/{candidate_id}/rating")
def update_rating(candidate_id: int, data: schemas.CandidateRatingUpdate, db: Session = Depends(database.get_db)):
    c = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Aday bulunamadı")
    c.rating = max(1, min(5, data.rating))
    db.commit()
    return {"rating": c.rating}

@router.patch("/{candidate_id}/notes")
def update_notes(candidate_id: int, data: schemas.CandidateNotesUpdate, db: Session = Depends(database.get_db)):
    c = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Aday bulunamadı")
    c.notes = data.notes
    db.commit()
    return {"notes": c.notes}

@router.patch("/{candidate_id}/favorite")
def toggle_favorite(candidate_id: int, db: Session = Depends(database.get_db)):
    c = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Aday bulunamadı")
    c.is_favorite = not c.is_favorite
    db.commit()
    return {"is_favorite": c.is_favorite}

@router.patch("/{candidate_id}/blacklist")
def toggle_blacklist(candidate_id: int, reason: str = Body(None, embed=True), db: Session = Depends(database.get_db)):
    c = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not c: raise HTTPException(status_code=404, detail="Aday bulunamadı")
    c.is_blacklisted = not c.is_blacklisted
    c.blacklist_reason = reason if c.is_blacklisted else None
    db.commit()
    return {"is_blacklisted": c.is_blacklisted, "reason": c.blacklist_reason}

@router.delete("/{candidate_id}")
def delete_candidate(candidate_id: int, db: Session = Depends(database.get_db)):
    c = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Aday bulunamadı")
    db.delete(c)
    db.commit()
    return {"ok": True}

@router.post("/compare", response_model=schemas.CandidateComparisonResponse)
def compare_candidates(request: schemas.CandidateComparisonRequest, db: Session = Depends(database.get_db)):
    if len(request.candidate_ids) != 2:
        raise HTTPException(status_code=400, detail="Tam 2 aday ID gerekli")
    c1 = db.query(models.Candidate).filter(models.Candidate.id == request.candidate_ids[0]).first()
    c2 = db.query(models.Candidate).filter(models.Candidate.id == request.candidate_ids[1]).first()
    if not c1 or not c2:
        raise HTTPException(status_code=404, detail="Aday bulunamadı")
    position = None
    if request.position_id:
        pos = db.query(models.Position).filter(models.Position.id == request.position_id).first()
        if pos:
            position = {"title": pos.title, "department": pos.department, "description": pos.description, "required_skills": pos.required_skills}
    def safe(v): return v if isinstance(v, list) else (json.loads(v) if isinstance(v, str) else [])
    cand1 = {"name": c1.name, "summary": c1.summary or "", "skills": safe(c1.skills), "experience": safe(c1.experience)}
    cand2 = {"name": c2.name, "summary": c2.summary or "", "skills": safe(c2.skills), "experience": safe(c2.experience)}
    return ai_analyzer.compare_candidates(cand1, cand2, position)

@router.get("/with-best-position")
def get_candidates_with_best_position(db: Session = Depends(database.get_db)):
    candidates = db.query(models.Candidate).all()
    positions = db.query(models.Position).filter(models.Position.is_active == True).all()
    
    results = []
    from services.llm_matcher import llm_matcher_service
    
    for cand in candidates:
        best_pos = None
        best_score = -1.0
        best_decision = "not_match"
        
        # Check pre-calculated match scores
        match_scores = db.query(models.MatchScore).filter(models.MatchScore.candidate_id == cand.id).all()
        
        if match_scores and positions:
            for ms in match_scores:
                pos = next((p for p in positions if p.id == ms.position_id), None)
                if pos and ms.overall_score > best_score:
                    best_score = ms.overall_score
                    best_pos = pos
                    best_decision = ms.decision
        
        # If not pre-calculated, evaluate
        if best_score == -1.0 and positions:
            for pos in positions:
                try:
                    ms = llm_matcher_service.match_candidate_position(cand.id, pos.id, db)
                    if ms.overall_score > best_score:
                        best_score = ms.overall_score
                        best_pos = pos
                        best_decision = ms.decision
                except Exception:
                    pass
                    
        results.append({
            "id": cand.id,
            "name": cand.name,
            "email": cand.email,
            "phone": cand.phone,
            "skills": cand.skills or [],
            "seniority_level": cand.seniority_level,
            "rating": cand.rating,
            "is_favorite": cand.is_favorite,
            "is_blacklisted": cand.is_blacklisted,
            "best_position": {
                "id": best_pos.id if best_pos else None,
                "title": best_pos.title if best_pos else "Eşleşme Yok",
                "department": best_pos.department if best_pos else None
            } if best_pos else None,
            "best_score": best_score if best_score != -1.0 else 0.0,
            "best_decision": best_decision
        })
        
    return results

@router.get("/{candidate_id}/best-position")
def get_candidate_best_position(candidate_id: int, db: Session = Depends(database.get_db)):
    candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Aday bulunamadı")
        
    positions = db.query(models.Position).filter(models.Position.is_active == True).all()
    if not positions:
        return {"best_position": None, "score": 0, "decision": "not_match"}
        
    from services.llm_matcher import llm_matcher_service
    best_pos = None
    best_score = -1.0
    best_decision = "not_match"
    best_match_details = None
    
    for pos in positions:
        try:
            match_score = llm_matcher_service.match_candidate_position(candidate.id, pos.id, db)
            if match_score.overall_score > best_score:
                best_score = match_score.overall_score
                best_pos = pos
                best_decision = match_score.decision
                best_match_details = {
                    "id": match_score.id,
                    "overall_score": match_score.overall_score,
                    "decision": match_score.decision,
                    "strengths": match_score.strengths,
                    "risks": match_score.risks,
                    "summary": match_score.summary,
                    "recommendation": match_score.recommendation
                }
        except Exception:
            pass
            
    if best_pos:
        return {
            "best_position": {
                "id": best_pos.id,
                "title": best_pos.title,
                "department": best_pos.department
            },
            "score": best_score,
            "decision": best_decision,
            "match_details": best_match_details
        }
    return {"best_position": None, "score": 0, "decision": "not_match"}

