from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import json, os
import models, schemas, database
from config import settings

router = APIRouter()

def _get_gemini():
    try:
        import google.generativeai as genai
        key = os.getenv("GEMINI_API_KEY")
        if key: genai.configure(api_key=key)
        return genai.GenerativeModel(settings.GEMINI_MODEL) if key else None
    except: return None

@router.post("/", response_model=schemas.InterviewOut, status_code=201)
def create_interview(data: schemas.InterviewCreate, db: Session = Depends(database.get_db)):
    app = db.query(models.Application).filter(models.Application.id == data.application_id).first()
    if not app: raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
    iv = models.Interview(
        application_id=data.application_id, round_number=data.round_number,
        interview_type=data.interview_type, status="scheduled",
        scheduled_at=data.scheduled_at, duration_minutes=data.duration_minutes,
        location=data.location, meeting_link=data.meeting_link,
        interviewer_name=data.interviewer_name,
    )
    db.add(iv)
    # Update application status
    app.status = "interview"
    h = app.status_history or []
    h.append({"status": "interview", "date": __import__("datetime").datetime.utcnow().isoformat(), "note": f"{data.round_number}. mülakat planlandı"})
    app.status_history = h
    db.commit()
    db.refresh(iv)
    return iv

@router.get("/application/{app_id}", response_model=List[schemas.InterviewOut])
def get_interviews(app_id: int, db: Session = Depends(database.get_db)):
    return db.query(models.Interview).filter(models.Interview.application_id == app_id).order_by(models.Interview.round_number).all()

@router.post("/{iv_id}/feedback", response_model=schemas.InterviewOut)
def save_feedback(iv_id: int, data: schemas.InterviewFeedback, db: Session = Depends(database.get_db)):
    iv = db.query(models.Interview).filter(models.Interview.id == iv_id).first()
    if not iv: raise HTTPException(status_code=404, detail="Mülakat bulunamadı")
    iv.overall_score = data.overall_score
    iv.technical_score = data.technical_score
    iv.cultural_score = data.cultural_score
    iv.notes = data.notes
    iv.strengths_noted = data.strengths_noted
    iv.concerns_noted = data.concerns_noted
    iv.recommendation = data.recommendation
    # New fields
    iv.result = data.result if hasattr(data, "result") else iv.recommendation
    iv.result_note = data.result_note if hasattr(data, "result_note") else None
    
    iv.status = "completed"
    db.commit()
    db.refresh(iv)
    return iv

@router.post("/{iv_id}/generate-questions")
def generate_questions(iv_id: int, db: Session = Depends(database.get_db)):
    """AI ile pozisyon + CV bilgisine göre mülakat soruları üret."""
    iv = db.query(models.Interview).options(
        joinedload(models.Interview.application).joinedload(models.Application.candidate),
        joinedload(models.Interview.application).joinedload(models.Application.position),
    ).filter(models.Interview.id == iv_id).first()
    if not iv: raise HTTPException(status_code=404, detail="Mülakat bulunamadı")
    model = _get_gemini()
    if not model:
        return {"questions": [{"category": "Genel", "question": "Kendinizden bahseder misiniz?", "purpose": "Genel tanışma"},
                               {"category": "Teknik", "question": "En güçlü teknik yetkinliğiniz nedir?", "purpose": "Teknik değerlendirme"},
                               {"category": "Davranışsal", "question": "Zor bir proje sürecinde nasıl ilerlediğinizi anlatır mısınız?", "purpose": "Problem çözme"}]}
    candidate = iv.application.candidate if iv.application else None
    position = iv.application.position if iv.application else None
    skills = ", ".join(candidate.skills or []) if candidate else "Belirtilmemiş"
    exp_count = len(candidate.experience or []) if candidate else 0
    seniority = candidate.seniority_level or "Belirtilmemiş" if candidate else "Belirtilmemiş"
    pos_title = position.title if position else "Genel"
    pos_skills = ", ".join(position.required_skills or []) if position else ""
    iv_type = iv.interview_type
    prompt = f"""
Sen uzman bir İK mülakatçısısın. Aşağıdaki bilgilere göre kapsamlı mülakat soruları hazırla.

POZİSYON: {pos_title}
GEREKLİ YETKİNLİKLER: {pos_skills}
ADAY SEVİYESİ: {seniority} ({exp_count} deneyim kaydı)
ADAY YETKİNLİKLERİ: {skills}
MÜLAKAT TÜRÜ: {iv_type}
MÜLAKAT TURU: {iv.round_number}

10 adet mülakat sorusu üret. Her soru için kategori (Teknik/Davranışsal/Durum/Motivasyon), soru metni ve değerlendirme amacını belirt.

JSON formatında döndür:
{{"questions": [{{"category": "Teknik", "question": "Soru metni...", "purpose": "Değerlendirme amacı..."}}]}}
"""
    try:
        m = __import__("google.generativeai", fromlist=["GenerativeModel"])
        model2 = m.GenerativeModel(settings.GEMINI_MODEL, generation_config={"response_mime_type": "application/json"})
        key = os.getenv("GEMINI_API_KEY")
        if key: m.configure(api_key=key)
        resp = model2.generate_content(prompt)
        result = json.loads(resp.text)
        questions = result.get("questions", [])
    except Exception as e:
        questions = [
            {"category": "Teknik", "question": f"{pos_title} pozisyonundaki en büyük teknik zorluğunuzu nasıl aştınız?", "purpose": "Problem çözme kapasitesi"},
            {"category": "Davranışsal", "question": "Ekip içinde çatışma yaşadığınız bir durumu ve nasıl çözdüğünüzü anlatır mısınız?", "purpose": "İletişim ve liderlik"},
            {"category": "Durum", "question": f"{pos_title} rolünde ilk 90 gününüzde ne yapardınız?", "purpose": "Önceliklendirme ve planlama"},
        ]
    iv.ai_questions = questions
    db.commit()
    return {"questions": questions}

