import google.generativeai as genai
import os
import json
import logging

from config import settings

logger = logging.getLogger(__name__)

API_KEY = settings.GEMINI_API_KEY
if API_KEY:
    genai.configure(api_key=API_KEY)


class LLMInterviewAnalyzerService:
    def generate_questions(self, candidate_summary: str, candidate_skills: list, position_title: str, position_desc: str) -> list:
        if not API_KEY:
            return [
                "Geçmiş projelerinizde karşılaştığınız en büyük teknik zorluk neydi?",
                "Pozisyonun gereksinimlerine göre en güçlü olduğunuz alan hangisidir?",
                "Ekip çalışmasında yaşadığınız bir anlaşmazlığı nasıl çözdünüz?"
            ]
        
        try:
            model = genai.GenerativeModel(settings.GEMINI_MODEL, generation_config={"response_mime_type": "application/json"})
            prompt = f"""
            Sen kurumsal seviyede bir İK Yapay Zeka Uzmanısın.
            Adayın özeti ve yetenekleri ile başvurulan pozisyonun detaylarına göre bu adaya özel 5 adet mülakat sorusu hazırla.
            Sorular hem teknik yetkinlikleri hem de kültürel uyumu sorgulamalıdır.
            TÜM SORULARI TÜRKÇE DİLİNDE HAZIRLA.

            ADAY BİLGİLERİ:
            Özet: {candidate_summary}
            Yetenekler: {candidate_skills}

            POZİSYON BİLGİLERİ:
            Başlık: {position_title}
            Açıklama: {position_desc}

            ÇIKTI FORMATI (Strict JSON):
            {{
                "questions": [
                    "Soru 1...",
                    "Soru 2...",
                    "Soru 3...",
                    "Soru 4...",
                    "Soru 5..."
                ]
            }}
            """
            response = model.generate_content(prompt)
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_text)
            return data.get("questions", [])
        except Exception as e:
            logger.error(f"Error generating interview questions: {e}")
            return [
                "Geçmiş projelerinizde karşılaştığınız en büyük teknik zorluk neydi?",
                "Pozisyonun gereksinimlerine göre en güçlü olduğunuz alan hangisidir?",
                "Ekip çalışmasında yaşadığınız bir anlaşmazlığı nasıl çözdünüz?"
            ]

    def analyze_notes(self, raw_notes: str) -> dict:
        if not API_KEY:
            return {
                "cleaned_notes": "Yapay zeka servisi aktif olmadığı için notlar temizlenemedi.",
                "communication_assessment": "Manuel değerlendirme önerilir.",
                "culture_fit_assessment": "Manuel değerlendirme önerilir.",
                "technical_assessment": "Manuel değerlendirme önerilir.",
                "ai_recommendation": "hold",
                "next_step": "İK İncelemesi",
                "overall_score": 5.0,
                "technical_score": 5.0,
                "cultural_score": 5.0
            }
        
        try:
            model = genai.GenerativeModel(settings.GEMINI_MODEL, generation_config={"response_mime_type": "application/json"})
            prompt = f"""
            Aşağıdaki ham mülakat notlarını analiz et.
            Bu notları temiz, profesyonel ve yapılandırılmış bir özete dönüştür.
            Adayın iletişim yeteneklerini, kültürel uyumunu ve teknik seviyesini değerlendir.
            0-10 arası puanlar üret. Bir sonraki adımı ve tavsiyeyi Türkçe olarak belirle.
            TÜM RAPORU VE METİNLERİ TÜRKÇE OLARAK DÖN.

            HAM MÜLAKAT NOTLARI:
            {raw_notes}

            DEĞERLENDİRME KRİTERLERİ:
            1. overall_score: 1.0 - 10.0 arası float değer.
            2. technical_score: 1.0 - 10.0 arası float değer.
            3. cultural_score: 1.0 - 10.0 arası float değer.
            4. ai_recommendation: "proceed" (olumlu/ilerle), "reject" (elendi), "hold" (beklemede).
            5. cleaned_notes: Notların düzgün Türkçe ile yazılmış özet hali.
            6. communication_assessment: İletişim becerileri analizi.
            7. culture_fit_assessment: Kültür uyumu analizi.
            8. technical_assessment: Teknik beceri ve yeterlilik analizi.
            9. next_step: Bir sonraki aday aşaması (Örn: Teknik Mülakat, Teklif vb.).

            ÇIKTI FORMATI (Strict JSON):
            {{
                "overall_score": 8.5,
                "technical_score": 8.0,
                "cultural_score": 9.0,
                "ai_recommendation": "proceed",
                "cleaned_notes": "Adayın mülakatı oldukça başarılı geçti...",
                "communication_assessment": "Aday kendisini gayet net ifade edebiliyor...",
                "culture_fit_assessment": "Ekip çalışmasına yatkın ve motive görünüyor...",
                "technical_assessment": "İlgili teknolojilerde temel ve orta düzey bilgiye sahip...",
                "next_step": "Teknik Mülakat"
            }}
            """
            response = model.generate_content(prompt)
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except Exception as e:
            logger.error(f"Error analyzing interview notes: {e}")
            return {
                "cleaned_notes": f"Analiz sırasında hata oluştu. Orijinal notlar: {raw_notes}",
                "communication_assessment": "Hata nedeniyle analiz edilemedi.",
                "culture_fit_assessment": "Hata nedeniyle analiz edilemedi.",
                "technical_assessment": "Hata nedeniyle analiz edilemedi.",
                "ai_recommendation": "hold",
                "next_step": "İnceleme Bekleniyor",
                "overall_score": 5.0,
                "technical_score": 5.0,
                "cultural_score": 5.0
            }

llm_interview_analyzer_service = LLMInterviewAnalyzerService()
