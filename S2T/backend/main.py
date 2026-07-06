import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager

from config.settings import get_settings
from models.database import init_db
from api.projects import router as projects_router
from api.realtime_routes import router as realtime_router
from api.llm import router as llm_router
from api.transcribe import router as transcribe_router
from api.viewpoint import router as viewpoint_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting S2T Server...")
    print(f"API: http://localhost:8000")
    
    init_db()
    print("Database initialized")
    
    upload_dir = Path(settings.storage.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    print(f"Upload directory: {upload_dir}")
    
    yield
    
    print("Server shutting down...")


app = FastAPI(
    title="S2T API",
    description="语音转写系统 API",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router)
app.include_router(realtime_router)
app.include_router(llm_router)
app.include_router(transcribe_router)
app.include_router(viewpoint_router)


@app.get("/")
async def root():
    return {
        "message": "S2T API is running",
        "version": "2.0.0",
        "status": "active"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/config")
async def get_config_info():
    return {
        "llm_provider": settings.llm.provider,
        "asr_engine": settings.asr.engine,
        "max_concurrent": settings.asr.max_concurrent,
        "supported_formats": settings.audio.supported_formats
    }


@app.get("/api/config")
async def get_api_config_info():
    return {
        "llm_provider": settings.llm.provider,
        "asr_engine": settings.asr.engine,
        "max_concurrent": settings.asr.max_concurrent,
        "supported_formats": settings.audio.supported_formats
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        reload=True
    )