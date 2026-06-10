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
