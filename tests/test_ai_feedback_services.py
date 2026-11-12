from types import SimpleNamespace
from unittest.mock import patch

import httpx
from django.test import SimpleTestCase, override_settings
from openai import (
    APIConnectionError,
    APIResponseValidationError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    RateLimitError,
)

from apps.ai_feedback.schemas import EnglishFeedbackSchema
from apps.ai_feedback.services import generate_ai_feedback
from common.exceptions import APIError

FEEDBACK = {
    "corrected_text": "I went to school yesterday.",
    "overall_feedback": "Good attempt.",
    "grammar_score": 80,
    "vocabulary_score": 75,
    "clarity_score": 85,
    "mistakes": [
        {
            "original": "go",
            "correction": "went",
            "explanation": "Use the past tense with yesterday.",
        }
    ],
    "suggestions": ["Practice irregular past tense verbs."],
}


@override_settings(
    OPENAI_API_KEY="unit-test-key",
    OPENAI_MODEL="unit-test-model",
    OPENAI_TIMEOUT_SECONDS=5,
    OPENAI_MAX_RETRIES=1,
)
class AIFeedbackProviderTests(SimpleTestCase):
    def setUp(self):
        self.client_patch = patch("apps.ai_feedback.services.OpenAI")
        self.client_factory = self.client_patch.start()
        self.addCleanup(self.client_patch.stop)
        self.client = self.client_factory.return_value.__enter__.return_value
        self.client.responses.parse.return_value = SimpleNamespace(
            status="completed",
            output=[],
            output_parsed=EnglishFeedbackSchema(**FEEDBACK),
        )
        self.request = httpx.Request("POST", "https://api.openai.com/v1/responses")

    def test_returns_validated_data_and_configures_timeout(self):
        result = generate_ai_feedback("I go to school yesterday.", english_level="B1")
        self.assertEqual(result["grammar_score"], 80)
        self.assertEqual(result["mistakes"][0]["correction"], "went")
        self.assertEqual(result["model_name"], "unit-test-model")
        self.client_factory.assert_called_once_with(
            api_key="unit-test-key", timeout=5, max_retries=1
        )
        args = self.client.responses.parse.call_args.kwargs
        self.assertEqual(args["input"][1]["content"], "I go to school yesterday.")
        self.assertIn("B1", args["input"][0]["content"])
        self.assertIs(args["text_format"], EnglishFeedbackSchema)

    @override_settings(OPENAI_API_KEY="")
    def test_missing_key_makes_no_provider_call(self):
        with self.assertRaises(APIError) as caught:
            generate_ai_feedback("Test sentence.")
        self.assertEqual(caught.exception.get_codes(), "ai_not_configured")
        self.client_factory.assert_not_called()

    @override_settings(OPENAI_MODEL="")
    def test_missing_model_makes_no_provider_call(self):
        with self.assertRaises(APIError) as caught:
            generate_ai_feedback("Test sentence.")
        self.assertEqual(caught.exception.get_codes(), "ai_not_configured")
        self.client_factory.assert_not_called()

    def test_timeout_has_safe_stable_error(self):
        self.client.responses.parse.side_effect = APITimeoutError(self.request)
        with self.assertRaises(APIError) as caught:
            generate_ai_feedback("Test sentence.")
        self.assertEqual(caught.exception.get_codes(), "ai_timeout")
        self.assertEqual(caught.exception.status_code, 504)

    def test_connection_error_has_safe_stable_error(self):
        self.client.responses.parse.side_effect = APIConnectionError(
            message="sensitive provider text", request=self.request
        )
        with self.assertRaises(APIError) as caught:
            generate_ai_feedback("Test sentence.")
        self.assertEqual(caught.exception.get_codes(), "ai_unavailable")
        self.assertNotIn("sensitive", str(caught.exception.detail))

    def test_provider_status_errors_are_classified_without_exposing_body(self):
        cases = (
            (RateLimitError, 429, "ai_rate_limited", 503),
            (AuthenticationError, 401, "ai_configuration_error", 503),
            (BadRequestError, 400, "ai_provider_request_error", 502),
            (InternalServerError, 500, "ai_unavailable", 503),
            (APIResponseValidationError, 200, "ai_invalid_response", 502),
        )
        for error_class, upstream_status, expected_code, expected_status in cases:
            with self.subTest(error=error_class.__name__):
                response = httpx.Response(upstream_status, request=self.request)
                if error_class is APIResponseValidationError:
                    error = error_class(response=response, body={"secret": "private"})
                else:
                    error = error_class(
                        "private provider message",
                        response=response,
                        body={"secret": "private"},
                    )
                self.client.responses.parse.side_effect = error
                with self.assertRaises(APIError) as caught:
                    generate_ai_feedback("Test sentence.")
                self.assertEqual(caught.exception.get_codes(), expected_code)
                self.assertEqual(caught.exception.status_code, expected_status)
                self.assertNotIn("private", str(caught.exception.detail))

    def test_refusal_is_not_treated_as_missing_result(self):
        self.client.responses.parse.return_value = SimpleNamespace(
            status="completed",
            output=[SimpleNamespace(type="message", content=[SimpleNamespace(type="refusal")])],
            output_parsed=None,
        )
        with self.assertRaises(APIError) as caught:
            generate_ai_feedback("Test sentence.")
        self.assertEqual(caught.exception.get_codes(), "ai_refused")
        self.assertEqual(caught.exception.status_code, 422)

    def test_incomplete_response_is_classified(self):
        self.client.responses.parse.return_value.status = "incomplete"
        with self.assertRaises(APIError) as caught:
            generate_ai_feedback("Test sentence.")
        self.assertEqual(caught.exception.get_codes(), "ai_incomplete_response")

    def test_missing_parsed_output_is_classified(self):
        self.client.responses.parse.return_value.output_parsed = None
        with self.assertRaises(APIError) as caught:
            generate_ai_feedback("Test sentence.")
        self.assertEqual(caught.exception.get_codes(), "ai_invalid_response")

    def test_invalid_score_is_not_persistable_provider_output(self):
        self.client.responses.parse.return_value.output_parsed = {**FEEDBACK, "grammar_score": 101}
        with self.assertRaises(APIError) as caught:
            generate_ai_feedback("Test sentence.")
        self.assertEqual(caught.exception.get_codes(), "ai_invalid_response")

    def test_unexpected_programming_error_is_not_disguised_as_provider_outage(self):
        self.client.responses.parse.side_effect = TypeError("programming error")
        with self.assertRaises(TypeError):
            generate_ai_feedback("Test sentence.")
