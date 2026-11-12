"""Sample seeding is repeat-safe and changes only a disposable test database."""

import io
from dataclasses import replace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIClient

from apps.quizzes.management.commands.seed_quizzes import prepare_seed_data
from apps.quizzes.models import Choice, Question, Quiz, QuizAttempt, QuizAttemptAnswer
from apps.quizzes.seed_data import QUIZ_SEEDS, seed_uuid
from apps.quizzes.services import submit_quiz

COMMAND_MODULE = "apps.quizzes.management.commands.seed_quizzes"


class SeedQuizzesTests(TestCase):
    def seed(self, **options):
        output = io.StringIO()
        # Capturing stdout alone doesn't disable Django's terminal color detection.
        call_command("seed_quizzes", stdout=output, no_color=True, **options)
        return output.getvalue()

    def counts(self):
        return Quiz.objects.count(), Question.objects.count(), Choice.objects.count()

    def test_seed_creates_five_useful_complete_quizzes(self):
        output = self.seed()
        self.assertEqual(self.counts(), (5, 15, 60))
        self.assertEqual(output, "Created 5 quiz(es); skipped 0 existing quiz(es).\n")
        self.assertEqual(
            set(Quiz.objects.values_list("title", flat=True)),
            {
                "Everyday Vocabulary",
                "Grammar Foundations",
                "Phrasal Verbs Basics",
                "Beginner English Check",
                "Intermediate English Check",
            },
        )
        for quiz in Quiz.objects.all():
            with self.subTest(quiz=quiz.title):
                self.assertTrue(quiz.is_active)
                self.assertGreaterEqual(quiz.questions.count(), 3)
                for question in quiz.questions.all():
                    self.assertEqual(question.question_type, Question.QuestionType.MULTIPLE_CHOICE)
                    self.assertEqual(question.choices.count(), 4)
                    self.assertEqual(question.choices.filter(is_correct=True).count(), 1)
                    self.assertTrue(question.explanation)
        for seed in QUIZ_SEEDS:
            for question in seed.questions:
                self.assertNotIn(question.explanation, output)

    def test_running_twice_preserves_all_ids_and_counts(self):
        self.seed()
        expected = tuple(
            set(model.objects.values_list("pk", flat=True)) for model in (Quiz, Question, Choice)
        )
        output = self.seed()
        self.assertIn("Created 0 quiz(es); skipped 5", output)
        self.assertEqual(self.counts(), (5, 15, 60))
        for model, ids in zip((Quiz, Question, Choice), expected):
            self.assertEqual(set(model.objects.values_list("pk", flat=True)), ids)

    def test_existing_quiz_edits_deleted_choices_inactive_flag_and_history_are_preserved(self):
        self.seed()
        quiz = Quiz.objects.get(pk=seed_uuid(QUIZ_SEEDS[0], "quiz"))
        user = get_user_model().objects.create_user(email="seed-history@example.com")
        answers = [
            {"question_id": question.pk, "choice_id": question.choices.get(is_correct=True).pk}
            for question in quiz.questions.all()
        ]
        attempt, _ = submit_quiz(user=user, quiz_id=quiz.pk, answers=answers)
        saved_history = list(
            attempt.answers.values("question_text", "choice_text", "explanation", "is_correct")
        )
        quiz.title = "My edited sample quiz"
        quiz.description = "A manually maintained description"
        quiz.is_active = False
        quiz.save()
        question = quiz.questions.first()
        question.text = "A manually edited question"
        question.explanation = "My edited explanation"
        question.save()
        removed_choice_id = question.choices.get(is_correct=True).pk
        Choice.objects.get(pk=removed_choice_id).delete()
        self.seed()
        quiz.refresh_from_db()
        question.refresh_from_db()
        self.assertEqual(quiz.title, "My edited sample quiz")
        self.assertEqual(quiz.description, "A manually maintained description")
        self.assertFalse(quiz.is_active)
        self.assertEqual(question.text, "A manually edited question")
        self.assertEqual(question.explanation, "My edited explanation")
        self.assertFalse(Choice.objects.filter(pk=removed_choice_id).exists())
        self.assertEqual(question.choices.count(), 3)
        self.assertEqual(
            list(
                attempt.answers.values("question_text", "choice_text", "explanation", "is_correct")
            ),
            saved_history,
        )
        self.assertEqual(QuizAttempt.objects.count(), 1)
        self.assertEqual(QuizAttemptAnswer.objects.count(), 3)

    def test_user_created_quiz_with_the_same_title_is_untouched(self):
        manual = Quiz.objects.create(
            title=QUIZ_SEEDS[0].title, description="My content", is_active=False
        )
        question = Question.objects.create(quiz=manual, text="My own question")
        self.seed()
        manual.refresh_from_db()
        self.assertEqual(Quiz.objects.count(), 6)
        self.assertEqual(manual.description, "My content")
        self.assertFalse(manual.is_active)
        self.assertEqual(list(manual.questions.values_list("pk", flat=True)), [question.pk])
        self.assertEqual(question.choices.count(), 0)

    def test_dry_run_reports_new_quizzes_without_database_writes(self):
        with CaptureQueriesContext(connection) as queries:
            output = self.seed(dry_run=True)
        self.assertIn("would create 5 quiz(es); would skip 0", output)
        self.assertIn("Database unchanged", output)
        self.assertEqual(self.counts(), (0, 0, 0))
        for query in queries:
            self.assertFalse(
                query["sql"]
                .lstrip()
                .upper()
                .startswith(("INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP"))
            )

    def test_dry_run_counts_existing_ids_without_repairing_them(self):
        for seed in QUIZ_SEEDS[:2]:
            Quiz.objects.create(
                pk=seed_uuid(seed, "quiz"), title="Manually edited", is_active=False
            )
        output = self.seed(dry_run=True)
        self.assertIn("would create 3 quiz(es); would skip 2", output)
        self.assertEqual(self.counts(), (2, 0, 0))
        self.assertEqual(Quiz.objects.filter(is_active=False).count(), 2)

    def test_write_failure_rolls_back_all_new_quizzes_and_keeps_existing_content(self):
        manual = Quiz.objects.create(title="Existing manual quiz")
        original_create = Choice.objects.bulk_create
        calls = 0

        def fail_on_second_quiz(objects, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise IntegrityError("seed write failed")
            return original_create(objects, **kwargs)

        with patch(f"{COMMAND_MODULE}.Choice.objects.bulk_create", side_effect=fail_on_second_quiz):
            with self.assertRaisesRegex(CommandError, "no new sample quizzes"):
                self.seed()
        self.assertEqual(self.counts(), (1, 0, 0))
        self.assertEqual(Quiz.objects.get().pk, manual.pk)

    def test_invalid_last_fixture_is_rejected_before_any_write(self):
        last = QUIZ_SEEDS[-1]
        question = last.questions[-1]
        bad_choices = tuple(replace(choice, is_correct=False) for choice in question.choices)
        invalid_last = replace(
            last,
            questions=last.questions[:-1] + (replace(question, choices=bad_choices),),
        )
        with patch(f"{COMMAND_MODULE}.QUIZ_SEEDS", QUIZ_SEEDS[:-1] + (invalid_last,)):
            with self.assertRaisesRegex(CommandError, "exactly one correct"):
                self.seed()
        self.assertEqual(self.counts(), (0, 0, 0))

    def test_invalid_model_field_in_fixture_is_rejected_before_any_write(self):
        last = replace(QUIZ_SEEDS[-1], difficulty="unsupported")
        with patch(f"{COMMAND_MODULE}.QUIZ_SEEDS", QUIZ_SEEDS[:-1] + (last,)):
            with self.assertRaisesRegex(CommandError, "difficulty"):
                self.seed()
        self.assertEqual(self.counts(), (0, 0, 0))

    def test_all_seeded_quizzes_score_correctly_and_public_responses_hide_answers(self):
        self.seed()
        user = get_user_model().objects.create_user(email="seed-api@example.com")
        client = APIClient()
        client.force_authenticate(user)
        for quiz in Quiz.objects.all():
            with self.subTest(quiz=quiz.title):
                detail = client.get(reverse("quizzes:detail", kwargs={"pk": quiz.pk}))
                self.assertEqual(detail.status_code, 200)
                for question in detail.data["data"]["questions"]:
                    self.assertNotIn("explanation", question)
                    self.assertNotIn("correct_choice_id", question)
                    for choice in question["choices"]:
                        self.assertNotIn("is_correct", choice)
                answers = [
                    {
                        "question_id": str(question.pk),
                        "choice_id": str(question.choices.get(is_correct=True).pk),
                    }
                    for question in quiz.questions.all()
                ]
                response = client.post(
                    reverse("quizzes:submit", kwargs={"pk": quiz.pk}),
                    {"answers": answers, "score": 0},
                    format="json",
                )
                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.data["data"]["score"], 100)
                self.assertEqual(response.data["data"]["correct_answers"], 3)
        self.assertEqual(QuizAttempt.objects.count(), 5)

    @override_settings(SETTINGS_MODULE="config.settings.production", DEBUG=False)
    def test_production_requires_explicit_opt_in_even_for_dry_run(self):
        for options in ({}, {"dry_run": True}):
            with self.subTest(options=options):
                with self.assertRaisesRegex(CommandError, "allow-production"):
                    self.seed(**options)
        self.assertEqual(self.counts(), (0, 0, 0))

    @override_settings(SETTINGS_MODULE="config.settings.production", DEBUG=False)
    def test_production_opt_in_is_explicit_and_works_on_test_database(self):
        self.seed(allow_production=True)
        self.assertEqual(self.counts(), (5, 15, 60))

    @override_settings(SETTINGS_MODULE="custom.settings", DEBUG=True)
    def test_custom_settings_do_not_bypass_guard_via_debug(self):
        with self.assertRaisesRegex(CommandError, "allow-production"):
            self.seed()
        self.assertEqual(self.counts(), (0, 0, 0))

    def test_versioned_identifiers_are_stable_and_new_versions_do_not_replace_old_content(self):
        self.seed()
        original = QUIZ_SEEDS[0]
        original_id = seed_uuid(original, "quiz")
        self.assertEqual(seed_uuid(original, "quiz"), original_id)
        new_version = replace(original, version=original.version + 1)
        self.assertNotEqual(seed_uuid(new_version, "quiz"), original_id)
        with patch(f"{COMMAND_MODULE}.QUIZ_SEEDS", (new_version,)):
            self.seed()
        self.assertTrue(Quiz.objects.filter(pk=original_id).exists())
        self.assertTrue(Quiz.objects.filter(pk=seed_uuid(new_version, "quiz")).exists())
        self.assertEqual(self.counts(), (6, 18, 72))

    def test_duplicate_fixture_identifiers_are_rejected_before_mutation(self):
        with self.assertRaisesRegex(CommandError, "duplicate content identifiers"):
            prepare_seed_data((QUIZ_SEEDS[0], QUIZ_SEEDS[0]))
        self.assertEqual(self.counts(), (0, 0, 0))
