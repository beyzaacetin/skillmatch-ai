from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from config import settings

import json
from sqlalchemy.types import TypeDecorator, TEXT

class RobustJSON(TypeDecorator):
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                json.loads(value)
                return value
            except Exception:
                pass
        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return json.loads(value)
        except Exception:
            return value

# Override JSON type
JSON = RobustJSON


# ─── MEVCUT (v3) ─────────────────────────────────────────────────────────────

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=True, default=1)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    full_name = Column(String, nullable=True)
    name = Column(String, index=True)
    email = Column(String, index=True, nullable=True)
    phone = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    skills = Column(JSON, default=[])
    experience = Column(JSON, default=[])
    education = Column(JSON, default=[])
    certifications = Column(JSON, default=[])
    projects = Column(JSON, default=[])
    seniority_level = Column(String, nullable=True)
    seniority_score = Column(Float, nullable=True)
    strengths = Column(JSON, default=[])
    areas_for_improvement = Column(JSON, default=[])
    original_filename = Column(String, nullable=True)
    upload_status = Column(String, default="Pending")
    # v4 new fields
    rating = Column(Float, nullable=True)          # 1-5 yıldız
    notes = Column(Text, nullable=True)             # İK notları
    tags = Column(JSON, default=[])                 # Etiketler
    is_favorite = Column(Boolean, default=False)
    is_blacklisted = Column(Boolean, default=False)
    blacklist_reason = Column(Text, nullable=True)
    ai_profile_summary = Column(Text, nullable=True)
    cv_file_path = Column(String, nullable=True)
    cv_file_data = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(String, nullable=True)
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")

class Position(Base):
    __tablename__ = "positions"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=True, default=1)
    title = Column(String, index=True)
    department = Column(String, nullable=True)
    description = Column(Text)
    required_skills = Column(JSON, default=[])
    preferred_skills = Column(JSON, default=[])
    min_experience_years = Column(Integer, default=0)
    seniority_level = Column(String, nullable=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    salary_currency = Column(String, default="TRY")
    # v4 new fields
    is_active = Column(Boolean, default=True)
    location = Column(String, nullable=True)
    headcount = Column(Integer, default=1)
    priority = Column(String, default="Orta")
    hiring_manager = Column(String, nullable=True)
    target_date = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    # Multi-hotel configurations
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    
    # Wizard and Job Ad fields
    employment_type = Column(String, nullable=True)
    contract_type = Column(String, nullable=True)
    accommodation = Column(String, nullable=True)
    salary_target = Column(Integer, nullable=True)
    offer_approval_rule = Column(String, nullable=True)
    pipeline_template = Column(String, nullable=True)
    department_manager = Column(String, nullable=True)
    rule_no_tech_without_hr = Column(Boolean, default=False)
    rule_approve_outside_band = Column(Boolean, default=False)
    rule_notify_new_application = Column(Boolean, default=False)
    job_ad_title = Column(String, nullable=True)
    job_ad_description = Column(Text, nullable=True)
    application_form_fields = Column(JSON, nullable=True)
    job_ad_language = Column(String, nullable=True)
    channel_link_qr = Column(Boolean, default=False)
    channel_career_portal = Column(Boolean, default=False)
    channel_linkedin = Column(Boolean, default=False)
    qr_code_path = Column(String, nullable=True)

    applications = relationship("Application", back_populates="position", cascade="all, delete-orphan")

# ─── YENİ (v4) ───────────────────────────────────────────────────────────────

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    # Pipeline status: applied|screening|interview|offer|hired|rejected
    status = Column(String, default="applied")
    status_history = Column(JSON, default=[])   # [{status, date, note}]
    # AI match scores (copied from matcher at application time)
    match_score = Column(Float, nullable=True)
    semantic_score = Column(Float, nullable=True)
    keyword_score = Column(Float, nullable=True)
    matching_skills = Column(JSON, default=[])
    # HR fields
    cover_letter = Column(Text, nullable=True)
    hr_notes = Column(Text, nullable=True)
    source = Column(String, nullable=True)       # linkedin, kariyer.net, direkt...
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    hired_at = Column(DateTime(timezone=True), nullable=True)
    
    # Configurable Ownership & locks
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=True)
    ownership_started_at = Column(DateTime(timezone=True), nullable=True)
    ownership_expires_at = Column(DateTime(timezone=True), nullable=True)
    extension_count = Column(Integer, default=0)
    lock_status = Column(String, default="UNLOCKED") # LOCKED, UNLOCKED, WAITING
    
    # UTM tracking fields
    utm_source = Column(String, nullable=True)
    utm_medium = Column(String, nullable=True)
    utm_campaign = Column(String, nullable=True)
    utm_content = Column(String, nullable=True)
    
    # Relations
    candidate = relationship("Candidate", back_populates="applications")
    position = relationship("Position", back_populates="applications")
    interviews = relationship("Interview", back_populates="application", cascade="all, delete-orphan")
    offer = relationship("Offer", back_populates="application", uselist=False, cascade="all, delete-orphan")

