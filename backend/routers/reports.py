from fastapi import APIRouter, Depends, HTTPException, Response, Body
from sqlalchemy.orm import Session
import os, io, json
import models, schemas, database, auth
from services.gemini_service import call_gemini
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

router = APIRouter()

# Font helper for Turkish character rendering in PDF on both Windows and Linux/Railway
def get_pdf_font():
    candidates = [
        # Windows candidates
        (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf", "Arial", "Arial-Bold"),
        # Linux / Ubuntu DejaVu Fonts (pre-installed on most nixpacks/debian servers)
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans", "DejaVuSans-Bold"),
        # Linux standard truetype Arial
        ("/usr/share/fonts/truetype/msttcorefonts/Arial.ttf", "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf", "Arial", "Arial-Bold"),
        # Linux liberation fonts
        ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "LiberationSans", "LiberationSans-Bold"),
    ]
    
    for path, bold_path, name, bold_name in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                if os.path.exists(bold_path):
                    pdfmetrics.registerFont(TTFont(bold_name, bold_path))
                    return name, bold_name
                else:
                    pdfmetrics.registerFont(TTFont(bold_name, path))
                    return name, bold_name
            except Exception as e:
                print(f"[PDF Font] Failed to register {name}: {e}")
                
    return "Helvetica", "Helvetica-Bold"


