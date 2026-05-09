# applaunch-api/main.py
"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import get_settings
from routers import apps, builds, credentials


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown events."""
    settings = get_settings()
    print(f"AppLaunch API starting [{settings.environment}]")
    yield
    print("AppLaunch API shutting down")


settings = get_settings()

app = FastAPI(
    title="AppLaunch API",
    version="0.1.0",
    description="Deploy LLM-generated mobile apps to Android & iOS stores.",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url=None,
)

# CORS — allow the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)

# Routers
app.include_router(apps.router)
app.include_router(builds.router)
app.include_router(credentials.router)


@app.get("/health", tags=["infra"])
async def health():
    """Railway health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}
