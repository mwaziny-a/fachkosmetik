from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        detail = exc.detail
        if isinstance(detail, dict):
            return JSONResponse(
                status_code=exc.status_code,
                content={"success": False, "error": detail},
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": str(detail)},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception on {request.url}: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "An unexpected error occurred. Please try again.",
            },
        )