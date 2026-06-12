from pydantic import BaseModel, field_validator
from typing import List, Optional, Any
from datetime import datetime

class CandidateBase(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    summary: Optional[str] = None
    skills: Optional[List[str]] = []
    experience: Optional[Any] = []
    education: Optional[Any] = []
    certifications: Optional[List[str]] = []
    seniority_level: Optional[str] = None
    seniority_score: Optional[float] = None
    strengths: Optional[List[str]] = []
    areas_for_improvement: Optional[List[str]] = []
    cv_file_path: Optional[str] = None
    cv_file_data: Optional[str] = None

    @field_validator('skills', 'experience', 'education', 'certifications', 'strengths', 'areas_for_improvement', mode='before')
    @classmethod
    def convert_null_or_string_to_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            try:
                import json
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            return [v]
        return v

class CandidateCreate(CandidateBase):
    original_filename: str

class CandidateSimple(CandidateBase):
    id: int
    upload_status: Optional[str] = "Pending"
    rating: Optional[float] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = []
    is_favorite: Optional[bool] = False
    is_blacklisted: Optional[bool] = False
    blacklist_reason: Optional[str] = None
    ai_profile_summary: Optional[str] = None
    is_deleted: Optional[bool] = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

    @field_validator('tags', mode='before')
    @classmethod
    def convert_tags(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            try:
                import json
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            return [v]
        return v

    @field_validator('upload_status', mode='before')
    @classmethod
    def convert_upload_status(cls, v):
        if v is None:
            return "Pending"
        return v

    @field_validator('is_favorite', 'is_blacklisted', 'is_deleted', mode='before')
    @classmethod
    def convert_bools(cls, v):
        if v is None:
            return False
        return v

class Candidate(CandidateBase):
    id: int
    upload_status: Optional[str] = "Pending"
    rating: Optional[float] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = []
    is_favorite: Optional[bool] = False
    is_blacklisted: Optional[bool] = False
    blacklist_reason: Optional[str] = None
    ai_profile_summary: Optional[str] = None
    is_deleted: Optional[bool] = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

    @field_validator('tags', mode='before')
    @classmethod
    def convert_tags(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            try:
                import json
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            return [v]
        return v

    @field_validator('upload_status', mode='before')
    @classmethod
    def convert_upload_status(cls, v):
        if v is None:
            return "Pending"
        return v

    @field_validator('is_favorite', 'is_blacklisted', 'is_deleted', mode='before')
    @classmethod
    def convert_bools(cls, v):
        if v is None:
            return False
        return v


class PositionBase(BaseModel):
    title: str
    department: Optional[str] = None
    description: str
    required_skills: Optional[List[str]] = []
    preferred_skills: Optional[List[str]] = []
    min_experience_years: Optional[int] = 0
    seniority_level: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = "TRY"
    is_active: Optional[bool] = True
    location: Optional[str] = None
    headcount: Optional[int] = 1

    @field_validator('required_skills', 'preferred_skills', mode='before')
    @classmethod
    def convert_null_or_string_to_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            try:
                import json
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            return [v]
        return v

class PositionCreate(PositionBase):
    pass

class Position(PositionBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class ApplicationCreate(BaseModel):
    candidate_id: int
    position_id: int
    cover_letter: Optional[str] = None
    source: Optional[str] = None

class ApplicationStatusUpdate(BaseModel):
    status: str
    note: Optional[str] = None

class ApplicationOut(BaseModel):
    id: int
    candidate_id: int
    position_id: int
    status: str
    status_history: Optional[List[Any]] = []
    match_score: Optional[float] = None
    semantic_score: Optional[float] = None
    keyword_score: Optional[float] = None
    matching_skills: Optional[List[str]] = []
    hr_notes: Optional[str] = None
    cover_letter: Optional[str] = None
    source: Optional[str] = None
    applied_at: datetime
    hired_at: Optional[datetime] = None
    candidate: Optional[CandidateSimple] = None
    position: Optional[Position] = None
    class Config:
        from_attributes = True

    @field_validator('status_history', 'matching_skills', mode='before')
    @classmethod
    def convert_null_or_string_to_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            try:
                import json
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            return [v]
        return v

class InterviewCreate(BaseModel):
    application_id: int
    interview_type: str = "hr"
    round_number: int = 1
    scheduled_at: Optional[datetime] = None
    duration_minutes: int = 60
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    interviewer_name: Optional[str] = None

class InterviewFeedback(BaseModel):
    overall_score: Optional[float] = None
    technical_score: Optional[float] = None
    cultural_score: Optional[float] = None
    notes: Optional[str] = None
    strengths_noted: List[str] = []
    concerns_noted: List[str] = []
    recommendation: Optional[str] = None
    result: Optional[str] = "pending"
    result_note: Optional[str] = None

class InterviewOut(BaseModel):
    id: int
    application_id: int
    round_number: int
    interview_type: str
    status: str
    scheduled_at: Optional[datetime] = None
    duration_minutes: int
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    interviewer_name: Optional[str] = None
    overall_score: Optional[float] = None
    technical_score: Optional[float] = None
    cultural_score: Optional[float] = None
    notes: Optional[str] = None
    strengths_noted: Optional[List[str]] = []
    concerns_noted: Optional[List[str]] = []
    recommendation: Optional[str] = None
    ai_questions: Optional[List[Any]] = []
    ai_summary: Optional[str] = None
    result: Optional[str] = None
    result_note: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

    @field_validator('strengths_noted', 'concerns_noted', 'ai_questions', mode='before')
    @classmethod
    def convert_null_or_string_to_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            try:
                import json
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            return [v]
        return v

class OfferCreate(BaseModel):
    application_id: int
    proposed_salary: Optional[int] = None
    currency: str = "TRY"
    start_date: Optional[datetime] = None
    position_title: Optional[str] = None
    benefits: List[str] = []
    notes: Optional[str] = None

class OfferOut(BaseModel):
    id: int
    application_id: int
    status: str
    proposed_salary: Optional[int] = None
    final_salary: Optional[int] = None
    currency: str
    start_date: Optional[datetime] = None
    position_title: Optional[str] = None
    benefits: Optional[List[str]] = []
    notes: Optional[str] = None
    negotiation_history: Optional[List[Any]] = []
    letter_content: Optional[str] = None
    sent_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True

    @field_validator('benefits', 'negotiation_history', mode='before')
    @classmethod
    def convert_null_or_string_to_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            try:
                import json
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            return [v]
        return v

class OnboardingTaskOut(BaseModel):
    id: int
    application_id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    responsible: Optional[str] = None
    due_days: int
    status: str
    completed_at: Optional[datetime] = None
    order_index: int
    created_at: datetime
    class Config:
        from_attributes = True

class MatchResult(BaseModel):
    candidate_id: int
    candidate_name: str
    match_score: float
    match_reasons: List[str]
    missing_skills: List[str]

class CandidateMatch(BaseModel):
    candidate: Candidate
    score: float
    matching_skills: List[str]
    semantic_score: Optional[float] = 0.0
    keyword_score: Optional[float] = 0.0
    learning_boost: Optional[float] = 0.0

class CandidateComparisonRequest(BaseModel):
    candidate_ids: List[int]
    position_id: Optional[int] = None

class ComparisonRow(BaseModel):
    criteria: str
    candidate1_val: str
    candidate2_val: str

class CandidateComparisonResponse(BaseModel):
    comparison: str
    recommendation: str
    candidate1_pros: List[str]
    candidate2_pros: List[str]
    comparison_table: List[ComparisonRow]

class FeedbackCreate(BaseModel):
    candidate_id: int
    position_id: int
    signal_type: str

class CandidateRatingUpdate(BaseModel):
    rating: float

class CandidateNotesUpdate(BaseModel):
    notes: str

class LogOut(BaseModel):
    id: int
    user_name: str
    action: str
    target_type: str
    target_id: int
    details: Any
    created_at: datetime
    class Config:
        from_attributes = True

class InterviewResultUpdate(BaseModel):
    result: str
    result_note: Optional[str] = None

# AUTH SCHEMAS
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Any # Using Any to avoid circular dependency problems for now

class UserBase(BaseModel):
    email: str
    full_name: str
    department: Optional[str] = None
    role: str = "hr"
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None

class UserOut(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    password: str

class UserPasswordChange(BaseModel):
    old_password: str
    new_password: str

class UserRoleUpdate(BaseModel):
    role: str

class MatchScoreOut(BaseModel):
    id: int
    candidate_id: int
    position_id: int
    overall_score: Optional[float] = None
    decision: Optional[str] = None
    required_skill_score: Optional[float] = None
    preferred_skill_score: Optional[float] = None
    experience_score: Optional[float] = None
    seniority_score: Optional[float] = None
    education_score: Optional[float] = None
    language_score: Optional[float] = None
    domain_fit_score: Optional[float] = None
    culture_fit_score: Optional[float] = None
    matching_skills: List[str] = []
    missing_skills: List[str] = []
    transferable_skills: List[str] = []
    strengths: List[str] = []
    risks: List[str] = []
    summary: Optional[str] = None
    recommendation: Optional[str] = None
    interview_focus_areas: List[str] = []
    suggested_questions: List[str] = []
    llm_model: Optional[str] = None
    prompt_version: Optional[str] = None
    calculated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class InterviewNotesAnalysisRequest(BaseModel):
    raw_notes: str

class InterviewNotesAnalysisResponse(BaseModel):
    cleaned_notes: Optional[str] = None
    communication_assessment: Optional[str] = None
    culture_fit_assessment: Optional[str] = None
    technical_assessment: Optional[str] = None
    ai_recommendation: Optional[str] = None
    next_step: Optional[str] = None
    overall_score: Optional[float] = None
    technical_score: Optional[float] = None
    cultural_score: Optional[float] = None

class InterviewQuestionsRequest(BaseModel):
    candidate_id: int
    position_id: int

class InterviewQuestionsResponse(BaseModel):
    questions: List[str]

class UserAdminUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class RecruitmentTaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[str] = "todo"
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None

class RecruitmentTaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class WhatsAppDraftRequest(BaseModel):
    candidate_id: int
    position_id: Optional[int] = None
    message_type: str  # first_contact, interview_invitation, rejection, talent_pool, onboarding, etc.
    tone: str  # professional, warm, short

class WhatsAppDraftResponse(BaseModel):
    message: str

class EmailDraftRequest(BaseModel):
    candidate_id: int
    position_id: Optional[int] = None
    email_type: str  # application_received, first_contact, interview_invitation, rejection, offer, etc.
    tone: str  # professional, warm, formal

class EmailDraftResponse(BaseModel):
    subject: str
    body: str

class CandidateActivityCreate(BaseModel):
    activity_type: str
    note: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    metadata_json: Optional[dict] = None
