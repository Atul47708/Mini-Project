import json
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from backend.config import MYSQL_URL, SQLITE_URL

logger = logging.getLogger("Database")
logging.basicConfig(level=logging.INFO)

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True)
    title = Column(String(255), default="Untitled Music Narrative")
    filename = Column(String(255), nullable=False)
    audio_path = Column(Text, nullable=False)
    video_path = Column(Text, nullable=True)
    duration = Column(Float, default=0.0)
    bpm = Column(Float, default=120.0)
    musical_style = Column(String(128), default="Cinematic")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Serialized JSON representations
    analysis_json = Column(Text, nullable=True)
    narrative_json = Column(Text, nullable=True)
    scenes_json = Column(Text, nullable=True)
    sync_json = Column(Text, nullable=True)

# Engine initialization with automatic fallback
def init_engine():
    try:
        # First attempt to connect to MySQL if configured
        engine = create_engine(MYSQL_URL, pool_recycle=3600, pool_pre_ping=True)
        with engine.connect() as conn:
            pass
        logger.info(f"Successfully connected to MySQL database: {MYSQL_URL.split('@')[-1]}")
        return engine
    except Exception as e:
        logger.warning(f"MySQL connection not available ({e}). Falling back to SQLite database at {SQLITE_URL}")
        sqlite_engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
        return sqlite_engine

engine = init_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
