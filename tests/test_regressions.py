"""Regressions for defects found by walking the UI in a browser.

Each test pins one bug that was live in the app and would otherwise come back
silently: they all passed *before* the fix only because the relevant table was
empty, or because nothing exercised the path.
"""
import sys
from unittest.mock import MagicMock
sys.modules['sentence_transformers'] = MagicMock()

import os
import re
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from database import Base, get_db
from main import app
import models

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_JS = os.path.join(REPO, "backend", "static", "app.js")
INDEX_HTML = os.path.join(REPO, "backend", "templates", "index.html")

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_regressions.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    if os.path.exists("test_regressions.db"):
        try: os.remove("test_regressions.db")
        except OSError: pass
    Base.metadata.create_all(bind=engine)
    yield
    if os.path.exists("test_regressions.db"):
        try: os.remove("test_regressions.db")
        except OSError: pass


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    # tests/test_hotfixes.py installs its own get_db override at import time, so
    # claim it for the duration of each test here and hand it back afterwards.
    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    db.close()

    yield

    if previous is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous


def make_hotel(name="Test Otel", code="TST"):
    """hotels.organization_id / city_id / region_id are all NOT NULL."""
    db = TestingSessionLocal()

    def get_or_create(model, **kw):
        """Several tests now build more than one hotel, and country/organization
        names are unique."""
        row = db.query(model).filter_by(**kw).first()
        if row is None:
            row = model(**kw)
            db.add(row)
            db.commit()
        return row

    org = get_or_create(models.Organization, name="Test Org", code="TORG")
    country = get_or_create(models.Country, name="Türkiye")
    city = get_or_create(models.City, name="Antalya", country_id=country.id)
    region = get_or_create(models.Region, name="Akdeniz", city_id=city.id)
    hotel = models.Hotel(name=name, code=code, organization_id=org.id,
                         city_id=city.id, region_id=region.id)
    db.add(hotel)
    db.commit()
    hotel_id = hotel.id
    db.close()
    return hotel_id


