"""Upgrade legacy quiz data on the test database only."""

from django.conf import settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class QuizHistoryMigrationTests(TransactionTestCase):
    migrate_from = ("quizzes", "0004_quizattempt")
    migrate_to = ("quizzes", "0005_attempt_answer_history_and_constraints")

    def setUp(self):
        executor = MigrationExecutor(connection)
        # Other apps remain at their current schema (not just the minimum
        # swappable-user dependency declared by the old quiz migration).
        targets = [node for node in executor.loader.graph.leaf_nodes() if node[0] != "quizzes"]
        targets.append(self.migrate_from)
        executor.migrate(targets)
        self.old_apps = executor.loader.project_state(targets).apps
        user_app, user_model = settings.AUTH_USER_MODEL.split(".")
        self.user = self.old_apps.get_model(user_app, user_model).objects.create(
            email="legacy-quiz@example.com"
        )
        self.quiz = self.old_apps.get_model("quizzes", "Quiz").objects.create(title="Legacy quiz")
        self.Attempt = self.old_apps.get_model("quizzes", "QuizAttempt")

    def tearDown(self):
        # Failed preflight deliberately leaves legacy rows untouched; remove
        # only our test rows before restoring the current test schema.
        self.Attempt.objects.filter(user_id=self.user.pk).delete()
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_upgrade_snapshots_legacy_quiz_without_inventing_answers(self):
        attempt = self.Attempt.objects.create(
            user_id=self.user.pk,
            quiz_id=self.quiz.pk,
            score=60,
            correct_answers=3,
            total_questions=5,
        )
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to])
        apps = executor.loader.project_state(executor.loader.graph.leaf_nodes()).apps
        upgraded = apps.get_model("quizzes", "QuizAttempt").objects.get(pk=attempt.pk)
        self.assertEqual(upgraded.quiz_id_snapshot, self.quiz.pk)
        self.assertEqual(upgraded.quiz_title_snapshot, "Legacy quiz")
        self.assertEqual(upgraded.score, 60)
        self.assertEqual(upgraded.answers.count(), 0)

    def test_upgrade_stops_with_actionable_ids_and_preserves_invalid_rows(self):
        invalid = self.Attempt.objects.create(
            user_id=self.user.pk,
            quiz_id=self.quiz.pk,
            score=101,
            correct_answers=1,
            total_questions=2,
        )
        self.Attempt.objects.create(
            user_id=self.user.pk,
            quiz_id=self.quiz.pk,
            score=50,
            correct_answers=3,
            total_questions=2,
        )
        with self.assertRaisesRegex(RuntimeError, str(invalid.pk)):
            MigrationExecutor(connection).migrate([self.migrate_to])
        self.assertEqual(self.Attempt.objects.count(), 2)
        self.assertEqual(self.Attempt.objects.get(pk=invalid.pk).score, 101)
