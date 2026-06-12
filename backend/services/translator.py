import google.generativeai as genai
import os
import json
import logging
import time
from sqlalchemy.orm import Session
import models
from config import settings

logger = logging.getLogger(__name__)

API_KEY = settings.GEMINI_API_KEY
if API_KEY:
    genai.configure(api_key=API_KEY)

# High-fidelity static translations for the 8 seeded candidates to avoid API quota errors on startup
STATIC_TRANSLATIONS = {
    "Nazlıcan Yılmaz": {
        "summary": "Dijital dönüşüm, süreç iyileştirme ve operasyon yönetimi alanlarında deneyime sahip, şu anda MBA yapan Endüstri Mühendisliği mezunu. Vardiya mühendisliği, savunma ve enerji sektörleri için teknik danışmanlık ve proje liderliği konularında kanıtlanmış başarı geçmişi. Akademik ve profesyonel danışma kurullarının aktif üyesi.",
        "strengths": ["Süreç İyileştirme", "Operasyon Yönetimi", "Proje Liderliği", "Teknik Danışmanlık"],
        "areas_for_improvement": ["Büyük Ekip Yönetimi", "Yazılım Geliştirme Deneyimi"],
        "experience": [
            {"title": "Kıdemli Operasyon Mühendisi", "company": "Aselsan", "years": "2021-Present", "description": "Savunma sanayi projelerinde operasyonel süreçlerin yönetimi ve optimizasyonu."},
            {"title": "Operasyon Mühendisi", "company": "Tüpraş", "years": "2019-2021", "description": "Üretim süreçlerinde dijital dönüşüm ve operasyonel verimlilik çalışmaları."}
        ],
        "education": [
            {"degree": "Endüstri Mühendisliği Lisans", "school": "Bilkent Üniversitesi", "year": "2019"},
            {"degree": "İşletme (MBA) Yüksek Lisans", "school": "Koç Üniversitesi", "year": "Devam Ediyor"}
        ]
    },
    "Şule Sıray": {
        "summary": "Veri analitiği, raporlama ve yapay zeka destekli sistemler konusunda deneyimli Finansal Veri Analisti. Power BI, otomasyon, Python ve veri mühendisliği araçlarında yetkin. Rixos Otelleri genelinde yapay zeka dönüşüm projelerine katkıda bulunmakta ve Veri Bilimi ile Makine Öğrenimi odaklı Elektrik-Elektronik Mühendisliği yüksek lisansı yapmaktadır.",
        "strengths": ["Veri Analitiği", "Power BI", "Python ve Otomasyon", "Makine Öğrenimi"],
        "areas_for_improvement": ["Bulut Mimarisi", "Sunum Becerileri"],
        "experience": [
            {"title": "Yapay Zeka & Veri Analisti", "company": "Rixos Hotels", "years": "2022-Present", "description": "Otel yönetim süreçlerinin yapay zeka ile entegrasyonu ve veri analitiği projeleri."},
            {"title": "Finansal Analist", "company": "Garanti BBVA", "years": "2020-2022", "description": "Finansal verilerin analiz edilmesi ve raporlanması."}
        ],
        "education": [
            {"degree": "Elektrik-Elektronik Mühendisliği Lisans", "school": "Akdeniz Üniversitesi", "year": "2020"},
            {"degree": "Elektrik-Elektronik Mühendisliği Yüksek Lisans (Veri Bilimi)", "school": "Akdeniz Üniversitesi", "year": "Devam Ediyor"}
        ]
    },
    "Erkut Oğuz": {
        "summary": "Düşük seviyeli sistem programlama, C geliştirme ve dijital dönüşüm konularına odaklanmış Bilgisayar Mühendisliği öğrencisi. Sanal makineler, dağıtık veritabanları ve süreç izleme araçları dahil olmak üzere karmaşık sistemleri sıfırdan oluşturma yeteneği. Savunma sanayinde BT desteği ve stratejik süreç optimizasyonu konularında deneyimli.",
        "strengths": ["Sistem Programlama (C/C++)", "Dağıtık Sistemler", "Süreç Optimizasyonu", "Problem Çözme"],
        "areas_for_improvement": ["Frontend Geliştirme", "Müşteri İlişkileri"],
        "experience": [
            {"title": "Sistem Programcı Stajyer", "company": "Havelsan", "years": "2023", "description": "Düşük seviyeli işletim sistemi araçları ve sistem programlama stajı."},
            {"title": "BT Destek Elemanı", "company": "Meteksan Savunma", "years": "2021-2022", "description": "Bilgi teknolojileri altyapı desteği ve süreç iyileştirme çalışmaları."}
        ],
        "education": [
            {"degree": "Bilgisayar Mühendisliği Lisans", "school": "ODTÜ", "year": "Devam Ediyor"}
        ]
    },
    "Büşra Karabaş": {
        "summary": "Gömülü sistemler konusunda uzmanlaşmış, son derece motive Elektrik-Elektronik Mühendisliği mezunu. Gömülü sistem tasarımı, geliştirilmesi ve optimizasyonu konularında güçlü bir temele sahip. Çeşitli iletişim protokolleri ve mikrodenetleyiciler konusunda yetkin.",
        "strengths": ["Gömülü Sistem Tasarımı", "Mikrodenetleyiciler", "Ar-Ge Deneyimi", "İletişim Protokolleri"],
        "areas_for_improvement": ["Yüksek Seviyeli Web Geliştirme", "Proje Yönetimi"],
        "experience": [
            {"title": "Gömülü Sistem Geliştirici", "company": "Arçelik Global", "years": "2022-Present", "description": "Akıllı ev aletleri gömülü yazılımlarının tasarımı ve kodlanması."},
            {"title": "Ar-Ge Mühendis Stajyeri", "company": "Vestel", "years": "2021", "description": "Elektronik kart tasarımları ve donanım doğrulama süreçleri."}
        ],
        "education": [
            {"degree": "Elektrik-Elektronik Mühendisliği Lisans", "school": "Hacettepe Üniversitesi", "year": "2022"}
        ]
    },
    "Elif Arslan": {
        "summary": "Yüksek Onur derecesiyle mezun olmuş Bilgisayar Mühendisliği mezunu ve Junior Veri Bilimci. Makine öğrenimi ve derin öğrenme, özellikle Doğal Dil İşleme (NLP) konularında güçlü akademik ve pratik altyapı. Bitirme projesinde %91.4 doğruluk oranına sahip bir duygu analizi modeli geliştirdi. Python, SQL ve temel makine öğrenimi kütüphanelerinde yetkin; Kaggle yarışmalarında ilk %15'lik dilimde.",
        "strengths": ["Doğal Dil İşleme (NLP)", "Makine Öğrenimi", "Python & SQL", "Analitik Düşünme"],
        "areas_for_improvement": ["Canlı Sistem Dağıtımı (Deployment)", "Büyük Veri Mimarileri"],
        "experience": [
            {"title": "Veri Bilimci (Junior)", "company": "Trendyol Group", "years": "2023-Present", "description": "Doğal dil işleme modelleri ve müşteri yorum analiz projeleri."},
            {"title": "Veri Bilimi Stajyeri", "company": "Insider", "years": "2022", "description": "Kişiselleştirme algoritmaları ve veri analitiği stajı."}
        ],
        "education": [
            {"degree": "Bilgisayar Mühendisliği Lisans (Yüksek Onur)", "school": "İTÜ", "year": "2023"}
        ]
    },
    "Mehmet Demir": {
        "summary": "Turizm ve perakende sektörlerinde 6 yıllık deneyime sahip, stratejik iş ortaklığı, yetenek yönetimi ve organizasyonel gelişim konularında uzmanlaşmış İK profesyoneli. SAP HR, Oracle HCM ve HRMS sistemlerinde ileri düzeyde yetkinlik; işe alım süreçlerinin dijitalleştirilmesi ve çok lokasyonlu büyük ölçekli organizasyonlar için çalışan bağlılığı programları tasarlama konusunda kanıtlanmış başarı geçmişi.",
        "strengths": ["Stratejik İşe Alım", "Yetenek Yönetimi", "İK Teknolojileri (SAP, Oracle)", "Organizasyonel Gelişim"],
        "areas_for_improvement": ["Bütçe Yönetimi", "Veri Modelleme"],
        "experience": [
            {"title": "İK İş Ortağı (HRBP)", "company": "Rixos Hotels", "years": "2021-Present", "description": "Tüm bölge otelleri için yetenek yönetimi ve işe alım süreçleri yönetimi."},
            {"title": "İK Uzmanı", "company": "Migros Ticaret A.Ş.", "years": "2018-2021", "description": "Perakende ekiplerinin işe alım ve performans süreçlerinin takibi."}
        ],
        "education": [
            {"degree": "Çalışma Ekonomisi ve Endüstri İlişkileri Lisans", "school": "Ankara Üniversitesi", "year": "2017"}
        ]
    },
    "Zeynep Kaya": {
        "summary": "Havacılık ve turizm sektörlerinde 4 yıllık deneyime sahip Gelir Yönetimi Uzmanı. IDeaS, STR Raporları ve OTA Insight gibi araçları kullanarak veri odaklı fiyatlandırma stratejileri, kapasite optimizasyonu ve analitik raporlama konusunda uzman. RevPAR büyümesi ve kanal karması optimizasyonunda kanıtlanmış başarı geçmişi.",
        "strengths": ["Gelir Yönetimi", "Fiyatlandırma Stratejileri", "Veri Analizi (OTA Insight, STR)", "Kapasite Optimizasyonu"],
        "areas_for_improvement": ["Bölgesel Pazarlama", "Takım Liderliği"],
        "experience": [
            {"title": "Gelir Yönetimi Şefi", "company": "Pegasus Airlines", "years": "2022-Present", "description": "Uçuş doluluk oranları ve dinamik fiyatlandırma yönetimi."},
            {"title": "Gelir Uzmanı", "company": "Maxx Royal Resorts", "years": "2020-2022", "description": "Otel odaları doluluk ve acente fiyatlandırma süreçleri yönetimi."}
        ],
        "education": [
            {"degree": "Turizm İşletmeciliği Lisans", "school": "Boğaziçi Üniversitesi", "year": "2019"}
        ]
    },
    "Ahmet YIlmaz": {
        "summary": "Ön Büro operasyonları ve misafir memnuniyeti konularında uzmanlaşmış, 5 yılı aşkın uluslararası turizm deneyimine sahip Ön Büro Şefi. Opera PMS, Fidelio ve Protel konularında ileri düzey yetkinlik. 5 yıldızlı tatil köyleri ve şehir otellerinde ekip liderliği, şikayet yönetimi ve gelir optimizasyonunda kanıtlanmış başarı.",
        "strengths": ["Ön Büro Operasyonları", "Opera PMS", "Ekip Liderliği", "Misafir İlişkileri"],
        "areas_for_improvement": ["Satış ve Pazarlama", "Bütçeleme"],
        "experience": [
            {"title": "Ön Büro Şefi (Supervisor)", "company": "Hilton Hotels & Resorts", "years": "2021-Present", "description": "Ön büro ekiplerinin yönetimi ve misafir deneyimi süreçleri."},
            {"title": "Resepsiyonist", "company": "Sheraton Hotels", "years": "2019-2021", "description": "Misafir giriş/çıkış işlemleri ve PMS veritabanı yönetimi."}
        ],
        "education": [
            {"degree": "Otel Yöneticiliği Lisans", "school": "Akdeniz Üniversitesi", "year": "2018"}
        ]
    },
    "Ahmet Yılmaz": {
        "summary": "Ön Büro operasyonları ve misafir memnuniyeti konularında uzmanlaşmış, 5 yılı aşkın uluslararası turizm deneyimine sahip Ön Büro Şefi. Opera PMS, Fidelio ve Protel konularında ileri düzey yetkinlik. 5 yıldızlı tatil köyleri ve şehir otellerinde ekip liderliği, şikayet yönetimi ve gelir optimizasyonunda kanıtlanmış başarı.",
        "strengths": ["Ön Büro Operasyonları", "Opera PMS", "Ekip Liderliği", "Misafir İlişkileri"],
        "areas_for_improvement": ["Satış ve Pazarlama", "Bütçeleme"],
        "experience": [
            {"title": "Ön Büro Şefi (Supervisor)", "company": "Hilton Hotels & Resorts", "years": "2021-Present", "description": "Ön büro ekiplerinin yönetimi ve misafir deneyimi süreçleri."},
            {"title": "Resepsiyonist", "company": "Sheraton Hotels", "years": "2019-2021", "description": "Misafir giriş/çıkış işlemleri ve PMS veritabanı yönetimi."}
        ],
        "education": [
            {"degree": "Otel Yöneticiliği Lisans", "school": "Akdeniz Üniversitesi", "year": "2018"}
        ]
    }
}

