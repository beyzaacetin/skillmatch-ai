import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import core FastAPI and SQLAlchemy libraries that are guaranteed to work
from fastapi import FastAPI, Request, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

app = None
import time
COMMIT_HASH = os.getenv("RAILWAY_GIT_COMMIT_SHA", os.getenv("COMMIT_SHA", ""))[:7]
if not COMMIT_HASH:
    try:
        import subprocess
        git_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("utf-8").strip()
        if git_hash:
            COMMIT_HASH = git_hash
    except Exception:
        pass
if not COMMIT_HASH:
    COMMIT_HASH = str(int(time.time()))

try:
    from database import engine, Base, get_db
    import models
    from sqlalchemy import text
    with engine.begin() as conn:
        try:
            conn.execute(text("SET lock_timeout = 3000"))
        except Exception:
            pass
        Base.metadata.create_all(bind=conn)

    # Auto-migrate database schema additions
    try:
        from sqlalchemy import text
        queries = [
            # candidates table migration
            "ALTER TABLE candidates ADD COLUMN name VARCHAR(255)",
            "ALTER TABLE candidates ADD COLUMN summary TEXT",
            "ALTER TABLE candidates ADD COLUMN skills JSON",
            "ALTER TABLE candidates ADD COLUMN experience JSON",
            "ALTER TABLE candidates ADD COLUMN education JSON",
            "ALTER TABLE candidates ADD COLUMN certifications JSON",
            "ALTER TABLE candidates ADD COLUMN projects JSON",
            "ALTER TABLE candidates ADD COLUMN seniority_level VARCHAR(255)",
            "ALTER TABLE candidates ADD COLUMN seniority_score FLOAT",
            "ALTER TABLE candidates ADD COLUMN strengths JSON",
            "ALTER TABLE candidates ADD COLUMN areas_for_improvement JSON",
            "ALTER TABLE candidates ADD COLUMN original_filename VARCHAR(255)",
            "ALTER TABLE candidates ADD COLUMN upload_status VARCHAR(255)",
            "ALTER TABLE candidates ADD COLUMN rating FLOAT",
            "ALTER TABLE candidates ADD COLUMN notes TEXT",
            "ALTER TABLE candidates ADD COLUMN tags JSON",
            "ALTER TABLE candidates ADD COLUMN is_favorite BOOLEAN",
            "ALTER TABLE candidates ADD COLUMN is_blacklisted BOOLEAN",
            "ALTER TABLE candidates ADD COLUMN blacklist_reason TEXT",
            "ALTER TABLE candidates ADD COLUMN ai_profile_summary TEXT",
            "ALTER TABLE candidates ADD COLUMN cv_file_path TEXT",
            "ALTER TABLE candidates ADD COLUMN cv_file_data TEXT",
            "ALTER TABLE candidates ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE",
            "ALTER TABLE candidates ADD COLUMN deleted_at TIMESTAMP",
            "ALTER TABLE candidates ADD COLUMN deleted_by VARCHAR(255)",
            "UPDATE candidates SET name = full_name WHERE name IS NULL AND full_name IS NOT NULL",
            
            # positions table migration
            "ALTER TABLE positions ADD COLUMN title VARCHAR(255)",
            "ALTER TABLE positions ADD COLUMN department VARCHAR(255)",
            "ALTER TABLE positions ADD COLUMN description TEXT",
            "ALTER TABLE positions ADD COLUMN required_skills JSON",
            "ALTER TABLE positions ADD COLUMN preferred_skills JSON",
            "ALTER TABLE positions ADD COLUMN min_experience_years INTEGER DEFAULT 0",
            "ALTER TABLE positions ADD COLUMN seniority_level VARCHAR(255)",
            "ALTER TABLE positions ADD COLUMN salary_min INTEGER",
            "ALTER TABLE positions ADD COLUMN salary_max INTEGER",
            "ALTER TABLE positions ADD COLUMN salary_currency VARCHAR(50) DEFAULT 'TRY'",
            "ALTER TABLE positions ADD COLUMN is_active BOOLEAN DEFAULT TRUE",
            "ALTER TABLE positions ADD COLUMN location VARCHAR(255)",
            "ALTER TABLE positions ADD COLUMN headcount INTEGER DEFAULT 1",
            "ALTER TABLE positions ADD COLUMN priority VARCHAR(50) DEFAULT 'Orta'",
            "ALTER TABLE positions ADD COLUMN hiring_manager VARCHAR(255)",
            "ALTER TABLE positions ADD COLUMN target_date VARCHAR(255)",
            "ALTER TABLE positions ADD COLUMN closed_at TIMESTAMP",
            
            # users table migration
            "ALTER TABLE users ADD COLUMN email VARCHAR(255)",
            "ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255)",
            "ALTER TABLE users ADD COLUMN full_name VARCHAR(255)",
            "ALTER TABLE users ADD COLUMN role VARCHAR(255) DEFAULT 'RECRUITER'",
            "ALTER TABLE users ADD COLUMN department VARCHAR(255)",
            "ALTER TABLE users ADD COLUMN phone VARCHAR(255)",
            "ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE",
            "ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE",
            "ALTER TABLE users ADD COLUMN last_login TIMESTAMP",
            "ALTER TABLE users ADD COLUMN candidate_access_token VARCHAR(255)",
            
            # interviews table migration
            "ALTER TABLE interviews ADD COLUMN application_id INTEGER",
            "ALTER TABLE interviews ADD COLUMN round_number INTEGER DEFAULT 1",
            "ALTER TABLE interviews ADD COLUMN scheduled_at TIMESTAMP",
            "ALTER TABLE interviews ADD COLUMN duration_minutes INTEGER DEFAULT 60",
            "ALTER TABLE interviews ADD COLUMN meeting_link VARCHAR(255)",
            "ALTER TABLE interviews ADD COLUMN interviewer_name VARCHAR(255)",
            "ALTER TABLE interviews ADD COLUMN overall_score FLOAT",
            "ALTER TABLE interviews ADD COLUMN technical_score FLOAT",
            "ALTER TABLE interviews ADD COLUMN cultural_score FLOAT",
            "ALTER TABLE interviews ADD COLUMN strengths_noted JSON",
            "ALTER TABLE interviews ADD COLUMN concerns_noted JSON",
            "ALTER TABLE interviews ADD COLUMN recommendation VARCHAR(255)",
            "ALTER TABLE interviews ADD COLUMN ai_questions JSON",
            "ALTER TABLE interviews ADD COLUMN ai_summary TEXT",
            "ALTER TABLE interviews ADD COLUMN result VARCHAR(255)",
            "ALTER TABLE interviews ADD COLUMN result_note TEXT",
            "ALTER TABLE interviews ADD COLUMN raw_notes TEXT",
            "ALTER TABLE interviews ADD COLUMN cleaned_notes TEXT",
            "ALTER TABLE interviews ADD COLUMN communication_assessment TEXT",
            "ALTER TABLE interviews ADD COLUMN culture_fit_assessment TEXT",
            "ALTER TABLE interviews ADD COLUMN technical_assessment TEXT",
            "ALTER TABLE interviews ADD COLUMN ai_recommendation VARCHAR(255)",
            "ALTER TABLE interviews ADD COLUMN next_step VARCHAR(255)",
            
            # offers table migration
            "ALTER TABLE offers ADD COLUMN application_id INTEGER",
            "ALTER TABLE offers ADD COLUMN proposed_salary INTEGER",
            "ALTER TABLE offers ADD COLUMN final_salary INTEGER",
            "ALTER TABLE offers ADD COLUMN currency VARCHAR(50) DEFAULT 'TRY'",
            "ALTER TABLE offers ADD COLUMN start_date TIMESTAMP",
            "ALTER TABLE offers ADD COLUMN position_title VARCHAR(255)",
            "ALTER TABLE offers ADD COLUMN benefits JSON",
            "ALTER TABLE offers ADD COLUMN negotiation_history JSON",
            "ALTER TABLE offers ADD COLUMN letter_content TEXT",
            "ALTER TABLE offers ADD COLUMN sent_at TIMESTAMP",
            "ALTER TABLE offers ADD COLUMN responded_at TIMESTAMP",
            
            "UPDATE applications SET status = 'hr_interview' WHERE status = 'interview'",

            # Drop NOT NULL constraints on tenant_id for compatibility with single-tenant model structure
            "ALTER TABLE candidates ALTER COLUMN tenant_id DROP NOT NULL",
            "ALTER TABLE positions ALTER COLUMN tenant_id DROP NOT NULL",
            "ALTER TABLE applications ALTER COLUMN tenant_id DROP NOT NULL",
            "ALTER TABLE interviews ALTER COLUMN tenant_id DROP NOT NULL",
            "ALTER TABLE offers ALTER COLUMN tenant_id DROP NOT NULL",
            "ALTER TABLE onboarding_tasks ALTER COLUMN tenant_id DROP NOT NULL",
            "ALTER TABLE users ALTER COLUMN tenant_id DROP NOT NULL",
            "ALTER TABLE logs ALTER COLUMN tenant_id DROP NOT NULL",
            "ALTER TABLE match_scores ALTER COLUMN tenant_id DROP NOT NULL",
            "ALTER TABLE candidate_activities ALTER COLUMN tenant_id DROP NOT NULL",
            "ALTER TABLE email_templates ALTER COLUMN tenant_id DROP NOT NULL",
            "ALTER TABLE email_logs ALTER COLUMN tenant_id DROP NOT NULL",
            "ALTER TABLE recruitment_tasks ALTER COLUMN tenant_id DROP NOT NULL",

            # Drop NOT NULL constraints on other non-nullable columns that do not exist or are not required in the single-tenant model
            "ALTER TABLE candidates ALTER COLUMN full_name DROP NOT NULL",
            "ALTER TABLE candidates ALTER COLUMN position_id DROP NOT NULL",
            "ALTER TABLE interviews ALTER COLUMN candidate_id DROP NOT NULL",
            "ALTER TABLE interviews ALTER COLUMN interviewer_id DROP NOT NULL",
            "ALTER TABLE interviews ALTER COLUMN position_id DROP NOT NULL",
            "ALTER TABLE interviews ALTER COLUMN interview_date DROP NOT NULL",
            "ALTER TABLE interviews ALTER COLUMN interview_time DROP NOT NULL",
            "ALTER TABLE interviews ALTER COLUMN interview_type DROP NOT NULL",
            "ALTER TABLE offers ALTER COLUMN candidate_id DROP NOT NULL",
            "ALTER TABLE offers ALTER COLUMN position_id DROP NOT NULL",
            "ALTER TABLE offers ALTER COLUMN recruiter_id DROP NOT NULL",
            "ALTER TABLE offers ALTER COLUMN offer_date DROP NOT NULL",
            "ALTER TABLE offers ALTER COLUMN offered_salary DROP NOT NULL",
            "ALTER TABLE positions ALTER COLUMN department DROP NOT NULL",
            
            # interview_answers table migration for HR / Technical split
            "ALTER TABLE interview_answers ADD COLUMN interview_type VARCHAR(50) DEFAULT 'HR'",
            "ALTER TABLE interview_answers ADD COLUMN interviewer_notes TEXT",
            "ALTER TABLE interview_answers ADD COLUMN red_flags TEXT",
            "ALTER TABLE interview_answers ADD COLUMN ai_summary TEXT",
            
            # position_reports table migration for Candidate reports visibility
            "ALTER TABLE position_reports ADD COLUMN candidate_id INTEGER",
            "ALTER TABLE position_reports ADD COLUMN application_id INTEGER",
            
            # Multi-hotel & dynamic role columns additions (v5)
            "ALTER TABLE users ADD COLUMN role_id INTEGER",
            "ALTER TABLE users ADD COLUMN hotel_access_ids JSON DEFAULT '[]'",
            "ALTER TABLE users ADD COLUMN region_access_ids JSON DEFAULT '[]'",
            "ALTER TABLE users ADD COLUMN department_access_ids JSON DEFAULT '[]'",
            "ALTER TABLE users ADD COLUMN data_visibility_scope VARCHAR(50) DEFAULT 'GLOBAL'",
            
            "ALTER TABLE positions ADD COLUMN hotel_id INTEGER",
            "ALTER TABLE positions ADD COLUMN department_id INTEGER",
            
            "ALTER TABLE applications ADD COLUMN hotel_id INTEGER",
            "ALTER TABLE applications ADD COLUMN ownership_started_at TIMESTAMP",
            "ALTER TABLE applications ADD COLUMN ownership_expires_at TIMESTAMP",
            "ALTER TABLE applications ADD COLUMN extension_count INTEGER DEFAULT 0",
            "ALTER TABLE applications ADD COLUMN lock_status VARCHAR(50) DEFAULT 'UNLOCKED'",
            "ALTER TABLE applications ADD COLUMN utm_source VARCHAR(255)",
            "ALTER TABLE applications ADD COLUMN utm_medium VARCHAR(255)",
            "ALTER TABLE applications ADD COLUMN utm_campaign VARCHAR(255)",
            "ALTER TABLE applications ADD COLUMN utm_content VARCHAR(255)",

            # offers table deviations & approvals (v6 Phase 4)
            "ALTER TABLE offers ADD COLUMN deviation_reason VARCHAR(255)",
            "ALTER TABLE offers ADD COLUMN deviation_explanation TEXT",
            "ALTER TABLE offers ADD COLUMN approved_by JSON DEFAULT '[]'",
            "ALTER TABLE offers ADD COLUMN approval_status VARCHAR(50) DEFAULT 'APPROVED'",

            # Phase 2-3-4 new columns
            "ALTER TABLE applications ADD COLUMN evaluation_deadline TIMESTAMP",
            "ALTER TABLE applications ADD COLUMN routing_level VARCHAR(255)",
            "ALTER TABLE applications ADD COLUMN routed_from_hotel_id INTEGER",

            "ALTER TABLE candidates ADD COLUMN cv_versions JSON DEFAULT '[]'",
            "ALTER TABLE candidates ADD COLUMN phone_normalized VARCHAR(255)",

            "ALTER TABLE match_scores ADD COLUMN skill_score FLOAT",
            "ALTER TABLE match_scores ADD COLUMN certification_score FLOAT",

            "ALTER TABLE staffing_needs ADD COLUMN needed_by DATE",

            # headcount artık FTE tutuyor (2,5 gibi). SQLite tip yakınlığı sayesinde
            # zaten ondalık saklıyor; PostgreSQL'de kolon tipini genişletmek gerek.
            "ALTER TABLE positions ALTER COLUMN headcount TYPE DOUBLE PRECISION"
        ]
        for q in queries:
            try:
                with engine.begin() as conn:
                    # Set short lock timeout (3 seconds) to prevent hanging on PostgreSQL locks
                    try:
                        conn.execute(text("SET lock_timeout = 3000"))
                    except Exception:
                        pass
                    conn.execute(text(q))
                print(f"Database migration: {q} executed.")
            except Exception:
                pass
                    
        # Normalize candidates experience and education if they are plain strings
        try:
            from database import SessionLocal
            db_session = SessionLocal()
            try:
                from routers.candidates import normalize_phone
                candidates = db_session.query(models.Candidate).all()
                for cand in candidates:
                    modified = False
                    # phone_normalized is read by the duplicate and blacklist checks
                    # but was never written, so it was NULL on every row and those
                    # checks only ever matched an identically formatted number.
                    if cand.phone and not cand.phone_normalized:
                        cand.phone_normalized = normalize_phone(cand.phone)
                        modified = True
                    if cand.experience and isinstance(cand.experience, str):
                        cand.experience = [{"title": "Deneyim", "company": "Belirtilmemiş", "years": "", "description": cand.experience}]
                        modified = True
                    if cand.education and isinstance(cand.education, str):
                        cand.education = [{"degree": "Eğitim", "school": cand.education, "year": ""}]
                        modified = True
                    if modified:
                        db_session.add(cand)
                db_session.commit()
                print("[Startup] Candidate phone, experience and education normalized.")

                # Applications added from the position workspace were stored with no
                # hotel_id, and that is the column the hotel filters match on, so
                # they were invisible to the hotel that owns the position.
                orphans = db_session.query(models.Application).filter(
                    models.Application.hotel_id.is_(None),
                    models.Application.position_id.isnot(None),
                ).all()
                if orphans:
                    hotels = dict(db_session.query(models.Position.id, models.Position.hotel_id).all())
                    fixed = 0
                    for a in orphans:
                        hotel_id = hotels.get(a.position_id)
                        if hotel_id:
                            a.hotel_id = hotel_id
                            db_session.add(a)
                            fixed += 1
                    db_session.commit()
                    print(f"[Startup] {fixed} application(s) given the hotel of their position.")

                # 10 günlük değerlendirme süresi: kolon vardı ama hiç yazılmıyordu.
                import datetime as _dt
                undated = db_session.query(models.Application).filter(
                    models.Application.evaluation_deadline.is_(None)
                ).all()
                if undated:
                    for a in undated:
                        start = a.applied_at or _dt.datetime.utcnow()
                        if getattr(start, "tzinfo", None) is not None:
                            start = start.replace(tzinfo=None)
                        a.evaluation_deadline = start + _dt.timedelta(days=10)
                        db_session.add(a)
                    db_session.commit()
                    print(f"[Startup] {len(undated)} application(s) given an evaluation deadline.")

                # Kullanıcıları izin matrisini taşıyan Role satırına bağla. role_id
                # yalnızca seed'deki demo adminde doluydu; check_permission onsuz
                # 403'e düştüğü için roles tablosundaki matris kimseye uygulanmıyordu.
                roles_by_code = {
                    (r.code or "").strip().lower(): r.id
                    for r in db_session.query(models.Role).all()
                }
                if roles_by_code:
                    linked = 0
                    for u in db_session.query(models.User).filter(models.User.role_id.is_(None)).all():
                        role_id = roles_by_code.get((u.role or "").strip().lower())
                        if role_id:
                            u.role_id = role_id
                            db_session.add(u)
                            linked += 1
                    if linked:
                        db_session.commit()
                        print(f"[Startup] {linked} user(s) linked to their role's permissions.")
            except Exception as norm_err:
                db_session.rollback()
                print(f"[Startup] Candidate normalization failed: {norm_err}")
            finally:
                db_session.close()
        except Exception as norm_init_err:
            print(f"[Startup] Candidate normalization initialization failed: {norm_init_err}")

        # Run candidate translation on startup in a background thread
        def run_translations_in_background():
            from database import SessionLocal
            from services.translator import translate_existing_candidates_to_turkish
            db_session = SessionLocal()
            try:
                translate_existing_candidates_to_turkish(db_session)
            except Exception as e:
                print(f"Background translation error: {e}")
            finally:
                db_session.close()

        import threading
        t = threading.Thread(target=run_translations_in_background)
        t.daemon = True
        t.start()
    except Exception as migration_err:
        print(f"Database migrations / translations failed to run on startup: {migration_err}")

    # Ensure demo user exists
    try:
        from database import SessionLocal
        from auth import get_password_hash
        db_session = SessionLocal()
        try:
            demo_user = db_session.query(models.User).filter(models.User.email == "demo@skillmatch.ai").first()
            if demo_user:
                demo_user.hashed_password = get_password_hash("demo123")
                demo_user.role = "ADMIN"
                demo_user.is_active = True
                demo_user.is_verified = True
                print("[Startup] Demo user password reset to demo123.")
            else:
                demo_user = models.User(
                    email="demo@skillmatch.ai",
                    hashed_password=get_password_hash("demo123"),
                    full_name="Demo Admin",
                    role="ADMIN",
                    is_active=True,
                    is_verified=True
                )
                db_session.add(demo_user)
                print("[Startup] Demo user created successfully.")
            db_session.commit()
        except Exception as db_err:
            db_session.rollback()
            print(f"[Startup] Demo user setup failed: {db_err}")
        finally:
            db_session.close()
    except Exception as demo_err:
        print(f"[Startup] Demo user setup package import failed: {demo_err}")

    # Seed multi-hotel hierarchy foundation
    try:
        from database import SessionLocal
        from services.seed import seed_multi_hotel_foundation
        db_session = SessionLocal()
        try:
            seed_multi_hotel_foundation(db_session)
        finally:
            db_session.close()
    except Exception as seed_err:
        print(f"[Startup] Seeding multi-hotel database failed: {seed_err}")

    app = FastAPI(title="SkillMatch AI v4", version="4.0.0", docs_url="/api/docs")

    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    @app.middleware("http")
    async def add_cache_control_header(request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(BASE_DIR, "static")
    templates_dir = os.path.join(BASE_DIR, "templates")
    os.makedirs(static_dir, exist_ok=True)
    os.makedirs(templates_dir, exist_ok=True)
    os.makedirs(os.path.join(static_dir, "uploads"), exist_ok=True)

    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    templates = Jinja2Templates(directory=templates_dir)

    # Routers
    from routers import candidates, positions, analytics, applications, interviews, offers, onboarding, auth, users, ai_recruitment, tasks, calendar, reports, custom_reports, settings, ownership, portal, campaigns, headcount, pipelines, organization_imports, staffing_needs

    # Most endpoints declared their own auth dependency, but ~90 of them never did:
    # offers, applications, interviews, onboarding, most of positions and analytics
    # answered anyone who could reach the port. Requiring login for a whole router
    # is the version that cannot be forgotten on the next endpoint added to it.
    # auth (login) and portal (public job ads + candidates authenticated by their
    # own link token) keep their own rules.
    from auth import get_current_user as _login_required
    staff_only = [Depends(_login_required)]
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(users.router, prefix="/api/users", tags=["users"], dependencies=staff_only)
    app.include_router(settings.router, prefix="/api/settings", tags=["settings"], dependencies=staff_only)
    app.include_router(ownership.router, prefix="/api/ownership", tags=["ownership"], dependencies=staff_only)
    app.include_router(portal.router, prefix="/api/portal", tags=["portal"])
    app.include_router(candidates.router, prefix="/api/candidates", tags=["candidates"], dependencies=staff_only)
    app.include_router(positions.router, prefix="/api/positions", tags=["positions"], dependencies=staff_only)
    app.include_router(reports.router, prefix="/api/reports", tags=["reports"], dependencies=staff_only)
    app.include_router(custom_reports.router, prefix="/api/reports", tags=["custom_reports"], dependencies=staff_only)
    app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"], dependencies=staff_only)
    app.include_router(applications.router, prefix="/api/applications", tags=["applications"], dependencies=staff_only)
    app.include_router(interviews.router, prefix="/api/interviews", tags=["interviews"], dependencies=staff_only)
    app.include_router(interviews.answers_router, prefix="/api/interview-answers", tags=["interview-answers"], dependencies=staff_only)
    app.include_router(offers.router, prefix="/api/offers", tags=["offers"], dependencies=staff_only)
    app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"], dependencies=staff_only)
    app.include_router(ai_recruitment.router, prefix="/api/ai", tags=["ai"], dependencies=staff_only)
    app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"], dependencies=staff_only)
    app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"], dependencies=staff_only)
    app.include_router(campaigns.router, dependencies=staff_only)
    app.include_router(headcount.router, prefix="/api/headcount", tags=["headcount"], dependencies=staff_only)
    app.include_router(pipelines.router, prefix="/api/pipelines", tags=["pipelines"], dependencies=staff_only)
    app.include_router(organization_imports.router, dependencies=staff_only)
    app.include_router(staffing_needs.router, prefix="/api/staffing-needs", tags=["staffing-needs"], dependencies=staff_only)

    from services.chatbot import chatbot_service
    @app.post("/api/chat")
    def chat_endpoint(message: str = Body(..., embed=True), db: Session = Depends(get_db), current_user: models.User = Depends(_login_required)):
        # The chatbot feeds every candidate's name, skills and summary to the model
        # as context, and an anonymous caller used to get the widest scope of all -
        # get_current_user_optional returned None, which skipped the hotel and
        # department filters entirely.
        return {"response": chatbot_service.chat(message, db, current_user)}

    @app.get("/health")
    def health(db: Session = Depends(get_db)):
        db_connected = False
        active_user_count = 0
        candidates_count = 0
        positions_count = 0
        
        try:
            db.execute(text("SELECT 1"))
            db_connected = True
            
            active_user_count = db.query(models.User).filter(models.User.is_active == True).count()
            candidates_count = db.query(models.Candidate).filter(models.Candidate.is_deleted == False).count()
            positions_count = db.query(models.Position).filter(models.Position.is_active == True).count()
        except Exception as e:
            print(f"[Health Check Error] Database status check failed: {e}")
            
        return {
            "status": "ok" if db_connected else "error",
            "version": "4.0.0",
            "commit": COMMIT_HASH,
            "db_connected": db_connected,
            "active_user_count": active_user_count,
            "candidates_count": candidates_count,
            "positions_count": positions_count,
            "features": ["candidate_communication_module"]
        }

    @app.get("/health/db")
    def health_db(db: Session = Depends(get_db)):
        from sqlalchemy import text
        try:
            db.execute(text("SELECT 1"))
            return {"status": "ok", "database": "connected"}
        except Exception as e:
            return {"status": "error", "database": "disconnected", "detail": str(e)}

    @app.get("/", response_class=HTMLResponse)
    def read_root(request: Request):
        return templates.TemplateResponse(request=request, name="index.html", context={"request": request, "commit_hash": COMMIT_HASH})

    @app.get("/{catchall:path}", response_class=HTMLResponse)
    def catchall_route(request: Request, catchall: str):
        if catchall.startswith("api") or catchall.startswith("static"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        return templates.TemplateResponse(request=request, name="index.html", context={"request": request, "commit_hash": COMMIT_HASH})

except Exception as startup_err:
    tb = traceback.format_exc()
    print("=" * 80)
    print("CRITICAL STARTUP ERROR IN MAIN.PY:")
    print(tb)
    print("=" * 80)
    
    # Define fallback app to expose the traceback on HTTP so we can read it on Railway
    app = FastAPI(title="SkillMatch AI v4 - Fallback Diagnostic Server", version="4.0.0")
    
    # The traceback is already on stdout above, which is where Railway's logs
    # read it from. Putting it in the HTTP response as well handed file paths,
    # library versions and sometimes connection strings to anyone who opened the
    # site while it was down, so that only happens with DEBUG on.
    try:
        from config import settings as _settings
        _show_traceback = bool(getattr(_settings, "DEBUG", False))
    except Exception:
        _show_traceback = False

    @app.get("/{rest_of_path:path}")
    def fallback_route(rest_of_path: str):
        if _show_traceback:
            body = f"""
                <h1 style="border-bottom: 2px solid #fcc; padding-bottom: 10px;">Critical Startup Error Traceback</h1>
                <pre style="background: #fff; border: 1px solid #ecc; padding: 15px; overflow-x: auto; border-radius: 4px;">{tb}</pre>
            """
        else:
            body = """
                <h1 style="border-bottom: 2px solid #fcc; padding-bottom: 10px;">Servis şu anda kullanılamıyor</h1>
                <p>Uygulama başlatılamadı. Hata ayrıntıları sunucu kayıtlarında.</p>
            """
        html_content = f"""
        <html>
            <head><title>SkillMatch AI</title></head>
            <body style="font-family: monospace; padding: 20px; background: #fff5f5; color: #900; line-height: 1.5;">
                {body}
                <p style="margin-top: 20px; color: #666; font-size: 12px;">SkillMatch AI v4</p>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=503)
