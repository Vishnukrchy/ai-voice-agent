import uuid

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.logger import logger


def register_exception_handlers(app: FastAPI) -> None:
    """Registers centralized exception handlers so every error path
    returns a consistent JSON shape and is logged with a correlation id."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        error_id = str(uuid.uuid4())
        logger.warning(f"[{error_id}] Validation error on {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error_id": error_id, "detail": exc.errors(), "message": "Validation failed"},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        error_id = str(uuid.uuid4())
        if exc.status_code >= 500:
            logger.error(f"[{error_id}] HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error_id": error_id, "message": exc.detail},
        )

    @app.exception_handler(SQLAlchemyError)
    async def db_exception_handler(request: Request, exc: SQLAlchemyError):
        error_id = str(uuid.uuid4())
        logger.error(f"[{error_id}] Database error on {request.url.path}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error_id": error_id, "message": "A database error occurred"},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        error_id = str(uuid.uuid4())
        logger.exception(f"[{error_id}] Unhandled exception on {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error_id": error_id, "message": "Internal server error"},
        )
