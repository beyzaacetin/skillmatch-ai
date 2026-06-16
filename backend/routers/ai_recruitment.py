from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import logging
import models, schemas, database, auth
from config import settings
import google.generativeai as genai
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter()

# Configure Gemini
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

@router.post("/talent-search")
def talent_search(data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    query = data.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Arama sorgusu boş olamaz.")
        
    # 1. Ask Gemini to parse query into structured filters
    model = genai.GenerativeModel(settings.GEMINI_MODEL, generation_config={"response_mime_type": "application/json"})
    prompt = f"""
    Aşağıdaki doğal dildeki aday arama sorgusunu analiz et ve filtre parametrelerini içeren bir JSON nesnesi döndür:
    Sorgu: "{query}"
    
    JSON şeması:
    {{
        "location": "şehir adı veya null",
        "min_experience_years": sayı veya null,
        "skills": ["yetenek1", "yetenek2"],
        "languages": ["dil1", "dil2"],
        "seniority": ["Junior", "Mid", "Senior"],
        "include_rejected": true/false,
        "include_talent_pool": true/false
    }}
    """
    
    filters = {}
    try:
        response = model.generate_content(prompt)
        text_clean = response.text.replace("```json", "").replace("```", "").strip()
        filters = json.loads(text_clean)
    except Exception as e:
        logger.error(f"Failed to parse query via Gemini: {e}")
        # Default fallback filters parsed from keywords
        filters = {
            "location": "İstanbul" if "istanbul" in query.lower() else ("Antalya" if "antalya" in query.lower() else None),
            "skills": [w for w in ["python", "react", "sql", "backend", "developer", "analist"] if w in query.lower()],
            "seniority": ["Senior"] if "senior" in query.lower() or "kıdemli" in query.lower() else (["Junior"] if "junior" in query.lower() else [])
        }

    # 2. Query candidates from database
    q = db.query(models.Candidate).filter(models.Candidate.is_deleted == False)
    candidates = q.all()
    
    # 3. Apply filters in python
    results = []
    for cand in candidates:
        if cand.is_blacklisted:
            continue
            
        # Location matching
        if filters.get("location"):
            loc = filters["location"].lower()
            text_to_search = f"{cand.summary or ''} {repr(cand.experience or '')} {repr(cand.education or '')}".lower()
            if loc not in text_to_search:
                continue
                
        # Skills matching
        matched_skills = []
        if filters.get("skills"):
            req_skills = [s.lower() for s in filters["skills"]]
            cand_skills = [s.lower() for s in (cand.skills or [])]
            matched_skills = [s for s in cand_skills if any(req in s for req in req_skills)]
            if not matched_skills:
                # search in text
                text_to_search = f"{cand.summary or ''} {repr(cand.experience or '')}".lower()
                matched_skills = [req for req in req_skills if req in text_to_search]
                if not matched_skills:
                    continue
                    
        # Seniority matching
        if filters.get("seniority"):
            req_sen = [s.lower() for s in filters["seniority"]]
            cand_sen = (cand.seniority_level or "").lower()
            mapped_sen = []
            for rs in req_sen:
                if "junior" in rs or "giriş" in rs: mapped_sen.append("giriş seviyesi")
                elif "mid" in rs or "orta" in rs: mapped_sen.append("orta seviye")
                elif "senior" in rs or "kıdemli" in rs: mapped_sen.append("kıdemli")
            if mapped_sen and not any(ms in cand_sen for ms in mapped_sen):
                continue
                
        # Calculate matching stats
        score = 75
        reasons = []
        risks = []
        
        if matched_skills:
            score += min(len(matched_skills) * 5, 20)
            reasons.append(f"Anahtar yetkinlikler eşleşiyor: {', '.join(matched_skills[:3])}")
        if filters.get("location"):
            reasons.append(f"Bölge/Lokasyon kriteri uygun ({filters['location']})")
            
        apps = cand.applications
        current_stage = "Aday Havuzu"
        last_activity = "Bilinmiyor"
        if apps:
            current_stage = apps[0].status
            last_activity = apps[0].applied_at.strftime("%d %B %Y") if apps[0].applied_at else "Bilinmiyor"
            
        results.append({
            "candidate_id": cand.id,
            "candidate_name": cand.name,
            "match_score": min(score, 100),
            "current_stage": current_stage,
            "last_activity": last_activity,
            "matched_reasons": reasons,
            "risks": risks or ["Belirgin bir risk bulunamadı."],
            "recommended_action": "Mülakat Daveti Gönder" if score >= 80 else "Aday Profilini İncele"
        })
        
    results.sort(key=lambda x: x["match_score"], reverse=True)
    
    return {
        "query_understanding": f"Aranan Kriterler: Konum: {filters.get('location') or 'Her Yerde'}, Yetkinlikler: {', '.join(filters.get('skills') or []) or 'Hepsi'}",
        "filters_applied": filters,
        "results": results
    }

@router.post("/whatsapp-draft", response_model=schemas.WhatsAppDraftResponse)
def generate_whatsapp_draft(
    req: schemas.WhatsAppDraftRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    user_role_upper = current_user.role.upper() if current_user.role else ""
    if user_role_upper == "VIEWER":
        raise HTTPException(status_code=403, detail="İzleyici (Viewer) rolü aday iletişim özelliklerini kullanamaz.")
        
    candidate = db.query(models.Candidate).filter(
        models.Candidate.id == req.candidate_id,
        models.Candidate.is_deleted == False
    ).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Aday bulunamadı.")
        
    position_title = None
    if req.position_id:
        position = db.query(models.Position).filter(models.Position.id == req.position_id).first()
        if position:
            position_title = position.title

    tone_str = "profesyonel ve kibar"
    if req.tone == "warm":
        tone_str = "samimi, sıcak ve cana yakın"
    elif req.tone == "short":
        tone_str = "oldukça kısa, net ve doğrudan konuya giren"
        
    msg_type_desc = {
        "first_contact": "ilk temas ve tanışma mesajı",
        "interview_invitation": "mülakat davet mesajı",
        "interview_reminder": "mülakat saati/tarihi hatırlatma mesajı",
        "document_request": "belge veya evrak talep mesajı",
        "rejection": "olumsuz dönüş / red mesajı",
        "talent_pool": "aday havuzunda tutulacağını bildiren mesaj",
        "onboarding": "işe başlama / oryantasyon tebrik mesajı"
    }.get(req.message_type, "iletişim mesajı")

    system_instruction = (
        "Sen SkillMatch AI platformunun akıllı işe alım asistanısın. "
        "Görevin, verilen aday ve pozisyon bilgilerine göre Türkçe bir WhatsApp mesajı taslağı oluşturmaktır."
    )

    user_prompt = f"""
    Aşağıdaki bilgilere göre bir WhatsApp mesaj taslağı oluştur:
    Aday Adı: {candidate.name}
    {f"Pozisyon Adı: {position_title}" if position_title else "Pozisyon: Belirtilmemiş"}
    Şirket Adı: SkillMatch AI
    Mesaj Tipi: {msg_type_desc}
    Mesaj Tonu: {tone_str}
    
    WhatsApp Mesaj Kuralları:
    - Dil tamamen Türkçe olmalı.
    - WhatsApp mesajları kısa, doğal ve akıcı olmalıdır. Çok resmi veya uzun e-posta dili kullanılmamalıdır.
    - Emoji çok az ve yerinde kullanılabilir, abartılmamalıdır.
    - Taslakta değişken isimleri yerine direkt yukarıdaki dinamik değerleri kullan.
    """

    message = ""
    try:
        if settings.GEMINI_API_KEY:
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            prompt = f"{system_instruction}\n\n{user_prompt}"
            response = model.generate_content(prompt)
            message = response.text.strip()
        else:
            raise ValueError("No API Key")
    except Exception as e:
        logger.error(f"[AI WhatsApp Draft Fallback] {e}")
        if position_title:
            message = f"Merhaba {candidate.name}, SkillMatch AI olarak başvurmuş olduğunuz {position_title} pozisyonu hakkında görüşmek istiyoruz. Uygun zamanınızı iletebilir misiniz?"
        else:
            message = f"Merhaba {candidate.name}, SkillMatch AI ekibi olarak başvuru sürecinizle ilgili sizinle iletişime geçmek istiyoruz. Uygun zamanınızı iletebilir misiniz?"

    # Log the activity
    try:
        activity = models.CandidateActivity(
            candidate_id=candidate.id,
            activity_type="whatsapp_draft_created",
            note=f"AI WhatsApp Taslağı Oluşturuldu",
            created_by=current_user.full_name,
            metadata_json={"channel": "whatsapp", "message_preview": message[:100]}
        )
        db.add(activity)
        db.commit()
    except Exception as log_err:
        logger.error(f"Failed to log activity: {log_err}")

    return schemas.WhatsAppDraftResponse(message=message)


@router.post("/email-draft", response_model=schemas.EmailDraftResponse)
def generate_email_draft(
    req: schemas.EmailDraftRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    user_role_upper = current_user.role.upper() if current_user.role else ""
    if user_role_upper == "VIEWER":
        raise HTTPException(status_code=403, detail="İzleyici (Viewer) rolü aday iletişim özelliklerini kullanamaz.")
        
    candidate = db.query(models.Candidate).filter(
        models.Candidate.id == req.candidate_id,
        models.Candidate.is_deleted == False
    ).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Aday bulunamadı.")
        
    position_title = None
    if req.position_id:
        position = db.query(models.Position).filter(models.Position.id == req.position_id).first()
        if position:
            position_title = position.title

    tone_str = "profesyonel, kurumsal ve kibar"
    if req.tone == "warm":
        tone_str = "samimi, sıcak ve cana yakın"
    elif req.tone == "formal":
        tone_str = "resmi, saygın ve kurumsal"
        
    email_type_desc = {
        "application_received": "başvurunun alındığına dair bilgilendirme",
        "first_contact": "ilk iletişim ve tanışma e-postası",
        "interview_invitation": "mülakat daveti",
        "interview_reminder": "mülakat saati ve tarihi hatırlatması",
        "technical_test": "teknik değerlendirme testi gönderimi",
        "rejection": "olumsuz dönüş / red bildirimi",
        "offer": "iş teklifi gönderimi",
        "onboarding": "işe alım kabulü ve ilk gün oryantasyon hazırlıkları",
        "document_request": "gerekli evrak ve belgelerin talep edilmesi"
    }.get(req.email_type, "iş başvurusu süreci bilgilendirmesi")

    system_instruction = (
        "Sen SkillMatch AI platformunun profesyonel işe alım asistanısın. "
        "Görevin, aday ve pozisyon bilgilerine göre profesyonel Türkçe bir e-posta konusu (Subject) ve e-posta gövdesi (Body) taslağı oluşturmaktır. "
        "Çıktıyı JSON formatında ver: {\"subject\": \"Konu başlığı buraya\", \"body\": \"E-posta içeriği buraya\"}"
    )

    user_prompt = f"""
    Aşağıdaki bilgilere göre bir e-posta taslağı oluştur:
    Aday Adı: {candidate.name}
    {f"Pozisyon Adı: {position_title}" if position_title else "Pozisyon: Belirtilmemiş"}
    Şirket Adı: SkillMatch AI
    E-posta Tipi: {email_type_desc}
    E-posta Tonu: {tone_str}
    
    E-posta Kuralları:
    - Dil tamamen Türkçe olmalı.
    - E-posta profesyonel, net ve imla kurallarına uygun olmalıdır.
    - Taslakta değişken isimleri yerine yukarıdaki değerleri kullan.
    - Çıktı SADECE geçerli bir JSON objesi olmalıdır: {{"subject": "...", "body": "..."}}
    """

    subject = ""
    body = ""

    try:
        if settings.GEMINI_API_KEY:
            model = genai.GenerativeModel(settings.GEMINI_MODEL, generation_config={"response_mime_type": "application/json"})
            prompt = f"{system_instruction}\n\n{user_prompt}"
            response = model.generate_content(prompt)
            raw_text = response.text.strip()
            
            # Clean markdown JSON block formatting if present
            if raw_text.startswith("```"):
                lines = raw_text.split("\n")
                if lines[0].startswith("```json") or lines[0].startswith("```"):
                    raw_text = "\n".join(lines[1:-1]).strip()
            
            try:
                data = json.loads(raw_text)
                subject = data.get("subject", "").strip()
                body = data.get("body", "").strip()
            except Exception:
                subject = f"{position_title if position_title else 'İş Başvurunuz'} Hakkında"
                body = raw_text
        else:
            raise ValueError("No API Key")
    except Exception as e:
        logger.error(f"[AI Email Draft Fallback] {e}")
        subject = f"{position_title if position_title else 'İş Başvurunuz'} Hakkında"
        body = f"Merhaba {candidate.name},\n\n{position_title if position_title else 'İş'} başvurunuz süreci ile ilgili sizinle iletişime geçmek istiyoruz. Uygun olduğunuzda dönüş yapmanızı rica ederiz.\n\nİyi günler,\nSkillMatch AI Ekibi"

    if not subject:
        subject = f"{position_title if position_title else 'İş Başvurunuz'} Hakkında"
    if not body:
        body = f"Merhaba {candidate.name},\n\nBaşvuru süreciniz hakkında sizinle iletişime geçmek isteriz."

    # Log the activity
    try:
        activity = models.CandidateActivity(
            candidate_id=candidate.id,
            activity_type="email_draft_created",
            note=f"AI E-posta Taslağı Oluşturuldu: {subject}",
            created_by=current_user.full_name,
            metadata_json={"channel": "email", "subject": subject, "message_preview": body[:100]}
        )
        db.add(activity)
        db.commit()
    except Exception as log_err:
        logger.error(f"Failed to log activity: {log_err}")

    return schemas.EmailDraftResponse(subject=subject, body=body)

@router.post("/manager-summary")
def generate_manager_summary(data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    candidate_id = data.get("candidate_id")
    position_id = data.get("position_id")
    
    cand = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    pos = db.query(models.Position).filter(models.Position.id == position_id).first()
    
    if not cand or not pos:
        raise HTTPException(status_code=404, detail="Aday veya pozisyon bulunamadı.")
        
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    prompt = f"""
    Aday '{cand.name}' profilini analiz et ve işe alım yöneticisine (Hiring Manager) sunulacak şekilde Türkçe bir yönetici özeti çıkar.
    Pozisyon: {pos.title}
    Özet Özgeçmiş: {cand.summary or ''}
    Yetenekler: {cand.skills or []}
    
    Lütfen şu başlıklar altında temiz, markdown formatında bir özet oluştur:
    - Genel Değerlendirme
    - Güçlü Yönler
    - Olası Riskler
    - Mülakat Odak Alanları
    - Tavsiye Edilen Karar
    """
    
    try:
        response = model.generate_content(prompt)
        return {"summary": response.text}
    except Exception as e:
        logger.error(f"Failed to generate manager summary: {e}")
        return {"summary": f"### {cand.name} Yönetici Özeti\n\nBu aday {pos.title} pozisyonu için değerlendirilmektedir. Güçlü yetkinlikleri ve iş deneyimi mevcuttur."}

@router.post("/job-description")
def generate_job_description(data: dict, current_user: models.User = Depends(auth.get_current_user)):
    draft_input = data.get("draft")
    if not draft_input:
        raise HTTPException(status_code=400, detail="Taslak içeriği boş olamaz.")
        
    model = genai.GenerativeModel(settings.GEMINI_MODEL, generation_config={"response_mime_type": "application/json"})
    prompt = f"""
    Aşağıdaki kısa taslak metninden yola çıkarak profesyonel, detaylı bir Türkçe iş ilanı (Job Description) metni oluştur:
    Taslak: "{draft_input}"
    
    Yanıtı şu JSON şemasına uygun döndür:
    {{
        "title": "İş İlanı Başlığı",
        "department": "Departman",
        "responsibilities": ["sorumluluk1", "sorumluluk2"],
        "required_skills": ["yetenek1", "yetenek2"],
        "preferred_skills": ["yetenek3"],
        "seniority_level": "Junior/Mid/Senior",
        "salary_range": "30,000 - 50,000 TRY (Temsili)",
        "evaluation_criteria": ["kriter1", "kriter2"]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text_clean = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text_clean)
    except Exception as e:
        logger.error(f"Failed to generate job description: {e}")
        return {
            "title": "Yeni Açık Pozisyon",
            "department": "Teknoloji",
            "responsibilities": ["Yazılım geliştirme süreçlerine katılmak."],
            "required_skills": ["Temel programlama bilgisi"],
            "preferred_skills": [],
            "seniority_level": "Mid",
            "salary_range": "Bilinmiyor",
            "evaluation_criteria": ["Teknik mülakat performansı"]
        }

@router.post("/talent-rediscovery")
def talent_rediscovery(data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    position_id = data.get("position_id")
    pos = db.query(models.Position).filter(models.Position.id == position_id).first()
    if not pos:
        raise HTTPException(status_code=404, detail="Pozisyon bulunamadı.")
        
    # Find candidates who applied to past positions, are rejected, or in talent pool
    candidates = db.query(models.Candidate).filter(models.Candidate.is_deleted == False, models.Candidate.is_blacklisted == False).all()
    
    matched_candidates = []
    req_skills = [s.lower() for s in (pos.required_skills or [])]
    
    for cand in candidates:
        # Check if they already have an active application for this position
        active_app = db.query(models.Application).filter(models.Application.candidate_id == cand.id, models.Application.position_id == pos.id).first()
        if active_app:
            continue
            
        cand_skills = [s.lower() for s in (cand.skills or [])]
        overlap = [s for s in cand_skills if any(req in s for req in req_skills)]
        
        if len(overlap) >= 1 or not req_skills:
            score = 70 + min(len(overlap) * 10, 25)
            matched_candidates.append({
                "candidate_id": cand.id,
                "candidate_name": cand.name,
                "match_score": score,
                "matched_skills": overlap,
                "seniority_level": cand.seniority_level
            })
            
    matched_candidates.sort(key=lambda x: x["match_score"], reverse=True)
    return {"results": matched_candidates[:10], "total_matches": len(matched_candidates)}

@router.post("/copilot")
def recruiter_copilot(data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    message = data.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="Mesaj boş olamaz.")
        
    # Get context from database
    candidates_count = db.query(models.Candidate).filter(models.Candidate.is_deleted == False).count()
    positions_count = db.query(models.Position).filter(models.Position.is_active == True).count()
    apps_count = db.query(models.Application).count()
    
    latest_candidates = db.query(models.Candidate).filter(models.Candidate.is_deleted == False).order_by(models.Candidate.id.desc()).limit(5).all()
    c_list = ", ".join([c.name for c in latest_candidates])
    
    context = f"""
    Sistem İstatistikleri:
    - Toplam Aday: {candidates_count}
    - Aktif Pozisyon: {positions_count}
    - Toplam Başvuru: {apps_count}
    - Son Eklenen Adaylar: {c_list}
    """
    
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    prompt = f"""
    Sen SkillMatch AI için bir Recruiter Copilot (İşe Alım Asistanı) rolündesin.
    Aşağıdaki sistem veritabanı bağlamını kullanarak kullanıcının işe alım sorusunu samimi, yardımcı ve profesyonel bir Türkçe ile yanıtla.
    Asla hayali adaylar veya bilgiler uydurma.
    
    Bağlam:
    {context}
    
    Kullanıcı Sorusu:
    "{message}"
    """
    
    try:
        response = model.generate_content(prompt)
        return {"response": response.text}
    except Exception as e:
        logger.error(f"Copilot error: {e}")
        return {"response": "Şu an bu sorguyu yanıtlayamıyorum, lütfen veritabanı bağlantısını kontrol edin."}