@router.post("/{iv_id}/ai-summary")
def generate_ai_summary(iv_id: int, db: Session = Depends(database.get_db)):
    """Mülakat notlarından AI özeti üret."""
    iv = db.query(models.Interview).filter(models.Interview.id == iv_id).first()
    if not iv: raise HTTPException(status_code=404, detail="Mülakat bulunamadı")
    if not iv.notes: raise HTTPException(status_code=400, detail="Özet için önce mülakat notu girilmeli")
    model = _get_gemini()
    if not model:
        iv.ai_summary = f"Mülakat {iv.round_number}. turda tamamlandı. Genel skor: {iv.overall_score or 'Girilmedi'}/10. Öneri: {iv.recommendation or 'Belirtilmedi'}."
        db.commit()
        return {"summary": iv.ai_summary}
    prompt = f"""
Aşağıdaki mülakat notlarından kısa, profesyonel bir İK değerlendirme özeti yaz (Türkçe, 3-5 cümle):

Mülakat Türü: {iv.interview_type} — Tur {iv.round_number}
Genel Skor: {iv.overall_score or 'Girilmedi'}/10
Teknik Skor: {iv.technical_score or 'Girilmedi'}/10
Kültürel Uyum: {iv.cultural_score or 'Girilmedi'}/10
Güçlü Yönler: {', '.join(iv.strengths_noted or [])}
Endişeler: {', '.join(iv.concerns_noted or [])}
Öneri: {iv.recommendation or 'Belirtilmedi'}
Notlar: {iv.notes}
"""
    try:
        resp = model.generate_content(prompt)
        iv.ai_summary = resp.text.strip()
    except:
        iv.ai_summary = f"Mülakat {iv.round_number}. tur tamamlandı. Skor: {iv.overall_score}/10."
    db.commit()
    return {"summary": iv.ai_summary}

@router.delete("/{iv_id}", status_code=204)
def delete_interview(iv_id: int, db: Session = Depends(database.get_db)):
    iv = db.query(models.Interview).filter(models.Interview.id == iv_id).first()
    if not iv: raise HTTPException(status_code=404, detail="Mülakat bulunamadı")
    db.delete(iv)
    db.commit()

@router.post("/{iv_id}/analyze-notes", response_model=schemas.InterviewOut)
def analyze_notes_endpoint(iv_id: int, data: schemas.InterviewNotesAnalysisRequest, db: Session = Depends(database.get_db)):
    iv = db.query(models.Interview).options(
        joinedload(models.Interview.application).joinedload(models.Application.candidate)
    ).filter(models.Interview.id == iv_id).first()
    if not iv:
        raise HTTPException(status_code=404, detail="Mülakat bulunamadı")
    
    from services.llm_interview_analyzer import llm_interview_analyzer_service
    analysis = llm_interview_analyzer_service.analyze_notes(data.raw_notes)
    
    iv.raw_notes = data.raw_notes
    iv.cleaned_notes = analysis.get("cleaned_notes")
    iv.communication_assessment = analysis.get("communication_assessment")
    iv.culture_fit_assessment = analysis.get("culture_fit_assessment")
    iv.technical_assessment = analysis.get("technical_assessment")
    iv.ai_recommendation = analysis.get("ai_recommendation")
    iv.next_step = analysis.get("next_step")
    
    # Optionally update scores if generated
    if analysis.get("overall_score") is not None:
        iv.overall_score = float(analysis.get("overall_score"))
    if analysis.get("technical_score") is not None:
        iv.technical_score = float(analysis.get("technical_score"))
    if analysis.get("cultural_score") is not None:
        iv.cultural_score = float(analysis.get("cultural_score"))
        
    iv.status = "completed"
    
    # Update Candidate's AI profile summary if application and candidate exist
    if iv.application and iv.application.candidate:
        cand = iv.application.candidate
        summary_addition = f"\nMülakat Değerlendirmesi ({iv.round_number}. Tur - {iv.interview_type}): {iv.cleaned_notes}"
        if cand.ai_profile_summary:
            cand.ai_profile_summary += summary_addition
        else:
            cand.ai_profile_summary = summary_addition
            
    db.commit()
    db.refresh(iv)
    return iv

@router.post("/ai/interview-questions", response_model=schemas.InterviewQuestionsResponse)
def generate_questions_endpoint(data: schemas.InterviewQuestionsRequest, db: Session = Depends(database.get_db)):
    cand = db.query(models.Candidate).filter(models.Candidate.id == data.candidate_id, models.Candidate.is_deleted == False).first()
    pos = db.query(models.Position).filter(models.Position.id == data.position_id).first()
    if not cand or not pos:
        raise HTTPException(status_code=404, detail="Aday veya pozisyon bulunamadı")
        
    from services.llm_interview_analyzer import llm_interview_analyzer_service
    questions = llm_interview_analyzer_service.generate_questions(
        candidate_summary=cand.summary or "",
        candidate_skills=cand.skills or [],
        position_title=pos.title,
        position_desc=pos.description
    )
    return {"questions": questions}

