"""FastAPI application main entry point."""

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import get_settings
from src.api.routes import health, query
from src.api.middleware.logging import LoggingMiddleware
from src.api.middleware.rate_limit import RateLimitMiddleware
from src.utils.logger import configure_logging

settings = get_settings()

# Configure logging
configure_logging(settings.LOG_LEVEL)
logger = structlog.get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Lanka Legal Analyst API",
    description="Agentic RAG system for Sri Lankan Law",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add middleware (order matters - last added is first executed)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error("Unhandled exception", exc_info=exc, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


# Include routers
app.include_router(health.router, prefix=settings.API_PREFIX, tags=["health"])
app.include_router(query.router, prefix=settings.API_PREFIX, tags=["query"])


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Starting Lanka Legal Analyst API", environment=settings.ENVIRONMENT)


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down Lanka Legal Analyst API")