def translate_with_gemini(data: dict) -> dict:
    """
    Sends English candidate profile data to Gemini to translate all text fields into Turkish.
    """
    if not API_KEY:
        logger.warning("No Gemini API key configured for translation.")
        return data

    model = genai.GenerativeModel(settings.GEMINI_MODEL, generation_config={"response_mime_type": "application/json"})
    
    prompt = f"""
    Sen uzman bir İK çevirmenisin. Aşağıda verilen adayın İngilizce İK bilgilerini Türkçe'ye çevir.
    Sadece değerleri Türkçe'ye çevir, JSON yapısını ve anahtarları (keys) kesinlikle değiştirme.
    İş tanımlarını (description), iş unvanlarını (title), özet (summary), güçlü yanlar (strengths) ve geliştirilmesi gereken yönleri (areas_for_improvement) profesyonel kurumsal İK dilinde Türkçe'ye çevir.
    Eğitim derecelerini (degree) ve okul adlarını (school) da uygun şekilde Türkçe'ye çevir (Örn: BS Computer Science -> Bilgisayar Mühendisliği Lisans).

    ÇEVİRİLECEK VERİ:
    {json.dumps(data, ensure_ascii=False)}

    ÇIKTI ŞABLONU (Aynı JSON yapısı, sadece değerler Türkçe):
    {json.dumps(data, ensure_ascii=False)}
    """
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        translated_data = json.loads(clean_text)
        return translated_data
    except Exception as e:
        logger.error(f"Failed to translate candidate profile via Gemini: {e}")
        return data

