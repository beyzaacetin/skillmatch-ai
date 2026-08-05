from fastapi import APIRouter, Depends, HTTPException, Body, Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas, database, auth
import json
from datetime import datetime
from services.gemini_service import call_gemini

# PDF generation imports
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import io

router = APIRouter()
reports_router = APIRouter(prefix="/api/reports", tags=["reports"])

# Font helper for Turkish character rendering in PDF
def get_pdf_font():
    font_path = r"C:\Windows\Fonts\arial.ttf"
    font_bold_path = r"C:\Windows\Fonts\arialbd.ttf"
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont("Arial", font_path))
            if os.path.exists(font_bold_path):
                pdfmetrics.registerFont(TTFont("Arial-Bold", font_bold_path))
            else:
                pdfmetrics.registerFont(TTFont("Arial-Bold", font_path))
            return "Arial", "Arial-Bold"
        except Exception:
            pass
    return "Helvetica", "Helvetica-Bold"


@router.post("/", response_model=schemas.Position)
def create_position(
    position: schemas.PositionCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user_optional)
):
    db_position = models.Position(**position.dict())
    db.add(db_position)
    db.commit()
    db.refresh(db_position)
    from services.audit_service import audit_service
    audit_service.log(db, current_user, "position_created", "position", db_position.id, {"title": db_position.title})
    return db_position


@router.get("/", response_model=List[schemas.Position])
def read_positions(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    q = db.query(models.Position)
    from services.scope_policy_service import scope_policy_service
    q = scope_policy_service.apply_position_scope(q, db, current_user)
    positions = q.offset(skip).limit(limit).all()
    return positions


@router.get("/{position_id}", response_model=schemas.Position)
def read_position(position_id: int, db: Session = Depends(database.get_db)):
    position = db.query(models.Position).filter(models.Position.id == position_id).first()
    if position is None:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.put("/{position_id}", response_model=schemas.Position)
def update_position(
    position_id: int, 
    position_data: schemas.PositionCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user_optional)
):
    position = db.query(models.Position).filter(models.Position.id == position_id).first()
    if position is None:
        raise HTTPException(status_code=404, detail="Position not found")
    
    for key, value in position_data.dict().items():
        setattr(position, key, value)
        
    db.commit()
    db.refresh(position)
    from services.audit_service import audit_service
    audit_service.log(db, current_user, "position_updated", "position", position.id, {"title": position.title})
    return position


@router.delete("/{position_id}", status_code=204)
def delete_position(
    position_id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user_optional)
):
    position = db.query(models.Position).filter(models.Position.id == position_id).first()
    if position is None:
        raise HTTPException(status_code=404, detail="Position not found")
    pos_id = position.id
    pos_title = position.title
    db.delete(position)
    db.commit()
    from services.audit_service import audit_service
    audit_service.log(db, current_user, "position_deleted", "position", pos_id, {"title": pos_title})
    return None


