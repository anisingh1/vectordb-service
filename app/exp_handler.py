import sys
from fastapi import Request
from fastapi.responses import JSONResponse
from moderator.interface import (ErrorResponse)
import uuid

from .utils.log import Logger
logger = Logger()


async def unhandledExceptionHandler(request: Request, exc: Exception) -> JSONResponse:
    """
    This middleware will log all unhandled exceptions.
    Unhandled exceptions are all exceptions that are not HTTPExceptions or RequestValidationErrors.
    """
    id = str(uuid.uuid4())
    exception_type, exception_value, exception_traceback = sys.exc_info()
    exception_name = getattr(exception_type, "__name__", None)
    response = ErrorResponse(request_id=id, code=str(500000), error=str(exception_name)).model_dump()
    logger.error(response)
    return JSONResponse(response, status_code=500)