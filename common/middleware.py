"""Attach a safe correlation ID to requests, responses, and logs."""

import logging
import time
import uuid

from .logging import request_id_context

logger = logging.getLogger(__name__)


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            request_id = str(uuid.UUID(request.headers.get("X-Request-ID", "")))
        except (ValueError, TypeError, AttributeError):
            request_id = str(uuid.uuid4())
        request.request_id = request_id
        token = request_id_context.set(request_id)
        started = time.monotonic()
        try:
            response = self.get_response(request)
            response["X-Request-ID"] = request_id
            view_name = getattr(getattr(request, "resolver_match", None), "view_name", "unresolved")
            logger.info(
                "request method=%s view=%s status=%s elapsed_ms=%.1f",
                request.method,
                view_name,
                response.status_code,
                (time.monotonic() - started) * 1000,
            )
            return response
        finally:
            request_id_context.reset(token)