class Interview(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=True, default=1)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    round_number = Column(Integer, default=1)
    interview_type = Column(String, default="hr")   # hr|technical|video|onsite
    status = Column(String, default="scheduled")    # scheduled|completed|cancelled
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, default=60)
    location = Column(String, nullable=True)
    meeting_link = Column(String, nullable=True)
    interviewer_name = Column(String, nullable=True)
    # Scores
    overall_score = Column(Float, nullable=True)
    technical_score = Column(Float, nullable=True)
    cultural_score = Column(Float, nullable=True)
    # Notes & AI
    notes = Column(Text, nullable=True)
    strengths_noted = Column(JSON, default=[])
    concerns_noted = Column(JSON, default=[])
    recommendation = Column(String, nullable=True)  # proceed|reject|hold
    ai_questions = Column(JSON, default=[])          # AI üretimi mülakat soruları
    ai_summary = Column(Text, nullable=True)         # AI mülakat özeti
    result = Column(String, nullable=True)           # "passed", "failed", "pending"
    result_note = Column(Text, nullable=True)        # Sonuç notu
    raw_notes = Column(Text, nullable=True)
    cleaned_notes = Column(Text, nullable=True)
    communication_assessment = Column(Text, nullable=True)
    culture_fit_assessment = Column(Text, nullable=True)
    technical_assessment = Column(Text, nullable=True)
    ai_recommendation = Column(String, nullable=True)
    next_step = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    application = relationship("Application", back_populates="interviews")

class Offer(Base):
    __tablename__ = "offers"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=True, default=1)
    application_id = Column(Integer, ForeignKey("applications.id"), unique=True, nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    offered_salary = Column(Float, nullable=True)
    offer_date = Column(String, nullable=True)
    status = Column(String, default="draft")    # draft|sent|accepted|rejected|negotiating
    proposed_salary = Column(Integer, nullable=True)
    final_salary = Column(Integer, nullable=True)
    currency = Column(String, default="TRY")
    start_date = Column(DateTime(timezone=True), nullable=True)
    position_title = Column(String, nullable=True)
    benefits = Column(JSON, default=[])
    notes = Column(Text, nullable=True)
    negotiation_history = Column(JSON, default=[])
    letter_content = Column(Text, nullable=True)   # AI üretimi teklif mektubu
    sent_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    deviation_reason = Column(String, nullable=True)
    deviation_explanation = Column(Text, nullable=True)
    approved_by = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    application = relationship("Application", back_populates="offer")
    approval_requests = relationship("OfferApprovalRequest", back_populates="offer", cascade="all, delete-orphan")

class OnboardingTask(Base):
    __tablename__ = "onboarding_tasks"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)       # Evrak|IT|Eğitim|Tanışma
    responsible = Column(String, nullable=True)    # İK|IT|Yönetici|Aday
    due_days = Column(Integer, default=1)
    status = Column(String, default="pending")     # pending|in_progress|completed|skipped
    completed_at = Column(DateTime(timezone=True), nullable=True)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

import enum
class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    RECRUITER = "RECRUITER"
    HR = "RECRUITER"  # backward compatibility alias
    HIRING_MANAGER = "HIRING_MANAGER"
    MANAGER = "HIRING_MANAGER"  # backward compatibility alias
    VIEWER = "VIEWER"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=True, default=1)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(String, default=UserRole.RECRUITER.value)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    department = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # candidate specific
    candidate_access_token = Column(String, nullable=True, index=True)
    
    # Scoped permissions
    hotel_access_ids = Column(JSON, default=[])
    region_access_ids = Column(JSON, default=[])
    department_access_ids = Column(JSON, default=[])
    data_visibility_scope = Column(String, default="GLOBAL") # GLOBAL, REGIONAL, HOTEL, DEPARTMENT

