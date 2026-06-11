import google.generativeai as genai
import os
import json
from datetime import datetime
from sqlalchemy.orm import Session
import models
import logging

from config import settings

logger = logging.getLogger(__name__)

API_KEY = settings.GEMINI_API_KEY
if API_KEY:
    genai.configure(api_key=API_KEY)


def extract_and_parse_json(text: str) -> dict:
    cleaned = text.strip()
    
    # 1. Remove markdown code fences if present
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
        
    # 2. Extract first {...} block
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    if start_idx == -1 or end_idx == -1 or start_idx > end_idx:
        raise ValueError(f"No valid JSON object found in text: {text[:200]}")
    
    json_str = cleaned[start_idx:end_idx+1]
    
    # 3. Handle trailing commas before closing braces/brackets
    import re
    json_str_clean = re.sub(r',\s*([\]}])', r'\1', json_str)
    
    # Try parsing
    try:
        return json.loads(json_str_clean)
    except Exception as e:
        # Fallback to original extracted block
        try:
            return json.loads(json_str)
        except Exception:
            raise ValueError(f"JSON parsing failed: {e}. Cleaned string: {json_str_clean}")

def validate_llm_data(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Parsed JSON is not a dictionary")
        
    # Check overall_score
    if "overall_score" not in data:
        raise ValueError("Missing overall_score in LLM response")
    try:
        data["overall_score"] = float(data["overall_score"])
    except (ValueError, TypeError):
        raise ValueError("overall_score is not a valid number")
        
    # Ensure other expected keys exist with fallback defaults
    defaults = {
        "decision": "potential_match",
        "required_skill_score": 50.0,
        "preferred_skill_score": 50.0,
        "experience_score": 50.0,
        "seniority_score": 50.0,
        "education_score": 50.0,
        "language_score": 50.0,
        "domain_fit_score": 50.0,
        "culture_fit_score": 50.0,
        "matching_skills": [],
        "missing_skills": [],
        "transferable_skills": [],
        "strengths": [],
        "risks": [],
        "summary": "Analiz tamamlandı.",
        "recommendation": "",
        "interview_focus_areas": [],
        "suggested_questions": []
    }
    
    for key, def_val in defaults.items():
        if key not in data or data[key] is None:
            data[key] = def_val
        else:
            # Cast numeric fields
            if isinstance(def_val, float):
                try:
                    data[key] = float(data[key])
                except (ValueError, TypeError):
                    data[key] = def_val
            # Ensure list fields are list
            elif isinstance(def_val, list):
                if not isinstance(data[key], list):
                    data[key] = [str(data[key])] if data[key] else []
            # Ensure string fields are string
            elif isinstance(def_val, str):
                data[key] = str(data[key])
                
    return data

class LLMMatcherService:
    def calculate_combined_score(self, llm_overall: float, skill_overlap_ratio: float, experience_fit_ratio: float) -> float:
        # Birleşik Skor = %70 LLM overall_score + %20 Skill Overlap + %10 Rule-based experience/seniority
        score = (0.7 * llm_overall) + (0.2 * skill_overlap_ratio * 100) + (0.1 * experience_fit_ratio * 100)
        return round(min(max(score, 0.0), 100.0), 1)

    def get_skill_overlap_ratio(self, candidate_skills, position_required_skills) -> float:
        if not position_required_skills:
            return 1.0
        c_skills = [s.lower().strip() for s in (candidate_skills or [])]
        p_skills = [s.lower().strip() for s in (position_required_skills or [])]
        
        overlap_count = 0
        for ps in p_skills:
            matched = False
            for cs in c_skills:
                # Substring/partial match (e.g. "python" and "python (pandas)")
                if ps in cs or cs in ps:
                    matched = True
                    break
            if matched:
                overlap_count += 1
        return overlap_count / len(p_skills)

    def normalize_seniority(self, sen: str) -> str:
        if not sen:
            return ""
        s = sen.lower().strip()
        if s in ["junior", "entry", "giriş seviyesi", "giriş"]:
            return "junior"
        if s in ["mid", "mid-level", "orta seviye", "orta"]:
            return "mid"
        if s in ["senior", "kıdemli", "uzman"]:
            return "senior"
        return s

    def get_experience_fit_ratio(self, candidate_seniority, position_seniority) -> float:
        if not position_seniority:
            return 1.0
        if not candidate_seniority:
            return 0.5
        c_sen = self.normalize_seniority(candidate_seniority)
        p_sen = self.normalize_seniority(position_seniority)
        if c_sen == p_sen:
            return 1.0
        if p_sen == "junior" and c_sen in ["mid", "senior"]:
            return 0.75
        if p_sen == "mid" and c_sen == "senior":
            return 0.75
        return 0.25

    def match_candidate_position(self, candidate_id: int, position_id: int, db: Session, force_recalculate: bool = False) -> models.MatchScore:
        candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id, models.Candidate.is_deleted == False).first()
        position = db.query(models.Position).filter(models.Position.id == position_id).first()
        
        if not candidate or not position:
            raise ValueError("Candidate or Position not found")

        # Check if MatchScore already exists
        match_score = db.query(models.MatchScore).filter(
            models.MatchScore.candidate_id == candidate_id,
            models.MatchScore.position_id == position_id
        ).first()

        if match_score and match_score.overall_score is not None and not force_recalculate:
            return match_score

        # Calculate rule-based components
        skill_overlap_ratio = self.get_skill_overlap_ratio(candidate.skills, position.required_skills)
        experience_fit_ratio = self.get_experience_fit_ratio(candidate.seniority_level, position.seniority_level)

        llm_data = None
        llm_success = False
        if API_KEY:
            try:
                # Setup prompt
                model = genai.GenerativeModel(settings.GEMINI_MODEL, generation_config={"response_mime_type": "application/json"})
                
                candidate_info = {
                    "name": candidate.name,
                    "summary": candidate.summary,
                    "skills": candidate.skills,
                    "experience": candidate.experience,
                    "education": candidate.education,
                    "seniority_level": candidate.seniority_level,
                    "strengths": candidate.strengths,
                    "areas_for_improvement": candidate.areas_for_improvement
                }
                
                position_info = {
                    "title": position.title,
                    "department": position.department,
                    "description": position.description,
                    "required_skills": position.required_skills,
                    "preferred_skills": position.preferred_skills,
                    "min_experience_years": position.min_experience_years,
                    "seniority_level": position.seniority_level
                }

                prompt = f"""
                Sen kurumsal seviyede bir İK Yapay Zeka Uzmanısın (AI Recruiter).
                Aşağıdaki aday bilgilerini ve pozisyon detaylarını analiz et.
                Adayın bu pozisyona uygunluğunu 0-100 arası puanlayarak detaylı bir eşleştirme analizi yap.
                TÜM YAZILI DEĞERLENDİRMELERİ VE METİNLERİ TÜRKÇE OLARAK DÖN.
 
                ADAY BİLGİLERİ:
                {json.dumps(candidate_info, ensure_ascii=False)}
 
                POZİSYON DETAYLARI:
                {json.dumps(position_info, ensure_ascii=False)}
 
                ANALİZ YÖNERGELERİ:
                1. overall_score: 0-100 arası tam sayı. Adayın pozisyonla genel uyumu.
                2. decision: "strong_match" (güçlü), "potential_match" (olası), "weak_match" (zayıf), veya "not_match" (uygun değil).
                3. required_skill_score: Gerekli yetkinliklerin karşılanma oranı (0-100).
                4. preferred_skill_score: Tercih edilen yetkinliklerin karşılanma oranı (0-100).
                5. experience_score: Deneyim süresi ve kalitesi uyumu (0-100).
                6. seniority_score: Kıdem/seviye uyumu (0-100).
                7. education_score: Eğitim geçmişi uyumu (0-100).
                8. language_score: Yabancı dil bilgisi uyumu (0-100).
                9. domain_fit_score: Sektör/alan bilgisi uyumu (0-100).
                10. culture_fit_score: Kültürel uyum tahmini (0-100).
                11. matching_skills: Eşleşen yetenekler listesi.
                12. missing_skills: Eksik olan kritik yetenekler listesi.
                13. transferable_skills: Farklı alanlardan aktarılabilir yetenekler listesi.
                14. strengths: Adayın güçlü yanları listesi (Türkçe).
                15. risks: Adayın pozisyona yönelik taşıdığı riskler/soru işaretleri listesi (Türkçe).
                16. summary: Değerlendirmenin Türkçe kısa bir özeti.
                17. recommendation: İşe alım yöneticisine yönelik Türkçe tavsiye.
                18. interview_focus_areas: Mülakatta odaklanılması gereken Türkçe konular/alanlar listesi.
                19. suggested_questions: Bu adaya özel mülakatta sorulabilecek 3 adet Türkçe soru.
 
                ÇIKTI ŞABLONU (Strict JSON):
                {{
                  "overall_score": 85,
                  "decision": "strong_match",
                  "required_skill_score": 90,
                  "preferred_skill_score": 70,
                  "experience_score": 80,
                  "seniority_score": 90,
                  "education_score": 85,
                  "language_score": 80,
                  "domain_fit_score": 90,
                  "culture_fit_score": 85,
                  "matching_skills": ["Python", "FastAPI"],
                  "missing_skills": ["AWS"],
                  "transferable_skills": ["Flask'tan FastAPI'ye geçiş"],
                  "strengths": ["Güçlü backend mimari bilgisi", "İletişimi kuvvetli"],
                  "risks": ["Bulut deneyimi kısıtlı"],
                  "summary": "Adayın teknik becerileri pozisyon gereksinimleriyle büyük ölçüde örtüşmektedir...",
                  "recommendation": "Teknik mülakat aşamasına geçirilmesi önerilir...",
                  "interview_focus_areas": ["Bulut teknolojileri", "Ölçeklenebilirlik"],
                  "suggested_questions": ["Daha önce hiç AWS kullandınız mı?", "Büyük veri yüklerini nasıl yönettiniz?"]
                }}
                """
                response = model.generate_content(prompt)
                llm_data = extract_and_parse_json(response.text)
                llm_data = validate_llm_data(llm_data)
                llm_success = True
                logger.info("LLM matching succeeded")
            except Exception as e:
                # Log raw response safely if possible
                raw_text = None
                try:
                    if 'response' in locals() and response is not None:
                        raw_text = response.text
                except Exception:
                    pass
                logger.error(f"LLM failed, rule fallback used. Error: {e}. Raw response: {raw_text}")

        # Fallback if LLM failed or API_KEY is missing
        if not llm_data:
            # We calculate keyword & semantic scores
            keyword_score_100 = skill_overlap_ratio * 100.0
            experience_score_100 = experience_fit_ratio * 100.0
            
            # Semantic calculation (fallback)
            semantic_score_100 = 50.0
            try:
                from services.semantic_matcher import semantic_matcher
                if semantic_matcher.model is not None:
                    exp_text = " ".join([f"{e.get('title','')} {e.get('description','')}" for e in (candidate.experience or [])])
                    cand_text = f"{candidate.name} {candidate.summary} {' '.join(candidate.skills or [])} {exp_text}"
                    pos_text = f"{position.title} {position.description} {' '.join(position.required_skills or [])}"
                    val = semantic_matcher.calculate_semantic_score(cand_text, pos_text)
                    if val > 0:
                        semantic_score_100 = val
                    else:
                        semantic_score_100 = max(50.0, keyword_score_100)
                else:
                    semantic_score_100 = max(50.0, keyword_score_100)
            except Exception as ml_err:
                logger.error(f"Semantic fallback failed: {ml_err}")

            overall_fallback = (0.5 * semantic_score_100) + (0.3 * keyword_score_100) + (0.2 * experience_score_100)
            overall_fallback = min(max(overall_fallback, 0.0), 100.0)

            decision = "potential_match" if overall_fallback >= 60 else "weak_match"
            if overall_fallback >= 80:
                decision = "strong_match"
            elif overall_fallback < 40:
                decision = "not_match"

            c_skills = set(s.lower() for s in (candidate.skills or []))
            p_skills = set(s.lower() for s in (position.required_skills or []))
            
            llm_data = {
                "overall_score": int(overall_fallback),
                "decision": decision,
                "required_skill_score": int(keyword_score_100),
                "preferred_skill_score": 50,
                "experience_score": int(experience_score_100),
                "seniority_score": int(experience_score_100),
                "education_score": 50,
                "language_score": 50,
                "domain_fit_score": 50,
                "culture_fit_score": 50,
                "matching_skills": [s for s in candidate.skills if s.lower() in p_skills],
                "missing_skills": [s for s in position.required_skills if s.lower() not in c_skills],
                "transferable_skills": [],
                "strengths": ["Veritabanından keyword/semantik eşleşme yapıldı (LLM Fallback)"],
                "risks": ["Yapay Zeka API bağlantısı kurulamadı, detaylı risk analizi yapılamadı"],
                "summary": "Gemini API bağlantısı başarısız olduğu için kural tabanlı algoritmalar ile eşleştirme yapılmıştır.",
                "recommendation": "Adayın CV'sini manuel inceleyiniz.",
                "interview_focus_areas": ["Teknik yetkinlikler", "Genel deneyim"],
                "suggested_questions": ["Geçmiş projelerinizdeki teknik zorluklardan bahseder misiniz?"]
            }

        # Calculate final combined score
        if llm_success:
            final_score = float(llm_data.get("overall_score", 0))
        else:
            final_score = self.calculate_combined_score(
                llm_overall=float(llm_data.get("overall_score", 0)),
                skill_overlap_ratio=skill_overlap_ratio,
                experience_fit_ratio=experience_fit_ratio
            )

        if not match_score:
            match_score = models.MatchScore(
                candidate_id=candidate_id,
                position_id=position_id
            )
            db.add(match_score)

        # Update fields
        match_score.overall_score = final_score
        match_score.decision = llm_data.get("decision")
        match_score.required_skill_score = float(llm_data.get("required_skill_score", 0))
        match_score.preferred_skill_score = float(llm_data.get("preferred_skill_score", 0))
        match_score.experience_score = float(llm_data.get("experience_score", 0))
        match_score.seniority_score = float(llm_data.get("seniority_score", 0))
        match_score.education_score = float(llm_data.get("education_score", 0))
        match_score.language_score = float(llm_data.get("language_score", 0))
        match_score.domain_fit_score = float(llm_data.get("domain_fit_score", 0))
        match_score.culture_fit_score = float(llm_data.get("culture_fit_score", 0))
        match_score.matching_skills = llm_data.get("matching_skills", [])
        match_score.missing_skills = llm_data.get("missing_skills", [])
        match_score.transferable_skills = llm_data.get("transferable_skills", [])
        match_score.strengths = llm_data.get("strengths", [])
        match_score.risks = llm_data.get("risks", [])
        match_score.summary = llm_data.get("summary")
        match_score.recommendation = llm_data.get("recommendation")
        match_score.interview_focus_areas = llm_data.get("interview_focus_areas", [])
        match_score.suggested_questions = llm_data.get("suggested_questions", [])
        match_score.llm_model = settings.GEMINI_MODEL if llm_success else "rule-fallback"
        match_score.prompt_version = "v1.0"
        match_score.calculated_at = datetime.utcnow()

        db.commit()
        db.refresh(match_score)

        # Update application match score if exists
        app = db.query(models.Application).filter(
            models.Application.candidate_id == candidate_id,
            models.Application.position_id == position_id
        ).first()
        if app:
            app.match_score = final_score
            app.matching_skills = match_score.matching_skills
            db.commit()

        return match_score

llm_matcher_service = LLMMatcherService()