# GET WORKSPACE STATE
@router.get("/{position_id}/workspace")
def get_position_workspace(position_id: int, db: Session = Depends(database.get_db)):
    position = db.query(models.Position).filter(models.Position.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
        
    # Get active applications for this position
    applications = db.query(models.Application).filter(models.Application.position_id == position_id).all()
    
    apps_data = []
    for app in applications:
        cand = db.query(models.Candidate).filter(models.Candidate.id == app.candidate_id, models.Candidate.is_deleted == False).first()
        if not cand:
            continue
        
        # Get matching score details
        match_score = db.query(models.MatchScore).filter(
            models.MatchScore.candidate_id == cand.id,
            models.MatchScore.position_id == position_id
        ).first()
        
        # Get HR and TECHNICAL interview statuses
        hr_iv = db.query(models.Interview).filter(
            models.Interview.application_id == app.id,
            models.Interview.interview_type == "HR"
        ).first()
        tech_iv = db.query(models.Interview).filter(
            models.Interview.application_id == app.id,
            models.Interview.interview_type == "TECHNICAL"
        ).first()
        
        hr_status = hr_iv.status if hr_iv else "not_started"
        tech_status = tech_iv.status if tech_iv else "not_started"
        
        apps_data.append({
            "id": app.id,
            "candidate_id": cand.id,
            "candidate": {
                "id": cand.id,
                "name": cand.name,
                "email": cand.email,
                "phone": cand.phone,
                "summary": cand.summary,
                "skills": cand.skills,
                "experience": cand.experience,
                "education": cand.education,
                "rating": cand.rating,
                "notes": cand.notes,
                "tags": cand.tags,
                "is_blacklisted": cand.is_blacklisted
            },
            "status": app.status,
            "match_score": app.match_score,
            "matching_skills": app.matching_skills,
            "applied_at": app.applied_at,
            "hr_status": hr_status,
            "tech_status": tech_status
        })
        
    # Get general insights
    insights = db.query(models.PositionInsights).filter(models.PositionInsights.position_id == position_id).first()
    
    # Get reports
    reports = db.query(models.PositionReport).filter(models.PositionReport.position_id == position_id).all()
    reports_list = [{"id": r.id, "report_type": r.report_type, "created_at": r.created_at} for r in reports]
    
    # Fetch headcount budget
    budget_entry = db.query(models.WorkforceHeadcountBudget).filter(
        models.WorkforceHeadcountBudget.hotel_id == position.hotel_id,
        models.WorkforceHeadcountBudget.department_id == position.department_id,
        func.lower(models.WorkforceHeadcountBudget.position_title) == func.lower(position.title)
    ).first()
    
    approved_budget = budget_entry.headcount_budget if budget_entry else position.headcount or 1
    
    active_employees = db.query(models.Application).filter(
        models.Application.position_id == position_id,
        models.Application.status == "hired"
    ).count()
    
    confirmed_starters = db.query(models.Application).join(models.Offer, isouter=True).filter(
        models.Application.position_id == position_id,
        models.Application.status == "offer",
        models.Offer.status == "accepted"
    ).count()
    
    interviews_count = db.query(models.Application).filter(
        models.Application.position_id == position_id,
        models.Application.status.in_(["hr_interview", "tech_interview", "manager_interview"])
    ).count()
    
    planned_leavers = 0
    net_open = max(0, approved_budget - active_employees + planned_leavers - confirmed_starters)
    
    # Salary policy
    sal_policy = db.query(models.SalaryPolicy).filter(
        func.lower(models.SalaryPolicy.position_title) == func.lower(position.title)
    ).first()
    salary_band = f"{sal_policy.min_salary // 1000}-{sal_policy.max_salary // 1000}K {sal_policy.currency}" if sal_policy else "Belirtilmemiş"
    
    # Avg offer salary
    avg_salary_query = db.query(models.Offer.final_salary).filter(
        models.Offer.position_id == position_id,
        models.Offer.status == "accepted"
    ).all()
    avg_salary = sum([s[0] for s in avg_salary_query if s[0]]) / len(avg_salary_query) if avg_salary_query else 0.0

    return {
        "position": {
            "id": position.id,
            "title": position.title,
            "department": position.department,
            "description": position.description,
            "required_skills": position.required_skills,
            "preferred_skills": position.preferred_skills,
            "min_experience_years": position.min_experience_years,
            "seniority_level": position.seniority_level,
            "salary_min": position.salary_min,
            "salary_max": position.salary_max,
            "salary_currency": position.salary_currency,
            "is_active": position.is_active,
            "location": position.location,
            "headcount": position.headcount,
            "priority": position.priority,
            "hiring_manager": position.hiring_manager,
            "target_date": position.target_date,
            "created_at": position.created_at
        },
        "applications": apps_data,
        "insights": {
            "id": insights.id,
            "time_to_fill_prediction": insights.time_to_fill_prediction,
            "pipeline_health": insights.pipeline_health,
            "market_competition": insights.market_competition,
            "candidate_pool_quality": insights.candidate_pool_quality,
            "budget_risk": insights.budget_risk,
            "offer_acceptance_prediction": insights.offer_acceptance_prediction,
            "actionable_recommendations": insights.actionable_recommendations,
            "market_avg_salary": insights.market_avg_salary,
            "our_offer": insights.our_offer,
            "market_open_positions": insights.market_open_positions,
            "market_avg_time_to_fill": insights.market_avg_time_to_fill,
            "risks": insights.risks,
            "recruitment_guide": insights.recruitment_guide
        } if insights else None,
        "reports": reports_list,
        "metrics": {
            "approved_budget": approved_budget,
            "active_employees": active_employees,
            "confirmed_starters": confirmed_starters,
            "interviews_count": interviews_count,
            "planned_leavers": planned_leavers,
            "net_open": net_open,
            "salary_band": salary_band,
            "avg_salary": avg_salary
        }
    }


@router.patch("/{position_id}/toggle-active")
def toggle_position_active(
    position_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Toggles active state of a position."""
    position = db.query(models.Position).filter(models.Position.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Pozisyon bulunamadı")
        
    position.is_active = not position.is_active
    if not position.is_active:
        position.closed_at = datetime.utcnow()
    else:
        position.closed_at = None
        
    db.commit()
    
    # Log audit action
    log = models.Log(
        user_id=current_user.id,
        user_name=current_user.full_name,
        action="toggle_position_active",
        target_type="position",
        target_id=position.id,
        details={"title": position.title, "is_active": position.is_active}
    )
    db.add(log)
    db.commit()
    
    return {"status": "success", "is_active": position.is_active, "closed_at": position.closed_at}



# GET CANDIDATES
@router.get("/{position_id}/candidates")
def get_position_candidates(position_id: int, db: Session = Depends(database.get_db)):
    # Get candidates not already applied
    applied_cand_ids = db.query(models.Application.candidate_id).filter(models.Application.position_id == position_id).all()
    applied_ids = [c[0] for c in applied_cand_ids]
    
    candidates = db.query(models.Candidate).filter(
        models.Candidate.is_deleted == False,
        ~models.Candidate.id.in_(applied_ids) if applied_ids else True
    ).all()
    
    return candidates


# POST CANDIDATE (Add existing candidate to position)
@router.post("/{position_id}/candidates")
def add_candidate_to_position(position_id: int, payload: dict = Body(...), db: Session = Depends(database.get_db)):
    candidate_id = payload.get("candidate_id")
    if not candidate_id:
        raise HTTPException(status_code=400, detail="Candidate ID is required")
        
    candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id, models.Candidate.is_deleted == False).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    # Check if application already exists
    exists = db.query(models.Application).filter(
        models.Application.position_id == position_id,
        models.Application.candidate_id == candidate_id
    ).first()
    if exists:
        return exists
        
    app = models.Application(
        candidate_id=candidate_id,
        position_id=position_id,
        status="applied",
        source="Manuel Ekleme"
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


# PATCH APPLICATION STAGE
@router.patch("/applications/{id}/stage")
def update_application_stage(id: int, payload: dict = Body(...), db: Session = Depends(database.get_db)):
    stage = payload.get("stage")
    if not stage:
        raise HTTPException(status_code=400, detail="Stage value is required")
        
    app = db.query(models.Application).filter(models.Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    old_stage = app.status
    app.status = stage
    
    # Save status history
    history = list(app.status_history or [])
    history.append({
        "status": stage,
        "date": datetime.now().isoformat(),
        "note": payload.get("note", "Aşama güncellendi.")
    })
    app.status_history = history
    
    db.commit()
    db.refresh(app)
    return app


# AI MATCHING - RUN MATCHING
@router.post("/{position_id}/matching/run")
def run_ai_matching(position_id: int, db: Session = Depends(database.get_db)):
    position = db.query(models.Position).filter(models.Position.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
        
    # Get active applications for this position
    applications = db.query(models.Application).filter(models.Application.position_id == position_id).all()
    
    for app in applications:
        cand = db.query(models.Candidate).filter(models.Candidate.id == app.candidate_id, models.Candidate.is_deleted == False).first()
        if not cand:
            continue
            
        prompt = f"""
        Analyze the candidate's profile against the position requirements.
        
        Position Title: {position.title}
        Position Description: {position.description}
        Required Skills: {', '.join(position.required_skills or [])}
        Preferred Skills: {', '.join(position.preferred_skills or [])}
        Min Experience Years: {position.min_experience_years}
        Seniority Level: {position.seniority_level or 'Not specified'}
        
        Candidate Name: {cand.name}
        Candidate Summary: {cand.summary or ''}
        Candidate Skills: {', '.join(cand.skills or [])}
        Candidate Experience: {json.dumps(cand.experience or [])}
        Candidate Education: {json.dumps(cand.education or [])}
        
        Evaluate the candidate on 4 dimensions:
        1. Required Skills match: score out of 100
        2. Relevant Experience (quantity and depth): score out of 100
        3. Role/Industry/Domain Fit: score out of 100
        4. Education & Languages & Certifications: score out of 100
        
        Return ONLY a JSON dictionary with the following structure:
        {{
            "required_skill_score": 0-100 float,
            "preferred_skill_score": 0-100 float,
            "experience_score": 0-100 float,
            "seniority_score": 0-100 float,
            "education_score": 0-100 float,
            "language_score": 0-100 float,
            "domain_fit_score": 0-100 float,
            "culture_fit_score": 0-100 float,
            "matching_skills": ["skill1", "skill2"],
            "missing_skills": ["missing1", "missing2"],
            "strengths": ["strength1", "strength2"],
            "risks": ["risk1", "risk2"],
            "summary": "Short explanation of the candidate fit...",
            "recommendation": "Recommendation text..."
        }}
        """
        
        try:
            res_text = call_gemini(db, prompt, json_mode=True)
            res_data = json.loads(res_text)
            
            # Apply formula: 40% required skills, 25% experience, 20% domain fit, 15% education
            req_score = float(res_data.get("required_skill_score", 50))
            exp_score = float(res_data.get("experience_score", 50))
            dom_score = float(res_data.get("domain_fit_score", 50))
            edu_score = float(res_data.get("education_score", 50))
            
            overall = 0.40 * req_score + 0.25 * exp_score + 0.20 * dom_score + 0.15 * edu_score
            overall = round(overall, 1)
            
            # Save or update MatchScore table
            m_score = db.query(models.MatchScore).filter(
                models.MatchScore.candidate_id == cand.id,
                models.MatchScore.position_id == position_id
            ).first()
            
            if not m_score:
                m_score = models.MatchScore(
                    candidate_id=cand.id,
                    position_id=position_id
                )
                db.add(m_score)
                
            m_score.overall_score = overall
            m_score.required_skill_score = req_score
            m_score.preferred_skill_score = float(res_data.get("preferred_skill_score", 50))
            m_score.experience_score = exp_score
            m_score.seniority_score = float(res_data.get("seniority_score", 50))
            m_score.education_score = edu_score
            m_score.language_score = float(res_data.get("language_score", 50))
            m_score.domain_fit_score = dom_score
            m_score.culture_fit_score = float(res_data.get("culture_fit_score", 50))
            m_score.matching_skills = res_data.get("matching_skills", [])
            m_score.missing_skills = res_data.get("missing_skills", [])
            m_score.strengths = res_data.get("strengths", [])
            m_score.risks = res_data.get("risks", [])
            m_score.summary = res_data.get("summary", "")
            m_score.recommendation = res_data.get("recommendation", "")
            
            # Update application match score & matching skills for view listings
            app.match_score = overall
            app.matching_skills = res_data.get("matching_skills", [])
            
            db.commit()
        except Exception as e:
            # Let it proceed to other candidates
            print(f"Failed matching for candidate {cand.id}: {e}")
            
    return {"status": "success"}


@router.get("/{position_id}/matches", response_model=List[schemas.CandidateMatch])
def match_candidates(position_id: int, db: Session = Depends(database.get_db)):
    from services.matcher import matcher_service
    matches = matcher_service.match_candidates(position_id, db)
    return matches


# GET MATCHING RESULTS
@router.get("/{position_id}/matching")
def get_ai_matching(position_id: int, db: Session = Depends(database.get_db)):
    results = db.query(models.MatchScore).filter(models.MatchScore.position_id == position_id).all()
    
    out = []
    for r in results:
        cand = db.query(models.Candidate).filter(models.Candidate.id == r.candidate_id, models.Candidate.is_deleted == False).first()
        if not cand:
            continue
        out.append({
            "candidate_id": cand.id,
            "candidate": {
                "name": cand.name,
                "skills": cand.skills,
                "experience": cand.experience,
                "summary": cand.summary,
                "education": cand.education
            },
            "overall_score": r.overall_score,
            "required_skill_score": r.required_skill_score,
            "experience_score": r.experience_score,
            "domain_fit_score": r.domain_fit_score,
            "education_score": r.education_score,
            "matching_skills": r.matching_skills,
            "missing_skills": r.missing_skills,
            "strengths": r.strengths,
            "risks": r.risks,
            "summary": r.summary,
            "recommendation": r.recommendation
        })
        
    # Sort by overall_score descending
    out.sort(key=lambda x: x["overall_score"] or 0, reverse=True)
    return out


# AI INSIGHTS - GENERATE
@router.post("/{position_id}/ai-insights/generate")
def generate_ai_insights(position_id: int, db: Session = Depends(database.get_db)):
    position = db.query(models.Position).filter(models.Position.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
        
    prompt = f"""
    Analyze the recruitment environment for the following position:
    Title: {position.title}
    Department: {position.department or 'General'}
    Description: {position.description}
    Required Skills: {', '.join(position.required_skills or [])}
    Salary Max: {position.salary_max or 'Not specified'}
    Salary Currency: {position.salary_currency or 'TRY'}
    
    Calculate realistic hiring metrics, risk analysis, and actionable suggestions for a Turkish company recruiting in tech.
    
    Return ONLY a JSON dictionary with the following structure:
    {{
        "time_to_fill_prediction": "12-16 Gün" (example, give a realistic estimate),
        "pipeline_health": 0-100 integer score,
        "market_competition": "Yüksek" | "Orta" | "Düşük",
        "candidate_pool_quality": 0-100 integer score,
        "budget_risk": "Yüksek" | "Orta" | "Düşük",
        "offer_acceptance_prediction": 0-100 integer score,
        "market_avg_salary": "Piyasa ortalama NET maaş aralığı",
        "our_offer": "Bütçe aralığımızı kıyaslayan kısa açıklama",
        "market_open_positions": "Sektördeki açık ilan durumu",
        "market_avg_time_to_fill": "Sektör ortalama doldurma süresi",
        "actionable_recommendations": [
            "Aday havuzunu genişletmek için alternatif ilan siteleri kullanın.",
            "Teknik mülakat süresini kısaltarak aday kaybını azaltın."
        ],
        "risks": [
            {{
                "severity": "Yüksek" | "Orta" | "Düşük",
                "title": "Risk açıklaması..."
            }}
        ],
        "recruitment_guide": [
            "İşe alım rehberi maddesi 1...",
            "İşe alım rehberi maddesi 2..."
        ]
    }}
    """
    
    res_text = call_gemini(db, prompt, json_mode=True)
    res_data = json.loads(res_text)
    
    insights = db.query(models.PositionInsights).filter(models.PositionInsights.position_id == position_id).first()
    if not insights:
        insights = models.PositionInsights(position_id=position_id)
        db.add(insights)
        
    insights.time_to_fill_prediction = res_data.get("time_to_fill_prediction", "14-20 Gün")
    insights.pipeline_health = int(res_data.get("pipeline_health", 80))
    insights.market_competition = res_data.get("market_competition", "Orta")
    insights.candidate_pool_quality = int(res_data.get("candidate_pool_quality", 80))
    insights.budget_risk = res_data.get("budget_risk", "Düşük")
    insights.offer_acceptance_prediction = int(res_data.get("offer_acceptance_prediction", 80))
    insights.actionable_recommendations = res_data.get("actionable_recommendations", [])
    insights.market_avg_salary = res_data.get("market_avg_salary", "Belirtilmedi")
    insights.our_offer = res_data.get("our_offer", "Belirtilmedi")
    insights.market_open_positions = res_data.get("market_open_positions", "Belirtilmedi")
    insights.market_avg_time_to_fill = res_data.get("market_avg_time_to_fill", "Belirtilmedi")
    insights.risks = res_data.get("risks", [])
    insights.recruitment_guide = res_data.get("recruitment_guide", [])
    
    db.commit()
    db.refresh(insights)
    return insights


# GET AI INSIGHTS
@router.get("/{position_id}/ai-insights")
def get_ai_insights(position_id: int, db: Session = Depends(database.get_db)):
    insights = db.query(models.PositionInsights).filter(models.PositionInsights.position_id == position_id).first()
    if not insights:
        raise HTTPException(status_code=404, detail="AI Insights not generated yet")
    return insights


# INTERVIEW QUESTIONS - GENERATE
@router.post("/{position_id}/interview-questions/generate")
def generate_interview_questions(position_id: int, payload: dict = Body(...), db: Session = Depends(database.get_db)):
    application_id = payload.get("application_id")
    if not application_id:
        raise HTTPException(status_code=400, detail="Application ID is required")
        
    interview_type = payload.get("interview_type", "HR").upper()
    if interview_type not in ("HR", "TECHNICAL"):
        interview_type = "HR"
        
    app = db.query(models.Application).filter(models.Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    cand = db.query(models.Candidate).filter(models.Candidate.id == app.candidate_id, models.Candidate.is_deleted == False).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    position = db.query(models.Position).filter(models.Position.id == position_id).first()
    
    # Get previous interview notes if any
    prev_interviews = db.query(models.Interview).filter(models.Interview.application_id == application_id).all()
    prev_notes = "\n".join([iv.notes for iv in prev_interviews if iv.notes])
    
    if interview_type == "TECHNICAL":
        role_description = "expert technical interviewer"
        focus_areas = "Generate structured questions assessing coding, algorithms, system architecture, position qualifications, past experiences, and debugging"
        sections = [
            "Algoritma & Veri Yapıları",
            "Sistem Tasarımı & Ölçeklenebilirlik",
            "Pozisyon Nitelikleri & Teknoloji Yetkinliği",
            "Geçmiş Deneyim & Teknik Kararlar",
            "Problem Çözme & Hata Ayıklama",
            "Ekip Çalışması & Teknik Kapanış"
        ]
    else:
        role_description = "expert HR interviewer"
        focus_areas = "Generate structured questions assessing candidate qualifications, past experience, cultural fit, motivation, and career expectations"
        sections = [
            "Tanışma & Giriş",
            "Pozisyon Nitelikleri & Yetkinlik Uyumu",
            "Geçmiş Deneyim & Başarılar",
            "Kültürel Uyum & İletişim Becerileri",
            "Motivasyon & Beklentiler",
            "Kariyer Hedefleri & Kapanış"
        ]
        
    sections_text = "\n".join([f"{idx}. {sec}" for idx, sec in enumerate(sections, 1)])
        
    prompt = f"""
    You are an {role_description}. {focus_areas} in Turkish.
    
    Position Title: {position.title}
    Required Skills: {', '.join(position.required_skills or [])}
    
    Candidate Name: {cand.name}
    Candidate CV Summary: {cand.summary or ''}
    Candidate Skills: {', '.join(cand.skills or [])}
    Candidate Experience: {json.dumps(cand.experience or [])}
    
    Previous Interview Notes:
    {prev_notes}
    
    Generate exactly 6 interview sections (exactly 1 question per section):
    {sections_text}
    
    Return ONLY a JSON list of dictionaries with this structure:
    [
        {{
            "section": "Section name here",
            "question": "Soru metni...",
            "expected_answer": "İdeal cevap değerlendirme rehberi...",
            "red_flag_warning": "Dikkat edilmesi gereken tehlike işaretleri (Red Flag)..."
        }}
    ]
    """
    
    res_text = call_gemini(db, prompt, json_mode=True)
    questions = json.loads(res_text)
    
    # Delete old questions for this specific application and type
    db.query(models.InterviewAnswer).filter(
        models.InterviewAnswer.application_id == application_id,
        models.InterviewAnswer.interview_type == interview_type
    ).delete()
    
    # Save new questions
    for idx, q in enumerate(questions):
        answer_rec = models.InterviewAnswer(
            application_id=application_id,
            question_index=idx,
            section=q.get("section", "Tanışma"),
            question=q.get("question", ""),
            expected_answer=q.get("expected_answer", ""),
            red_flag_warning=q.get("red_flag_warning", ""),
            is_completed=False,
            interview_type=interview_type
        )
        db.add(answer_rec)
        
    db.commit()
    
    # Return questions
    return db.query(models.InterviewAnswer).filter(
        models.InterviewAnswer.application_id == application_id,
        models.InterviewAnswer.interview_type == interview_type
    ).all()


# GET INTERVIEW ANSWERS
@router.get("/applications/{application_id}/interviews")
def get_interview_answers(application_id: int, db: Session = Depends(database.get_db)):
    answers = db.query(models.InterviewAnswer).filter(models.InterviewAnswer.application_id == application_id).all()
    # Sort by question_index
    answers_sorted = sorted(answers, key=lambda x: x.question_index)
    return answers_sorted


# POST INTERVIEW ANSWER
@router.post("/applications/{application_id}/interview-answers")
def save_interview_answer(application_id: int, payload: dict = Body(...), db: Session = Depends(database.get_db)):
    question_index = payload.get("question_index")
    if question_index is None:
        raise HTTPException(status_code=400, detail="question_index is required")
        
    ans = db.query(models.InterviewAnswer).filter(
        models.InterviewAnswer.application_id == application_id,
        models.InterviewAnswer.question_index == question_index
    ).first()
    
    if not ans:
        # Create a blank record if it doesn't exist
        ans = models.InterviewAnswer(
            application_id=application_id,
            question_index=question_index,
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
    
    # Check if there is an Interview object in interviews table to mirror this summary
    # Retrieve all answers for calculations
    all_ans = db.query(models.InterviewAnswer).filter(models.InterviewAnswer.application_id == application_id).all()
    completed = [a for a in all_ans if a.is_completed and a.score is not None]
    if completed:
        avg_score = sum([a.score for a in completed]) / len(completed)
        
        # Mirror / Save to the general Interview model so candidates page can see it!
        iv = db.query(models.Interview).filter(models.Interview.application_id == application_id).first()
        if not iv:
            iv = models.Interview(
                application_id=application_id,
                interview_type="hr",
                status="completed"
            )
            db.add(iv)
        iv.overall_score = float(avg_score)
        iv.notes = f"Soru-Cevap modülünden otomatik derlenen puan: {avg_score:.1f}\n" + "\n".join([f"- {a.section}: {a.notes}" for a in completed if a.notes])
        db.commit()
        
    return ans


# PUT INTERVIEW ANSWER (Update by ID)
@router.put("/interview-answers/{id}")
def update_interview_answer(id: int, payload: dict = Body(...), db: Session = Depends(database.get_db)):
    ans = db.query(models.InterviewAnswer).filter(models.InterviewAnswer.id == id).first()
    if not ans:
        raise HTTPException(status_code=404, detail="Interview answer record not found")
        
    if "candidate_answer" in payload:
        ans.candidate_answer = payload["candidate_answer"]
    if "score" in payload:
        ans.score = payload["score"]
    if "notes" in payload:
        ans.notes = payload["notes"]
    if "is_completed" in payload:
        ans.is_completed = payload["is_completed"]
        
    db.commit()
    db.refresh(ans)
    return ans


# HIRING DECISION - GET
@router.get("/applications/{application_id}/decision")
def get_hiring_decision(application_id: int, db: Session = Depends(database.get_db)):
    decision = db.query(models.HiringDecision).filter(models.HiringDecision.application_id == application_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Hiring decision not submitted yet")
    return decision


# HIRING DECISION - POST (Save/Update)
@router.post("/applications/{application_id}/decision")
def save_hiring_decision(application_id: int, payload: dict = Body(...), db: Session = Depends(database.get_db)):
    app = db.query(models.Application).filter(models.Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    decision_val = payload.get("decision")  # "hired", "hold", "rejected"
    if not decision_val:
        raise HTTPException(status_code=400, detail="Decision is required")
        
    dec = db.query(models.HiringDecision).filter(models.HiringDecision.application_id == application_id).first()
    if not dec:
        dec = models.HiringDecision(application_id=application_id)
        db.add(dec)
        
    dec.decision = decision_val
    dec.technical_score = payload.get("technical_score")
    dec.interview_score = payload.get("interview_score")
    dec.cultural_score = payload.get("cultural_score")
    dec.hiring_confidence = payload.get("hiring_confidence")
    dec.strengths = payload.get("strengths", [])
    dec.concerns = payload.get("concerns", [])
    dec.recommended_salary = payload.get("recommended_salary")
    dec.performance_bonus = payload.get("performance_bonus")
    dec.start_date = payload.get("start_date")
    dec.work_model = payload.get("work_model")
    
    # Reflect result in application status
    if decision_val == "hired":
        app.status = "hired"
    elif decision_val == "rejected":
        app.status = "rejected"
    elif decision_val == "hold":
        app.status = "screening" # keep in pipeline screening or other custom status
        
    # Also update candidate rating/notes based on mülakat score if present
    cand = db.query(models.Candidate).filter(models.Candidate.id == app.candidate_id).first()
    if cand:
        # Reflect overall score average into rating (1-5 range)
        scores = [s for s in [dec.technical_score, dec.interview_score, dec.cultural_score] if s is not None]
        if scores:
            avg = sum(scores) / len(scores) # out of 10
            cand.rating = round(avg / 2, 1) # scale 1-10 to 1-5
        
        # Add to candidate notes
        note_text = f"[{datetime.now().strftime('%d.%m.%Y')}] İşe Alım Kararı: {decision_val.upper()}."
        if dec.hiring_confidence:
            note_text += f" İşe Alım Güveni: {dec.hiring_confidence}."
        if cand.notes:
            cand.notes = note_text + "\n" + cand.notes
        else:
            cand.notes = note_text
            
    db.commit()
    db.refresh(dec)
    return dec


# REPORT GENERATION - POST
@reports_router.post("/position/{position_id}/generate")
def generate_position_report(position_id: int, payload: dict = Body(...), db: Session = Depends(database.get_db)):
    application_id = payload.get("application_id")
    report_type = payload.get("report_type")
    
    if not application_id or not report_type:
        raise HTTPException(status_code=400, detail="application_id and report_type are required")
        
    app = db.query(models.Application).filter(models.Application.id == application_id).first()
    cand = db.query(models.Candidate).filter(models.Candidate.id == app.candidate_id, models.Candidate.is_deleted == False).first()
    position = db.query(models.Position).filter(models.Position.id == position_id).first()
    
    # Gather mülakat score and decisions if available
    dec = db.query(models.HiringDecision).filter(models.HiringDecision.application_id == application_id).first()
    m_score = db.query(models.MatchScore).filter(models.MatchScore.candidate_id == cand.id, models.MatchScore.position_id == position_id).first()
    
    prompt = f"""
    Create a highly professional assessment report in Turkish.
    Report Type: {report_type}
    
    Position: {position.title} ({position.department or 'Genel'})
    Candidate: {cand.name}
    Match Score: {app.match_score or 'N/A'}%
    
    Candidate Skills: {', '.join(cand.skills or [])}
    Candidate Summary: {cand.summary or ''}
    
    Hiring Decision Data:
    - Technical Score: {dec.technical_score if dec else 'N/A'}/10
    - Interview Score: {dec.interview_score if dec else 'N/A'}/10
    - Cultural Score: {dec.cultural_score if dec else 'N/A'}/10
    - Recommended Salary: {dec.recommended_salary if dec else 'N/A'} TRY
    - Strengths: {', '.join(dec.strengths if dec else [])}
    - Concerns: {', '.join(dec.concerns if dec else [])}
    
    AI Match Score details:
    - Strengths: {', '.join(m_score.strengths if m_score else [])}
    - Risks: {', '.join(m_score.risks if m_score else [])}
    
    Structure the report with section titles, a formal executive summary, detailed analysis, and a final recommendation. Use markdown.
    """
    
    res_text = call_gemini(db, prompt)
    
    rep = models.PositionReport(
        position_id=position_id,
        report_type=report_type,
        report_content=res_text
    )
    db.add(rep)
    db.commit()
    db.refresh(rep)
    return rep


# REPORT GENERATION - GET LIST FOR POSITION
@reports_router.get("/position/{position_id}")
def get_position_reports(position_id: int, db: Session = Depends(database.get_db)):
    reports = db.query(models.PositionReport).filter(models.PositionReport.position_id == position_id).all()
    return reports


# REPORT GENERATION - DOWNLOAD PDF (reportlab with Turkish characters)
@reports_router.get("/{report_id}/download")
def download_pdf_report(report_id: int, db: Session = Depends(database.get_db)):
    rep = db.query(models.PositionReport).filter(models.PositionReport.id == report_id).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Report not found")
        
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    story = []
    
    styles = getSampleStyleSheet()
    font_name, font_bold_name = get_pdf_font()
    
    # Custom styles supporting registered TrueType Turkish Font
    title_style = ParagraphStyle(
        name="ReportTitle",
        parent=styles["Normal"],
        fontName=font_bold_name,
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=20,
        alignment=1 # Center
    )
    
    heading_style = ParagraphStyle(
        name="ReportHeading",
        parent=styles["Normal"],
        fontName=font_bold_name,
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#2563EB"),
        spaceBefore=15,
        spaceAfter=10
    )
    
    body_style = ParagraphStyle(
        name="ReportBody",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#374151"),
        spaceAfter=8
    )
    
    # Title
    story.append(Paragraph(rep.report_type, title_style))
    story.append(Spacer(1, 10))
    
    # Content parsing (Markdown-to-Paragraph basic translation)
    lines = rep.report_content.split("\n")
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            story.append(Spacer(1, 6))
            continue
            
        if line_clean.startswith("#"):
            # Header
            level = len(line_clean) - len(line_clean.lstrip("#"))
            text = line_clean.replace("#", "").strip()
            story.append(Paragraph(text, heading_style))
        elif line_clean.startswith("-") or line_clean.startswith("*"):
            # Bullet point
            text = line_clean[1:].strip()
            bullet_text = f"• {text}"
            story.append(Paragraph(bullet_text, body_style))
        else:
            # Paragraph
            # Strip standard markdown bold / italic symbols safely
            clean_text = line_clean.replace("**", "").replace("*", "").replace("`", "")
            story.append(Paragraph(clean_text, body_style))
            
    doc.build(story)
    pdf_out = buffer.getvalue()
    buffer.close()
    
    filename = f"{rep.report_type.replace(' ', '_')}.pdf"
    
    return Response(
        content=pdf_out,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
