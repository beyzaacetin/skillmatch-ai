from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"Connecting to database: {SQLALCHEMY_DATABASE_URL.split('@')[-1] if '@' in SQLALCHEMY_DATABASE_URL else SQLALCHEMY_DATABASE_URL}")

connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args=connect_args
    )
else:
    # Check if external Railway URL (usually contains 'railway.app' or 'up.railway.app', does not contain 'internal')
    is_external = ("internal" not in SQLALCHEMY_DATABASE_URL) and ("localhost" not in SQLALCHEMY_DATABASE_URL)
    if is_external:
        connect_args["sslmode"] = "require"
        
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10
    )

# Clear startup database test query
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        print("Database connection test successful (SELECT 1).")
        
    # Run automatic dynamic migration for positions table
    from sqlalchemy import inspect
    inspector = inspect(engine)
    if "positions" in inspector.get_table_names():
        existing_cols = [c["name"].lower() for c in inspector.get_columns("positions")]
        cols_to_add = [
            ("employment_type", "VARCHAR(255)"),
            ("contract_type", "VARCHAR(255)"),
            ("accommodation", "VARCHAR(255)"),
            ("salary_target", "INTEGER"),
            ("offer_approval_rule", "VARCHAR(255)"),
            ("pipeline_template", "VARCHAR(255)"),
            ("department_manager", "VARCHAR(255)"),
            ("rule_no_tech_without_hr", "BOOLEAN DEFAULT FALSE"),
            ("rule_approve_outside_band", "BOOLEAN DEFAULT FALSE"),
            ("rule_notify_new_application", "BOOLEAN DEFAULT FALSE"),
            ("job_ad_title", "VARCHAR(255)"),
            ("job_ad_description", "TEXT"),
            ("application_form_fields", "TEXT"),
            ("job_ad_language", "VARCHAR(255)"),
            ("channel_link_qr", "BOOLEAN DEFAULT FALSE"),
            ("channel_career_portal", "BOOLEAN DEFAULT FALSE"),
            ("channel_linkedin", "BOOLEAN DEFAULT FALSE"),
            ("qr_code_path", "VARCHAR(255)")
        ]
        with engine.begin() as conn:
            for col_name, col_type in cols_to_add:
                if col_name.lower() not in existing_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE positions ADD COLUMN {col_name} {col_type}"))
                        print(f"Migration: added column {col_name} to positions table.")
                    except Exception as ex:
                        print(f"Migration warning: failed to add column {col_name}: {ex}")
except Exception as e:
    print(f"Database connection test failed on startup: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