class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True) # İleride auth eklendiğinde
    user_name = Column(String, default="Admin")
    action = Column(String)  # 'candidate_added', 'status_changed', etc.
    target_type = Column(String) # 'candidate', 'application', etc.
    target_id = Column(Integer)
    details = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MatchScore(Base):
    __tablename__ = "match_scores"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    overall_score = Column(Float, nullable=True)
    decision = Column(String, nullable=True) # strong_match | potential_match | weak_match | not_match
    required_skill_score = Column(Float, nullable=True)
    preferred_skill_score = Column(Float, nullable=True)
    experience_score = Column(Float, nullable=True)
    seniority_score = Column(Float, nullable=True)
    education_score = Column(Float, nullable=True)
    language_score = Column(Float, nullable=True)
    domain_fit_score = Column(Float, nullable=True)
    culture_fit_score = Column(Float, nullable=True)
    matching_skills = Column(JSON, default=[])
    missing_skills = Column(JSON, default=[])
    transferable_skills = Column(JSON, default=[])
    strengths = Column(JSON, default=[])
    risks = Column(JSON, default=[])
    summary = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    interview_focus_areas = Column(JSON, default=[])
    suggested_questions = Column(JSON, default=[])
    llm_model = Column(String, default=lambda: settings.GEMINI_MODEL)
    prompt_version = Column(String, default="v1.0")
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    candidate = relationship("Candidate")
    position = relationship("Position")

class CandidateActivity(Base):
    __tablename__ = "candidate_activities"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    activity_type = Column(String)  # candidate_created, stage_changed, etc.
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    note = Column(Text, nullable=True)
    created_by = Column(String, default="System")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column(JSON, default={})

class EmailTemplate(Base):
    __tablename__ = "email_templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    subject = Column(String)
    body = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class EmailLog(Base):
    __tablename__ = "email_logs"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    subject = Column(String)
    body = Column(Text)
    sent_by = Column(String)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

class RecruitmentTask(Base):
    __tablename__ = "recruitment_tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="todo") # todo | in_progress | done
    assigned_to = Column(String, nullable=True)
    due_date = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AIRequest(Base):
    __tablename__ = "ai_requests"
    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    model_name = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PositionInsights(Base):
    __tablename__ = "position_insights"
    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    time_to_fill_prediction = Column(String, nullable=True)
    pipeline_health = Column(Integer, default=100)
    market_competition = Column(String, nullable=True)
    candidate_pool_quality = Column(Integer, default=100)
    budget_risk = Column(String, nullable=True)
    offer_acceptance_prediction = Column(Integer, default=100)
    actionable_recommendations = Column(JSON, default=[])
    market_avg_salary = Column(String, nullable=True)
    our_offer = Column(String, nullable=True)
    market_open_positions = Column(String, nullable=True)
    market_avg_time_to_fill = Column(String, nullable=True)
    risks = Column(JSON, default=[])
    recruitment_guide = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    question_index = Column(Integer, nullable=False)
    section = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    expected_answer = Column(Text, nullable=True)
    red_flag_warning = Column(Text, nullable=True)
    candidate_answer = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    interview_type = Column(String, default="HR")
    interviewer_notes = Column(Text, nullable=True)
    red_flags = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)


class HiringDecision(Base):
    __tablename__ = "hiring_decisions"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), unique=True, nullable=False)
    decision = Column(String, nullable=False)  # "hired", "hold", "rejected"
    technical_score = Column(Float, nullable=True)
    interview_score = Column(Float, nullable=True)
    cultural_score = Column(Float, nullable=True)
    hiring_confidence = Column(String, nullable=True)
    strengths = Column(JSON, default=[])
    concerns = Column(JSON, default=[])
    recommended_salary = Column(Integer, nullable=True)
    performance_bonus = Column(Integer, nullable=True)
    start_date = Column(String, nullable=True)
    work_model = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PositionReport(Base):
    __tablename__ = "position_reports"
    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    report_type = Column(String, nullable=False)
    report_content = Column(Text, nullable=True)
    pdf_path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CandidateNote(Base):
    __tablename__ = "candidate_notes"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    note_text = Column(Text, nullable=False)
    created_by = Column(String, default="Recruiter")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(String, default="reminder") # interview | task | reminder | deadline
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("recruitment_tasks.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── Multi-Hotel Settings & Structure (v5) ───────────────────────────────────

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    code = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Country(Base):
    __tablename__ = "countries"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    code = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)

