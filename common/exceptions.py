"""Stable API errors with request IDs; keep unexpected exception details in logs."""

import logging

from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler, set_rollback

from .logging import get_request_id

logger = logging.getLogger(__name__)


class APIError(APIException):
    def __init__(self, message, code, status_code=400):
        self.status_code = status_code
        super().__init__(detail=message, code=code)


def _first_code(codes):
    if isinstance(codes, dict):
        return next((_first_code(value) for value in codes.values()), "error")
    if isinstance(codes, list):
        return _first_code(codes[0]) if codes else "error"
    return str(codes)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    request = context.get("request")
    request_id = getattr(request, "request_id", get_request_id())
    if response is None:
        set_rollback()
        logger.error(
            "Unhandled API exception (%s)",
            type(exc).__name__,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        code, message, details = "internal_error", "An unexpected error occurred.", None
        response = Response(status=500)
    else:
        details = response.data
        code = _first_code(exc.get_codes()) if isinstance(exc, APIException) else "error"
        if isinstance(exc, ValidationError):
            message = "Check the submitted fields."
            if code in {"invalid", "required", "blank", "null", "error"}:
                code = "validation_error"
        elif isinstance(details, dict):
            message = str(details.get("detail", "The request could not be processed."))
        else:
            message = str(details)
    response.data = {
        "success": False,
        "error": {"code": code, "message": message, "details": details},
        "request_id": request_id,
    }
    response["X-Request-ID"] = request_id
    return response
