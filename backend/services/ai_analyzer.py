from config import settings
import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path, override=True)

API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)

def analyze_cv(text: str):
    """
    Analyzes CV text using Gemini to extract structured data.
    """
    if not API_KEY:
        return extract_basic_cv_data(text)

    model = genai.GenerativeModel(settings.GEMINI_MODEL, generation_config={"response_mime_type": "application/json"})
    
    prompt = f"""
    Sen uzman bir İK Yapay Zeka Asistanısın. Aşağıdaki CV metnini analiz et ve yapılandırılmış bilgileri çıkar.
    Çıkarttığın TÜM alanları (kişi adı hariç); profesyonel özet (summary), iş unvanları (title), iş tanımları (description), eğitim dereceleri ve bölümleri (degree), okul isimleri (school), sertifikalar, projeler, kıdem seviyesi, güçlü yanlar (strengths) ve geliştirilmesi gereken yönler (areas_for_improvement) dahil olmak üzere KESİNLİKLE TÜRKÇE'ye çevirerek Türkçe olarak oluştur.
    Kıdem seviyesini (seniority_level) "Giriş Seviyesi", "Orta Seviye", veya "Kıdemli" değerlerinden biri olarak ata.

    Çıktıyı kesinlikle aşağıdaki şemaya uygun bir JSON nesnesi olarak döndür:
    {{
        "name": "Aday Adı Soyadı",
        "email": "email@example.com",
        "phone": "+123456789",
        "summary": "Türkçe profesyonel özet...",
        "skills": ["Skill1", "Skill2"],
        "experience": [
            {{"title": "İş Unvanı", "company": "Şirket", "years": "2020-2022", "description": "İş tanımı..."}}
        ],
        "education": [
            {{"degree": "Derece/Bölüm", "school": "Okul", "year": "2019"}}
        ],
        "certifications": ["Sertifika 1", "Sertifika 2"],
        "projects": ["Proje 1", "Proje 2"],
        "seniority_level": "Giriş Seviyesi/Orta Seviye/Kıdemli",
        "seniority_score": 85.5,
        "strengths": ["Güçlü Yön 1", "Güçlü Yön 2"],
        "areas_for_improvement": ["Gelişmesi Gereken Yön 1", "Gelişmesi Gereken Yön 2"]
    }}

    CV Metni:
    {text}
    """
    
    try:
        response = model.generate_content(prompt)
        text_clean = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text_clean)
        
        # Enforce Turkish seniority mappings just in case
        sen_level = data.get("seniority_level", "Orta Seviye")
        sen_map = {
            "junior": "Giriş Seviyesi",
            "entry": "Giriş Seviyesi",
            "mid": "Orta Seviye",
            "senior": "Kıdemli"
        }
        if sen_level.lower() in sen_map:
            data["seniority_level"] = sen_map[sen_level.lower()]
            
        return data
    except Exception as e:
        print(f"AI Analysis failed: {e}")
        return extract_basic_cv_data(text)


EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?:\+90|0)?[\s.-]?\(?5\d{2}\)?[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}")
NAME_RE = re.compile(r"^[A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+){1,3}$")


def extract_basic_cv_data(text: str) -> dict:
    """Best-effort read of a CV without the AI.

    This used to return a fixed sample persona ("Mock Candidate", a senior
    Python developer), which was written straight into the candidate record and
    read as if it had come from the uploaded file. Pull out what can actually be
    read from the text and leave the AI-only fields empty rather than inventing
    a profile.
    """
    text = text or ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    email_match = EMAIL_RE.search(text)
    phone_match = PHONE_RE.search(text)

    name = None
    for line in lines[:15]:
        if NAME_RE.match(line):
            name = line
            break
    if not name and email_match:
        name = email_match.group(0).split("@")[0].replace(".", " ").replace("_", " ").title()
    if not name and lines:
        name = lines[0][:80]

    return {
        "name": name or "İsimsiz Aday",
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0).strip() if phone_match else None,
        "summary": "Bu CV yapay zeka ile analiz edilmedi (GEMINI_API_KEY tanımlı değil). "
                   "Ad, e-posta ve telefon dosyadan okundu; diğer alanlar boş bırakıldı.",
        "skills": [],
        "experience": [],
        "education": [],
        "certifications": [],
        "projects": [],
        "seniority_level": None,
        "seniority_score": None,
        "strengths": [],
        "areas_for_improvement": []
    }

