"""Demo veri seti — sunum öncesi çalıştırılır.

Boş bir veritabanı sunumda kötü görünür; bu script uygulamanın kendi modelleri
üzerinden gerçekçi bir başlangıç durumu kurar. Sunum sırasında canlı olarak
oluşturulacak kayıtlar (yeni kadro talebi, kampanya, QR başvurusu, mülakat,
teklif) BİLEREK eklenmez — onları sahnede siz oluşturursunuz.

Kullanım (backend/ dizininden):
    ../venv/bin/python scripts/seed_demo.py

`--reset` verilirse önce mevcut aday/başvuru/teklif/mülakat kayıtları silinir.
Oteller, departmanlar ve kullanıcılar korunur.
"""
import os
import sys
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal  # noqa: E402
import models  # noqa: E402
from routers.candidates import normalize_phone  # noqa: E402

random.seed(20260917)

POSITIONS = [
    ("Garson", "Yiyecek ve İçecek", 12, "Kritik"),
    ("Komi", "Yiyecek ve İçecek", 8, "Yüksek"),
    ("Resepsiyonist", "Ön Büro", 6, "Yüksek"),
    ("Kat Görevlisi", "Kat Hizmetleri", 14, "Kritik"),
    ("Aşçı", "Mutfak", 5, "Orta"),
    ("Cankurtaran", "Recreation", 4, "Orta"),
]

FIRST = ["Elif", "Mert", "Zeynep", "Burak", "Selin", "Emre", "Deniz", "Ayça",
         "Kaan", "Merve", "Onur", "Ece", "Barış", "Pelin", "Tolga", "Nur"]
LAST = ["Yılmaz", "Demir", "Şahin", "Çelik", "Kaya", "Aydın", "Arslan", "Doğan",
        "Kurt", "Öztürk", "Koç", "Aksoy"]

SKILLS = {
    "Garson": ["Servis", "Müşteri İlişkileri", "İngilizce", "Takım Çalışması"],
    "Komi": ["Servis", "Hijyen", "Takım Çalışması"],
    "Resepsiyonist": ["Opera PMS", "İngilizce", "Rusça", "Müşteri İlişkileri"],
    "Kat Görevlisi": ["Hijyen", "Detay Odaklılık", "Zaman Yönetimi"],
    "Aşçı": ["Sıcak Mutfak", "HACCP", "Menü Planlama"],
    "Cankurtaran": ["İlk Yardım", "Yüzme Brövesi", "Kriz Yönetimi"],
}

# (durum, kaç aday) — sunumda pipeline'ın dolu görünmesi için
STAGE_PLAN = [
    ("applied", 9),
    ("screening", 6),
    ("hr_interview", 4),
    ("tech_interview", 3),
    ("offer", 2),
    ("hired", 3),
]


def reset(db):
    for model in (models.OfferApprovalRequest, models.Offer, models.Interview,
                  models.OnboardingTask, models.MatchScore, models.Application,
                  models.Candidate, models.RecruitmentCampaign, models.StaffingNeed,
                  models.WorkforceHeadcountBudget, models.WorkforcePlanLine,
                  models.WorkforceBudgetRecord):
        db.query(model).delete()
    # sunumda kafa karıştıran, kadrosu olmayan artık pozisyonları temizle
    keep = {title for title, *_ in POSITIONS}
    for pos in db.query(models.Position).all():
        if pos.title not in keep:
            db.query(models.Application).filter_by(position_id=pos.id).delete()
            db.delete(pos)
    db.commit()
    print("  önceki aday/başvuru/teklif kayıtları ve artık pozisyonlar silindi")


