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
COMMIT_HASH = "6e8dab7_prod"
try:
    import subprocess
    git_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("utf-8").strip()
    if git_hash:
        COMMIT_HASH = git_hash
except Exception:
    pass

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
            "ALTER TABLE positions ALTER COLUMN department DROP NOT NULL"
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
                candidates = db_session.query(models.Candidate).all()
                for cand in candidates:
                    modified = False
                    if cand.experience and isinstance(cand.experience, str):
                        cand.experience = [{"title": "Deneyim", "company": "Belirtilmemiş", "years": "", "description": cand.experience}]
                        modified = True
                    if cand.education and isinstance(cand.education, str):
                        cand.education = [{"degree": "Eğitim", "school": cand.education, "year": ""}]
                        modified = True
                    if modified:
                        db_session.add(cand)
                db_session.commit()
                print("[Startup] Candidate experience and education normalized.")
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
    from routers import candidates, positions, analytics, applications, interviews, offers, onboarding, auth, users, ai_recruitment, tasks
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(users.router, prefix="/api/users", tags=["users"])
    app.include_router(candidates.router, prefix="/api/candidates", tags=["candidates"])
    app.include_router(positions.router, prefix="/api/positions", tags=["positions"])
    app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
    app.include_router(applications.router, prefix="/api/applications", tags=["applications"])
    app.include_router(interviews.router, prefix="/api/interviews", tags=["interviews"])
    app.include_router(offers.router, prefix="/api/offers", tags=["offers"])
    app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"])
    app.include_router(ai_recruitment.router, prefix="/api/ai", tags=["ai"])
    app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])

    from services.chatbot import chatbot_service
    @app.post("/api/chat")
    def chat_endpoint(message: str = Body(..., embed=True), db: Session = Depends(get_db)):
        return {"response": chatbot_service.chat(message, db)}

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
    
    @app.get("/{rest_of_path:path}")
    def fallback_route(rest_of_path: str):
        html_content = f"""
        <html>
            <head><title>Startup Error Traceback</title></head>
            <body style="font-family: monospace; padding: 20px; background: #fff5f5; color: #900; line-height: 1.5;">
                <h1 style="border-bottom: 2px solid #fcc; padding-bottom: 10px;">Critical Startup Error Traceback</h1>
                <pre style="background: #fff; border: 1px solid #ecc; padding: 15px; overflow-x: auto; border-radius: 4px;">{tb}</pre>
                <p style="margin-top: 20px; color: #666; font-size: 12px;">SkillMatch AI v4 - Fallback Diagnostic Server</p>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=200)
