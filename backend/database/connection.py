import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.config import MYSQL_URL, SQLITE_URL
from backend.database.models import Base

logger = logging.getLogger("Database")
logging.basicConfig(level=logging.INFO)

def create_database_engine():
    """
    Attempts to connect to MySQL first.
    If MySQL is unreachable or disabled, falls back seamlessly to SQLite.
    """
    if not MYSQL_URL or not MYSQL_URL.startswith("mysql"):
        logger.info(f"Database: Using SQLite database at {SQLITE_URL}")
        return create_engine(SQLITE_URL, connect_args={"check_same_thread": False})

    try:
        engine = create_engine(
            MYSQL_URL,
            pool_recycle=3600,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 2}
        )
        # Test connection
        with engine.connect() as conn:
            pass
        logger.info(f"Database: Connected to MySQL ({MYSQL_URL.split('@')[-1] if '@' in MYSQL_URL else MYSQL_URL})")
        return engine
    except Exception as e:
        logger.warning(f"Database: MySQL unavailable ({e}). Using SQLite fallback at {SQLITE_URL}")
        sqlite_engine = create_engine(
            SQLITE_URL,
            connect_args={"check_same_thread": False}
        )
        return sqlite_engine

engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")

def get_db():
    """Dependency for database session in FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