def main(do_reset: bool):
    db = SessionLocal()
    try:
        if do_reset:
            reset(db)

        hotels = {h.code: h for h in db.query(models.Hotel).all()}
        depts = {d.name: d for d in db.query(models.Department).all()}
        sungate = hotels.get("SUN") or next(iter(hotels.values()))

        # ── pozisyonlar ────────────────────────────────────────────────
        created_positions = []
        for title, dept_name, headcount, priority in POSITIONS:
            dept = depts.get(dept_name)
            pos = db.query(models.Position).filter_by(title=title, hotel_id=sungate.id).first()
            if not pos:
                pos = models.Position(
                    title=title,
                    hotel_id=sungate.id,
                    department_id=dept.id if dept else None,
                    department=dept_name,
                    description=f"{sungate.name} bünyesinde {dept_name} departmanı için {title} pozisyonu.",
                    required_skills=SKILLS.get(title, []),
                    headcount=headcount,
                    priority=priority,
                    is_active=True,
                    salary_currency="TRY",
                )
                db.add(pos)
                db.commit()
                db.refresh(pos)
            created_positions.append(pos)
        print(f"  {len(created_positions)} pozisyon hazır")

        # ── maaş politikaları ──────────────────────────────────────────
        bands = {"Garson": (32000, 36000, 41000), "Komi": (28000, 31000, 35000),
                 "Resepsiyonist": (34000, 39000, 45000), "Kat Görevlisi": (30000, 33000, 37000),
                 "Aşçı": (42000, 48000, 56000), "Cankurtaran": (33000, 37000, 42000),
                 # Sunumda canlı açılacak pozisyonun bandı önceden tanımlı olmalı:
                 # merkez İK ücret bantlarını pozisyon açılmadan belirler, ve
                 # demo bu bandın aşılmasıyla devreye giren onay akışını gösterir.
                 "Bar Şefi": (38000, 43000, 48000)}
        for title in list(bands):
            if db.query(models.SalaryPolicy).filter_by(position_title=title, hotel_id=sungate.id).first():
                continue
            pos = next((p for p in created_positions if p.title == title), None)
            lo, mid, hi = bands[title]
            db.add(models.SalaryPolicy(
                hotel_id=sungate.id,
                department_id=pos.department_id if pos else None,
                position_title=title,
                min_salary=lo, target_salary=mid, max_salary=hi, currency="TRY",
                is_active=True, version=1, status="active",
                accommodation=True, meal=True, transportation=True))
        db.commit()
        print(f"  {len(bands)} maaş politikası hazır (Bar Şefi dahil)")

        # ── adaylar ve başvurular ──────────────────────────────────────
        now = datetime.utcnow()
        used = set()
        total = 0
        for stage, count in STAGE_PLAN:
            for _ in range(count):
                while True:
                    name = f"{random.choice(FIRST)} {random.choice(LAST)}"
                    if name not in used:
                        used.add(name)
                        break
                pos = random.choice(created_positions)
                slug = name.lower().replace(" ", ".").replace("ı", "i").replace("ş", "s") \
                           .replace("ç", "c").replace("ö", "o").replace("ü", "u").replace("ğ", "g")
                phone = f"+90 5{random.randint(30, 59)} {random.randint(100,999)} {random.randint(10,99)} {random.randint(10,99)}"
                applied = now - timedelta(days=random.randint(2, 40))

                cand = models.Candidate(
                    name=name, full_name=name,
                    email=f"{slug}@ornek.com",
                    phone=phone, phone_normalized=normalize_phone(phone),
                    skills=random.sample(SKILLS[pos.title], k=min(3, len(SKILLS[pos.title]))),
                    experience=[{"title": pos.title, "company": "Önceki Otel",
                                 "years": f"{2019 + random.randint(0,4)}-2026",
                                 "description": f"{pos.title} olarak görev yaptı."}],
                    education=[{"degree": "Turizm ve Otel İşletmeciliği", "school": "Anadolu Üniversitesi", "year": "2019"}],
                    seniority_level=random.choice(["Giriş Seviyesi", "Orta Seviye", "Kıdemli"]),
                    summary=f"{pos.title} pozisyonunda deneyimli aday.",
                    tenant_id=1,
                )
                db.add(cand)
                db.commit()
                db.refresh(cand)

                app = models.Application(
                    candidate_id=cand.id, position_id=pos.id, hotel_id=sungate.id,
                    status=stage, applied_at=applied,
                    source=random.choice(["QR Walk-In", "Kariyer.net", "LinkedIn", "Referans"]),
                    match_score=round(random.uniform(58, 94), 1),
                    lock_status="LOCKED",
                    ownership_started_at=applied,
                    ownership_expires_at=applied + timedelta(days=10),
                    hired_at=(applied + timedelta(days=random.randint(9, 22))) if stage == "hired" else None,
                )
                db.add(app)
                db.commit()
                total += 1
        print(f"  {total} aday ve başvuru oluşturuldu")

        # ── kadro bütçesi (dashboard "Açık kadro" ve doluluk için) ─────
        for pos in created_positions:
            if db.query(models.WorkforceHeadcountBudget).filter_by(
                    hotel_id=sungate.id, position_title=pos.title).first():
                continue
            lo, mid, hi = bands[pos.title]
            db.add(models.WorkforceHeadcountBudget(
                hotel_id=sungate.id, department_id=pos.department_id,
                position_title=pos.title, headcount_budget=pos.headcount,
                target_salary_min=lo, target_salary_max=hi, currency="TRY"))
        db.commit()
        print(f"  {len(created_positions)} kadro bütçesi satırı")

        # ── aylık bütçe FTE kayıtları (Kadro İhtiyaçları tablosu) ──────
        month_now = datetime.utcnow().month
        for pos in created_positions:
            dept_name = next(d for t, d, *_ in POSITIONS if t == pos.title)
            for month in range(1, 13):
                # sezonluk otel: yaz aylarında kadro artar
                season = 1.0 + (0.25 if 5 <= month <= 9 else -0.1)
                db.add(models.WorkforceBudgetRecord(
                    hotel_code=sungate.code, hotel_sub="Ana Otel",
                    department=dept_name, sub_department=dept_name,
                    position_title=pos.title, month_of_year=month,
                    total_fte=round(pos.headcount * season, 2)))
        db.commit()
        print(f"  {len(created_positions) * 12} aylık bütçe FTE kaydı")

        # ── FTE planı (Genel Bakış'taki "FTE açığı özeti" için) ────────
        period = db.query(models.WorkforcePlanPeriod).filter_by(period_code="2026-09").first()
        if not period:
            period = models.WorkforcePlanPeriod(period_code="2026-09", is_active=True)
            db.add(period)
            db.commit()
            db.refresh(period)
        for pos in created_positions:
            node = db.query(models.OrganizationNode).filter_by(name=pos.title).first()
            if not node:
                node = models.OrganizationNode(name=pos.title, code=pos.title.upper().replace(" ", "_"), level=4, tenant_id=1, is_active=True)
                db.add(node)
                db.commit()
                db.refresh(node)
            if db.query(models.WorkforcePlanLine).filter_by(
                    period_id=period.id, node_id=node.id).first():
                continue
            budget_fte = float(pos.headcount)
            db.add(models.WorkforcePlanLine(
                period_id=period.id, node_id=node.id,
                budget_fte=budget_fte,
                active_fte=round(budget_fte * random.uniform(0.72, 0.92), 2),
                hired_pending_fte=float(random.randint(0, 2))))
        db.commit()
        print(f"  {len(created_positions)} FTE plan satırı")

        # ── mevcut kadro (otelde hâlihazırda çalışanlar) ───────────────
        # Bunlar olmadan doluluk oranı %5 görünüyor; gerçek bir otelde kadronun
        # çoğu doludur ve açık kadro birkaç kişidir.
        existing = 0
        for pos in created_positions:
            filled = int(pos.headcount * random.uniform(0.78, 0.92))
            for _ in range(filled):
                while True:
                    name = f"{random.choice(FIRST)} {random.choice(LAST)}"
                    if name not in used:
                        used.add(name)
                        break
                started = now - timedelta(days=random.randint(120, 900))
                slug = f"calisan{existing}"
                phone = f"+90 5{random.randint(30,59)} {random.randint(100,999)} {random.randint(10,99)} {random.randint(10,99)}"
                cand = models.Candidate(
                    name=name, full_name=name, email=f"{slug}@ornek.com",
                    phone=phone, phone_normalized=normalize_phone(phone),
                    skills=SKILLS[pos.title][:2], experience=[], education=[],
                    summary=f"{pos.title} — mevcut kadro.", tenant_id=1)
                db.add(cand)
                db.commit()
                db.refresh(cand)
                db.add(models.Application(
                    candidate_id=cand.id, position_id=pos.id, hotel_id=sungate.id,
                    status="hired", applied_at=started,
                    hired_at=started + timedelta(days=random.randint(10, 25)),
                    source="Mevcut Kadro", match_score=round(random.uniform(70, 95), 1),
                    lock_status="UNLOCKED"))
                db.commit()
                existing += 1
        print(f"  {existing} mevcut çalışan kaydı (doluluk oranı için)")

        # ── geçmiş mülakatlar (rapor rakamları için) ───────────────────
        iv_apps = db.query(models.Application).filter(
            models.Application.status.in_(["hr_interview", "tech_interview", "offer", "hired"])).all()
        for app in iv_apps:
            if db.query(models.Interview).filter_by(application_id=app.id).first():
                continue
            db.add(models.Interview(
                application_id=app.id,
                interview_type=random.choice(["hr", "technical"]),
                status="completed",
                scheduled_at=app.applied_at + timedelta(days=random.randint(3, 8)),
                duration_minutes=45,
                interviewer_name=random.choice(["Şule Sıray", "Beyza Çetin"]),
                overall_score=round(random.uniform(6.0, 9.2), 1),
                result="passed",
            ))
        db.commit()
        print(f"  {len(iv_apps)} tamamlanmış mülakat kaydı")

        # ── işe alınanlar için onboarding görevleri ────────────────────
        hired = db.query(models.Application).filter_by(status="hired").all()
        tasks = [("Kimlik belgelerini teslim et", "Evrak", "Aday"),
                 ("İş sözleşmesini imzala", "Evrak", "İK"),
                 ("SGK bildirimi", "Evrak", "İK"),
                 ("Kurumsal e-posta oluştur", "IT Setup", "IT"),
                 ("Üniforma teslimi", "Evrak", "İK"),
                 ("Oryantasyon eğitimi", "Eğitim", "İK")]
        for app in hired:
            if db.query(models.OnboardingTask).filter_by(application_id=app.id).first():
                continue
            for i, (title, cat, resp) in enumerate(tasks):
                db.add(models.OnboardingTask(
                    application_id=app.id, title=title, category=cat, responsible=resp,
                    due_days=i + 1, order_index=i,
                    status="completed" if i < 3 else "pending"))
        db.commit()
        print(f"  {len(hired)} işe alınan için onboarding listesi")

        print("\nDemo verisi hazır. Sunumda canlı oluşturacaklarınız bilerek eklenmedi:")
        print("  kadro talebi · kampanya/QR · QR'dan başvuru · mülakat · teklif")
    finally:
        db.close()


if __name__ == "__main__":
    main("--reset" in sys.argv)
