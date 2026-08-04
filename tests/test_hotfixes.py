import sys
from unittest.mock import MagicMock
sys.modules['sentence_transformers'] = MagicMock()

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# Ensure backend folder is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from database import Base, get_db
from main import app
import models
from config import settings
from services.llm_matcher import extract_and_parse_json, validate_llm_data, llm_matcher_service
from services.semantic_matcher import semantic_matcher

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_temp.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    # Remove existing if any
    if os.path.exists("test_temp.db"):
        try: os.remove("test_temp.db")
        except: pass
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up test database file after all tests complete
    if os.path.exists("test_temp.db"):
        try: os.remove("test_temp.db")
        except: pass

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    # Clean tables before each test
    db = TestingSessionLocal()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    db.close()

def test_delete_candidate_with_match_scores():
    from auth import get_current_user
    db = TestingSessionLocal()
    
    test_user = models.User(
        email="admin_delete@example.com",
        full_name="admin",
        hashed_password="mocked_password",
        role="ADMIN",
        is_active=True
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    def mock_get_current_user():
        return test_user
        
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    try:
        # Create candidate
        candidate = models.Candidate(
            name="John Doe",
            email="john@example.com",
            skills=["Python"],
            experience=[]
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        
        # Create position
        position = models.Position(
            title="Python Developer",
            description="Write Python code",
            required_skills=["Python"]
        )
        db.add(position)
        db.commit()
        db.refresh(position)
        
        # Create match score
        match_score = models.MatchScore(
            candidate_id=candidate.id,
            position_id=position.id,
            overall_score=85.0,
            llm_model=settings.GEMINI_MODEL
        )
        db.add(match_score)
        db.commit()
        
        # Try soft deleting via API
        response = client.delete(f"/api/candidates/{candidate.id}")
        assert response.status_code == 200
        
        # Verify candidate is soft deleted
        db.refresh(candidate)
        assert candidate.is_deleted is True
        assert candidate.deleted_at is not None
        assert candidate.deleted_by == "admin"
        
        # Verify candidate does not show up in listing
        get_response = client.get("/api/candidates/")
        assert get_response.status_code == 200
        candidates_list = get_response.json()
        assert len(candidates_list) == 0
    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        db.close()

def test_restore_candidate():
    db = TestingSessionLocal()
    candidate = models.Candidate(
        name="Alice Smith",
        is_deleted=True,
        deleted_at=None,
        deleted_by="admin"
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    
    # Restore candidate
    response = client.put(f"/api/candidates/{candidate.id}/restore")
    assert response.status_code == 200
    assert response.json()["ok"] is True
    
    # Verify restored
    db.refresh(candidate)
    assert candidate.is_deleted is False
    assert candidate.deleted_at is None
    assert candidate.deleted_by is None
    
    db.close()

def test_hard_delete_candidate():
    db = TestingSessionLocal()
    candidate = models.Candidate(
        name="Bob Johnson",
        skills=["Java"]
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    
    position = models.Position(
        title="Java Developer",
        description="Java"
    )
    db.add(position)
    db.commit()
    db.refresh(position)
    
    match_score = models.MatchScore(
        candidate_id=candidate.id,
        position_id=position.id,
        overall_score=90.0
    )
    db.add(match_score)
    
    application = models.Application(
        candidate_id=candidate.id,
        position_id=position.id,
        status="applied"
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    
    interview = models.Interview(
        application_id=application.id,
        status="scheduled"
    )
    db.add(interview)
    
    onboarding_task = models.OnboardingTask(
        application_id=application.id,
        title="Check papers",
        status="pending"
    )
    db.add(onboarding_task)
    db.commit()
    app_id = application.id
    # Hard delete
    response = client.delete(f"/api/candidates/{candidate.id}/hard-delete")
    assert response.status_code == 200
    
    # Verify completely deleted from database
    c_in_db = db.query(models.Candidate).filter(models.Candidate.id == candidate.id).first()
    assert c_in_db is None
    
    # Verify related entities deleted
    ms_in_db = db.query(models.MatchScore).filter(models.MatchScore.candidate_id == candidate.id).all()
    assert len(ms_in_db) == 0
    
    apps_in_db = db.query(models.Application).filter(models.Application.candidate_id == candidate.id).all()
    assert len(apps_in_db) == 0
    
    tasks_in_db = db.query(models.OnboardingTask).filter(models.OnboardingTask.application_id == app_id).all()
    assert len(tasks_in_db) == 0
    
    db.close()

def test_llm_matcher_json_parsing():
    # Test valid json with markdown fences
    raw_text = "```json\n{\n  \"overall_score\": 90,\n  \"decision\": \"strong_match\"\n}\n```"
    parsed = extract_and_parse_json(raw_text)
    assert parsed["overall_score"] == 90
    assert parsed["decision"] == "strong_match"
    
    # Test trailing commas
    raw_text_trailing = '{"overall_score": 85, "decision": "potential_match", "matching_skills": ["Python",],}'
    parsed_trailing = extract_and_parse_json(raw_text_trailing)
    assert parsed_trailing["overall_score"] == 85
    assert parsed_trailing["decision"] == "potential_match"
    assert parsed_trailing["matching_skills"] == ["Python"]
    
    # Test validation
    validated = validate_llm_data(parsed_trailing)
    assert validated["overall_score"] == 85.0
    assert validated["decision"] == "potential_match"
    assert validated["education_score"] == 50.0 # Default value
    
    # Test missing overall_score raises ValueError
    invalid_data = {"decision": "strong_match"}
    with pytest.raises(ValueError):
        validate_llm_data(invalid_data)

def test_invalid_gemini_response_fallback(monkeypatch):
    db = TestingSessionLocal()
    
    candidate = models.Candidate(
        name="Test Candidate",
        skills=["Python"],
        experience=[]
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    
    position = models.Position(
        title="Test Position",
        description="Test description",
        required_skills=["Python"]
    )
    db.add(position)
    db.commit()
    db.refresh(position)
    
    # Mock model generation to raise exception
    class MockModel:
        def generate_content(self, prompt):
            raise Exception("Gemini Quota Exceeded")
            
    # Enable API_KEY and mock model call
    monkeypatch.setattr("services.llm_matcher.API_KEY", "dummy_key")
    monkeypatch.setattr("google.generativeai.GenerativeModel", lambda *args, **kwargs: MockModel())
    
    # Perform match
    match_score = llm_matcher_service.match_candidate_position(candidate.id, position.id, db, force_recalculate=True)
    
    # Verify it completed with fallback
    assert match_score.llm_model == "rule-fallback"
    assert match_score.overall_score is not None
    assert match_score.decision in ["strong_match", "potential_match", "weak_match", "not_match"]
    
    db.close()

def test_repeated_matching_cached_score(monkeypatch):
    db = TestingSessionLocal()
    
    candidate = models.Candidate(
        name="Test Candidate 2",
        skills=["Python"],
        experience=[]
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    
    position = models.Position(
        title="Test Position 2",
        description="Test description 2",
        required_skills=["Python"]
    )
    db.add(position)
    db.commit()
    db.refresh(position)
    
    # Pre-save a cached score
    cached_score = models.MatchScore(
        candidate_id=candidate.id,
        position_id=position.id,
        overall_score=78.5,
        llm_model="rule-fallback"
    )
    db.add(cached_score)
    db.commit()
    
    # Mock semantic matcher to track calls
    call_count = 0
    def mock_semantic_score(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return 50.0
        
    monkeypatch.setattr(semantic_matcher, "calculate_semantic_score", mock_semantic_score)
    monkeypatch.setattr("services.llm_matcher.API_KEY", None) # Force fallback path if called
    
    # Fetch matches
    response = client.get(f"/api/positions/{position.id}/matches")
    assert response.status_code == 200
    
    # Verify cached score is returned and semantic matcher was NOT called
    assert call_count == 0
    matches = response.json()
    assert len(matches) == 1
    assert matches[0]["score"] == 78.5
    
    db.close()


def test_dashboard_stats():
    from auth import get_current_user
    db = TestingSessionLocal()
    
    test_user = models.User(
        email="test_sule@example.com",
        full_name="Şule Sıray",
        hashed_password="mocked_password",
        role="ADMIN",
        is_active=True
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    org = models.Organization(name="Rixos")
    db.add(org)
    db.commit()
    db.refresh(org)
    
    country = models.Country(name="Türkiye")
    db.add(country)
    db.commit()
    db.refresh(country)
    
    city = models.City(country_id=country.id, name="Antalya")
    db.add(city)
    db.commit()
    db.refresh(city)
    
    region = models.Region(city_id=city.id, name="Akdeniz")
    db.add(region)
    db.commit()
    db.refresh(region)
    
    hotel = models.Hotel(organization_id=org.id, city_id=city.id, region_id=region.id, name="Rixos Premium Belek", is_active=True)
    db.add(hotel)
    db.commit()
    db.refresh(hotel)
    
    dept = models.Department(name="Yiyecek & İçecek")
    db.add(dept)
    db.commit()
    db.refresh(dept)
    
    budget = models.WorkforceHeadcountBudget(
        hotel_id=hotel.id,
        department_id=dept.id,
        position_title="Garson",
        headcount_budget=10
    )
    db.add(budget)
    db.commit()

    def mock_get_current_user():
        return test_user
        
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    try:
        response = client.get("/api/analytics/dashboard-stats")
        assert response.status_code == 200
        data = response.json()
        assert data["user_name"] == "Şule Sıray"
        assert len(data["active_positions"]) > 0
        assert len(data["action_items"]) > 0
    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        db.close()


def test_dashboard_settings():
    from auth import get_current_user
    db = TestingSessionLocal()
    
    test_user = models.User(
        email="test_settings_user@example.com",
        full_name="Fatma Güler",
        hashed_password="mocked_password",
        role="RECRUITER",
        is_active=True
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    def mock_get_current_user():
        return test_user
        
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    try:
        # 1. GET default settings
        res = client.get("/api/analytics/dashboard-settings")
        assert res.status_code == 200
        data = res.json()
        assert data["preset"] == "operation"
        assert data["widgets"]["assistant"] is True

        # 2. POST custom settings
        payload = {
            "preset": "manager",
            "widgets": {
                "assistant": True,
                "schedule": False,
                "positions": True,
                "candidates": False,
                "actions": True,
                "recent_activities": True
            },
            "rules": {
                "default_for_role": False,
                "keep_actions_top": False,
                "hide_empty_widgets": True
            }
        }
        res_post = client.post("/api/analytics/dashboard-settings", json=payload)
        assert res_post.status_code == 200
        
        # 3. GET custom settings again
        res_get = client.get("/api/analytics/dashboard-settings")
        assert res_get.status_code == 200
        data_get = res_get.json()
        assert data_get["preset"] == "manager"
        assert data_get["widgets"]["schedule"] is False
    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        db.close()


def test_audit_logging():
    db = TestingSessionLocal()
    
    # 1. Direct logging test
    test_user = models.User(
        email="test_audit_user@example.com",
        full_name="Audit Tester",
        hashed_password="mocked_password",
        role="ADMIN",
        is_active=True
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    from services.audit_service import audit_service
    entry = audit_service.log(
        db=db,
        user=test_user,
        action="manual_test",
        target_type="system",
        target_id=999,
        details={"test": True}
    )
    assert entry is not None
    assert entry.action == "manual_test"
    assert entry.user_name == "Audit Tester"
    assert entry.user_id == test_user.id
    
    # 2. Endpoint client post test
    payload = {
        "title": "Audited Barista",
        "department": "F&B",
        "description": "Brew coffee",
        "required_skills": ["Coffee"],
        "preferred_skills": ["Latte Art"],
        "min_experience_years": 1,
        "seniority_level": "Mid",
        "salary_min": 30000,
        "salary_max": 40000,
        "salary_currency": "TRY",
        "is_active": True,
        "location": "Antalya",
        "headcount": 1,
        "priority": "Orta",
        "hiring_manager": "Mert Koç",
        "target_date": "2026-09-01"
    }
    res = client.post("/api/positions/", json=payload)
    assert res.status_code == 200
    pos_id = res.json()["id"]

    logs = db.query(models.ImmutableAuditLog).filter(
        models.ImmutableAuditLog.action == "position_created",
        models.ImmutableAuditLog.target_type == "position",
        models.ImmutableAuditLog.target_id == pos_id
    ).all()
    
    assert len(logs) == 1
    assert logs[0].action == "position_created"
    
    db.close()


def test_role_scope_filtering():
    from auth import get_current_user
    db = TestingSessionLocal()
    
    # Create test scope hotels
    h1 = models.Hotel(organization_id=1, city_id=1, region_id=1, name="Hotel Scope A", code="HSA")
    h2 = models.Hotel(organization_id=1, city_id=1, region_id=1, name="Hotel Scope B", code="HSB")
    db.add(h1)
    db.add(h2)
    db.commit()
    db.refresh(h1)
    db.refresh(h2)
    
    # Create positions in separate hotels
    pos1 = models.Position(title="Hotel A Barista", is_active=True, hotel_id=h1.id, description="F&B service")
    pos2 = models.Position(title="Hotel B Lifeguard", is_active=True, hotel_id=h2.id, description="Pool safety")
    db.add(pos1)
    db.add(pos2)
    db.commit()
    
    # Create scoped user
    scoped_user = models.User(
        email="scoped_user@example.com",
        full_name="Scoped User",
        hashed_password="mocked_password",
        role="RECRUITER",
        data_visibility_scope="HOTEL",
        hotel_access_ids=[h1.id],
        is_active=True
    )
    db.add(scoped_user)
    db.commit()
    db.refresh(scoped_user)
    
    def mock_get_current_user():
        return scoped_user
        
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    try:
        res = client.get("/api/positions/")
        assert res.status_code == 200
        positions = res.json()
        
        # Should only see the position in Hotel A (Hotel Scope A)
        titles = [p["title"] for p in positions]
        assert "Hotel A Barista" in titles
        assert "Hotel B Lifeguard" not in titles
    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        db.close()



