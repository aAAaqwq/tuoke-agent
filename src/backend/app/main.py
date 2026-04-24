from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.routers.health import router as health_router
from app.routers.prospects import router as prospects_router

app = FastAPI(title="Tuoke Agent Backend", version="0.1.0")
"""Main FastAPI application for the Tuoke Agent backend."""

HTTP_ERROR_CODE_MAP = {
    status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
    status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
    status.HTTP_403_FORBIDDEN: "FORBIDDEN",
    status.HTTP_404_NOT_FOUND: "NOT_FOUND",
    status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
    status.HTTP_409_CONFLICT: "CONFLICT",
    status.HTTP_429_TOO_MANY_REQUESTS: "TOO_MANY_REQUESTS",
}


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(
    request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    message = "; ".join(
        f"{'.'.join(str(part) for part in detail['loc'][1:])}: {detail['msg']}"
        for detail in error.errors()
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "code": "VALIDATION_ERROR",
            "message": message,
            "data": None,
        },
    )


@app.exception_handler(HTTPException)
@app.exception_handler(StarletteHTTPException)
async def handle_http_exception(
    request: Request,
    error: HTTPException | StarletteHTTPException,
) -> JSONResponse:
    message = error.detail if isinstance(error.detail, str) else "request failed"
    code = HTTP_ERROR_CODE_MAP.get(error.status_code, "HTTP_ERROR")
    return JSONResponse(
        status_code=error.status_code,
        content={
            "code": code,
            "message": message,
            "data": None,
        },
    )


app.include_router(health_router, prefix="/api/v1")
app.include_router(prospects_router, prefix="/api/v1")
