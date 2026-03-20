# Code Execution Microservice - Main Application

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .routers import code, terminal, preview

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

# Include routers
app.include_router(code.router, prefix="/code", tags=["Code Execution"])
app.include_router(terminal.router, prefix="/terminal", tags=["Terminal"])
app.include_router(preview.router, prefix="/preview", tags=["Preview"])

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
