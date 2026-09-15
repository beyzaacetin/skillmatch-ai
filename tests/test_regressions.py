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
from sqlalchemy import create_engine
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
    org = models.Organization(name="Test Org", code="TORG")
    country = models.Country(name="Türkiye")
    db.add_all([org, country])
    db.commit()
    city = models.City(name="Antalya", country_id=country.id)
    db.add(city)
    db.commit()
    region = models.Region(name="Akdeniz", city_id=city.id)
    db.add(region)
    db.commit()
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
