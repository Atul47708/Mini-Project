import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# App Info
APP_TITLE = "Secure Multimodal AI Companion"
APP_VERSION = "1.0.0"

# Directories
STORAGE_DIR = BASE_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
AUDIO_CACHE_DIR = STORAGE_DIR / "audio_cache"
VECTOR_STORE_DIR = STORAGE_DIR / "vector_store"

for directory in [STORAGE_DIR, UPLOADS_DIR, AUDIO_CACHE_DIR, VECTOR_STORE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Model Settings
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-004")

# Database URLs
MYSQL_URL = os.getenv(
    "MYSQL_URL",
    "mysql+pymysql://root:password@localhost:3306/multimodal_companion"
)
SQLITE_URL = f"sqlite:///{STORAGE_DIR / 'companion.db'}"

# Limits and Configuration
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

RAG_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "700"))
RAG_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))

APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