def translate_existing_candidates_to_turkish(db: Session):
    """
    Detects candidates with English profiles and translates them to Turkish.
    Also ensures every candidate has a persisted CV file.
    """
    import time
    candidates = db.query(models.Candidate).all()
    
    # Ensure static/uploads exists
    import os
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir = os.path.join(BASE_DIR, "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    english_keywords = ["and ", "with ", "experience", "motivated", "specializing", "proven", "track record", "graduate", "management", "developed"]
    
    for candidate in candidates:
        # Check static translations dictionary first (avoids Gemini 429 daily quotas and is highly accurate)
        if candidate.name in STATIC_TRANSLATIONS:
            logger.info(f"Applying high-fidelity static translation for {candidate.name}...")
            translated = STATIC_TRANSLATIONS[candidate.name]
            
            # Apply all fields
            candidate.summary = translated.get("summary", candidate.summary)
            candidate.experience = translated.get("experience", candidate.experience)
            candidate.education = translated.get("education", candidate.education)
            candidate.strengths = translated.get("strengths", candidate.strengths)
            candidate.areas_for_improvement = translated.get("areas_for_improvement", candidate.areas_for_improvement)
            candidate.certifications = translated.get("certifications", candidate.certifications)
            candidate.projects = translated.get("projects", candidate.projects)
            
            if candidate.seniority_level:
                sen_map = {
                    "junior": "Giriş Seviyesi",
                    "entry": "Giriş Seviyesi",
                    "mid": "Orta Seviye",
                    "senior": "Kıdemli"
                }
                c_sen = candidate.seniority_level.lower()
                if c_sen in sen_map:
                    candidate.seniority_level = sen_map[c_sen]
            
            db.commit()
            logger.info(f"Successfully applied static translation for {candidate.name}")
            
        else:
            summary_lower = (candidate.summary or "").lower()
            is_english = any(kw in summary_lower for kw in english_keywords)
            
            # Also check experience descriptions for English
            if not is_english and candidate.experience:
                for exp in candidate.experience:
                    if isinstance(exp, dict):
                        exp_desc = (exp.get("description", "") or "").lower()
                    else:
                        exp_desc = ""
                    if any(kw in exp_desc for kw in english_keywords):
                        is_english = True
                        break
            
            if is_english:
                logger.info(f"Translating profile of Candidate #{candidate.id} ({candidate.name}) to Turkish...")
                
                # Prepare data payload for translation
                payload = {
                    "summary": candidate.summary or "",
                    "experience": candidate.experience or [],
                    "education": candidate.education or [],
                    "strengths": candidate.strengths or [],
                    "areas_for_improvement": candidate.areas_for_improvement or [],
                    "certifications": candidate.certifications or [],
                    "projects": candidate.projects or []
                }
                translated = translate_with_gemini(payload)
                
                # Update candidate record
                candidate.summary = translated.get("summary", candidate.summary)
                candidate.experience = translated.get("experience", candidate.experience)
                candidate.education = translated.get("education", candidate.education)
                candidate.strengths = translated.get("strengths", candidate.strengths)
                candidate.areas_for_improvement = translated.get("areas_for_improvement", candidate.areas_for_improvement)
                candidate.certifications = translated.get("certifications", candidate.certifications)
                candidate.projects = translated.get("projects", candidate.projects)
                
                if candidate.seniority_level:
                    sen_map = {
                        "junior": "Giriş Seviyesi",
                        "entry": "Giriş Seviyesi",
                        "mid": "Orta Seviye",
                        "senior": "Kıdemli"
                    }
                    c_sen = candidate.seniority_level.lower()
                    if c_sen in sen_map:
                        candidate.seniority_level = sen_map[c_sen]
                
                db.commit()
                logger.info(f"Successfully translated Candidate #{candidate.id} ({candidate.name}) profile to Turkish.")
                # Sleep to respect rate limits (Gemini free tier allows 15 RPM)
                time.sleep(10)
            
        # Ensure CV file exists on disk
        has_file = False
        if candidate.cv_file_path:
            full_path = os.path.join(BASE_DIR, candidate.cv_file_path.lstrip("/"))
            if os.path.exists(full_path):
                has_file = True
            elif candidate.cv_file_data:
                try:
                    import base64
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "wb") as f:
                        f.write(base64.b64decode(candidate.cv_file_data.encode('utf-8')))
                    has_file = True
                    logger.info(f"Restored CV file from database for Candidate #{candidate.id} ({candidate.name})")
                except Exception as restore_err:
                    logger.error(f"Failed to restore CV file from database for Candidate #{candidate.id}: {restore_err}")
                
        if not has_file:
            # Generate a structured text CV file
            filename = f"{candidate.id}_cv.txt"
            cv_relative_path = f"/static/uploads/{filename}"
            full_path = os.path.join(upload_dir, filename)
            
            exp_lines = []
            for exp in (candidate.experience or []):
                if isinstance(exp, dict):
                    exp_lines.append(f"- {exp.get('title', 'Pozisyon')} @ {exp.get('company', 'Şirket')} ({exp.get('years', '')})\n  {exp.get('description', '')}")
                else:
                    exp_lines.append(f"- {exp}")
            
            edu_lines = []
            for edu in (candidate.education or []):
                if isinstance(edu, dict):
                    edu_lines.append(f"- {edu.get('degree', 'Bölüm')} - {edu.get('school', 'Okul')} ({edu.get('year', '')})")
                else:
                    edu_lines.append(f"- {edu}")
                
            skills_str = ", ".join(candidate.skills or [])
            strengths_str = "\n".join([f"- {s}" for s in (candidate.strengths or [])])
            improvements_str = "\n".join([f"- {i}" for i in (candidate.areas_for_improvement or [])])
            exp_str = "\n".join(exp_lines) if exp_lines else 'Belirtilmemiş'
            edu_str = "\n".join(edu_lines) if edu_lines else 'Belirtilmemiş'
            
            cv_text = f"""SKILLMATCH AI - ADAY ÖZGEÇMİŞ RAPORU
 
ADAY: {candidate.name}
E-POSTA: {candidate.email or 'Belirtilmemiş'}
TELEFON: {candidate.phone or 'Belirtilmemiş'}
 
PROFESYONEL ÖZET:
{candidate.summary or 'Belirtilmemiş'}
 
YETKİNLİKLER:
{skills_str or 'Belirtilmemiş'}
 
İŞ DENEYİMİ:
{exp_str}
 
EĞİTİM:
{edu_str}
 
GÜÇLÜ YÖNLER:
{strengths_str or 'Belirtilmemiş'}
 
GELİŞİM ALANLARI:
{improvements_str or 'Belirtilmemiş'}
"""
            try:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(cv_text)
                candidate.cv_file_path = cv_relative_path
                db.commit()
                logger.info(f"Generated mock CV file for Candidate #{candidate.id} ({candidate.name}) at {cv_relative_path}")
            except Exception as file_err:
                logger.error(f"Failed to generate mock CV file: {file_err}")
