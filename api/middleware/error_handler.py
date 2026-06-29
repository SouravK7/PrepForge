"""
Global error handler middleware.

Converts exceptions to structured JSON responses.
All errors follow a consistent format.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError


def register_error_handlers(app: FastAPI) -> None:
    """
    Register global error handlers on the FastAPI app.

    Args:
        app: FastAPI application instance.
    """

    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request, exc: ValueError
    ) -> JSONResponse:
        """Handle ValueError as 400 Bad Request."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Bad Request",
                "detail": str(exc),
            },
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(
        request: Request, exc: IntegrityError
    ) -> JSONResponse:
        """Handle database integrity errors as 409 Conflict."""
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "Conflict",
                "detail": "A record with this data already exists.",
            },
        )

    @app.exception_handler(FileNotFoundError)
    async def not_found_error_handler(
        request: Request, exc: FileNotFoundError
    ) -> JSONResponse:
        """Handle FileNotFoundError as 404."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "Not Found",
                "detail": str(exc),
            },
        )

    @app.exception_handler(Exception)
    async def general_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected errors as 500."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred.",
            },
        )
