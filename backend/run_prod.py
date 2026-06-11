import sys
import os
import traceback

# Add current directory and 'backend' directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
backend_dir = os.path.join(current_dir, "backend")
if os.path.exists(backend_dir):
    sys.path.insert(0, backend_dir)

print("Starting production runner...")
print("sys.path:", sys.path)

try:
    # 1. Connect to database and run create_all
    print("Testing database connection and running metadata create_all...")
    from database import engine, Base
    import models
    Base.metadata.create_all(bind=engine)
    print("Metadata create_all completed successfully.")

    # 2. Run migrations
    print("Running database migrations...")
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
        "ALTER TABLE candidates ADD COLUMN deleted_by VARCHAR(255)"
    ]
    for q in queries:
        try:
            with engine.begin() as conn:
                conn.execute(text(q))
            print(f"Executed: {q}")
        except Exception as q_err:
            print(f"Skipped/Failed {q}: {q_err}")

    # 3. Start uvicorn
    print("Starting uvicorn server...")
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    # Import app to verify it imports successfully before passing it to uvicorn
    from main import app
    uvicorn.run("main:app", host="0.0.0.0", port=port)

except Exception as e:
    tb = traceback.format_exc()
    print("=" * 80)
    print("CRITICAL RUNTIME ERROR AT STARTUP:")
    print(tb)
    print("=" * 80)
    
    # Try to write error log to the production database so we can fetch it via API
    try:
        from database import SessionLocal
        import models
        db = SessionLocal()
        # Clean any aborted transactions if any
        db.rollback()
        log = models.Log(
            action="startup_crash",
            target_type="system",
            target_id=0,
            details={"traceback": tb}
        )
        db.add(log)
        db.commit()
        db.close()
        print("Successfully logged startup crash to the database.")
    except Exception as db_err:
        print("Failed to log crash to database:", db_err)
    
    sys.exit(1)