@router.post("/generate", response_model=schemas.PositionReportOut)
def generate_report(payload: dict = Body(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    """AI ile mülakat sonuçlarına dayalı rapor üret."""
    app_id = payload.get("application_id")
    report_type = payload.get("report_type") # HR, TECHNICAL, or COMBINED
    
    if not app_id or not report_type:
        raise HTTPException(status_code=400, detail="application_id ve report_type alanları zorunludur.")
        
    app = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Başvuru bulunamadı.")
        
    cand = app.candidate
    pos = app.position
    
    if not cand or not pos:
        raise HTTPException(status_code=404, detail="Aday veya Pozisyon bulunamadı.")
        
    # Map custom report types to HR / TECHNICAL / COMBINED
    report_type_upper = report_type.upper()
    resolved_type = "COMBINED"
    if "HR" in report_type_upper or "İK" in report_type_upper or "IK" in report_type_upper:
        resolved_type = "HR"
    elif "TEKNİK" in report_type_upper or "TECHNICAL" in report_type_upper or "TECH" in report_type_upper:
        resolved_type = "TECHNICAL"

    # Gather answers from DB
    answers_query = db.query(models.InterviewAnswer).filter(models.InterviewAnswer.application_id == app_id)
    if resolved_type == "HR":
        answers_query = answers_query.filter(models.InterviewAnswer.interview_type == "HR")
    elif resolved_type == "TECHNICAL":
        answers_query = answers_query.filter(models.InterviewAnswer.interview_type == "TECHNICAL")
        
    answers = answers_query.all()
    
    answers_text = ""
    for idx, ans in enumerate(answers, 1):
        answers_text += f"\nSoru {idx} ({ans.section}): {ans.question}\n"
        answers_text += f"Adayın Cevabı: {ans.candidate_answer or 'Yanıtlanmadı'}\n"
        answers_text += f"Değerlendirme Puanı: {ans.score if ans.score is not None else 'Puanlanmadı'}/10\n"
        answers_text += f"Mülakatçı Notları: {ans.notes or 'Not yok'}\n"
        
    dec = db.query(models.HiringDecision).filter(models.HiringDecision.application_id == app_id).first()
    m_score = db.query(models.MatchScore).filter(models.MatchScore.candidate_id == cand.id, models.MatchScore.position_id == pos.id).first()
    
    prompt = f"""
    Sen SkillMatch AI değerlendirme asistanısın. Aşağıdaki verilere dayanarak aday için son derece profesyonel bir '{report_type}' değerlendirme raporu hazırla (Türkçe).
    
    ADAY: {cand.name}
    POZİSYON: {pos.title} ({pos.department or 'Genel'})
    UYUM SKORU: %{app.match_score or 'Belirtilmemiş'}
    
    ADAY CEVAPLARI VE DEĞERLENDİRMELERİ:
    {answers_text}
    
    İŞE ALIM KARAR VERİLERİ:
    - Teknik Skor: {dec.technical_score if dec else 'Belirtilmemiş'}/10
    - Mülakat Puanı: {dec.interview_score if dec else 'Belirtilmemiş'}/10
    - Kültürel Uyum: {dec.cultural_score if dec else 'Belirtilmemiş'}/10
    - Karar Güveni: {dec.hiring_confidence if dec else 'Belirtilmemiş'}
    - Notlar: {dec.notes if dec else 'Not yok'}
    
    Kural: Adayın verdiği cevapları ham (raw) olarak kopyalama. Gemini olarak bu yanıtları analiz et, profesyonel bir dille temizle, geliştir et ve öyle özetle.
    
    Raporu şu başlıklarla Türkçe olarak yapılandır:
    1. Yönetici Özeti (Executive Summary)
    2. Adayın Güçlü Yönleri (Strengths)
    3. Gelişim Alanları ve Riskler (Risks & Areas for Improvement)
    4. Mülakat Değerlendirme Özeti (Temizlenmiş ve profesyonel hale getirilmiş yanıt analizi)
    5. Nihai Karar ve İşe Alım Önerisi
    """
    
    res_text = call_gemini(db, prompt)
    
    rep = models.PositionReport(
        position_id=pos.id,
        candidate_id=cand.id,
        application_id=app_id,
        report_type=f"{report_type} Interview Report",
        report_content=res_text
    )
    db.add(rep)
    db.commit()
    db.refresh(rep)
    
    # Update PDF download path
    rep.pdf_path = f"/api/reports/{rep.id}/download"
    db.commit()
    
    # Log activity
    act = models.CandidateActivity(
        candidate_id=cand.id,
        application_id=app_id,
        activity_type="report_generated",
        note=f"{report_type} Değerlendirme Raporu oluşturuldu.",
        created_by="SkillMatch AI"
    )
    db.add(act)
    db.commit()
    
    return rep


@router.get("/{report_id}", response_model=schemas.PositionReportOut)
def get_report(report_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    rep = db.query(models.PositionReport).filter(models.PositionReport.id == report_id).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Rapor bulunamadı.")
    return rep


@router.get("/{report_id}/download")
def download_report_pdf(report_id: int, db: Session = Depends(database.get_db)):
    rep = db.query(models.PositionReport).filter(models.PositionReport.id == report_id).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Rapor bulunamadı.")
        
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    story = []
    
    styles = getSampleStyleSheet()
    font_name, font_bold_name = get_pdf_font()
    
    # Custom styling
    title_style = ParagraphStyle(
        name="ReportTitle",
        parent=styles["Normal"],
        fontName=font_bold_name,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=15,
        alignment=1 # Center
    )
    
    heading_style = ParagraphStyle(
        name="ReportHeading",
        parent=styles["Normal"],
        fontName=font_bold_name,
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2563eb"),
        spaceBefore=12,
        spaceAfter=8
    )
    
    body_style = ParagraphStyle(
        name="ReportBody",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6
    )
    
    # Document header
    story.append(Paragraph(rep.report_type.upper(), title_style))
    story.append(Spacer(1, 10))
    
    # Parse markdown content safely
    lines = rep.report_content.split("\n")
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            story.append(Spacer(1, 4))
            continue
            
        if line_clean.startswith("#"):
            text = line_clean.replace("#", "").strip()
            story.append(Paragraph(text, heading_style))
        elif line_clean.startswith("-") or line_clean.startswith("*"):
            text = line_clean[1:].strip()
            bullet_text = f"• {text}"
            story.append(Paragraph(bullet_text, body_style))
        else:
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
