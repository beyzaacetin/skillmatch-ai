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
- [/] **Single-Excel Importer Endpoint:** Accept combined `Organizasyon_Butce_FTE` Excel containing:
  - `Donem`, `OtelKodu`, `OtelAdi`, `Sehir`, `Bolge`, `AnaKategori`, `AltAnaKategori`, `AltKategori`, `PozisyonKodu`, `PozisyonAdi`, `ButceFTE`, `AktifFTE`
- [ ] **Database Schema Enhancements:**
  - Create models for dynamic organization nodes closure/materialized paths, workforce plan periods, workforce plan lines, and import logs.
- [ ] **Dynamic Alias & Otel Matcher:** Automatically recommend or link imported hotels with canonical ones.
- [/] **Settings Import Panel UI:** Excel drag-drop, col map parser, 50-row preview, validation checks, warning logs.
- [ ] **Drill-Down Headcount Reports:** Hierarchical open FTE position deficiency reporting.

### Faz 2: Need Models & Operational Positions
- [ ] Kadro İhtiyacı (Plan Needs) model & table
- [ ] Operasyonel İşe Alım Pozisyonu (Recruitment Positions) model & table
- [ ] Budget check logic & approval pipeline workflows
- [ ] Public headhunting link generation (QR code + campaigns UTM analyzer)

### Faz 3: Candidate Application & Candidate 360
- [ ] Public mobil-friendly apply form
- [ ] Candidate duplicate check (email + phone normalized matching)
- [ ] Versioned CV document storage & asynchronous parse jobs
- [ ] Candidate 360-degree profile (Applications, Matches, Interviews, Blacklist tabs)

### Faz 4: Pipeline Stages, Evaluation & Meaningful Locks
- [ ] Pipeline templates settings page
- [ ] 10-day evaluation counter logic
- [ ] 7-day meaningful locks mechanism (candidate exclusive processing status)
- [ ] Common talent pool release scheduler jobs
- [ ] Regional candidate routing hierarchy (Same Hotel → Region → City → Pool)

### Faz 5: AI Matching, Interviews & Assistant
- [ ] Explanable score component (Alt-skorlar: Deneyim, yetkinlik, sertifika, vb.)
- [ ] AI Interview Question Generator & Candidate Scorecards
- [ ] Auth/RBAC scoped semantic Assistant Chatbot

### Faz 6: Compensation, Onboarding, Blacklist & Custom Reports
- [ ] Salary policy referential bands
- [ ] Onboarding checklist with document OCR confidence validator
- [ ] Blacklist records, reason codes, evidence, and approvals
- [ ] Executive dashboards & Custom Report builder

### Faz 7: Hardening, Security & Concurrency
- [ ] Optimistic lock version columns and transactional integrity checks
- [ ] Field-level encryption for PII
- [ ] Playwright E2E integration test suite
