import sqlite3
import os

def migrate():
    # Try multiple common relative paths for sqlite database file
    db_paths = ["backend/skillmatch.db", "skillmatch.db", "../backend/skillmatch.db"]
    db_path = None
    for p in db_paths:
        if os.path.exists(p):
            db_path = p
            break
            
    if not db_path:
        print("No database file found to migrate.")
        return

    print(f"Migrating database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get columns of applications
    cursor.execute("PRAGMA table_info(applications)")
    cols = [c[1] for c in cursor.fetchall()]

    # Add UTM columns if missing
    utm_cols = ["utm_source", "utm_medium", "utm_campaign", "utm_content"]
    for col in utm_cols:
        if col not in cols:
            print(f"Adding column {col} to applications table...")
            cursor.execute(f"ALTER TABLE applications ADD COLUMN {col} TEXT")

    conn.commit()
    conn.close()
    print("Migration check completed successfully.")

if __name__ == "__main__":
    migrate()
