"""
Main FastAPI application entry point.

This file is intentionally minimal during scaffold initialization.
Routes and services will be implemented in later phases.
"""

from fastapi import FastAPI


app = FastAPI(
    title="AI Interview Assistant API",
    version="1.0.0",
    description=(
        "Backend API for the AI-Powered Interview Preparation and "
        "Career Readiness Assistant."
    ),
)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "ok"}