@pytest.fixture
def as_admin():
    from auth import get_current_user
    db = TestingSessionLocal()
    user = models.User(email="regression@example.com", full_name="Regression Admin",
                       hashed_password="x", role="ADMIN", is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides.pop(get_current_user, None)
    db.close()


# ── staffing needs ───────────────────────────────────────────────────────────

def test_staffing_needs_list_serializes_rows(as_admin):
    """response_model=list cannot serialize ORM objects under Pydantic v2, so the
    endpoint 500'd as soon as one row existed."""
    hotel_id = make_hotel()

    created = client.post("/api/staffing-needs/", json={
        "hotel_id": hotel_id, "position_title": "Garson",
        "needed_fte": 2.5, "needed_by": "2026-11-30", "priority": "urgent",
    })
    assert created.status_code == 200, created.text

    listed = client.get("/api/staffing-needs/")
    assert listed.status_code == 200, listed.text
    rows = listed.json()
    assert len(rows) == 1
    assert rows[0]["position_title"] == "Garson"
    assert rows[0]["needed_by"] == "2026-11-30"


def test_staffing_need_status_is_lowercase(as_admin):
    """The table gated Onayla/Reddet on 'PENDING'; the model stores 'pending'."""
    hotel_id = make_hotel()

    client.post("/api/staffing-needs/", json={"hotel_id": hotel_id, "position_title": "Aşçı"})
    assert client.get("/api/staffing-needs/").json()[0]["status"] == "pending"
    # and the filter has to match regardless of the casing the caller sends
    assert len(client.get("/api/staffing-needs/?status=PENDING").json()) == 1
    assert len(client.get("/api/staffing-needs/?status=pending").json()) == 1


def test_staffing_need_requires_a_hotel(as_admin):
    """payload["hotel_id"] raised KeyError -> 500 when the form was submitted empty."""
    r = client.post("/api/staffing-needs/", json={"position_title": "Garson"})
    assert r.status_code == 400
    assert "Otel" in r.json()["detail"]


def test_staffing_summary_reports_rejected(as_admin):
    """The UI read .rejected_count, which the endpoint never returned."""
    hotel_id = make_hotel()

    client.post("/api/staffing-needs/", json={"hotel_id": hotel_id, "position_title": "Garson"})
    need_id = client.get("/api/staffing-needs/").json()[0]["id"]
    client.put(f"/api/staffing-needs/{need_id}/reject", json={"reason": "Bütçe yok"})

    s = client.get("/api/staffing-needs/summary").json()
    assert s["rejected_count"] == 1
    assert set(s) >= {"pending_count", "approved_count", "rejected_count", "total_gap_fte"}


def test_approving_a_need_keeps_the_positions_list_readable(as_admin):
    """The position an approval creates has no description, and PositionBase
    required one, so /api/positions/ 500'd afterwards."""
    hotel_id = make_hotel()

    client.post("/api/staffing-needs/", json={"hotel_id": hotel_id, "position_title": "Lifeguard"})
    need_id = client.get("/api/staffing-needs/").json()[0]["id"]
    assert client.put(f"/api/staffing-needs/{need_id}/approve").status_code == 200

    listed = client.get("/api/positions/")
    assert listed.status_code == 200, listed.text
    assert any(p["title"] == "Lifeguard" for p in listed.json())


# ── headcount / FTE ──────────────────────────────────────────────────────────

def test_headcount_total_is_not_truncated(as_admin):
    """int() per row before summing lost the fractional part of every row, so the
    page total came out below the imported Excel's SUM."""
    make_hotel()
    db = TestingSessionLocal()
    for i in range(10):
        db.add(models.WorkforceBudgetRecord(
            hotel_code="TST", department="Yiyecek ve İçecek",
            position_title=f"Garson {i}", month_of_year=8, total_fte=4.58))
    db.commit()
    db.close()

    kpis = client.get("/api/headcount/summary?month=8").json()["kpis"]
    assert kpis["approved_budget"] == pytest.approx(45.8, abs=0.01)  # not 40


def test_budget_template_matches_the_importer(as_admin):
    """The Şablon indir button had no handler; the template it now serves has to
    carry exactly the columns upload_headcount_excel validates."""
    import io
    import pandas as pd

    r = client.get("/api/headcount/budget-template")
    assert r.status_code == 200
    df = pd.read_excel(io.BytesIO(r.content))
    required = ['Otel', 'Otel_Alt', 'Ana Kategori', 'Alt Kategori',
                'Tanım (Pozisyon/İsim/Grade)', 'MonthOfYear', 'Toplam FTE']
    assert list(df.columns) == required


# ── blacklist ────────────────────────────────────────────────────────────────

def test_blacklist_can_be_added_and_removed(as_admin):
    """The endpoint only ever set the flag, and the UI sent PATCH to a POST route."""
    db = TestingSessionLocal()
    db.add(models.Candidate(name="Ali Veli", email="ali@example.com", skills=[], experience=[]))
    db.commit()
    cid = db.query(models.Candidate).first().id
    db.close()

    on = client.post(f"/api/candidates/{cid}/blacklist", json={"reason": "Devamsızlık"})
    assert on.status_code == 200, on.text
    assert on.json()["is_blacklisted"] is True
    assert "Devamsızlık" in on.json()["reason"]

    off = client.post(f"/api/candidates/{cid}/blacklist", json={"is_blacklisted": False})
    assert off.status_code == 200, off.text
    assert off.json()["is_blacklisted"] is False


# ── offers ───────────────────────────────────────────────────────────────────

def test_creating_an_offer_does_not_blow_up_on_approval_status(as_admin):
    """routers/offers.py passes approval_status= to models.Offer and reads it back
    in the status transitions, and main.py migrates the column in, but the model
    never declared it: every POST /api/offers/ raised TypeError."""
    hotel_id = make_hotel()
    db = TestingSessionLocal()
    candidate = models.Candidate(name="Mehmet Kaya", email="mk@example.com", skills=[], experience=[])
    position = models.Position(title="Gece Resepsiyonisti", hotel_id=hotel_id, is_active=True, headcount=1)
    db.add_all([candidate, position])
    db.commit()
    application = models.Application(candidate_id=candidate.id, position_id=position.id, status="hr_interview")
    db.add(application)
    db.commit()
    app_id = application.id
    db.close()

    created = client.post("/api/offers/", json={
        "application_id": app_id,
        "proposed_salary": 42000,
        "currency": "TRY",
        "position_title": "Gece Resepsiyonisti",
        "benefits": ["Yemek kartı"],
    })
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["proposed_salary"] == 42000
    assert body["approval_status"] in ("APPROVED", "PENDING_APPROVAL")

    fetched = client.get(f"/api/offers/application/{app_id}")
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["position_title"] == "Gece Resepsiyonisti"


# ── organization / budget Excel import ───────────────────────────────────────

def test_org_import_reads_the_sheet_it_documents(as_admin):
    """The upload lower-cased df.columns but then mapped each key back to the
    ORIGINAL spelling, so every row.get() missed: the whole sheet came through as
    the literal string "None" with 0.0 FTE, and because every row then looked
    identical, all but the first were flagged as duplicates. The documented
    headers (Donem, OtelKodu, ...) are mixed case, so it never worked as
    documented."""
    import io
    import pandas as pd

    make_hotel(name="Rixos Sungate", code="SUN")
    rows = [{
        "Donem": 2026, "OtelKodu": "SUN", "OtelAdi": "Rixos Sungate",
        "Sehir": "Antalya", "Bolge": "Akdeniz", "AnaKategori": "Yiyecek ve İçecek",
        "AltAnaKategori": "Ana Otel", "AltKategori": "Servis",
        "PozisyonKodu": "GRS", "PozisyonAdi": "Garson",
        "ButceFTE": 12.5, "AktifFTE": 10,
    }, {
        "Donem": 2026, "OtelKodu": "SUN", "OtelAdi": "Rixos Sungate",
        "Sehir": "Antalya", "Bolge": "Akdeniz", "AnaKategori": "Ön Büro",
        "AltAnaKategori": "Ana Otel", "AltKategori": "Resepsiyon",
        "PozisyonKodu": "RSP", "PozisyonAdi": "Resepsiyonist",
        "ButceFTE": 8.25, "AktifFTE": 7,
    }]
    buf = io.BytesIO()
    pd.DataFrame(rows).to_excel(buf, index=False)
    buf.seek(0)

    r = client.post(
        "/api/organization-imports/upload",
        files={"file": ("org.xlsx", buf,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total_rows"] == 2
    # two genuinely different positions are not duplicates of each other
    assert body["warning_count"] == 0, body["preview_rows"]

    preview = {row["position_name"]: row for row in body["preview_rows"]}
    assert set(preview) == {"Garson", "Resepsiyonist"}
    assert preview["Garson"]["hotel_code"] == "SUN"
    assert preview["Garson"]["budget_fte"] == 12.5
    assert preview["Resepsiyonist"]["budget_fte"] == 8.25
    assert preview["Resepsiyonist"]["main_category"] == "Ön Büro"


# ── interview scheduling vs. the kanban board ────────────────────────────────

def test_scheduling_an_interview_keeps_the_candidate_on_the_board(as_admin):
    """Both scheduling paths set app.status = "interview", which is not one of the
    pipeline columns, so the candidate vanished from the Kanban board the moment
    an interview was booked. main.py still ships a migration rewriting that
    legacy value, which is the giveaway."""
    from routers.interviews import interview_stage

    stages = ["applied", "screening", "hr_interview", "tech_interview",
              "manager_interview", "reference_check", "offer", "hired", "rejected", "hold"]
    assert interview_stage("hr") == "hr_interview"
    assert interview_stage("technical") == "tech_interview"
    assert interview_stage("manager") == "manager_interview"
    # an unknown type still has to land on a real column
    assert interview_stage("video") in stages
    assert interview_stage(None) in stages

    hotel_id = make_hotel()
    app_id = _make_application(hotel_id, title="Bar Şefi", email="kanban@example.com")
    r = client.post("/api/interviews/", json={
        "application_id": app_id, "round_number": 1, "interview_type": "technical",
        "scheduled_at": "2026-10-01T10:30:00", "duration_minutes": 60,
        "interviewer_name": "Şule Sıray",
    })
    assert r.status_code in (200, 201), r.text

    db = TestingSessionLocal()
    status = db.get(models.Application, app_id).status
    db.close()
    assert status == "tech_interview", status
    assert status in stages


# ── dashboard vs. real interviews ────────────────────────────────────────────

def test_dashboard_survives_a_scheduled_interview(as_admin):
    """dashboard-stats read iv.candidate_id / iv.position_id, which models.Interview
    does not have (only application_id), so the dashboard 500'd as soon as a single
    interview existed. It also listed every scheduled interview under "Bugünkü
    programım" regardless of date."""
    from datetime import datetime, timedelta

    hotel_id = make_hotel()
    db = TestingSessionLocal()
    candidate = models.Candidate(name="Mehmet Kaya", email="mk2@example.com", skills=[], experience=[])
    position = models.Position(title="Gece Resepsiyonisti", hotel_id=hotel_id, is_active=True, headcount=1)
    db.add_all([candidate, position])
    db.commit()
    application = models.Application(candidate_id=candidate.id, position_id=position.id, status="hr_interview")
    db.add(application)
    db.commit()
    now = datetime.now()
    db.add(models.Interview(application_id=application.id, interview_type="technical",
                            status="scheduled",
                            scheduled_at=now.replace(hour=10, minute=30, second=0, microsecond=0),
                            interviewer_name="Şule Sıray"))
    db.add(models.Interview(application_id=application.id, interview_type="hr",
                            status="scheduled", scheduled_at=now + timedelta(days=15),
                            interviewer_name="Şule Sıray"))
    db.commit()
    db.close()

    r = client.get("/api/analytics/dashboard-stats")
    assert r.status_code == 200, r.text
    data = r.json()

    # building the row needs the candidate and position, which hang off the
    # application rather than the interview
    assert len(data["schedule"]) == 1, data["schedule"]
    assert data["schedule"][0]["candidate_name"] == "Mehmet Kaya"
    assert data["schedule"][0]["position_title"] == "Gece Resepsiyonisti"
    # and the one two weeks out stays off today's list
    assert data["today_interviews"] == 1

    # and the hotel-scoped variant must not fall over either
    assert client.get(f"/api/analytics/dashboard-stats?hotel_id={hotel_id}").status_code == 200


# ── phone matching / blacklist bypass ────────────────────────────────────────

def test_normalize_phone_folds_turkish_formats_together():
    from routers.candidates import normalize_phone
    same = {normalize_phone("+90 555 987 65 43"),
            normalize_phone("0555 987 65 43"),
            normalize_phone("+905559876543"),
            normalize_phone("555 987 65 43")}
    assert same == {"905559876543"}, same
    assert normalize_phone("") == ""
    assert normalize_phone(None) == ""


def test_blacklist_cannot_be_bypassed_by_reformatting_the_phone(as_admin):
    """The blacklist compared the raw phone string, so the same person got back in
    by writing 0555... instead of +90 555... with a different e-mail address."""
    hotel_id = make_hotel()
    db = TestingSessionLocal()
    db.add(models.Candidate(
        name="Kemal Demir", email="kemal@example.com",
        phone="+90 555 987 65 43", phone_normalized="905559876543",
        is_blacklisted=True, blacklist_reason="Görüşmeye gelmedi",
        skills=[], experience=[]))
    position = models.Position(title="Garson", hotel_id=hotel_id, is_active=True, headcount=1)
    db.add(position)
    db.commit()
    db.close()

    from routers.candidates import normalize_phone

    # every spelling of that number resolves to the blacklisted record
    for spelling in ("+90 555 987 65 43", "0555 987 65 43", "+905559876543"):
        db = TestingSessionLocal()
        norm = normalize_phone(spelling)
        hit = db.query(models.Candidate).filter(
            models.Candidate.is_blacklisted == True,
            ((models.Candidate.email == "baska@example.com") |
             (models.Candidate.phone == spelling) |
             (models.Candidate.phone_normalized == norm))
        ).first()
        db.close()
        assert hit is not None, f"{spelling} kara listeyi atlattı"

    # an unrelated number is not caught by it
    db = TestingSessionLocal()
    other = db.query(models.Candidate).filter(
        models.Candidate.is_blacklisted == True,
        models.Candidate.phone_normalized == normalize_phone("0533 111 22 33")
    ).first()
    db.close()
    assert other is None


def test_new_candidates_get_their_phone_normalized(as_admin):
    """phone_normalized is read by the duplicate and blacklist checks but was
    written nowhere, so it was NULL on every row."""
    app_js_paths = [
        os.path.join(REPO, "backend", "routers", "portal.py"),
        os.path.join(REPO, "backend", "routers", "candidates.py"),
    ]
    for path in app_js_paths:
        src = open(path, encoding="utf-8").read()
        assert "phone_normalized=norm_phone" in src, f"{path} aday oluştururken normalize telefonu yazmıyor"
        assert "phone_normalized == norm_phone" in src, f"{path} kontrollerde normalize telefonu kullanmıyor"


# ── schemas stricter than the database ───────────────────────────────────────

def test_salary_policy_list_survives_null_version_and_status(as_admin):
    """SalaryPolicyOut required version/status, which are nullable columns with
    Python-side ORM defaults only. Any row inserted another way — including a
    backfill through this repo's ALTER TABLE migration list — reads back NULL and
    500s the whole settings list, the way PositionBase.description used to."""
    hotel_id = make_hotel()
    db = TestingSessionLocal()
    policy = models.SalaryPolicy(hotel_id=hotel_id, position_title="Garson",
                                 min_salary=30000, target_salary=35000, max_salary=40000,
                                 currency="TRY", is_active=True)
    db.add(policy)
    db.commit()
    # simulate a row that never went through the ORM defaults
    policy.version = None
    policy.status = None
    db.commit()
    db.close()

    r = client.get("/api/settings/salary-policy")
    assert r.status_code == 200, r.text
    assert r.json()[0]["position_title"] == "Garson"


# ── offer approval chain ─────────────────────────────────────────────────────

def _make_application(hotel_id, title="Garson", email="approval@example.com"):
    db = TestingSessionLocal()
    candidate = models.Candidate(name="Aday", email=email, skills=[], experience=[])
    position = models.Position(title=title, hotel_id=hotel_id, is_active=True, headcount=1)
    db.add_all([candidate, position])
    db.commit()
    application = models.Application(candidate_id=candidate.id, position_id=position.id,
                                     hotel_id=hotel_id, status="tech_interview")
    db.add(application)
    db.commit()
    app_id = application.id
    db.close()
    return app_id


def test_offer_outside_the_salary_band_needs_approval_before_it_can_be_sent(as_admin):
    """An offer above the position's salary policy has to go through the sequential
    approval chain, and must not be sendable until it clears."""
    hotel_id = make_hotel()
    app_id = _make_application(hotel_id, title="Garson")

    db = TestingSessionLocal()
    db.add(models.SalaryPolicy(hotel_id=hotel_id, position_title="Garson",
                               min_salary=30000, target_salary=35000, max_salary=40000,
                               currency="TRY", is_active=True))
    db.commit()
    db.close()

    # inside the band -> straight through
    ok = client.post("/api/offers/", json={"application_id": app_id, "proposed_salary": 35000,
                                           "currency": "TRY", "position_title": "Garson"})
    assert ok.status_code == 201, ok.text
    assert ok.json()["approval_status"] == "APPROVED"

    # above the band -> held, with a reason, and two sequential requests raised
    db = TestingSessionLocal()
    db.query(models.Offer).delete()
    db.commit()
    db.close()
    over = client.post("/api/offers/", json={"application_id": app_id, "proposed_salary": 48000,
                                             "currency": "TRY", "position_title": "Garson"})
    assert over.status_code == 201, over.text
    offer_id = over.json()["id"]
    assert over.json()["approval_status"] == "PENDING_APPROVAL"
    assert over.json()["deviation_reason"]

    db = TestingSessionLocal()
    reqs = db.query(models.OfferApprovalRequest).filter_by(offer_id=offer_id).order_by(
        models.OfferApprovalRequest.sequence_number).all()
    steps = [(r.approver_role, r.status) for r in reqs]
    first_id, second_id = reqs[0].id, reqs[1].id
    db.close()
    assert steps == [("HOTEL_HR", "PENDING"), ("CENTRAL_HR", "WAITING")], steps

    # cannot be sent while it is still pending
    blocked = client.patch(f"/api/offers/{offer_id}/status?status=sent")
    assert blocked.status_code == 400
    assert "onaylanmadı" in blocked.json()["detail"]

    # first approval promotes the second step
    assert client.post(f"/api/offers/approvals/{first_id}/resolve",
                       json={"status": "APPROVED", "notes": "Uygun"}).status_code == 200
    db = TestingSessionLocal()
    assert db.get(models.OfferApprovalRequest, second_id).status == "PENDING"
    db.close()

    # second approval clears the offer, and only then can it be sent
    assert client.post(f"/api/offers/approvals/{second_id}/resolve",
                       json={"status": "APPROVED", "notes": "Merkez onayı"}).status_code == 200
    db = TestingSessionLocal()
    assert db.get(models.Offer, offer_id).approval_status == "APPROVED"
    db.close()
    assert client.patch(f"/api/offers/{offer_id}/status?status=sent").status_code == 200


def test_rejecting_one_step_stops_the_whole_offer(as_admin):
    hotel_id = make_hotel()
    app_id = _make_application(hotel_id, title="Aşçı", email="reject@example.com")
    db = TestingSessionLocal()
    db.add(models.SalaryPolicy(hotel_id=hotel_id, position_title="Aşçı",
                               min_salary=30000, target_salary=35000, max_salary=40000,
                               currency="TRY", is_active=True))
    db.commit()
    db.close()

    offer_id = client.post("/api/offers/", json={"application_id": app_id, "proposed_salary": 60000,
                                                 "currency": "TRY", "position_title": "Aşçı"}).json()["id"]
    db = TestingSessionLocal()
    first = db.query(models.OfferApprovalRequest).filter_by(offer_id=offer_id, sequence_number=1).first().id
    db.close()

    assert client.post(f"/api/offers/approvals/{first}/resolve",
                       json={"status": "REJECTED", "notes": "Bütçe uygun değil"}).status_code == 200

    db = TestingSessionLocal()
    offer = db.get(models.Offer, offer_id)
    waiting = db.query(models.OfferApprovalRequest).filter_by(offer_id=offer_id, sequence_number=2).first()
    assert offer.approval_status == "REJECTED"
    # the step that was still waiting is cancelled too
    assert waiting.status == "REJECTED"
    db.close()

    blocked = client.patch(f"/api/offers/{offer_id}/status?status=sent")
    assert blocked.status_code == 400
    assert "reddedildi" in blocked.json()["detail"]


# ── matching ─────────────────────────────────────────────────────────────────

def test_no_required_skills_is_not_a_perfect_match():
    """A position listing no required skills scored 1.0 skill overlap, which drove
    the rule-based fallback to 100 and showed every candidate as %100 eşleşme."""
    from services.llm_matcher import llm_matcher_service

    assert llm_matcher_service.get_skill_overlap_ratio(["Python"], []) == 0.5
    assert llm_matcher_service.get_skill_overlap_ratio([], None) == 0.5
    # a real overlap still scores on its merits
    assert llm_matcher_service.get_skill_overlap_ratio(["Python", "SQL"], ["Python"]) == 1.0
    assert llm_matcher_service.get_skill_overlap_ratio(["Java"], ["Python"]) == 0.0


# ── CV parsing without an API key ────────────────────────────────────────────

def test_cv_fallback_reads_the_file_instead_of_inventing_a_person():
    """With no GEMINI_API_KEY the parser returned a fixed persona ("Mock
    Candidate", a senior Python developer) that was written into the candidate
    record as if it had been read from the upload."""
    from services.ai_analyzer import extract_basic_cv_data

    data = extract_basic_cv_data(
        "Ayse Yildirim\n"
        "Kat Hizmetleri Gorevlisi\n"
        "ayse.yildirim@ornek.com\n"
        "+90 532 444 55 66\n"
    )
    assert data["name"] == "Ayse Yildirim"
    assert data["email"] == "ayse.yildirim@ornek.com"
    assert "532" in data["phone"]
    # nothing is invented for the fields only the AI could fill
    assert data["skills"] == []
    assert data["experience"] == []
    assert data["seniority_level"] is None
    assert "analiz edilmedi" in data["summary"]


# ── settings load under a non-admin role ─────────────────────────────────────

def test_settings_batch_tolerates_a_forbidden_endpoint():
    """loadSettings() fetched eleven endpoints with Promise.all. A non-admin gets
    403 on audit-logs, which rejected the whole batch, so settingsData stayed
    empty and every hotel/department dropdown in the app was blank for them —
    they could not create a staffing need, a campaign, or filter by hotel."""
    app_js = open(APP_JS, encoding="utf-8").read()
    start = app_js.index("async function loadSettings()")
    body = app_js[start:start + 2000]
    assert "Promise.allSettled" in body, "loadSettings tek bir 403'te komple düşmemeli"
    assert "Promise.all(" not in body


# ── frontend wiring (static checks, no browser needed) ───────────────────────

def test_every_nav_target_has_a_page_template():
    """Kampanyalar, İşe Giriş and Blacklist had a nav entry but no template, so
    they rendered a blank content area."""
    html = open(INDEX_HTML, encoding="utf-8").read()
    nav_targets = set(re.findall(r"page='([a-z_]+)'", html))
    templates = set(re.findall(r'<template v-if="page===\'([a-z_]+)\'"', html))
    missing = {t for t in nav_targets if t not in templates}
    assert not missing, f"Bu sayfalara gidiliyor ama şablonu yok: {sorted(missing)}"


def test_setup_exposes_every_name_the_template_binds():
    """app.js returned the salary ref as `salary_stats` while index.html read
    `salaryStats`; the failed lookup tore down the whole Vue app."""
    app_js = open(APP_JS, encoding="utf-8").read()
    html = open(INDEX_HTML, encoding="utf-8").read()

    lines = app_js.split("\n")
    start = next(i for i, l in enumerate(lines) if l.strip() == "return {" and i > 3000)
    depth, block = 0, []
    for l in lines[start:]:
        block.append(l)
        depth += l.count("{") - l.count("}")
        if depth == 0 and len(block) > 1:
            break
    exposed = set()
    for l in block:
        for part in re.sub(r"//.*", "", l).strip().rstrip(",").split(","):
            part = part.split(":")[0].strip()
            if re.fullmatch(r"[A-Za-z_$][\w$]*", part):
                exposed.add(part)

    for name in ("salaryStats", "staffingNeeds", "campaigns", "blacklistedCandidates",
                 "onboardingApps", "departmentPills", "downloadBudgetTemplate"):
        assert name in exposed, f"index.html {name} kullanıyor ama setup() döndürmüyor"
        assert name in html, f"{name} export ediliyor ama şablonda kullanılmıyor"


def test_onboarding_checklist_survives_a_page_reload(as_admin):
    """GET /api/onboarding/{id} returns {completion_percentage, tasks} but both
    front-end callers assigned the whole envelope to the task array, so a
    generated checklist turned into junk rows as soon as the page was reloaded
    (and the application modal threw `onboardingTasks.filter is not a function`)."""
    hotel_id = make_hotel()
    db = TestingSessionLocal()
    pos = models.Position(title="Bar Şefi", hotel_id=hotel_id)
    cand = models.Candidate(name="Sinem Kaplan", email="sinem@ornek.com")
    db.add_all([pos, cand]); db.commit()
    app_row = models.Application(candidate_id=cand.id, position_id=pos.id, status="offer")
    db.add(app_row); db.commit()
    app_id = app_row.id
    db.close()

    assert client.post(f"/api/onboarding/{app_id}/generate").status_code == 200
    body = client.get(f"/api/onboarding/{app_id}").json()
    assert isinstance(body, dict) and isinstance(body["tasks"], list) and body["tasks"]

    app_js = open(APP_JS, encoding="utf-8").read()
    for fn in ("async function loadOnboarding()", "async function selectOnboardingApp("):
        start = app_js.index(fn)
        block = app_js[start:start + 500]
        get_call = re.search(r"api\('GET', `/api/onboarding/\$\{[^`]+`\);", block)
        assert get_call, f"{fn} artık onboarding GET çağırmıyor"
        assigned = block[:get_call.start()].rstrip().endswith("=")
        assert not assigned, f"{fn} yanıtın tamamını diziye atıyor, .tasks okumalı"
        assert ".tasks || []" in block[get_call.end():get_call.end() + 120]


def test_qr_code_is_drawn_locally_not_fetched_from_a_web_service(tmp_path, as_admin):
    """The QR was downloaded from api.qrserver.com while the recruiter stood in
    front of the candidate; any network hiccup left qr_code_path empty and the
    campaign row showed a dash where the QR belongs."""
    import socket
    from routers.campaigns import generate_qr_code_helper

    real_socket = socket.socket

    def no_network(*a, **k):
        raise AssertionError("QR üretimi dış servise çıkmamalı")

    socket.socket = no_network
    try:
        path = generate_qr_code_helper("http://ornek/portal/job/9?utm_source=instagram", "test_qr.png")
    finally:
        socket.socket = real_socket

    assert path == "/static/qrcodes/test_qr.png"
    on_disk = os.path.join(REPO, "backend", "static", "qrcodes", "test_qr.png")
    try:
        assert os.path.getsize(on_disk) > 0
        from PIL import Image
        assert Image.open(on_disk).size[0] >= 100, "QR okunamayacak kadar küçük"
    finally:
        os.remove(on_disk)


def test_every_funnel_key_has_a_turkish_label():
    """/api/analytics/stats reports the interview stages under one `interview`
    key, which stageLabelMap had no entry for, so the report screen printed the
    raw English key next to the Turkish ones."""
    analytics = open(os.path.join(REPO, "backend", "routers", "analytics.py"), encoding="utf-8").read()
    stages = re.search(r'stages = \[([^\]]+)\]', analytics).group(1)
    keys = re.findall(r'"([a-z_]+)"', stages)
    assert keys, "analytics.py artık funnel aşamalarını bu şekilde listelemiyor"

    app_js = open(APP_JS, encoding="utf-8").read()
    start = app_js.index("const stageLabelMap = {")
    labelled = set(re.findall(r"^\s*([a-z_]+):", app_js[start:app_js.index("};", start)], re.M))
    missing = [k for k in keys if k not in labelled]
    assert not missing, f"stageLabelMap'te karşılığı olmayan funnel anahtarı: {missing}"


def test_form_controls_use_the_ui_font():
    """font-family is not inherited by button/select/input, so every control in
    the app rendered in the browser's default face next to Inter body text."""
    css = open(os.path.join(REPO, "backend", "static", "style.css"), encoding="utf-8").read()
    assert re.search(r"button[^{}]*\{[^{}]*font-family:\s*inherit", css), \
        "button/input/select için font-family:inherit sıfırlaması yok"


def test_sidebar_items_are_all_built_the_same_way():
    """One nav entry was an <a> with an inline-styled svg instead of a <button>
    with a .nav-icon, so it sat further right and in a different typeface."""
    html = open(INDEX_HTML, encoding="utf-8").read()
    nav = html[html.index('<nav class="sb-nav">'):html.index("</nav>")]
    assert "<a " not in nav, "sb-nav içindeki bağlantı .nav-item düğmeleriyle hizalanmıyor"
    stray = re.findall(r'(?<!<span class="nav-icon">)<svg', nav)
    assert not stray, "nav ikonları .nav-icon içinde olmalı"


def test_a_hotel_cannot_approve_its_own_staffing_request():
    """Approving a staffing need opens a position, so it is a central decision.
    Neither the endpoint nor the table checked the role, so the hotel HR who
    filed the request could approve it themselves."""
    from auth import get_current_user
    db = TestingSessionLocal()
    hotel_id = make_hotel()
    hotel_hr = models.User(email="otelik-rg@example.com", full_name="Otel İK", hashed_password="x",
                           role="HOTEL_HR", is_active=True, hotel_access_ids=[hotel_id])
    db.add(hotel_hr); db.commit(); db.refresh(hotel_hr)
    db.close()

    app.dependency_overrides[get_current_user] = lambda: hotel_hr
    try:
        created = client.post("/api/staffing-needs/", json={
            "hotel_id": hotel_id, "position_title": "Bar Şefi", "needed_fte": 1,
            "needed_by": "2026-11-15", "priority": "normal",
        })
        assert created.status_code == 200, created.text
        need_id = created.json()["id"]

        blocked = client.put(f"/api/staffing-needs/{need_id}/approve")
        assert blocked.status_code == 403, blocked.text
        assert client.put(f"/api/staffing-needs/{need_id}/reject", json={"reason": "x"}).status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    db = TestingSessionLocal()
    central = models.User(email="merkez-rg@example.com", full_name="Merkez", hashed_password="x",
                          role="CENTRAL_HR", is_active=True)
    db.add(central); db.commit(); db.refresh(central)
    db.close()
    app.dependency_overrides[get_current_user] = lambda: central
    try:
        ok = client.put(f"/api/staffing-needs/{need_id}/approve")
        assert ok.status_code == 200, ok.text
        assert ok.json()["created_position_id"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_every_page_with_its_own_data_reloads_when_you_navigate_to_it():
    """Positions, candidates and the dashboard were only fetched at startup, so
    a position opened by approving a staffing need mid-session did not appear
    on Pozisyonlar until the browser was reloaded."""
    app_js = open(APP_JS, encoding="utf-8").read()
    start = app_js.index("watch(page, async (p) => {")
    body = app_js[start:start + 1200]
    for page_name, loader in (("dashboard", "loadDashboardStats"), ("jobs", "loadPositions"),
                              ("talent", "loadCandidates"), ("headcount", "loadHeadcount"),
                              ("staffing", "loadStaffingNeeds"), ("campaigns", "loadCampaigns"),
                              ("onboarding", "loadOnboardingBoard")):
        assert f"p === '{page_name}'" in body and loader in body, \
            f"{page_name} sayfasına geçişte {loader} çağrılmıyor"


def test_position_list_reports_how_many_applied(as_admin):
    """The Pozisyonlar table read p.applications, which /api/positions/ has
    never returned, so every row said "0 Aday" and every pipeline bar 0%."""
    db = TestingSessionLocal()
    hotel_id = make_hotel()
    pos = models.Position(title="Bar Şefi", hotel_id=hotel_id, headcount=2)
    db.add(pos); db.commit()
    pos_id = pos.id
    for i, st in enumerate(["applied", "screening", "hired"]):
        cand = models.Candidate(name=f"Aday {i}", email=f"aday{i}-pc@ornek.com")
        db.add(cand); db.commit()
        db.add(models.Application(candidate_id=cand.id, position_id=pos_id, status=st))
    db.commit(); db.close()

    row = next(p for p in client.get("/api/positions/").json() if p["id"] == pos_id)
    assert row["application_count"] == 3
    assert row["hired_count"] == 1

    app_js = open(APP_JS, encoding="utf-8").read()
    html = open(INDEX_HTML, encoding="utf-8").read()
    assert "p.applications?.length" not in html
    start = app_js.index("function positionProgress(")
    assert ".applications" not in app_js[start:start + 400]


def test_a_candidate_named_ahmet_is_not_handed_a_91_percent_match(as_admin):
    """/with-best-position stamped hardcoded showcase scores on any candidate
    whose name matched an original seed name, and persisted them to
    match_scores, so a real applicant carried a score nobody computed."""
    db = TestingSessionLocal()
    hotel_id = make_hotel()
    pos = models.Position(title="Garson", hotel_id=hotel_id, required_skills=["Servis"])
    cand = models.Candidate(name="Ahmet Yıldız", email="ahmet-rg@ornek.com", skills=[])
    db.add_all([pos, cand]); db.commit()
    cand_id = cand.id
    db.close()

    row = next(c for c in client.get("/api/candidates/with-best-position").json() if c["id"] == cand_id)
    assert row["best_score"] != 91.0, "uydurma eşleşme skoru hâlâ veriliyor"

    db = TestingSessionLocal()
    stored = db.query(models.MatchScore).filter(models.MatchScore.candidate_id == cand_id).all()
    assert not [m for m in stored if m.overall_score == 91.0]
    db.close()


def test_an_offer_awaiting_approval_does_not_offer_a_send_button():
    """/api/offers/{id}/status refuses to send an offer whose approval is still
    pending, but the offer tab showed "Taslak" and a Teklifi Gönder button that
    could only ever produce an error."""
    html = open(INDEX_HTML, encoding="utf-8").read()
    start = html.index("currentOffer.status==='draft'?'Taslak'")
    block = html[start:start + 1600]
    assert "PENDING_APPROVAL" in block, "onay bekleyen teklif için rozet yok"
    send = block.index("sendOffer()")
    guard = block[:send]
    assert "approval_status!=='REJECTED'" in guard and "approval_status==='PENDING_APPROVAL'" in guard, \
        "Gönder butonu onay durumuna bakmıyor"


def test_the_candidate_s_answer_to_an_offer_can_be_recorded(as_admin):
    """Nothing in the UI could move an offer past "Gönderildi": the accepted and
    rejected states existed in the badge and in the acceptance report, but no
    screen ever called the endpoint that sets them."""
    db = TestingSessionLocal()
    hotel_id = make_hotel()
    pos = models.Position(title="Bar Şefi", hotel_id=hotel_id)
    cand = models.Candidate(name="Teklif Adayı", email="teklif-rg@ornek.com")
    db.add_all([pos, cand]); db.commit()
    app_row = models.Application(candidate_id=cand.id, position_id=pos.id, status="offer")
    db.add(app_row); db.commit()
    offer = models.Offer(application_id=app_row.id, proposed_salary=40000,
                         status="sent", approval_status="APPROVED")
    db.add(offer); db.commit()
    offer_id, app_id = offer.id, app_row.id
    db.close()

    assert client.patch(f"/api/offers/{offer_id}/status?status=accepted").status_code == 200

    db = TestingSessionLocal()
    assert db.query(models.Offer).get(offer_id).status == "accepted"
    assert db.query(models.Application).get(app_id).status == "hired"
    db.close()

    html = open(INDEX_HTML, encoding="utf-8").read()
    assert "respondToOffer('accepted')" in html and "respondToOffer('rejected')" in html
    app_js = open(APP_JS, encoding="utf-8").read()
    assert "async function respondToOffer(" in app_js


def test_internal_endpoints_refuse_anonymous_callers():
    """Around ninety endpoints declared no auth dependency at all: POST /api/offers/
    created a job offer, DELETE /api/candidates/{id}/hard-delete erased a
    candidate and GET /api/analytics/salary-report returned the salary report,
    all without a token. POST /api/chat was worse than unauthenticated — it fed
    every candidate's name, skills and summary to the model as context, and a
    caller with no user skipped the hotel/department scoping entirely."""
    from fastapi.testclient import TestClient
    from auth import get_current_user

    saved = {k: v for k, v in app.dependency_overrides.items()}
    app.dependency_overrides.pop(get_current_user, None)
    anon = TestClient(app)
    try:
        for method, path in [
            ("post", "/api/offers/"),
            ("get", "/api/applications/"),
            ("get", "/api/candidates/with-best-position"),
            ("delete", "/api/candidates/1/hard-delete"),
            ("get", "/api/analytics/salary-report"),
            ("get", "/api/interviews/application/1"),
            ("get", "/api/onboarding/1"),
            ("post", "/api/chat"),
            ("get", "/api/positions/1"),
        ]:
            call = getattr(anon, method)
            res = call(path, json={}) if method in ("post", "put", "patch") else call(path)
            assert res.status_code == 401, f"{method.upper()} {path} kimliksiz erişime {res.status_code} döndü"

        # Aday tarafı ve sağlık ucu açık kalmalı
        assert anon.get("/health").status_code == 200
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(saved)


def test_a_position_and_its_offer_stay_inside_the_hotel_that_owns_them():
    """The position list filters by hotel_access_ids, but reading one by id did
    not, so a hotel's HR could open another hotel's posting — and with it the
    offer on that posting, salary included — just by changing the id."""
    from auth import get_current_user
    db = TestingSessionLocal()
    mine = make_hotel(name="Benim Otel", code="MINE")
    theirs = make_hotel(name="Komşu Otel", code="THRS")
    pos = models.Position(title="GİZLİ Müdür", hotel_id=theirs)
    cand = models.Candidate(name="Komşu Aday", email="komsu-rg@ornek.com")
    db.add_all([pos, cand]); db.commit()
    app_row = models.Application(candidate_id=cand.id, position_id=pos.id,
                                 hotel_id=theirs, status="offer")
    db.add(app_row); db.commit()
    db.add(models.Offer(application_id=app_row.id, position_id=pos.id, candidate_id=cand.id,
                        proposed_salary=175000, status="draft", approval_status="APPROVED"))
    hotel_hr = models.User(email="baska-otel-rg@ornek.com", full_name="Başka Otel İK",
                           hashed_password="x", role="HOTEL_HR", is_active=True,
                           data_visibility_scope="HOTEL", hotel_access_ids=[mine])
    db.add(hotel_hr); db.commit(); db.refresh(hotel_hr)
    pos_id, app_id = pos.id, app_row.id
    db.close()

    previous = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: hotel_hr
    try:
        assert client.get(f"/api/positions/{pos_id}").status_code == 404
        assert client.get(f"/api/offers/application/{app_id}").status_code == 404
        titles = [p["title"] for p in client.get("/api/positions/").json()]
        assert "GİZLİ Müdür" not in titles, "liste zaten sızdırıyor"
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = previous


def test_adding_a_candidate_from_the_position_workspace_stamps_the_hotel():
    """Every other path that creates an application copies the position's
    hotel_id; POST /api/positions/{id}/candidates did not. hotel_id is what the
    hotel filters match on, so such an application was invisible to the hotel
    that owns it — including in the offer approval queue, where an offer on it
    never reached the approver."""
    from auth import get_current_user
    db = TestingSessionLocal()
    hotel_id = make_hotel(name="Kapsam Otel", code="KPSM")
    pos = models.Position(title="Bar Şefi", hotel_id=hotel_id)
    cand = models.Candidate(name="Workspace Adayı", email="ws-rg@ornek.com")
    db.add_all([pos, cand]); db.commit()
    pos_id, cand_id = pos.id, cand.id
    hotel_hr = models.User(email="kapsam-hr@ornek.com", full_name="Kapsam İK",
                           hashed_password="x", role="HOTEL_HR", is_active=True,
                           data_visibility_scope="HOTEL", hotel_access_ids=[hotel_id])
    db.add(hotel_hr); db.commit(); db.refresh(hotel_hr)
    db.close()

    previous = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: hotel_hr
    try:
        res = client.post(f"/api/positions/{pos_id}/candidates", json={"candidate_id": cand_id})
        assert res.status_code == 200, res.text
        app_id = res.json()["id"]

        db = TestingSessionLocal()
        row = db.query(models.Application).get(app_id)
        assert row.hotel_id == hotel_id, "başvuru hangi otele ait olduğunu taşımıyor"
        db.add(models.Offer(application_id=app_id, position_id=pos_id, candidate_id=cand_id,
                            proposed_salary=52000, status="draft",
                            approval_status="PENDING_APPROVAL"))
        db.commit()
        req = models.OfferApprovalRequest(
            offer_id=db.query(models.Offer).filter_by(application_id=app_id).first().id,
            approver_role="HOTEL_HR", sequence_number=1, status="PENDING")
        db.add(req); db.commit(); db.close()

        pending = client.get("/api/offers/approvals/pending").json()
        assert any(p.get("application_id") == app_id or p.get("offer_id") for p in pending), \
            "otelin kendi teklifi onay kuyruğuna hiç düşmüyor"
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = previous


def test_one_hotel_cannot_move_or_reject_another_hotels_application():
    """An application carries its hotel's approval chain and ownership lock, but
    the status, stage, notes and delete endpoints looked it up by id alone — the
    HR of one hotel could reject another hotel's candidate outright."""
    from auth import get_current_user
    db = TestingSessionLocal()
    mine = make_hotel(name="Bizim Otel", code="BZM")
    theirs = make_hotel(name="Öteki Otel", code="OTK")
    pos = models.Position(title="Aşçı", hotel_id=theirs)
    cand = models.Candidate(name="Öteki Aday", email="oteki-rg@ornek.com")
    db.add_all([pos, cand]); db.commit()
    app_row = models.Application(candidate_id=cand.id, position_id=pos.id,
                                 hotel_id=theirs, status="applied")
    db.add(app_row); db.commit()
    app_id = app_row.id
    db.add(models.Interview(application_id=app_id, interview_type="technical",
                            status="scheduled"))
    db.commit()
    intruder = models.User(email="baska-hr2@ornek.com", full_name="Bizim İK",
                           hashed_password="x", role="HOTEL_HR", is_active=True,
                           data_visibility_scope="HOTEL", hotel_access_ids=[mine])
    db.add(intruder); db.commit(); db.refresh(intruder)
    db.close()

    previous = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: intruder
    try:
        assert client.patch(f"/api/applications/{app_id}/status",
                            json={"status": "rejected"}).status_code == 404
        assert client.patch(f"/api/applications/{app_id}/stage",
                            json={"stage": "hired"}).status_code == 404
        assert client.put(f"/api/applications/{app_id}/notes?notes=x").status_code == 404
        assert client.delete(f"/api/applications/{app_id}").status_code == 404
        assert client.get(f"/api/interviews/application/{app_id}").status_code == 404
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = previous

    db = TestingSessionLocal()
    assert db.query(models.Application).get(app_id).status == "applied", "durum yine de değişmiş"
    db.close()


def test_an_interview_row_with_nulls_does_not_500_the_whole_list(as_admin):
    """round_number, interview_type, status and duration_minutes are nullable
    columns with python-side defaults, but InterviewOut required all four, so a
    row that did not come through the ORM turned the interview list for that
    application into a 500."""
    db = TestingSessionLocal()
    hotel_id = make_hotel(name="Null Otel", code="NULO")
    pos = models.Position(title="Garson", hotel_id=hotel_id)
    cand = models.Candidate(name="Null Aday", email="null-rg@ornek.com")
    db.add_all([pos, cand]); db.commit()
    app_row = models.Application(candidate_id=cand.id, position_id=pos.id,
                                 hotel_id=hotel_id, status="applied")
    db.add(app_row); db.commit()
    app_id = app_row.id
    db.execute(text("INSERT INTO interviews (application_id, round_number, interview_type,"
                    " status, duration_minutes) VALUES (:a, NULL, NULL, NULL, NULL)"),
               {"a": app_id})
    db.commit(); db.close()

    res = client.get(f"/api/interviews/application/{app_id}")
    assert res.status_code == 200, res.text
    row = res.json()[0]
    assert row["round_number"] == 1 and row["duration_minutes"] == 60
    assert row["interview_type"] == "hr" and row["status"] == "scheduled"


def test_the_kanban_board_only_shows_the_hotels_own_candidates():
    """The candidate and position lists filter by hotel, but /pipeline — the
    board people actually work on — did not, so a hotel saw every other hotel's
    candidates on it. Dragging such a card now hits the scoped stage endpoint
    and fails, so an unscoped board would show cards that refuse to move."""
    from auth import get_current_user
    db = TestingSessionLocal()
    mine = make_hotel(name="Pano Otel", code="PANO")
    theirs = make_hotel(name="Uzak Otel", code="UZAK")
    for hotel_id, who in ((mine, "Bizim Aday"), (theirs, "Uzak Aday")):
        pos = models.Position(title=f"{who} Pozisyonu", hotel_id=hotel_id)
        cand = models.Candidate(name=who, email=f"{who.replace(' ', '')}@ornek.com")
        db.add_all([pos, cand]); db.commit()
        db.add(models.Application(candidate_id=cand.id, position_id=pos.id,
                                  hotel_id=hotel_id, status="applied"))
    db.commit()
    hotel_hr = models.User(email="pano-hr@ornek.com", full_name="Pano İK",
                           hashed_password="x", role="HOTEL_HR", is_active=True,
                           data_visibility_scope="HOTEL", hotel_access_ids=[mine])
    db.add(hotel_hr); db.commit(); db.refresh(hotel_hr)
    db.close()

    previous = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: hotel_hr
    try:
        board = client.get("/api/applications/pipeline").json()
        names = [(a.get("candidate") or {}).get("name")
                 for col in board["columns"] for a in col["applications"]]
        assert "Bizim Aday" in names
        assert "Uzak Aday" not in names, "pano başka otelin adayını gösteriyor"
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = previous


def make_department_manager(db, department_id, hotel_id, email="mudur-rg@ornek.com"):
    user = models.User(email=email, full_name="Departman Müdürü", hashed_password="x",
                       role="DEPARTMENT_MANAGER", is_active=True,
                       data_visibility_scope="DEPARTMENT",
                       hotel_access_ids=[hotel_id], department_access_ids=[department_id])
    db.add(user); db.commit(); db.refresh(user)
    return user


def test_a_department_manager_sees_their_own_department_and_only_that():
    """Three separate problems met here. The candidate pool came back EMPTY for a
    department manager — apply_candidate_scope joined Candidate straight to
    Position, which has no path to follow, so the filter matched nothing while
    their board showed cards. Headcount and the staffing-need list, meanwhile,
    showed every department: the hotel restriction had no department counterpart."""
    from auth import get_current_user
    db = TestingSessionLocal()
    hotel_id = make_hotel(name="Müdür Otel", code="MDR")
    mine = models.Department(name="Mutfak", code="KITCHEN-RG")
    theirs = models.Department(name="Ön Büro", code="FRONT-RG")
    db.add_all([mine, theirs]); db.commit()

    for dept, who in ((mine, "Aşçı"), (theirs, "Resepsiyonist")):
        pos = models.Position(title=who, hotel_id=hotel_id, department_id=dept.id,
                              department=dept.name)
        cand = models.Candidate(name=f"{who} Adayı", email=f"{who}-rg@ornek.com")
        db.add_all([pos, cand]); db.commit()
        db.add(models.Application(candidate_id=cand.id, position_id=pos.id,
                                  hotel_id=hotel_id, status="applied"))
        db.add(models.StaffingNeed(hotel_id=hotel_id, department_id=dept.id,
                                   position_title=who, needed_fte=1, status="pending"))
    db.commit()
    manager = make_department_manager(db, mine.id, hotel_id)
    mine_name, theirs_name = mine.name, theirs.name
    db.close()

    previous = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: manager
    try:
        pool = client.get("/api/candidates/with-best-position").json()
        names = [c["name"] for c in pool]
        assert "Aşçı Adayı" in names, "kendi departmanının adayını göremiyor"
        assert "Resepsiyonist Adayı" not in names

        titles = [p["title"] for p in client.get("/api/positions/").json()]
        assert titles == ["Aşçı"], titles

        board = client.get("/api/applications/pipeline").json()
        depts = {(a.get("position") or {}).get("department")
                 for col in board["columns"] for a in col["applications"]}
        assert depts <= {mine_name}, depts

        needs = client.get("/api/staffing-needs/").json()
        assert [n["position_title"] for n in needs] == ["Aşçı"], needs
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = previous


def test_a_department_manager_cannot_ask_for_another_departments_headcount():
    """/api/headcount/summary pinned the hotel for a HOTEL-scoped user but had no
    department counterpart, so a department manager read every department's
    headcount — and could name someone else's department outright."""
    from auth import get_current_user
    db = TestingSessionLocal()
    hotel_id = make_hotel(name="Kadro Otel", code="KDR")
    hotel = db.query(models.Hotel).get(hotel_id)
    mine = models.Department(name="Mutfak", code="KITCHEN-HC")
    theirs = models.Department(name="Kat Hizmetleri", code="HK-HC")
    db.add_all([mine, theirs]); db.commit()
    for dept, title in ((mine, "Aşçı"), (theirs, "Kat Görevlisi")):
        db.add(models.WorkforceBudgetRecord(hotel_code=hotel.code, department=dept.name,
                                            position_title=title, month_of_year=8,
                                            total_fte=3))
    db.commit()
    manager = make_department_manager(db, mine.id, hotel_id, email="kadro-mudur@ornek.com")
    db.close()

    previous = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: manager
    try:
        rows = client.get("/api/headcount/summary?month=8").json()["rows"]
        assert {r["department"] for r in rows} == {"Mutfak"}, rows
        denied = client.get("/api/headcount/summary?month=8&department=Kat Hizmetleri")
        assert denied.status_code == 403, denied.text
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = previous


def test_picking_a_department_from_the_headcount_filter_actually_filters(as_admin):
    """The dropdown was filled from the Department table while the rows keep the
    spelling the imported sheet used, and the importer matches departments
    case-insensitively — so a table holding "Mutfak" next to a sheet saying
    "MUTFAK" produced an option that returned nothing, and people filtered by
    typing into the search box instead."""
    db = TestingSessionLocal()
    hotel_id = make_hotel(name="Filtre Otel", code="FLT")
    code = db.query(models.Hotel).get(hotel_id).code
    db.add(models.Department(name="Mutfak", code="KITCHEN-F"))
    db.add(models.Department(name="Ön Büro", code="FRONT-F"))
    # Sheet spelling deliberately differs from the table's.
    for dept, title in (("MUTFAK", "Aşçı"), ("Ön Büro", "Resepsiyonist")):
        db.add(models.WorkforceBudgetRecord(hotel_code=code, department=dept,
                                            position_title=title, month_of_year=8,
                                            total_fte=2))
    db.commit(); db.close()

    body = client.get(f"/api/headcount/summary?month=8&hotel_id={hotel_id}").json()
    offered = body["available_departments"]
    assert offered, "filtreye gelecek departman listesi boş"

    for name in offered:
        rows = client.get(f"/api/headcount/summary?month=8&hotel_id={hotel_id}",
                          params={"department": name}).json()["rows"]
        assert rows, f"listedeki '{name}' seçeneği hiç satır döndürmüyor"

    # Turkish names must survive the fold: SQLite's lower() leaves Ö and İ alone.
    for spelling in ("Mutfak", "mutfak", "MUTFAK", "ön büro", "ÖN BÜRO"):
        rows = client.get(f"/api/headcount/summary?month=8&hotel_id={hotel_id}",
                          params={"department": spelling}).json()["rows"]
        assert rows, f"'{spelling}' yazımı eşleşmiyor"


def test_a_department_manager_can_be_assigned_from_the_user_form(as_admin):
    """The backend scoped on data_visibility_scope and department_access_ids all
    along, but no screen ever sent them and the schemas dropped them, so a
    department manager could only be wired up with SQL."""
    db = TestingSessionLocal()
    dept = models.Department(name="Mutfak", code="KITCHEN-U")
    db.add(dept); db.commit()
    dept_id = dept.id
    db.close()

    created = client.post("/api/users/", json={
        "email": "mudur-form@ornek.com", "full_name": "Mutfak Müdürü",
        "password": "Mudur1234!", "role": "DEPARTMENT_MANAGER",
        "data_visibility_scope": "DEPARTMENT", "department_access_ids": [dept_id],
        "hotel_access_ids": [],
    })
    assert created.status_code == 201, created.text
    user_id = created.json()["id"]

    db = TestingSessionLocal()
    saved = db.query(models.User).get(user_id)
    assert saved.data_visibility_scope == "DEPARTMENT"
    assert saved.department_access_ids == [dept_id]
    db.close()

    # A scope with nothing selected would show nothing at all.
    empty = client.post("/api/users/", json={
        "email": "bos-kapsam@ornek.com", "full_name": "Kapsamsız",
        "password": "x", "role": "DEPARTMENT_MANAGER",
        "data_visibility_scope": "DEPARTMENT", "department_access_ids": [],
    })
    assert empty.status_code == 400, empty.text

    assert client.put(f"/api/users/{user_id}", json={
        "data_visibility_scope": "GLOBAL", "department_access_ids": [],
    }).status_code == 200
    db = TestingSessionLocal()
    assert db.query(models.User).get(user_id).data_visibility_scope == "GLOBAL"
    db.close()

    html = open(INDEX_HTML, encoding="utf-8").read()
    assert html.count("data_visibility_scope") >= 4, "kapsam alanı iki kullanıcı formunda da yok"
    assert "department_access_ids" in html


def test_an_offer_and_its_onboarding_stay_with_the_hotel_that_owns_the_application():
    """The rest of the offer and onboarding endpoints took an id and nothing
    else: one hotel could raise an offer on another hotel's application, mark
    that offer accepted — which hires the candidate — read its salary band, and
    generate or tick off the new hire's onboarding checklist."""
    from auth import get_current_user
    db = TestingSessionLocal()
    mine = make_hotel(name="Teklif Otel", code="TKF")
    theirs = make_hotel(name="Komşu Teklif", code="KTK")
    pos = models.Position(title="Bar Şefi", hotel_id=theirs)
    cand = models.Candidate(name="Komşu Teklif Adayı", email="kt-rg@ornek.com")
    db.add_all([pos, cand]); db.commit()
    app_row = models.Application(candidate_id=cand.id, position_id=pos.id,
                                 hotel_id=theirs, status="offer")
    db.add(app_row); db.commit()
    offer = models.Offer(application_id=app_row.id, position_id=pos.id,
                         candidate_id=cand.id, proposed_salary=90000,
                         status="sent", approval_status="APPROVED")
    db.add(offer); db.commit()
    task = models.OnboardingTask(application_id=app_row.id, title="SGK bildirimi",
                                 status="pending")
    db.add(task); db.commit()
    intruder = models.User(email="teklif-hr@ornek.com", full_name="Teklif İK",
                           hashed_password="x", role="HOTEL_HR", is_active=True,
                           data_visibility_scope="HOTEL", hotel_access_ids=[mine])
    db.add(intruder); db.commit(); db.refresh(intruder)
    app_id, offer_id, task_id = app_row.id, offer.id, task.id
    db.close()

    previous = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: intruder
    try:
        assert client.post("/api/offers/", json={
            "application_id": app_id, "proposed_salary": 1, "currency": "TRY",
        }).status_code == 404
        assert client.get(f"/api/offers/{offer_id}/salary-check").status_code == 404
        assert client.patch(f"/api/offers/{offer_id}/status?status=accepted").status_code == 404
        assert client.post(f"/api/offers/{offer_id}/generate-letter").status_code == 404
        assert client.get(f"/api/onboarding/{app_id}").status_code == 404
        assert client.post(f"/api/onboarding/{app_id}/generate").status_code == 404
        assert client.patch(f"/api/onboarding/task/{task_id}?status=completed").status_code == 404
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = previous

    db = TestingSessionLocal()
    assert db.query(models.Offer).get(offer_id).status == "sent", "teklif yine de değişmiş"
    assert db.query(models.Application).get(app_id).status == "offer", "aday yine de işe alınmış"
    assert db.query(models.OnboardingTask).get(task_id).status == "pending"
    db.close()


def test_the_position_workspace_and_interview_edits_stay_inside_the_hotel():
    """What was left after the offer and onboarding round: the position
    workspace, its candidate and match lists, the interview answers on an
    application, and editing or deleting an interview outright."""
    from auth import get_current_user
    db = TestingSessionLocal()
    mine = make_hotel(name="Son Otel", code="SON")
    theirs = make_hotel(name="Son Komşu", code="SNK")
    pos = models.Position(title="Aşçı", hotel_id=theirs)
    cand = models.Candidate(name="Son Aday", email="son-rg@ornek.com")
    db.add_all([pos, cand]); db.commit()
    app_row = models.Application(candidate_id=cand.id, position_id=pos.id,
                                 hotel_id=theirs, status="applied")
    db.add(app_row); db.commit()
    iv = models.Interview(application_id=app_row.id, interview_type="technical",
                          status="scheduled", round_number=1)
    db.add(iv); db.commit()
    intruder = models.User(email="son-hr@ornek.com", full_name="Son İK",
                           hashed_password="x", role="HOTEL_HR", is_active=True,
                           data_visibility_scope="HOTEL", hotel_access_ids=[mine])
    db.add(intruder); db.commit(); db.refresh(intruder)
    pos_id, app_id, iv_id = pos.id, app_row.id, iv.id
    db.close()

    previous = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: intruder
    try:
        for path in (f"/api/positions/{pos_id}/candidates",
                     f"/api/positions/{pos_id}/matches",
                     f"/api/positions/{pos_id}/workspace",
                     f"/api/applications/{app_id}/interviews"):
            assert client.get(path).status_code == 404, path
        assert client.patch(f"/api/interviews/{iv_id}", json={"status": "completed"}).status_code == 404
        assert client.delete(f"/api/interviews/{iv_id}").status_code == 404
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = previous

    db = TestingSessionLocal()
    survivor = db.query(models.Interview).get(iv_id)
    assert survivor is not None and survivor.status == "scheduled", "mülakat yine de değişmiş/silinmiş"
    db.close()


def test_a_hotel_can_only_act_on_a_candidate_that_applied_to_it():
    """Reading a candidate is open across hotels by design — the pool is shared
    and another hotel's lock only masks the record. Acting on one was open too:
    any hotel could blacklist, rate or delete a candidate that had never applied
    to them."""
    from auth import get_current_user
    db = TestingSessionLocal()
    mine = make_hotel(name="Eylem Otel", code="EYL")
    theirs = make_hotel(name="Eylem Komşu", code="EYK")
    pos = models.Position(title="Aşçı", hotel_id=theirs)
    stranger = models.Candidate(name="Yabancı Aday", email="yabanci-rg@ornek.com")
    ours = models.Candidate(name="Bizim Aday", email="bizim-rg@ornek.com")
    db.add_all([pos, stranger, ours]); db.commit()
    db.add(models.Application(candidate_id=stranger.id, position_id=pos.id,
                              hotel_id=theirs, status="applied"))
    mine_pos = models.Position(title="Garson", hotel_id=mine)
    db.add(mine_pos); db.commit()
    db.add(models.Application(candidate_id=ours.id, position_id=mine_pos.id,
                              hotel_id=mine, status="applied"))
    db.commit()
    hotel_hr = models.User(email="eylem-hr@ornek.com", full_name="Eylem İK",
                           hashed_password="x", role="HOTEL_HR", is_active=True,
                           data_visibility_scope="HOTEL", hotel_access_ids=[mine])
    db.add(hotel_hr); db.commit(); db.refresh(hotel_hr)
    stranger_id, ours_id = stranger.id, ours.id
    db.close()

    previous = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: hotel_hr
    try:
        # Okumak serbest - ortak havuz tasarımı
        assert client.get(f"/api/candidates/{stranger_id}").status_code == 200

        # Ama üzerinde işlem yapmak değil
        assert client.post(f"/api/candidates/{stranger_id}/blacklist",
                           json={"reason": "x"}).status_code == 403
        assert client.patch(f"/api/candidates/{stranger_id}/rating",
                            json={"rating": 1}).status_code == 403
        assert client.delete(f"/api/candidates/{stranger_id}").status_code == 403

        # Kendi otelinin adayında sorun yok
        assert client.patch(f"/api/candidates/{ours_id}/rating",
                            json={"rating": 4}).status_code == 200
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = previous

    db = TestingSessionLocal()
    left_alone = db.query(models.Candidate).get(stranger_id)
    assert not left_alone.is_blacklisted and not left_alone.is_deleted
    db.close()


def test_an_expired_ownership_returns_the_candidate_to_the_pool():
    """The release marked the application "rejected" — the candidate was
    eliminated because HR had been slow — while the note it wrote beside it said
    "Ortak havuza aktarıldı". The lock is what expires, not the application."""
    import datetime
    from auth import get_current_user
    db = TestingSessionLocal()
    hotel_id = make_hotel(name="Kilit Otel", code="KLT")
    pos = models.Position(title="Garson", hotel_id=hotel_id)
    cand = models.Candidate(name="Kilitli Aday", email="kilit-rg@ornek.com")
    db.add_all([pos, cand]); db.commit()
    app_row = models.Application(
        candidate_id=cand.id, position_id=pos.id, hotel_id=hotel_id,
        status="screening", lock_status="LOCKED",
        ownership_expires_at=datetime.datetime.utcnow() - datetime.timedelta(days=1))
    db.add(app_row); db.commit()
    app_id = app_row.id
    db.close()

    from services.ownership_service import check_and_release_expired_ownerships
    db = TestingSessionLocal()
    check_and_release_expired_ownerships(db)
    db.close()

    db = TestingSessionLocal()
    released = db.query(models.Application).get(app_id)
    assert released.lock_status == "UNLOCKED"
    assert released.status == "screening", "süre dolunca aday elenmiş"
    assert released.ownership_expires_at is None
    note = (released.status_history or [])[-1]
    assert "havuza" in note["note"].lower()
    db.close()


def test_approving_two_and_a_half_fte_does_not_lose_the_half():
    """headcount was an integer and the approval did int(needed_fte), so a 2.5
    FTE request opened a position for 2 — half a post quietly dropped, and
    across sixteen hotels that adds up."""
    from auth import get_current_user
    db = TestingSessionLocal()
    hotel_id = make_hotel(name="FTE Otel", code="FTE")
    central = models.User(email="fte-merkez@ornek.com", full_name="Merkez",
                          hashed_password="x", role="CENTRAL_HR", is_active=True,
                          data_visibility_scope="GLOBAL")
    db.add(central); db.commit(); db.refresh(central)
    db.close()

    previous = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: central
    try:
        created = client.post("/api/staffing-needs/", json={
            "hotel_id": hotel_id, "position_title": "Garson",
            "needed_fte": 2.5, "priority": "normal",
        })
        assert created.status_code == 200, created.text
        approved = client.put(f"/api/staffing-needs/{created.json()['id']}/approve")
        assert approved.status_code == 200, approved.text
        pos_id = approved.json()["created_position_id"]
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = previous

    db = TestingSessionLocal()
    assert db.query(models.Position).get(pos_id).headcount == 2.5
    db.close()

    app_js = open(APP_JS, encoding="utf-8").read()
    html = open(INDEX_HTML, encoding="utf-8").read()
    assert "function fte(" in app_js, "ondalık FTE için biçimlendirici yok"
    assert "{{ p.headcount }}" not in html, "FTE ham basılıyor, 2.5 olarak görünür"


def test_importing_salary_policies_updates_instead_of_wiping(as_admin):
    """The import deleted every policy before reading the file, so one wrong or
    partial spreadsheet erased all the salary bands — and the bands are what
    trips the offer approval chain, so the loss stayed silent until someone
    made an offer."""
    import io as _io
    from openpyxl import Workbook

    db = TestingSessionLocal()
    hotel_id = make_hotel(name="Bant Otel", code="BNT")
    hotel_name = db.query(models.Hotel).get(hotel_id).name
    db.add(models.SalaryPolicy(hotel_id=hotel_id, position_title="Garson",
                               min_salary=30000, target_salary=33000, max_salary=36000,
                               currency="TRY", is_active=True))
    db.add(models.SalaryPolicy(hotel_id=hotel_id, position_title="Dokunulmayan",
                               min_salary=1, target_salary=2, max_salary=3,
                               currency="TRY", is_active=True))
    db.commit(); db.close()

    wb = Workbook()
    ws = wb.active
    ws.append(["Otel", "Pozisyon", "Min Maaş", "Hedef Maaş", "Max Maaş"])
    ws.append([hotel_name, "Garson", 32000, 35000, 38000])
    ws.append([hotel_name, "Komi", 28000, 30000, 33000])
    buf = _io.BytesIO(); wb.save(buf); buf.seek(0)

    res = client.post("/api/settings/salary-policy/import",
                      files={"file": ("bant.xlsx", buf.read(),
                                      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert res.status_code == 200, res.text

    db = TestingSessionLocal()
    titles = {p.position_title: p for p in db.query(models.SalaryPolicy).all()}
    assert "Dokunulmayan" in titles, "dosyada olmayan politika silinmiş"
    assert titles["Garson"].max_salary == 38000, "mevcut politika güncellenmemiş"
    assert "Komi" in titles, "yeni politika eklenmemiş"
    assert len([p for p in db.query(models.SalaryPolicy).all() if p.position_title == "Garson"]) == 1, \
        "aynı politika iki kez yazılmış"
    db.close()
def test_every_application_gets_a_ten_day_evaluation_deadline(as_admin):
    """IMPLEMENTATION_STATUS.md ticked the 10-day evaluation counter as done, but
    evaluation_deadline was never written or read anywhere — an empty column."""
    import datetime
    db = TestingSessionLocal()
    hotel_id = make_hotel(name="Sayaç Otel", code="SYC")
    pos = models.Position(title="Garson", hotel_id=hotel_id)
    cand = models.Candidate(name="Sayaç Adayı", email="sayac-rg@ornek.com")
    db.add_all([pos, cand]); db.commit()
    fresh = models.Application(candidate_id=cand.id, position_id=pos.id,
                               hotel_id=hotel_id, status="applied")
    db.add(fresh); db.commit()
    app_id = fresh.id
    assert fresh.evaluation_deadline is not None, "sayaç hiç kurulmuyor"
    days = (fresh.evaluation_deadline.replace(tzinfo=None) - datetime.datetime.utcnow()).days
    assert 9 <= days <= 10, days
    db.close()

    board = client.get("/api/applications/pipeline").json()
    row = next(a for col in board["columns"] for a in col["applications"] if a["id"] == app_id)
    assert row["evaluation_deadline"], "pano sayacı taşımıyor, rozet çizilemez"

    app_js = open(APP_JS, encoding="utf-8").read()
    html = open(INDEX_HTML, encoding="utf-8").read()
    assert "function evaluationOverdue(" in app_js
    assert "evaluationOverdue(app)" in html


def test_email_is_wired_but_a_missing_smtp_never_breaks_the_flow(as_admin):
    """email_service.py existed but nothing imported it and fastapi_mail was not
    installed, so the app sent nothing, ever. Now two events send — and because
    SMTP is unset on most installs, a send that cannot happen must not take the
    application or the offer down with it."""
    from services import email_service

    assert email_service.is_configured() is False
    assert email_service.fast_mail is None, "SMTP yokken istemci kurulmamalı"

    import asyncio
    sent = asyncio.get_event_loop().run_until_complete(
        email_service.send_email(["x@ornek.com"], "konu", "<p>gövde</p>"))
    assert sent is False, "SMTP yokken gönderildi diye raporlamamalı"

    portal = open(os.path.join(REPO, "backend", "routers", "portal.py"), encoding="utf-8").read()
    offers = open(os.path.join(REPO, "backend", "routers", "offers.py"), encoding="utf-8").read()
    assert "send_status_update" in portal, "başvuru alındı bildirimi bağlı değil"
    assert "send_offer_notification" in offers, "teklif bildirimi bağlı değil"
    assert "BackgroundTasks" in offers, "teklif e-postası isteği bekletmemeli"

    reqs = open(os.path.join(REPO, "requirements.txt"), encoding="utf-8").read()
    assert "fastapi-mail" in reqs


def test_reports_are_scoped_the_same_way_the_screens_are():
    """The screens were scoped but analytics was not: a department manager whose
    board showed one position and nine candidates read 65 candidates, six
    positions, every hotel's funnel and the whole chain's salary report."""
    from auth import get_current_user
    db = TestingSessionLocal()
    hotel_id = make_hotel(name="Rapor Otel", code="RPR")
    mine = models.Department(name="Mutfak", code="KITCHEN-A")
    theirs = models.Department(name="Ön Büro", code="FRONT-A")
    db.add_all([mine, theirs]); db.commit()
    for dept, title in ((mine, "Aşçı"), (theirs, "Resepsiyonist")):
        pos = models.Position(title=title, hotel_id=hotel_id, department_id=dept.id,
                              department=dept.name, is_active=True)
        cand = models.Candidate(name=f"{title} Adayı", email=f"{title}-an@ornek.com")
        db.add_all([pos, cand]); db.commit()
        app_row = models.Application(candidate_id=cand.id, position_id=pos.id,
                                     hotel_id=hotel_id, status="hired")
        db.add(app_row); db.commit()
        db.add(models.Offer(application_id=app_row.id, position_id=pos.id,
                            candidate_id=cand.id, proposed_salary=40000, status="accepted"))
        db.add(models.SalaryPolicy(hotel_id=hotel_id, department_id=dept.id,
                                   position_title=title, min_salary=1, target_salary=2,
                                   max_salary=3, currency="TRY", is_active=True))
    db.commit()
    manager = make_department_manager(db, mine.id, hotel_id, email="rapor-mudur@ornek.com")
    db.close()

    previous = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: manager
    try:
        stats = client.get("/api/analytics/stats?date_range=all").json()
        assert stats["total_positions"] == 1, stats["total_positions"]
        assert stats["total_candidates"] == 1, stats["total_candidates"]

        board = client.get("/api/analytics/dashboard-stats").json()
        depts = {p.get("department") for p in board.get("active_positions") or []}
        assert depts == {"Mutfak"}, depts

        assert client.get("/api/analytics/funnel").json()["hired"] == 1

        salary = client.get("/api/analytics/salary-report").json()
        titles = {b["position"] for b in salary.get("policy_benchmarks") or []}
        assert titles == {"Aşçı"}, titles
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = previous


def test_a_user_is_linked_to_the_permissions_their_role_defines(as_admin):
    """The roles table carries a real permission matrix — CENTRAL_HR may open
    settings, HOTEL_HR may blacklist but not, DEPARTMENT_MANAGER neither — and
    check_permission reads it through user.role_id. Only the seeded demo admin
    ever had role_id set, so every other user fell through to 403 no matter
    what their own role said. The matrix applied to nobody."""
    from auth import get_current_user, check_permission
    db = TestingSessionLocal()
    db.add(models.Role(code="CENTRAL_HR", name="Merkez İK",
                       permissions={"can_access_settings": True, "can_approve_offers": True}))
    db.add(models.Role(code="HOTEL_HR", name="Otel İK",
                       permissions={"can_access_settings": False, "can_blacklist": True}))
    db.commit(); db.close()

    central = client.post("/api/users/", json={
        "email": "merkez-izin@ornek.com", "full_name": "Merkez İK",
        "password": "x", "role": "CENTRAL_HR",
    })
    hotel = client.post("/api/users/", json={
        "email": "otel-izin@ornek.com", "full_name": "Otel İK",
        "password": "x", "role": "HOTEL_HR",
    })
    assert central.status_code == 201 and hotel.status_code == 201

    db = TestingSessionLocal()
    central_user = db.query(models.User).get(central.json()["id"])
    hotel_user = db.query(models.User).get(hotel.json()["id"])
    assert central_user.role_id is not None, "kullanıcı izin matrisine bağlanmıyor"
    assert hotel_user.role_id is not None

    checker = check_permission("can_access_settings")
    assert checker(current_user=central_user, db=db) is central_user
    with pytest.raises(HTTPException) as denied:
        checker(current_user=hotel_user, db=db)
    assert denied.value.status_code == 403
    db.close()
