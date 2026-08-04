from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks
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

    from datetime import timedelta
    cfg_simul = db.query(models.SystemConfiguration).filter_by(key="simultaneous_applications_allowed").first()
    simultaneous_allowed = cfg_simul.value if cfg_simul else False

    if not simultaneous_allowed:
        active_app = db.query(models.Application).filter(
            models.Application.candidate_id == data.candidate_id,
            models.Application.lock_status == 'LOCKED',
            models.Application.status.notin_(['hired', 'rejected', 'withdrawn'])
        ).first()
        if active_app and active_app.hotel_id != position.hotel_id:
            raise HTTPException(
                status_code=400, 
                detail="Bu adayın başka bir otelde kilitli aktif başvurusu bulunmaktadır. Eş zamanlı süreç başlatılamaz."
            )

    cfg_days = db.query(models.SystemConfiguration).filter_by(key="ownership_duration_days").first()
    days = int(cfg_days.value) if cfg_days else 10

    now_utc = datetime.now(timezone.utc)
    app = models.Application(
        candidate_id=data.candidate_id, position_id=data.position_id,
        status="applied",
        status_history=[{"status": "applied", "date": now_utc.isoformat(), "note": "Başvuru oluşturuldu"}],
        cover_letter=data.cover_letter, source=data.source,
        match_score=score_val,
        semantic_score=semantic_val,
        keyword_score=keyword_val,
        matching_skills=skills_val,
        hotel_id=position.hotel_id,
        ownership_started_at=now_utc,
        ownership_expires_at=now_utc + timedelta(days=days),
        lock_status='LOCKED'
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
    try:
        from services.ownership_service import check_and_release_expired_ownerships
        check_and_release_expired_ownerships(db)
    except Exception as err:
        logger.error(f"Error auto-releasing expired ownerships: {err}")

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
    try:
        from services.ownership_service import reset_ownership_timer
        reset_ownership_timer(a.id, db, "status_changed")
    except Exception:
        pass
    
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


@router.patch("/{app_id}/stage")
def update_application_stage(app_id: int, payload: dict = Body(...), db: Session = Depends(database.get_db)):
    stage = payload.get("stage")
    if not stage:
        raise HTTPException(status_code=400, detail="Stage value is required")
        
    a = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
        
    old_status = a.status
    _push_history(a, stage, payload.get("note", "Aşama güncellendi."))
    if stage == "hired":
        a.hired_at = datetime.now(timezone.utc)
    db.commit()
    try:
        from services.ownership_service import reset_ownership_timer
        reset_ownership_timer(a.id, db, "status_changed")
    except Exception:
        pass
    return {"status": a.status}


@router.get("/{app_id}/interviews", response_model=List[schemas.InterviewAnswerOut])
def get_interview_answers(app_id: int, type: Optional[str] = "HR", db: Session = Depends(database.get_db)):
    q = db.query(models.InterviewAnswer).filter(models.InterviewAnswer.application_id == app_id)
    if type:
        q = q.filter(models.InterviewAnswer.interview_type == type)
    answers = q.all()
    answers_sorted = sorted(answers, key=lambda x: x.question_index)
    
    if not answers_sorted and type in ("HR", "TECHNICAL"):
        default_qs = []
        if type == "HR":
            default_qs = [
                ("Tanışma & Giriş", "Kısaca kendinizden bahseder misiniz? Özgeçmişinizdeki temel dönüm noktaları nelerdir?"),
                ("Pozisyon Nitelikleri", "Başvurduğunuz pozisyonun gereksinimleri ile kendi becerilerinizi nasıl eşleştiriyorsunuz? Hangi yönlerinizin bu pozisyona değer katacağını düşünüyorsunuz?"),
                ("Geçmiş Deneyimler", "Önceki rollerinizde üstlendiğiniz en önemli sorumluluk neydi? Karşılaştığınız en büyük zorluğu ve nasıl aştığınızı anlatır mısınız?"),
                ("Kültürel Uyum & İletişim", "Çalışma ortamında nasıl bir kültür arıyorsunuz? Ekip içi fikir ayrılıklarında nasıl bir iletişim tarzı benimsersiniz?"),
                ("Motivasyon & Beklentiler", "Bizimle çalışma konusundaki temel motivasyonunuz nedir? Bu rolden profesyonel beklentileriniz nelerdir?"),
                ("Kariyer Hedefleri & Kapanış", "Önümüzdeki 2-3 yıl için kariyer hedefleriniz nelerdir? Son olarak, maaş beklentiniz ve işe başlama (ihbar) süreniz nedir?")
            ]
        else:
            default_qs = [
                ("Algoritma & Veri Yapıları", "Projelerinizde karmaşık veri yapıları kullanmanız gereken bir senaryoyu ve performans etkilerini anlatabilir misiniz?"),
                ("Sistem Tasarımı", "Yüksek trafik altında çalışan, ölçeklenebilir ve yedekli bir web uygulaması mimarisi tasarlarken hangi teknolojileri ve veri tabanı katmanlarını tercih edersiniz?"),
                ("Pozisyon Nitelikleri & Dil Yetkinliği", "Bu pozisyonda kullanılan ana diller/framework'ler konusundaki uzmanlık düzeyinizi ve derinlemesine hakim olduğunuz özellikleri belirtir misiniz?"),
                ("Geçmiş Deneyim & Teknik Kararlar", "Geçmiş bir projenizde verdiğiniz ve projenin gidişatını etkileyen en kritik teknik karar neydi? Sonuçları nasıl yönettiniz?"),
                ("Problem Çözme & Hata Ayıklama", "Üretim (production) ortamında kritik bir çökme veya performans dar boğazı yaşandığında, sorunu izlemek ve çözmek için nasıl bir hata ayıklama ve loglama stratejisi izlersiniz?"),
                ("Teknik Kapanış & Ekip Çalışması", "Teknik ekiplerle kod kalitesini (code review, test otomasyonu vb.) korumak için nasıl bir süreç yürütürsünüz?")
            ]
        
        for idx, (section, q_text) in enumerate(default_qs):
            ans_rec = models.InterviewAnswer(
                application_id=app_id,
                question_index=idx,
                interview_type=type,
                section=section,
                question=q_text,
                is_completed=False
            )
            db.add(ans_rec)
        db.commit()
        
        answers = db.query(models.InterviewAnswer).filter(
            models.InterviewAnswer.application_id == app_id,
            models.InterviewAnswer.interview_type == type
        ).all()
        answers_sorted = sorted(answers, key=lambda x: x.question_index)
        
    return answers_sorted


def generate_completed_interview_ai_analysis(db: Session, app_id: int, iv_type: str):
    # Fetch application
    app = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app:
        return
        
    cand = app.candidate
    pos = app.position
    if not cand or not pos:
        return
        
    # Get all interview answers
    answers = db.query(models.InterviewAnswer).filter(
        models.InterviewAnswer.application_id == app_id,
        models.InterviewAnswer.interview_type == iv_type
    ).all()
    
    if not answers:
        return
        
    # Build prompt to summarize and comment on answers in JSON format
    answers_data = []
    for a in answers:
        answers_data.append({
            "question_index": a.question_index,
            "section": a.section,
            "question": a.question,
            "candidate_answer": a.candidate_answer or "Yanıtlanmadı",
            "score": a.score,
            "notes": a.notes or ""
        })
        
    prompt = f"""
    Sen SkillMatch AI mülakat değerlendirme asistanısın. Aday {cand.name} için yapılan '{iv_type}' mülakatının cevaplarını düzenle ve yorumlar ekle.
    
    Adayın ham mülakat cevapları aşağıdadır:
    {json.dumps(answers_data, ensure_ascii=False, indent=2)}
    
    Adayın cevaplarını daha profesyonel ve düzenli bir Türkçe haline getir. Ayrıca her bir cevap için yapıcı bir AI yorumu (değerlendirme, güçlü yönler veya riskler içeren) ekle.
    Son olarak tüm mülakatın genel bir özetini (overall_summary) çıkar.
    
    Lütfen aşağıdaki JSON şemasında yanıt dön. Başka hiçbir açıklama yazma:
    {{
        "answers": [
            {{
                "question_index": 0,
                "ai_summary": "Temizlenmiş profesyonel cevap özeti ve eklenen yapıcı AI yorumu/analizi..."
            }}
        ],
        "overall_summary": "Tüm mülakatın genel AI özeti..."
    }}
    """
    
    from services.gemini_service import call_gemini
    try:
        res_text = call_gemini(db, prompt, json_mode=True)
        res_data = json.loads(res_text)
        
        # Update answers
        for ans_update in res_data.get("answers", []):
            q_idx = ans_update.get("question_index")
            ai_sum = ans_update.get("ai_summary")
            if q_idx is not None and ai_sum:
                # Find matching answer record
                ans_rec = db.query(models.InterviewAnswer).filter(
                    models.InterviewAnswer.application_id == app_id,
                    models.InterviewAnswer.question_index == q_idx,
                    models.InterviewAnswer.interview_type == iv_type
                ).first()
                if ans_rec:
                    ans_rec.ai_summary = ai_sum
                    
        # Update interview overall summary
        iv = db.query(models.Interview).filter(
            models.Interview.application_id == app_id,
            models.Interview.interview_type == iv_type
        ).first()
        if not iv:
            # try lowercase for compatibility
            iv = db.query(models.Interview).filter(
                models.Interview.application_id == app_id,
                models.Interview.interview_type == iv_type.lower()
            ).first()
        if iv:
            iv.ai_summary = res_data.get("overall_summary", "")
            
        db.commit()
        
        # Now automatically generate the overall report PDF and DB record
        from routers.reports import generate_report
        from unittest.mock import MagicMock
        mock_user = MagicMock()
        mock_user.full_name = "SkillMatch AI"
        
        report_type = "HR" if iv_type == "HR" else "TECHNICAL"
        payload = {
            "application_id": app_id,
            "report_type": report_type
        }
        generate_report(payload, db, current_user=mock_user)
        
    except Exception as e:
        logger.error(f"Failed to generate completion AI analysis/report: {e}")


@router.post("/{app_id}/interview-answers", response_model=schemas.InterviewAnswerOut)
def save_interview_answer(app_id: int, payload: dict = Body(...), db: Session = Depends(database.get_db), background_tasks: BackgroundTasks = BackgroundTasks()):
    question_index = payload.get("question_index")
    if question_index is None:
        raise HTTPException(status_code=400, detail="question_index is required")
        
    iv_type = payload.get("interview_type", "HR")
    
    ans = db.query(models.InterviewAnswer).filter(
        models.InterviewAnswer.application_id == app_id,
        models.InterviewAnswer.question_index == question_index,
        models.InterviewAnswer.interview_type == iv_type
    ).first()
    
    if not ans:
        ans = models.InterviewAnswer(
            application_id=app_id,
            question_index=question_index,
            interview_type=iv_type,
            section=payload.get("section", "Mülakat"),
            question=payload.get("question", ""),
            is_completed=True
        )
        db.add(ans)
        
    ans.candidate_answer = payload.get("candidate_answer", "")
    ans.score = payload.get("score")
    ans.notes = payload.get("notes", "")
    ans.is_completed = True
    
    db.commit()
    db.refresh(ans)
    
    all_ans = db.query(models.InterviewAnswer).filter(
        models.InterviewAnswer.application_id == app_id,
        models.InterviewAnswer.interview_type == iv_type
    ).all()
    completed = [a for a in all_ans if a.is_completed and a.score is not None]
    
    if completed:
        avg_score = sum([a.score for a in completed]) / len(completed)
        
        iv = db.query(models.Interview).filter(
            models.Interview.application_id == app_id,
            models.Interview.interview_type == iv_type
        ).first()
        if not iv:
            # try lowercase for compatibility
            iv = db.query(models.Interview).filter(
                models.Interview.application_id == app_id,
                models.Interview.interview_type == iv_type.lower()
            ).first()
        if not iv:
            iv = models.Interview(
                application_id=app_id,
                interview_type=iv_type,
                status="completed"
            )
            db.add(iv)
        else:
            if len(completed) >= len(all_ans):
                iv.status = "completed"
                background_tasks.add_task(generate_completed_interview_ai_analysis, db, app_id, iv_type)
        
        iv.overall_score = float(avg_score)
        
        # Sync notes to candidate timeline
        app_rec = db.query(models.Application).filter(models.Application.id == app_id).first()
        if app_rec and app_rec.candidate:
            cand = app_rec.candidate
            if ans.notes:
                note_rec = models.CandidateNote(
                    candidate_id=cand.id,
                    application_id=app_id,
                    position_id=app_rec.position_id,
                    note_text=f"[{iv_type} Mülakatı] Soru {question_index+1} Notu: {ans.notes}",
                    created_by="Recruiter"
                )
                db.add(note_rec)
                
                act = models.CandidateActivity(
                    candidate_id=cand.id,
                    application_id=app_id,
                    activity_type="note_added",
                    note=f"[{iv_type} Mülakatı] Soru {question_index+1} Notu: {ans.notes}",
                    created_by="Recruiter"
                )
                db.add(act)
        
        db.commit()
        
    return ans


@router.post("/{app_id}/interviews")
def schedule_or_init_interview(app_id: int, payload: dict = Body(...), db: Session = Depends(database.get_db)):
    iv_type = payload.get("interview_type", "HR")
    round_num = payload.get("round_number", 1)
    
    app = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    # parse date safely
    scheduled_at = None
    if payload.get("scheduled_at"):
        try:
            scheduled_at = datetime.fromisoformat(payload["scheduled_at"].replace("Z", "+00:00"))
        except Exception:
            pass
            
    iv = models.Interview(
        application_id=app_id,
        round_number=round_num,
        interview_type=iv_type,
        status="scheduled",
        scheduled_at=scheduled_at,
        duration_minutes=payload.get("duration_minutes", 60),
        meeting_link=payload.get("meeting_link"),
        interviewer_name=payload.get("interviewer_name", "Recruiter")
    )
    db.add(iv)
    
    # Update application stage to match
    app.status = "interview"
    
    db.commit()
    db.refresh(iv)
    
    # Also create calendar event
    event = models.CalendarEvent(
        title=f"Mülakat: {app.candidate.name if app.candidate else 'Aday'} - {app.position.title if app.position else 'Pozisyon'}",
        description=f"İş Görüşmesi ({iv_type})",
        event_type="interview",
        start_time=iv.scheduled_at or datetime.utcnow(),
        candidate_id=app.candidate_id,
        position_id=app.position_id,
        application_id=app_id,
        interview_id=iv.id
    )
    db.add(event)
    
    # Log activity
    if app.candidate:
        act = models.CandidateActivity(
            candidate_id=app.candidate_id,
            application_id=app_id,
            activity_type="interview_scheduled",
            note=f"[{iv_type} Mülakatı] Planlandı: {round_num}. Tur",
            created_by="Recruiter"
        )
        db.add(act)
        
    db.commit()
    return iv


