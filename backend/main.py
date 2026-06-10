import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import os
from database import engine, Base, get_db
import models

Base.metadata.create_all(bind=engine)

# Auto-migrate database schema additions
try:
    from sqlalchemy import text
    with engine.connect() as conn:
        queries = [
            "ALTER TABLE candidates ADD COLUMN ai_profile_summary TEXT",
            "ALTER TABLE interviews ADD COLUMN raw_notes TEXT",
            "ALTER TABLE interviews ADD COLUMN cleaned_notes TEXT",
            "ALTER TABLE interviews ADD COLUMN communication_assessment TEXT",
            "ALTER TABLE interviews ADD COLUMN culture_fit_assessment TEXT",
            "ALTER TABLE interviews ADD COLUMN technical_assessment TEXT",
            "ALTER TABLE interviews ADD COLUMN ai_recommendation VARCHAR(255)",
            "ALTER TABLE interviews ADD COLUMN next_step VARCHAR(255)"
        ]
        for q in queries:
            try:
                conn.execute(text(q))
                if hasattr(conn, "commit"):
                    conn.commit()
                print(f"Database migration: {q} executed.")
            except Exception:
                pass
except Exception as migration_err:
    print(f"Database migrations failed to run on startup: {migration_err}")


app = FastAPI(title="SkillMatch AI v4", version="4.0.0", docs_url="/api/docs")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(
    directory=templates_dir,
    variable_start_string='((',
    variable_end_string='))'
)

# Routers
from routers import candidates, positions, analytics, applications, interviews, offers, onboarding, auth
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(candidates.router, prefix="/api/candidates", tags=["candidates"])
app.include_router(positions.router, prefix="/api/positions", tags=["positions"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(applications.router, prefix="/api/applications", tags=["applications"])
app.include_router(interviews.router, prefix="/api/interviews", tags=["interviews"])
app.include_router(offers.router, prefix="/api/offers", tags=["offers"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"])

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
