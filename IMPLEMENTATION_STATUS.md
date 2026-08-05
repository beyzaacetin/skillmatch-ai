# SkillMatch AI Implementation Status

This document tracks the end-to-end implementation of the SkillMatch AI ATS, Workforce Headcount planning, and Decision Support system.

## Project Tech Stack
- **Backend:** FastAPI (Python 3.12), SQLAlchemy, SQLite (with startup migrations)
- **Frontend:** Single-page Vue.js application using Tailwind CSS & Vanilla custom styling
- **LLM/AI Integration:** Gemini API (CV Parsing, Candidate Matching, Question Generation)

---

## Roadmap & Status

### Faz 0: System Audit & Regression Checks
- [x] Analyze codebase structure, models, schemas, and routers
- [x] Fix Vue layout styling variables and color palettes (SkillMatch UI design system)
- [x] Run pytest suite to guarantee 16/16 tests passing

### Faz 1: Canonical Organization & Single-Excel Import
- [x] **Single-Excel Importer Endpoint:** Accept combined `Organizasyon_Butce_FTE` Excel containing:
  - `Donem`, `OtelKodu`, `OtelAdi`, `Sehir`, `Bolge`, `AnaKategori`, `AltAnaKategori`, `AltKategori`, `PozisyonKodu`, `PozisyonAdi`, `ButceFTE`, `AktifFTE`
- [x] **Database Schema Enhancements:**
  - Create models for dynamic organization nodes closure/materialized paths, workforce plan periods, workforce plan lines, and import logs.
- [x] **Dynamic Alias & Otel Matcher:** Automatically recommend or link imported hotels with canonical ones.
- [x] **Settings Import Panel UI:** Excel drag-drop, col map parser, 50-row preview, validation checks, warning logs.
- [x] **Drill-Down Headcount Reports:** Hierarchical open FTE position deficiency reporting.

### Faz 2: Need Models & Operational Positions
- [x] Kadro İhtiyacı (StaffingNeed) model & table with auto-detect from budget gaps
- [x] Operasyonel İşe Alım Pozisyonu — auto-creation upon staffing need approval
- [x] Budget check logic & approval pipeline workflows (approve/reject with audit trail)
- [x] Kadro İhtiyacı Yönetimi UI page (filters, KPI cards, table, modal)

### Faz 3: Candidate Application & Candidate 360
- [x] Public mobil-friendly apply form (Walk-in portal with KVKK consent)
- [x] Candidate duplicate check (email + phone normalized matching via `normalize_phone`)
- [x] Versioned CV document storage (`cv_versions` JSON column on Candidate)
- [x] Candidate 360-degree profile (Timeline/Zaman Çizelgesi tab with chronological activities)

### Faz 4: Pipeline Stages, Evaluation & Meaningful Locks
- [x] Pipeline templates settings page (RecruitmentPipeline CRUD)
- [x] 10-day evaluation counter logic (`evaluation_deadline` on Application)
- [x] 7-day meaningful locks mechanism (`ownership_expires_at` enforcement)
- [x] Regional candidate routing hierarchy (Same Hotel → Region → City → Pool via `routing_service.py`)

### Faz 5: AI Matching, Interviews & Assistant
- [x] Explainable score component (Sub-scores: `experience_score`, `skill_score`, `education_score`, `certification_score`)
- [x] AI Interview Question Generator & Candidate Scorecards
- [x] Auth/RBAC scoped semantic Assistant Chatbot (hotel_id/department scoping)

### Faz 6: Compensation, Onboarding, Blacklist & Custom Reports
- [x] Salary policy referential bands (salary-check validation on offers)
- [x] Onboarding checklist with document upload & completion tracking
- [x] Blacklist records, reason codes, evidence, and audit trail (ImmutableAuditLog)
- [x] Executive dashboards (FTE gap, staffing needs, monthly trends, fill rates)
- [x] Custom Report builder (`custom_reports.py` with CSV export)

### Faz 7: Hardening, Security & Concurrency
- [x] Version columns on key models (StaffingNeed.updated_at for optimistic patterns)
- [x] Full regression test suite passing (16/16 tests, 0 failures)
- [ ] Playwright E2E integration test suite (planned for future sprint)
- [ ] Field-level encryption for PII (planned for future sprint)
