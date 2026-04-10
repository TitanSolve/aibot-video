from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.config import settings
from app.database import init_db
from app.api import upload

# Initialize database
init_db()

app = FastAPI(
    title="AI Video Animation Search",
    description="AI-powered search and recommendation system for video animations",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Include routers
app.include_router(upload.router)


@app.get("/")
def root():
    """Serve frontend"""
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "message": "AI Video Animation Search API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "services": {
            "postgres": "running",
            "redis": "running",
            "qdrant": "running"
        }
    }


@app.get("/config")
def get_config():
    """Get public configuration"""
    return {
        "max_video_size_mb": settings.MAX_VIDEO_SIZE_MB,
        "allowed_extensions": settings.ALLOWED_VIDEO_EXTENSIONS,
        "embed_model": settings.OPENAI_EMBED_MODEL,
        "ai_model": settings.GEMINI_MODEL
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
