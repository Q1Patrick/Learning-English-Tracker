"""Request correlation and privacy tests for API error reporting."""

import io
import logging
import sys
from contextlib import contextmanager
from uuid import UUID, uuid4

from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import path
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework.views import APIView

from common.logging import PrivateTracebackFormatter, RequestContextFilter, get_request_id
from common.middleware import RequestIDMiddleware

PRIVATE_MESSAGE = "private learner input that must never reach logs"


class SuccessfulView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"success": True})


class ValidationFailureView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        raise ValidationError({"word": ["This record already exists."]}, code="duplicate_record")


class BrokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        raise ValueError(PRIVATE_MESSAGE)


urlpatterns = [
    path("success/", SuccessfulView.as_view()),
    path("validation/", ValidationFailureView.as_view()),
    path("broken/", BrokenView.as_view()),
]


@contextmanager
def captured_private_logs():
    logger = logging.getLogger("common.exceptions")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.addFilter(RequestContextFilter())
    handler.setFormatter(
        PrivateTracebackFormatter("%(levelname)s request_id=%(request_id)s %(message)s")
    )
    previous_level = logger.level
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    try:
        yield stream
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)
        handler.close()


@override_settings(ROOT_URLCONF=__name__)
class RequestCorrelationTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()

    def assert_uuid_header(self, response):
        request_id = response["X-Request-ID"]
        self.assertEqual(str(UUID(request_id)), request_id)
        return request_id

    def test_success_response_has_request_id(self):
        response = self.client.get("/success/")
        self.assertEqual(response.status_code, 200)
        self.assert_uuid_header(response)

    def test_missing_route_still_has_correlation_header(self):
        response = self.client.get("/does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assert_uuid_header(response)

    def test_context_is_reset_even_when_downstream_raises(self):
        original_context = get_request_id()

        def fail(request):
            raise ValueError(PRIVATE_MESSAGE)

        request = RequestFactory().get("/broken/")
        with self.assertRaises(ValueError):
            RequestIDMiddleware(fail)(request)
        self.assertEqual(get_request_id(), original_context)

    def test_valid_incoming_request_id_is_preserved(self):
        request_id = str(uuid4())
        response = self.client.get("/success/", HTTP_X_REQUEST_ID=request_id)
        self.assertEqual(response["X-Request-ID"], request_id)

    def test_arbitrary_incoming_header_is_replaced(self):
        value = "untrusted text containing private data"
        response = self.client.get("/success/", HTTP_X_REQUEST_ID=value)
        self.assertNotEqual(response["X-Request-ID"], value)
        self.assert_uuid_header(response)

    def test_validation_error_has_stable_code_details_and_request_id(self):
        response = self.client.post("/validation/", {}, format="json")
        self.assertEqual(response.status_code, 400)
        request_id = self.assert_uuid_header(response)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["request_id"], request_id)
        self.assertEqual(response.data["error"]["code"], "duplicate_record")
        self.assertIn("word", response.data["error"]["details"])

    def test_unexpected_error_is_logged_without_exception_message(self):
        request_id = str(uuid4())
        with captured_private_logs() as stream:
            response = self.client.get("/broken/", HTTP_X_REQUEST_ID=request_id)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data["error"]["code"], "internal_error")
        self.assertEqual(response.data["request_id"], request_id)
        self.assertEqual(response["X-Request-ID"], request_id)
        self.assertNotIn(PRIVATE_MESSAGE, str(response.data))
        logs = stream.getvalue()
        self.assertIn(request_id, logs)
        self.assertIn("ValueError", logs)
        self.assertIn("test_observability.py", logs)
        self.assertNotIn(PRIVATE_MESSAGE, logs)

    def test_request_context_does_not_leak_to_next_request_or_background_log(self):
        first_id = str(uuid4())
        self.client.get("/success/", HTTP_X_REQUEST_ID=first_id)
        record = logging.LogRecord("background", logging.INFO, __file__, 1, "done", (), None)
        self.assertTrue(RequestContextFilter().filter(record))
        self.assertNotEqual(record.request_id, first_id)
        next_response = self.client.get("/success/")
        self.assertNotEqual(next_response["X-Request-ID"], first_id)


class PrivateLoggingTests(SimpleTestCase):
    @override_settings(
        SECRET_KEY="test-secret-key-never-log-this-value",
        OPENAI_API_KEY="test-provider-key-never-log-this-value",
    )
    def test_configured_secrets_bearer_and_jwt_are_redacted(self):
        bearer = "private-access-token-value"
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiMSJ9.c2lnbmF0dXJl"
        message = (
            "key=test-provider-key-never-log-this-value "
            "secret=test-secret-key-never-log-this-value "
            f"Authorization: Bearer {bearer} jwt={jwt}"
        )
        record = logging.LogRecord("audit", logging.INFO, __file__, 1, message, (), None)
        RequestContextFilter().filter(record)
        rendered = PrivateTracebackFormatter("%(request_id)s %(message)s").format(record)
        for value in (
            "test-provider-key-never-log-this-value",
            "test-secret-key-never-log-this-value",
            bearer,
            jwt,
        ):
            with self.subTest(value_type=value.split("-")[0]):
                self.assertNotIn(value, rendered)

    def test_traceback_retains_location_and_type_without_exception_value(self):
        try:
            raise ValueError(PRIVATE_MESSAGE)
        except ValueError:
            record = logging.LogRecord(
                "audit", logging.ERROR, __file__, 1, "Operation failed", (), sys.exc_info()
            )
        rendered = PrivateTracebackFormatter("%(message)s").format(record)
        self.assertIn("ValueError", rendered)
        self.assertIn("test_observability.py", rendered)
        self.assertNotIn(PRIVATE_MESSAGE, rendered)