def compare_candidates(candidate1: dict, candidate2: dict, position: dict = None) -> dict:
    """
    Compares two candidates using Gemini AI, optionally against a specific position.
    """
    if not API_KEY:
        return {
            "comparison": "API Key eksik. Mock karşılaştırma.",
            "recommendation": "API Key giriniz.",
            "candidate1_pros": ["Mock Pro 1"],
            "candidate2_pros": ["Mock Pro 2"],
            "comparison_table": []
        }

    model = genai.GenerativeModel(settings.GEMINI_MODEL, generation_config={"response_mime_type": "application/json"})
    
    position_context = ""
    if position:
        position_context = f"""
        İŞ DETAYLARI:
        Adayları özellikle şu pozisyon için karşılaştır:
        Pozisyon Başlığı: {position['title']}
        Departman: {position['department']}
        Açıklama: {position['description']}
        Gerekli Yetkinlikler: {', '.join(position['required_skills'])}
        
        Her adayın BU pozisyona ne kadar uygun olduğuna odaklan.
        """

    prompt = f"""
    Sen uzman bir İK Yapay Zeka Asistanısın. Aşağıdaki iki adayı karşılaştır.
    TÜM YAZILI DEĞERLENDİRMELERİ, TAVSİYELERİ, ARTILARI/EKSİLERİ VE TABLO DEĞERLERİNİ KESİNLİKLE TÜRKÇE OLARAK DÖNDÜR.
    {position_context}

    ADAY 1:
    Adı: {candidate1['name']}
    Özet: {candidate1['summary']}
    Yetenekler: {', '.join(candidate1['skills'])}
    Deneyim: {json.dumps(candidate1['experience'], ensure_ascii=False)}

    ADAY 2:
    Adı: {candidate2['name']}
    Özet: {candidate2['summary']}
    Yetenekler: {', '.join(candidate2['skills'])}
    Deneyim: {json.dumps(candidate2['experience'], ensure_ascii=False)}

    ÇIKTI BİÇİMİ (Strict JSON):
    {{
        "comparison": "Detaylı Türkçe karşılaştırma metni...",
        "recommendation": "Kimi, neden işe alacağınıza dair net Türkçe İK tavsiyesi...",
        "candidate1_pros": ["Artı Yön 1", "Artı Yön 2"],
        "candidate2_pros": ["Artı Yön 1", "Artı Yön 2"],
        "comparison_table": [
            {{"criteria": "Teknik Yetkinlikler", "candidate1_val": "Güçlü Python...", "candidate2_val": "Expert Java..."}},
            {{"criteria": "Deneyim", "candidate1_val": "5 yıl...", "candidate2_val": "3 yıl..."}},
            {{"criteria": "Eğitim", "candidate1_val": "...", "candidate2_val": "..."}},
            {{"criteria": "Sosyal Beceriler", "candidate1_val": "...", "candidate2_val": "..."}},
            {{"criteria": "Genel Uyum", "candidate1_val": "Yüksek", "candidate2_val": "Orta"}}
        ]
    }}
    JSON yapısının geçerli olduğundan emin ol.
    """
    
    try:
        response = model.generate_content(prompt)
        # Clean up potential markdown code blocks
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"Error comparing candidates: {e}")
        return {
            "comparison": "Error generating comparison.",
            "recommendation": "N/A",
            "candidate1_pros": [],
            "candidate2_pros": [],
            "comparison_table": []
        }