class City(Base):
    __tablename__ = "cities"
    id = Column(Integer, primary_key=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    name = Column(String, index=True)
    is_active = Column(Boolean, default=True)

class Region(Base):
    __tablename__ = "regions"
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    name = Column(String, index=True)
    is_active = Column(Boolean, default=True)

class Hotel(Base):
    __tablename__ = "hotels"
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    name = Column(String, index=True)
    code = Column(String, unique=True, index=True)
    branding_settings = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    order_index = Column(Integer, default=0)

class HotelDepartmentPositionMapping(Base):
    __tablename__ = "hotel_department_position_mappings"
    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    position_title = Column(String, nullable=False)

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    code = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    permissions = Column(JSON, default={})
    is_custom = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SystemConfiguration(Base):
    __tablename__ = "system_configurations"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(JSON, nullable=True)
    category = Column(String, index=True)
    description = Column(Text, nullable=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=True)

class ImmutableAuditLog(Base):
    __tablename__ = "immutable_audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    user_name = Column(String, nullable=True)
    action = Column(String, index=True)
    target_type = Column(String, index=True)
    target_id = Column(Integer, nullable=True)
    details = Column(JSON, default={})
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CandidateExtensionRequest(Base):
    __tablename__ = "candidate_extension_requests"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason_category = Column(String, nullable=False)
    custom_explanation = Column(Text, nullable=True)
    status = Column(String, default="PENDING")  # PENDING, APPROVED, REJECTED
    days_requested = Column(Integer, default=10)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CandidateInterestWaitingList(Base):
    __tablename__ = "candidate_interest_waiting_lists"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WorkforceHeadcountBudget(Base):
    __tablename__ = "workforce_headcount_budgets"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=True, default=1)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    position_title = Column(String, nullable=False)
    headcount_budget = Column(Integer, default=0)
    target_salary_min = Column(Integer, nullable=True)
    target_salary_max = Column(Integer, nullable=True)
    currency = Column(String, default='TRY')
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CandidateRoutingSuggestion(Base):
    __tablename__ = "candidate_routing_suggestions"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    source_hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    target_hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    position_title = Column(String, nullable=False)
    status = Column(String, default='PENDING') # PENDING, ACCEPTED, REJECTED
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SalaryPolicy(Base):
    __tablename__ = "salary_policies"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=True, default=1)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    position_title = Column(String, nullable=False, index=True)
    seniority_level = Column(String, nullable=True)  # Junior, Mid, Senior
    min_salary = Column(Integer, nullable=False)
    target_salary = Column(Integer, nullable=False)
    max_salary = Column(Integer, nullable=False)
    accommodation = Column(Boolean, default=False)
    transportation = Column(Boolean, default=False)
    meal = Column(Boolean, default=False)
    bonus = Column(String, nullable=True)
    additional_benefits = Column(JSON, default=[])
    currency = Column(String, default='TRY')
    effective_start_date = Column(DateTime(timezone=True), nullable=True)
    effective_end_date = Column(DateTime(timezone=True), nullable=True)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    status = Column(String, default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OfferApprovalRequest(Base):
    __tablename__ = "offer_approval_requests"
    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=False)
    approver_role = Column(String, nullable=False)  # HOTEL_HR, CENTRAL_HR
    sequence_number = Column(Integer, default=1)
    status = Column(String, default='PENDING')  # PENDING, APPROVED, REJECTED
    decision_notes = Column(Text, nullable=True)
    resolved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    offer = relationship("Offer", back_populates="approval_requests")
    resolved_by = relationship("User")


class RecruitmentCampaign(Base):
    __tablename__ = "recruitment_campaigns"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    source = Column(String, default="QR Code")
    utm_source = Column(String, nullable=True)
    utm_medium = Column(String, nullable=True)
    utm_campaign = Column(String, nullable=True)
    qr_code_path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class WorkforceBudgetRecord(Base):
    __tablename__ = "workforce_budget_records"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=True, default=1)
    hotel_code = Column(String, index=True, nullable=False) # Otel (PRM, SUN)
    hotel_sub = Column(String, nullable=True) # Otel_Alt
    department = Column(String, index=True, nullable=False) # Ana Kategori
    sub_department = Column(String, nullable=True) # Alt Kategori
    position_title = Column(String, index=True, nullable=False) # Tanım
    month_of_year = Column(Integer, nullable=False) # MonthOfYear 1-12
    total_fte = Column(Float, default=0.0) # Toplam FTE
    budget_amount = Column(Float, nullable=True) # Bütçe
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RecruitmentPipeline(Base):
    __tablename__ = "recruitment_pipelines"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    stages = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)

