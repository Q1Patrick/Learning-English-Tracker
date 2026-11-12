from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.db import OperationalError
from django.test import SimpleTestCase

from common.database import retry_sqlite_locked


class SQLiteRetryTests(SimpleTestCase):
    def setUp(self):
        self.connection = SimpleNamespace(vendor="sqlite", in_atomic_block=False)
        self.connections_patch = patch("common.database.connections", {"default": self.connection})
        self.connections_patch.start()
        self.addCleanup(self.connections_patch.stop)

    @patch("common.database.time.sleep")
    def test_transient_locks_are_retried_with_finite_backoff(self, sleep):
        operation = Mock(
            side_effect=[
                OperationalError("database table is locked: ai_feedback_aifeedback"),
                OperationalError("database is locked"),
                "claimed",
            ]
        )
        self.assertEqual(retry_sqlite_locked(operation), "claimed")
        self.assertEqual(operation.call_count, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [0.01, 0.02])

    @patch("common.database.time.sleep")
    def test_exhaustion_raises_original_error_after_six_attempts(self, sleep):
        error = OperationalError("database is locked")
        operation = Mock(side_effect=error)
        with self.assertRaises(OperationalError) as caught:
            retry_sqlite_locked(operation)
        self.assertIs(caught.exception, error)
        self.assertEqual(operation.call_count, 6)
        self.assertAlmostEqual(sum(call.args[0] for call in sleep.call_args_list), 0.31)

    @patch("common.database.time.sleep")
    def test_unrelated_database_error_is_not_retried(self, sleep):
        error = OperationalError("no such table: missing_table")
        operation = Mock(side_effect=error)
        with self.assertRaises(OperationalError) as caught:
            retry_sqlite_locked(operation)
        self.assertIs(caught.exception, error)
        operation.assert_called_once()
        sleep.assert_not_called()

    @patch("common.database.time.sleep")
    def test_retry_does_not_continue_inside_callers_transaction(self, sleep):
        self.connection.in_atomic_block = True
        operation = Mock(side_effect=OperationalError("database is locked"))
        with self.assertRaises(OperationalError):
            retry_sqlite_locked(operation)
        operation.assert_called_once()
        sleep.assert_not_called()

    @patch("common.database.time.sleep")
    def test_other_database_engines_are_not_retried(self, sleep):
        self.connection.vendor = "postgresql"
        operation = Mock(side_effect=OperationalError("database is locked"))
        with self.assertRaises(OperationalError):
            retry_sqlite_locked(operation)
        operation.assert_called_once()
        sleep.assert_not_called()
