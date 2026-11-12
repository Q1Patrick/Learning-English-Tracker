import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.quizzes.models import Choice, Question, Quiz, QuizAttempt, QuizAttemptAnswer
from apps.quizzes.services import submit_quiz


class QuizAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(email="quiz@example.com")
        cls.other_user = get_user_model().objects.create_user(email="other-quiz@example.com")
        cls.quiz = Quiz.objects.create(title="Past tense")
        cls.q1 = Question.objects.create(
            quiz=cls.quiz, text="Past of go?", explanation="Irregular verb."
        )
        cls.q2 = Question.objects.create(
            quiz=cls.quiz, text="Past of walk?", order=2, explanation="Add -ed."
        )
        cls.correct1 = Choice.objects.create(question=cls.q1, text="went", is_correct=True)
        cls.wrong1 = Choice.objects.create(question=cls.q1, text="goed")
        cls.correct2 = Choice.objects.create(question=cls.q2, text="walked", is_correct=True)
        cls.wrong2 = Choice.objects.create(question=cls.q2, text="walk")

    def setUp(self):
        self.client.force_authenticate(self.user)
        self.submit_url = reverse("quizzes:submit", kwargs={"pk": self.quiz.pk})
        self.answers = [
            {"question_id": str(self.q1.pk), "choice_id": str(self.correct1.pk)},
            {"question_id": str(self.q2.pk), "choice_id": str(self.correct2.pk)},
        ]

    def submit(self, answers=None, key=None, **extra):
        headers = {"HTTP_IDEMPOTENCY_KEY": str(key)} if key is not None else {}
        return self.client.post(
            self.submit_url,
            {"answers": self.answers if answers is None else answers, **extra},
            format="json",
            **headers,
        )

    def test_all_quiz_endpoints_require_authentication(self):
        self.client.force_authenticate(None)
        for name, kwargs in [
            ("quizzes:list", {}),
            ("quizzes:detail", {"pk": self.quiz.pk}),
            ("quizzes:attempt-list", {}),
            ("quizzes:attempt-detail", {"pk": uuid.uuid4()}),
        ]:
            with self.subTest(endpoint=name):
                self.assertEqual(self.client.get(reverse(name, kwargs=kwargs)).status_code, 401)
        self.assertEqual(self.submit().status_code, 401)

    def test_list_is_paginated_and_hides_inactive_quizzes(self):
        hidden = Quiz.objects.create(title="Draft", is_active=False)
        response = self.client.get(reverse("quizzes:list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["question_count"], 2)
        self.assertNotIn(str(hidden.pk), str(response.data))

    def test_detail_excludes_answers_and_explanations(self):
        response = self.client.get(reverse("quizzes:detail", kwargs={"pk": self.quiz.pk}))
        self.assertEqual(response.status_code, 200)
        question = response.data["data"]["questions"][0]
        self.assertNotIn("explanation", question)
        self.assertNotIn("is_correct", question["choices"][0])
        self.assertNotIn("correct_choice_id", question)

    def test_server_scores_answers_and_ignores_client_score(self):
        response = self.submit(score=0, correct_answers=0)
        self.assertEqual(response.status_code, 201)
        data = response.data["data"]
        self.assertEqual(
            (data["score"], data["correct_answers"], data["total_questions"]), (100, 2, 2)
        )
        self.assertEqual(len(data["answers"]), 2)
        self.assertEqual(data["answers"][0]["question_text"], "Past of go?")
        self.assertEqual(data["answers"][0]["correct_choice_text"], "went")
        self.assertEqual(data["answers"][0]["explanation"], "Irregular verb.")
        self.assertEqual(QuizAttemptAnswer.objects.count(), 2)

    def test_partial_and_zero_scores(self):
        self.answers[0]["choice_id"] = str(self.wrong1.pk)
        self.assertEqual(self.submit().data["data"]["score"], 50)
        self.answers[1]["choice_id"] = str(self.wrong2.pk)
        self.assertEqual(self.submit().data["data"]["score"], 0)

    def test_missing_duplicate_and_extra_questions_are_rejected(self):
        foreign_quiz = Quiz.objects.create(title="Another")
        foreign_question = Question.objects.create(quiz=foreign_quiz, text="Foreign")
        variants = [
            self.answers[:1],
            [self.answers[0], self.answers[0]],
            self.answers
            + [{"question_id": str(foreign_question.pk), "choice_id": str(self.correct1.pk)}],
            [],
        ]
        for answers in variants:
            with self.subTest(answers=answers):
                self.assertEqual(self.submit(answers=answers).status_code, 400)
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_choice_from_another_question_is_rejected(self):
        self.answers[0]["choice_id"] = str(self.correct2.pk)
        self.assertEqual(self.submit().status_code, 400)
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_invalid_question_and_choice_ids_are_rejected(self):
        self.answers[0]["question_id"] = "invalid"
        self.assertEqual(self.submit().status_code, 400)
        self.answers[0]["question_id"] = str(self.q1.pk)
        self.answers[0]["choice_id"] = str(uuid.uuid4())
        self.assertEqual(self.submit().status_code, 400)

    def test_inactive_and_missing_quizzes_are_not_available(self):
        self.quiz.is_active = False
        self.quiz.save(update_fields=["is_active"])
        self.assertEqual(self.submit().status_code, 404)
        self.assertEqual(
            self.client.get(reverse("quizzes:detail", kwargs={"pk": self.quiz.pk})).status_code, 404
        )
        self.submit_url = reverse("quizzes:submit", kwargs={"pk": uuid.uuid4()})
        self.assertEqual(self.submit().status_code, 404)

    def test_empty_and_unsupported_quizzes_are_not_scored(self):
        empty = Quiz.objects.create(title="Empty")
        self.submit_url = reverse("quizzes:submit", kwargs={"pk": empty.pk})
        self.assertEqual(self.submit().status_code, 409)
        self.submit_url = reverse("quizzes:submit", kwargs={"pk": self.quiz.pk})
        self.q1.question_type = Question.QuestionType.TRANSLATION
        self.q1.save(update_fields=["question_type"])
        self.assertEqual(self.submit().status_code, 409)
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_quiz_with_no_or_multiple_correct_choices_is_rejected(self):
        self.correct1.is_correct = False
        self.correct1.save(update_fields=["is_correct"])
        self.assertEqual(self.submit().status_code, 409)
        Choice.objects.filter(question=self.q1).update(is_correct=True)
        self.assertEqual(self.submit().status_code, 409)
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_attempt_history_is_private(self):
        attempt_id = self.submit().data["data"]["id"]
        own = self.client.get(reverse("quizzes:attempt-detail", kwargs={"pk": attempt_id}))
        self.assertEqual(own.status_code, 200)
        self.client.force_authenticate(self.other_user)
        self.assertEqual(
            self.client.get(
                reverse("quizzes:attempt-detail", kwargs={"pk": attempt_id})
            ).status_code,
            404,
        )
        self.assertEqual(self.client.get(reverse("quizzes:attempt-list")).data["count"], 0)

    def test_history_alias_matches_attempts_and_preserves_private_access(self):
        self.submit()
        alias = self.client.get("/api/v1/quizzes/history/")
        original = self.client.get(reverse("quizzes:attempt-list"))
        self.assertEqual(alias.status_code, 200)
        self.assertEqual(alias.data, original.data)
        self.client.force_authenticate(self.other_user)
        self.assertEqual(self.client.get("/api/v1/quizzes/history/").data["count"], 0)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/v1/quizzes/history/").status_code, 401)

    def test_history_survives_content_edits_and_deletion(self):
        initial = self.submit().data["data"]
        Quiz.objects.filter(pk=self.quiz.pk).update(title="Changed title")
        Question.objects.filter(pk=self.q1.pk).update(
            text="Changed question", explanation="Changed explanation"
        )
        Choice.objects.filter(pk=self.correct1.pk).update(text="Changed choice", is_correct=False)
        self.quiz.delete()
        response = self.client.get(reverse("quizzes:attempt-detail", kwargs={"pk": initial["id"]}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], initial)
        self.assertEqual(QuizAttempt.objects.get(pk=initial["id"]).quiz_id, None)
        self.assertFalse(QuizAttemptAnswer.objects.filter(question__isnull=False).exists())

    def test_idempotent_retry_reorders_answers_without_rescoring(self):
        key = uuid.uuid4()
        first = self.submit(key=key)
        self.answers.reverse()
        second = self.submit(key=key)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data, first.data)
        self.assertEqual(QuizAttempt.objects.count(), 1)

    def test_idempotent_replay_still_works_after_quiz_deletion(self):
        key = uuid.uuid4()
        first = self.submit(key=key)
        self.quiz.delete()
        second = self.submit(key=key)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data, first.data)

    def test_key_reuse_with_different_payload_or_quiz_conflicts(self):
        key = uuid.uuid4()
        self.assertEqual(self.submit(key=key).status_code, 201)
        self.answers[0]["choice_id"] = str(self.wrong1.pk)
        self.assertEqual(self.submit(key=key).status_code, 409)
        self.submit_url = reverse("quizzes:submit", kwargs={"pk": uuid.uuid4()})
        self.assertEqual(self.submit(key=key).status_code, 409)
        self.assertEqual(QuizAttempt.objects.count(), 1)

    def test_same_key_is_scoped_to_the_user(self):
        key = uuid.uuid4()
        self.assertEqual(self.submit(key=key).status_code, 201)
        self.client.force_authenticate(self.other_user)
        self.assertEqual(self.submit(key=key).status_code, 201)
        self.assertEqual(QuizAttempt.objects.count(), 2)

    def test_malformed_idempotency_key_is_rejected(self):
        self.assertEqual(self.submit(key="not-a-uuid").status_code, 400)
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_answer_write_failure_rolls_back_the_entire_attempt(self):
        answers = [
            {"question_id": uuid.UUID(a["question_id"]), "choice_id": uuid.UUID(a["choice_id"])}
            for a in self.answers
        ]
        with patch(
            "apps.quizzes.services.QuizAttemptAnswer.objects.bulk_create",
            side_effect=IntegrityError("unrelated integrity failure"),
        ):
            with self.assertRaises(IntegrityError):
                submit_quiz(
                    user=self.user,
                    quiz_id=self.quiz.pk,
                    answers=answers,
                    idempotency_key=uuid.uuid4(),
                )
        self.assertEqual(QuizAttempt.objects.count(), 0)
        self.assertEqual(QuizAttemptAnswer.objects.count(), 0)
