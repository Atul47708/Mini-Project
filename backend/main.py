from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import APP_TITLE, APP_VERSION, STORAGE_DIR, AUDIO_CACHE_DIR, UPLOADS_DIR, GEMINI_API_KEY
from backend.database.connection import init_db, engine
from backend.database.schemas import HealthResponse
from backend.routes.chat import router as chat_router
from backend.routes.documents import router as documents_router
from backend.routes.media import router as media_router
from backend.routes.conversations import router as conversations_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database
    logger.info("Initializing database tables...")
    init_db()
    yield
    # Shutdown
    logger.info("Application shutting down.")

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="Intelligent, empathetic, and privacy-conscious Multimodal AI Companion powered by Gemini and RAG.",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static storage directories for audio playback and image previews
app.mount("/storage/audio_cache", StaticFiles(directory=str(AUDIO_CACHE_DIR)), name="audio_cache")
app.mount("/storage/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Include Routers
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(media_router)
app.include_router(conversations_router)

@app.get("/", tags=["Root"])
def root():
    return {
        "app": APP_TITLE,
        "version": APP_VERSION,
        "status": "online",
        "docs_url": "/docs"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Verify application health, database connectivity, and API configuration."""
    db_status = "connected"
    try:
        with engine.connect() as conn:
            pass
    except Exception as e:
        db_status = f"unhealthy: {e}"

    return HealthResponse(
        status="healthy" if "unhealthy" not in db_status else "degraded",
        version=APP_VERSION,
        database=db_status,
        gemini_api_configured=bool(GEMINI_API_KEY)
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
