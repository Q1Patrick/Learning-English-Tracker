import hashlib
import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.ai_feedback.models import AIFeedback
from common.exceptions import APIError
from tests.test_ai_feedback_services import FEEDBACK

User = get_user_model()


@override_settings(
    AI_FEEDBACK_THROTTLE_RATE="100/hour",
    OPENAI_API_KEY="unit-test-key",
    OPENAI_MODEL="unit-test-model",
)
class AIFeedbackAPITests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(email="ai-api@example.com", password=None)
        self.other = User.objects.create_user(email="other-ai@example.com", password=None)
        self.client.force_authenticate(user=self.user)
        self.url = "/api/v1/ai-feedback/"
        self.text = "I go to school yesterday."
        self.provider_patch = patch("apps.ai_feedback.services.generate_ai_feedback")
        self.provider = self.provider_patch.start()
        self.addCleanup(self.provider_patch.stop)
        self.provider.return_value = {**FEEDBACK, "model_name": "unit-test-model"}

    def post(self, key=None, text=None):
        headers = {"HTTP_IDEMPOTENCY_KEY": str(key)} if key is not None else {}
        return self.client.post(
            self.url, {"text": self.text if text is None else text}, format="json", **headers
        )

    def test_create_requires_authentication(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.post().status_code, 401)
        self.provider.assert_not_called()

    def test_create_persists_completed_feedback(self):
        def generate(**kwargs):
            pending = AIFeedback.objects.get(user=self.user)
            self.assertEqual(pending.status, AIFeedback.Status.PENDING)
            return {**FEEDBACK, "model_name": "unit-test-model"}

        self.provider.side_effect = generate
        response = self.post()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["corrected_text"], FEEDBACK["corrected_text"])
        feedback = AIFeedback.objects.get()
        self.assertEqual(feedback.status, AIFeedback.Status.COMPLETED)
        self.assertEqual(feedback.error_code, "")
        self.provider.assert_called_once_with(text=self.text, english_level="A1")

    def test_invalid_input_does_not_create_records_or_call_provider(self):
        for text in ("", "  ", "ab", "x" * 5001):
            with self.subTest(text_length=len(text)):
                self.assertEqual(self.post(text=text).status_code, 400)
        self.assertFalse(AIFeedback.objects.exists())
        self.provider.assert_not_called()

    def test_provider_failure_persists_safe_failed_state(self):
        self.provider.side_effect = APIError(
            "AI feedback timed out.", "ai_timeout", status_code=504
        )
        response = self.post()
        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.data["error"]["code"], "ai_timeout")
        feedback = AIFeedback.objects.get()
        self.assertEqual(feedback.status, AIFeedback.Status.FAILED)
        self.assertEqual(feedback.error_code, "ai_timeout")

    def test_unexpected_error_returns_500_and_is_recorded_without_sensitive_detail(self):
        self.provider.side_effect = TypeError("private learner text in exception")
        response = self.post()
        self.assertEqual(response.status_code, 500)
        feedback = AIFeedback.objects.get()
        self.assertEqual(feedback.status, AIFeedback.Status.FAILED)
        self.assertEqual(feedback.error_code, "internal_error")
        self.assertNotIn("private", feedback.error_message)
        self.assertNotIn("private", str(response.data))

    def test_completed_idempotent_replay_does_not_call_provider_again(self):
        key = uuid.uuid4()
        first = self.post(key)
        second = self.post(key)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data["data"]["id"], second.data["data"]["id"])
        self.assertEqual(AIFeedback.objects.count(), 1)
        self.provider.assert_called_once()

    def test_same_key_with_different_text_is_rejected(self):
        key = uuid.uuid4()
        self.post(key)
        response = self.post(key, text="Different writing for the same key.")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["error"]["code"], "idempotency_conflict")
        self.provider.assert_called_once()

    def test_pending_idempotent_replay_is_rejected_without_another_call(self):
        key = uuid.uuid4()
        AIFeedback.objects.create(
            user=self.user,
            original_text=self.text,
            idempotency_key=key,
            request_fingerprint=hashlib.sha256(self.text.encode()).hexdigest(),
        )
        response = self.post(key)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["error"]["code"], "request_in_progress")
        self.provider.assert_not_called()

    def test_failed_replay_requires_a_new_key_to_retry(self):
        key = uuid.uuid4()
        self.provider.side_effect = APIError(
            "AI feedback is unavailable.", "ai_unavailable", status_code=503
        )
        self.assertEqual(self.post(key).status_code, 503)
        response = self.post(key)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["error"]["code"], "ai_unavailable")
        self.provider.assert_called_once()
        self.assertEqual(AIFeedback.objects.count(), 1)

    def test_idempotency_keys_are_scoped_to_user(self):
        key = uuid.uuid4()
        self.assertEqual(self.post(key).status_code, 201)
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.post(key).status_code, 201)
        self.assertEqual(AIFeedback.objects.count(), 2)
        self.assertEqual(self.provider.call_count, 2)

    def test_invalid_idempotency_key_is_rejected(self):
        response = self.post("not-a-uuid")
        self.assertEqual(response.status_code, 400)
        self.provider.assert_not_called()
        self.assertFalse(AIFeedback.objects.exists())

    def test_history_is_paginated_and_only_contains_own_records(self):
        own = AIFeedback.objects.create(user=self.user, original_text=self.text)
        AIFeedback.objects.create(user=self.other, original_text="Another user's text.")
        response = self.client.get(self.url + "history/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(own.pk))

    def test_detail_is_private_and_does_not_expose_internal_error_message(self):
        feedback = AIFeedback.objects.create(
            user=self.user, original_text=self.text, error_message="internal-only"
        )
        own = self.client.get(self.url + str(feedback.pk) + "/")
        self.assertEqual(own.status_code, 200)
        self.assertNotIn("error_message", own.data)
        self.assertNotIn("idempotency_key", own.data)
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.client.get(self.url + str(feedback.pk) + "/").status_code, 404)

    def test_history_and_detail_require_authentication(self):
        feedback = AIFeedback.objects.create(user=self.user, original_text=self.text)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(self.url + "history/").status_code, 401)
        self.assertEqual(self.client.get(self.url + str(feedback.pk) + "/").status_code, 401)

    @override_settings(AI_FEEDBACK_THROTTLE_RATE="1/hour")
    def test_submission_throttle_blocks_excess_requests(self):
        self.assertEqual(self.post().status_code, 201)
        self.assertEqual(self.post().status_code, 429)
        self.provider.assert_called_once()