def deep_rank_candidates(position_dict: dict, candidates_list: list, all_positions_list: list = None) -> list:
    """
    Explainable AI for Recruitment Decision Support System.
    Deeply analyzes and ranks multiple candidates for a specific position.
    """
    if not API_KEY:
        raise Exception("API Key eksik. Explainable AI çalıştırılamıyor.")

    model = genai.GenerativeModel(settings.GEMINI_MODEL, generation_config={"response_mime_type": "application/json"})
    
    # Trim candidate data to fit within reasonable prompt size
    trimmed_candidates = []
    for c in candidates_list:
        trimmed_candidates.append({
            "id": c.get("id"),
            "name": c.get("name"),
            "summary": c.get("summary"),
            "skills": c.get("skills"),
            "experience": c.get("experience", [])[:3], # keep last 3 experiences
            "education": c.get("education", [])[:2],
            "seniority_level": c.get("seniority_level")
        })

    alt_positions_str = ""
    if all_positions_list:
        alt_pos_short = [{"id": p.get("id"), "title": p.get("title")} for p in all_positions_list if p.get("id") != position_dict.get("id")]
        alt_positions_str = f"Available alternative positions in the company: {json.dumps(alt_pos_short)}\n"

    prompt = f"""
    Sen uzman bir "Açıklanabilir İşe Alım Karar Destek Yapay Zeka Sistemi" (Explainable AI for Recruitment) uygulamasısın.
    Adayları, verilen iş pozisyonuna göre değerlendir, derecelendir ve derinlemesine analiz et.
    TÜM YAZILI BİLGİLERİ, GÜÇLÜ/ZAYIF YÖNLERİ, RİSKLERİ VE AÇIKLAMALARI KESİNLİKLE TÜRKÇE OLARAK DÖNDÜR.

    İŞ POZİSYONU DETAYLARI:
    Başlık: {position_dict.get('title')}
    Departman: {position_dict.get('department')}
    Açıklama: {position_dict.get('description')}
    Gerekli Yetkinlikler: {', '.join(position_dict.get('required_skills', []))}
    Kıdem Seviyesi: {position_dict.get('seniority_level')}

    ADAYLAR:
    {json.dumps(trimmed_candidates, ensure_ascii=False)}

    {alt_positions_str}
    
    YÖNERGELER:
    1. Her adayı iş pozisyonuna göre analiz et.
    2. Adayları uygunluklarına göre en iyiden en kötüye doğru sırala.
    3. Her biri için 0 ile 100 arasında bir eşleşme skoru (match_score) belirle.
    4. Açıklanabilir Yapay Zeka gerekçeleri sağla: güçlü yönler (strengths), zayıf yönler (weaknesses), riskler (risks), yetenek açığı analizi (skill_gap) ve bu sırayı neden aldıklarına dair Türkçe bir açıklama (explanation).
    5. Adayın 6 ay içinde ne kadar uygun hale gelebileceğini gösteren bir gelecek potansiyel skoru (future_potential_score) (0-100) ver.
    6. Adayın profiline ve pozisyon gereksinimlerine özel olarak hazırlanmış 3 adet Türkçe mülakat sorusu (interview_questions) üret.
    7. Aday bu iş için zayıf bir eşleşmeyse ancak önerilen alternatif bir pozisyona (all_positions_list) uygunsa, alternatif pozisyonun başlığını (alternative_position) öner.

    ÇIKTI BİÇİMİ: KESİNLİKLE aşağıdaki şemaya tam uyan bir JSON dizisi döndür:
    [
      {{
        "candidate_id": 123,
        "rank": 1,
        "match_score": 95,
        "strengths": ["Güçlü Python bilgisi", "Liderlik becerileri"],
        "weaknesses": ["AWS deneyimi yok"],
        "risks": ["Sık iş değiştirme riski (2 yılda 3 iş)"],
        "skill_gap": "Bulut dağıtım becerileri eksik (AWS/GCP).",
        "explanation": "Aday, bulut deneyimi eksik olmasına rağmen, backend teknoloji yığınındaki mükemmel eşleşmesi nedeniyle yüksek sırada yer almaktadır.",
        "future_potential_score": 98,
        "interview_questions": ["FastAPI ile geliştirdiğiniz projede performansı nasıl artırdınız?", "AWS deneyimi olmamasına rağmen bulut teknolojilerine nasıl adapte olursunuz?"],
        "alternative_position": null
      }}
    ]
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"Error in deep ranking: {e}")
        raise e
