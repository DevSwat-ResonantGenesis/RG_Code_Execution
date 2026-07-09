# Code Execution Microservice - Main Application

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .security import require_internal_key
from .routers import code

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print(f"🚀 Starting {settings.SERVICE_NAME} v{settings.VERSION}...")
    yield
    print(f"👋 Shutting down {settings.SERVICE_NAME}...")

app = FastAPI(
    title="Code Execution Microservice",
    description="Isolated code execution, terminal commands, and preview server management",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# /terminal/execute and /preview/* are disabled: they ran arbitrary shell
# commands directly on this container (which also has /var/run/docker.sock
# mounted) with no real caller authentication - the chat UI's client calls
# them without ever sending x-internal-service-key, so require_internal_key
# never actually gated the traffic that mattered. Only /code/execute (the
# per-run sandboxed Docker path in executor.py) is mounted now.
_internal_only = [Depends(require_internal_key)]
app.include_router(code.router, prefix="/code", tags=["Code Execution"], dependencies=_internal_only)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
        "status": "ok"
    }

@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
        "endpoints": {
            "code_execute": "/code/execute",
            "terminal_execute": "/terminal/execute",
            "preview_start": "/preview/start",
            "preview_stop": "/preview/stop",
            "health": "/health"
        }
    }
