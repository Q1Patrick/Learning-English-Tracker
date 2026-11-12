import uuid
from datetime import datetime
from datetime import timezone as datetime_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.forms.models import inlineformset_factory
from django.test import TestCase
from django.utils import timezone

from apps.quizzes.admin import ChoiceInlineFormSet
from apps.quizzes.models import Choice, Question, Quiz, QuizAttempt, QuizAttemptAnswer
from apps.quizzes.services import submit_quiz
from common.exceptions import APIError


class QuizModelLifecycleTests(TestCase):
    """Check stored relationships and history, not just the HTTP representation."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(email="quiz-lifecycle@example.com")
        cls.other_user = get_user_model().objects.create_user(
            email="quiz-lifecycle-other@example.com"
        )
        cls.quiz = Quiz.objects.create(title="Phrasal verbs", description="Choose the meaning.")
        cls.question = Question.objects.create(
            quiz=cls.quiz,
            text="What does figure out mean?",
            explanation="It means to understand or solve something.",
            order=2,
        )
        cls.correct = Choice.objects.create(
            question=cls.question, text="Understand or solve", is_correct=True, order=1
        )
        cls.wrong = Choice.objects.create(question=cls.question, text="Sleep", order=2)

    def submit(self, *, user=None, choice=None):
        attempt, _ = submit_quiz(
            user=user or self.user,
            quiz_id=self.quiz.pk,
            answers=[{"question_id": self.question.pk, "choice_id": (choice or self.correct).pk}],
        )
        return attempt

    def test_quiz_can_be_created_and_retrieved_with_defaults(self):
        quiz = Quiz.objects.get(pk=self.quiz.pk)
        quiz.full_clean()
        self.assertEqual(quiz.title, "Phrasal verbs")
        self.assertTrue(quiz.is_active)
        self.assertEqual(quiz.difficulty, Quiz.Difficulty.BEGINNER)
        self.assertTrue(timezone.is_aware(quiz.created_at))
        self.assertGreaterEqual(quiz.updated_at, quiz.created_at)

    def test_quiz_title_is_required_during_model_validation(self):
        for title in ("", None):
            with self.subTest(title=title):
                with self.assertRaises(ValidationError) as error:
                    Quiz(title=title).full_clean()
                self.assertIn("title", error.exception.message_dict)

    def test_quiz_string_representation_is_its_title(self):
        self.assertEqual(str(self.quiz), "Phrasal verbs")

    def test_question_is_stored_under_its_quiz_with_explanation(self):
        question = self.quiz.questions.get(pk=self.question.pk)
        self.assertEqual(question.quiz_id, self.quiz.pk)
        self.assertEqual(question.explanation, "It means to understand or solve something.")
        self.assertEqual(question.question_type, Question.QuestionType.MULTIPLE_CHOICE)

    def test_question_order_controls_quiz_question_order(self):
        first = Question.objects.create(quiz=self.quiz, text="First question", order=1)
        self.assertEqual(
            list(self.quiz.questions.values_list("pk", flat=True)), [first.pk, self.question.pk]
        )

    def test_choice_is_stored_under_its_question_with_correctness(self):
        self.assertEqual(
            self.question.choices.get(pk=self.correct.pk).question_id, self.question.pk
        )
        self.assertEqual(
            list(self.question.choices.values_list("is_correct", flat=True)), [True, False]
        )

    def test_deleting_quiz_cascades_questions_and_choices(self):
        question_id, choice_id = self.question.pk, self.correct.pk
        self.quiz.delete()
        self.assertFalse(Question.objects.filter(pk=question_id).exists())
        self.assertFalse(Choice.objects.filter(pk=choice_id).exists())

    def test_attempt_records_owner_quiz_and_completion_timestamp(self):
        completed_at = datetime(2026, 11, 10, 3, 0, tzinfo=datetime_timezone.utc)
        with patch("django.utils.timezone.now", return_value=completed_at):
            attempt = self.submit()
        stored = self.user.quiz_attempts.get(pk=attempt.pk)
        self.assertEqual(stored.quiz_id, self.quiz.pk)
        self.assertEqual(stored.quiz_id_snapshot, self.quiz.pk)
        self.assertEqual(stored.completed_at, completed_at)
        self.assertTrue(timezone.is_aware(stored.completed_at))

    def test_each_user_owns_separate_attempts(self):
        own = self.submit()
        other = self.submit(user=self.other_user)
        self.assertEqual(list(self.user.quiz_attempts.values_list("pk", flat=True)), [own.pk])
        self.assertEqual(
            list(self.other_user.quiz_attempts.values_list("pk", flat=True)), [other.pk]
        )

    def test_correct_answer_is_persisted_with_full_score(self):
        attempt = self.submit()
        answer = attempt.answers.get()
        self.assertEqual(
            (attempt.score, attempt.correct_answers, attempt.total_questions), (100, 1, 1)
        )
        self.assertEqual(answer.question_id, self.question.pk)
        self.assertEqual(answer.choice_id, self.correct.pk)
        self.assertTrue(answer.is_correct)

    def test_incorrect_answer_is_persisted_with_zero_score(self):
        attempt = self.submit(choice=self.wrong)
        answer = attempt.answers.get()
        self.assertEqual(
            (attempt.score, attempt.correct_answers, attempt.total_questions), (0, 0, 1)
        )
        self.assertEqual(answer.choice_id, self.wrong.pk)
        self.assertEqual(answer.correct_choice_id_snapshot, self.correct.pk)
        self.assertFalse(answer.is_correct)

    def test_choice_from_another_question_does_not_create_history(self):
        other_quiz = Quiz.objects.create(title="Another quiz")
        other_question = Question.objects.create(quiz=other_quiz, text="Different question")
        foreign_choice = Choice.objects.create(
            question=other_question, text="Unrelated", is_correct=True
        )
        with self.assertRaises(APIError) as error:
            self.submit(choice=foreign_choice)
        self.assertEqual(error.exception.get_codes(), "invalid_answers")
        self.assertEqual(QuizAttempt.objects.count(), 0)
        self.assertEqual(QuizAttemptAnswer.objects.count(), 0)

    def test_deleting_selected_choice_preserves_answer_snapshot(self):
        attempt = self.submit()
        original_id = self.correct.pk
        self.correct.delete()
        answer = attempt.answers.get()
        self.assertIsNone(answer.choice_id)
        self.assertEqual(answer.choice_id_snapshot, original_id)
        self.assertEqual(answer.choice_text, "Understand or solve")
        self.assertTrue(answer.is_correct)

    def test_deleting_attempt_cascades_answers_but_keeps_source_content(self):
        attempt = self.submit()
        answer_id = attempt.answers.get().pk
        attempt.delete()
        self.assertFalse(QuizAttemptAnswer.objects.filter(pk=answer_id).exists())
        self.assertTrue(Quiz.objects.filter(pk=self.quiz.pk).exists())
        self.assertTrue(Choice.objects.filter(pk=self.correct.pk).exists())


class QuizDatabaseConstraintTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(email="quiz-model@example.com")
        cls.quiz = Quiz.objects.create(title="Constraints")

    def create_attempt(self, **kwargs):
        values = {
            "user": self.user,
            "quiz": self.quiz,
            "score": 50,
            "correct_answers": 1,
            "total_questions": 2,
        }
        values.update(kwargs)
        return QuizAttempt.objects.create(**values)

    def test_database_rejects_out_of_range_scores_and_answer_counts(self):
        for values in [{"score": 101}, {"score": -1}, {"correct_answers": 3}]:
            with self.subTest(values=values):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    self.create_attempt(**values)

    def test_idempotency_key_is_unique_per_user(self):
        key = uuid.uuid4()
        self.create_attempt(idempotency_key=key)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_attempt(idempotency_key=key)
        # Independent attempts without a key remain valid.
        self.create_attempt()
        self.create_attempt()

    def test_database_rejects_duplicate_question_answers(self):
        attempt = self.create_attempt()
        values = {
            "attempt": attempt,
            "question_id_snapshot": uuid.uuid4(),
            "choice_id_snapshot": uuid.uuid4(),
            "correct_choice_id_snapshot": uuid.uuid4(),
            "question_text": "Q",
            "choice_text": "A",
            "correct_choice_text": "B",
            "is_correct": False,
            "order": 1,
        }
        QuizAttemptAnswer.objects.create(**values)
        with self.assertRaises(IntegrityError), transaction.atomic():
            QuizAttemptAnswer.objects.create(**values)


class QuizChoiceAdminValidationTests(TestCase):
    def setUp(self):
        quiz = Quiz.objects.create(title="Admin")
        self.question = Question.objects.create(quiz=quiz, text="One correct answer")
        self.formset_class = inlineformset_factory(
            Question,
            Choice,
            formset=ChoiceInlineFormSet,
            fields=("text", "is_correct", "order"),
            extra=0,
            can_delete=True,
        )

    def formset(self, flags):
        data = {"choices-TOTAL_FORMS": str(len(flags)), "choices-INITIAL_FORMS": "0"}
        for index, flag in enumerate(flags):
            data.update(
                {
                    f"choices-{index}-text": f"Choice {index}",
                    f"choices-{index}-order": str(index + 1),
                }
            )
            if flag:
                data[f"choices-{index}-is_correct"] = "on"
        return self.formset_class(data=data, instance=self.question, prefix="choices")

    def test_exactly_one_correct_choice_is_required(self):
        self.assertTrue(self.formset([True, False]).is_valid())
        self.assertFalse(self.formset([False, False]).is_valid())
        self.assertFalse(self.formset([True, True]).is_valid())

    def test_at_least_two_choices_are_required(self):
        self.assertFalse(self.formset([True]).is_valid())
