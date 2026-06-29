"""
FastAPI application entry point.

Registers all routers, middleware, and startup events.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware.error_handler import register_error_handlers
from api.routes.auth_routes import router as auth_router
from api.routes.interview_routes import router as interview_router
from api.routes.evaluation_routes import router as evaluation_router
from api.routes.recommendation_routes import router as recommendation_router
from api.routes.analytics_routes import router as analytics_router
from api.routes.competency_routes import router as competency_router
from api.routes.benchmark_routes import router as benchmark_router
from database.db_setup import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    print("Database initialized")
    yield
    print("Application shutdown")


app = FastAPI(
    title="AI Interview Assistant API",
    version="1.0.0",
    description=(
        "AI-Powered Interview Preparation and Career Readiness Assistant. "
        "Competency-driven adaptive interview evaluation with explainable "
        "multi-dimensional NLP scoring."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handlers
register_error_handlers(app)

# Routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(interview_router, prefix="/api/interview", tags=["Interview"])
app.include_router(evaluation_router, prefix="/api/evaluation", tags=["Evaluation"])
app.include_router(recommendation_router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(competency_router, prefix="/api/competencies", tags=["Competencies"])
app.include_router(benchmark_router, prefix="/api/benchmark", tags=["Benchmark"])


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    """Root endpoint with API info."""
    return {
        "name": "AI Interview Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
    }
