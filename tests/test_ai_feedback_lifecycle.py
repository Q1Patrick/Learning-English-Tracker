import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import OperationalError, close_old_connections, connection, connections
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from apps.ai_feedback.models import AIFeedback
from apps.ai_feedback.services import submit_feedback
from common.exceptions import APIError
from tests.test_ai_feedback_services import FEEDBACK


class AIFeedbackTransactionTests(TransactionTestCase):
    def test_network_call_happens_without_an_open_database_transaction(self):
        user = get_user_model().objects.create_user(email="no-transaction@example.com")
        with patch("apps.ai_feedback.services.generate_ai_feedback") as provider:

            def generate(**kwargs):
                self.assertFalse(connection.in_atomic_block)
                return {**FEEDBACK, "model_name": "unit-test-model"}

            provider.side_effect = generate
            feedback, created = submit_feedback(user=user, text="Test writing.")
        self.assertTrue(created)
        self.assertEqual(feedback.status, AIFeedback.Status.COMPLETED)

    def test_failure_status_write_does_not_mask_original_programming_error(self):
        user = get_user_model().objects.create_user(email="failure-write@example.com")
        with patch("apps.ai_feedback.services.generate_ai_feedback") as provider:
            provider.side_effect = TypeError("original programming error")
            with patch.object(AIFeedback.objects, "filter") as queryset:
                queryset.return_value.update.side_effect = OperationalError("write failed")
                with self.assertLogs("apps.ai_feedback.services", level="ERROR"):
                    with self.assertRaisesRegex(TypeError, "original programming error"):
                        submit_feedback(user=user, text="Test writing.")

    def test_concurrent_idempotent_requests_make_one_provider_call(self):
        user = get_user_model().objects.create_user(email="concurrent-ai@example.com")
        key = uuid.uuid4()
        start = threading.Barrier(2)

        def request():
            close_old_connections()
            try:
                thread_user = get_user_model().objects.get(pk=user.pk)
                start.wait(timeout=5)
                try:
                    feedback, created = submit_feedback(
                        user=thread_user, text="Concurrent writing.", idempotency_key=key
                    )
                    return str(feedback.pk), created
                except APIError as exc:
                    return None, exc.get_codes()
            finally:
                connections.close_all()

        with patch("apps.ai_feedback.services.generate_ai_feedback") as provider:

            def generate(**kwargs):
                # Keep the first request in flight while the second replays.
                time.sleep(0.04)
                return {**FEEDBACK, "model_name": "unit-test-model"}

            provider.side_effect = generate
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(request) for _ in range(2)]
                outcomes = [future.result(timeout=10) for future in futures]
        self.assertEqual(AIFeedback.objects.count(), 1)
        self.assertEqual(sum(created is True for _, created in outcomes), 1)
        self.assertTrue(
            all(created in (True, False, "request_in_progress") for _, created in outcomes)
        )
        provider.assert_called_once()


@override_settings(OPENAI_TIMEOUT_SECONDS=5, OPENAI_MAX_RETRIES=1)
class AIFeedbackRecoveryTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email="recovery@example.com")
        self.old = AIFeedback.objects.create(user=self.user, original_text="Old request.")
        AIFeedback.objects.filter(pk=self.old.pk).update(
            updated_at=timezone.now() - timedelta(hours=2)
        )
        self.active = AIFeedback.objects.create(user=self.user, original_text="Active request.")

    def test_dry_run_keeps_pending_state(self):
        output = StringIO()
        call_command("expire_ai_feedback", dry_run=True, stdout=output)
        self.old.refresh_from_db()
        self.assertEqual(self.old.status, AIFeedback.Status.PENDING)
        self.assertIn("Would expire 1", output.getvalue())

    def test_recovery_expires_only_old_pending_records(self):
        call_command("expire_ai_feedback", stdout=StringIO())
        self.old.refresh_from_db()
        self.active.refresh_from_db()
        self.assertEqual(self.old.status, AIFeedback.Status.FAILED)
        self.assertEqual(self.old.error_code, "ai_request_expired")
        self.assertEqual(self.active.status, AIFeedback.Status.PENDING)

    def test_recovery_rejects_dangerously_short_cutoff(self):
        with self.assertRaises(CommandError):
            call_command("expire_ai_feedback", older_than_minutes=1, stdout=StringIO())

    def test_late_provider_response_does_not_overwrite_expired_request(self):
        with patch("apps.ai_feedback.services.generate_ai_feedback") as provider:

            def generate(**kwargs):
                AIFeedback.objects.filter(original_text="Late writing.").update(
                    status=AIFeedback.Status.FAILED, error_code="ai_request_expired"
                )
                return {**FEEDBACK, "model_name": "unit-test-model"}

            provider.side_effect = generate
            with self.assertRaises(APIError) as caught:
                submit_feedback(user=self.user, text="Late writing.")
        self.assertEqual(caught.exception.get_codes(), "ai_request_expired")
        feedback = AIFeedback.objects.get(original_text="Late writing.")
        self.assertEqual(feedback.status, AIFeedback.Status.FAILED)


class AIFeedbackSmokeCommandTests(TestCase):
    @patch("apps.ai_feedback.management.commands.ai_feedback_smoke.generate_ai_feedback")
    def test_smoke_calls_provider_without_persisting_feedback(self, provider):
        provider.return_value = {**FEEDBACK, "model_name": "unit-test-model"}
        output = StringIO()
        call_command("ai_feedback_smoke", english_level="B1", stdout=output)
        provider.assert_called_once_with("I go to school yesterday.", english_level="B1")
        self.assertIn("unit-test-model", output.getvalue())
        self.assertFalse(AIFeedback.objects.exists())

    @patch("apps.ai_feedback.management.commands.ai_feedback_smoke.generate_ai_feedback")
    def test_smoke_reports_safe_provider_error(self, provider):
        provider.side_effect = APIError(
            "AI feedback is not configured.", "ai_not_configured", status_code=503
        )
        with self.assertRaisesRegex(CommandError, "ai_not_configured"):
            call_command("ai_feedback_smoke", stdout=StringIO())

    @patch("apps.ai_feedback.management.commands.ai_feedback_smoke.generate_ai_feedback")
    def test_smoke_rejects_invalid_input_without_calling_provider(self, provider):
        with self.assertRaises(CommandError):
            call_command("ai_feedback_smoke", text="ab", stdout=StringIO())
        provider.assert_not_called()
