"""Request context and tracebacks without private exception payloads."""

import logging
import re
import traceback
from contextvars import ContextVar

from django.conf import settings

request_id_context = ContextVar("request_id", default="-")


def get_request_id():
    return request_id_context.get()


class RequestContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_request_id()
        if record.request_id == "-":
            record.request_id = getattr(getattr(record, "request", None), "request_id", "-")
        message = record.getMessage()
        for name in ("OPENAI_API_KEY", "SECRET_KEY"):
            secret = getattr(settings, name, "")
            if secret:
                message = message.replace(secret, "[REDACTED]")
        message = re.sub(r"(?i)Bearer\s+\S+", "Bearer [REDACTED]", message)
        message = re.sub(
            r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[REDACTED JWT]", message
        )
        record.msg, record.args = message, ()
        return True


class PrivateTracebackFormatter(logging.Formatter):
    def formatException(self, exc_info):
        exception_type, _, tb = exc_info
        frames = traceback.extract_tb(tb)
        stack = "\n".join(
            f'  File "{frame.filename}", line {frame.lineno}, in {frame.name}' for frame in frames
        )
        return f"Traceback (most recent call last):\n{stack}\n{exception_type.__name__}"
