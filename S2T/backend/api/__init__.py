from .projects import router as projects_router
from .transcribe import router as transcribe_router
from .audio import router as audio_router
from .llm import router as llm_router
from .websocket_routes import router as ws_router

__all__ = ['projects_router', 'transcribe_router', 'audio_router', 'llm_router', 'ws_router']