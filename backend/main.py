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
            "ALTER TABLE candidates ADD COLUMN ai_profile_summary TEXT",
            "ALTER TABLE interviews ADD COLUMN raw_notes TEXT",
            "ALTER TABLE interviews ADD COLUMN cleaned_notes TEXT",
            "ALTER TABLE interviews ADD COLUMN communication_assessment TEXT",
            "ALTER TABLE interviews ADD COLUMN culture_fit_assessment TEXT",
            "ALTER TABLE interviews ADD COLUMN technical_assessment TEXT",
            "ALTER TABLE interviews ADD COLUMN ai_recommendation VARCHAR(255)",
            "ALTER TABLE interviews ADD COLUMN next_step VARCHAR(255)",
            "ALTER TABLE candidates ADD COLUMN cv_file_path TEXT",
            "ALTER TABLE candidates ADD COLUMN cv_file_data TEXT",
            "ALTER TABLE candidates ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE",
            "ALTER TABLE candidates ADD COLUMN deleted_at TIMESTAMP",
            "ALTER TABLE candidates ADD COLUMN deleted_by VARCHAR(255)",
            "UPDATE applications SET status = 'hr_interview' WHERE status = 'interview'"
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

    app = FastAPI(title="SkillMatch AI v4", version="4.0.0", docs_url="/api/docs")

    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

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
    def health(): return {"status": "ok", "version": "4.0.0"}

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
        return templates.TemplateResponse(request=request, name="index.html", context={"request": request})

    @app.get("/{catchall:path}", response_class=HTMLResponse)
    def catchall_route(request: Request, catchall: str):
        if catchall.startswith("api") or catchall.startswith("static"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        return templates.TemplateResponse(request=request, name="index.html", context={"request": request})

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
