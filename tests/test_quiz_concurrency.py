"""Exercise duplicate requests using independent database connections."""

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connections
from django.test import TransactionTestCase

from apps.quizzes.models import Choice, Question, Quiz, QuizAttempt
from apps.quizzes.services import submit_quiz


class ConcurrentQuizSubmissionTests(TransactionTestCase):
    def test_simultaneous_retries_produce_one_attempt(self):
        user = get_user_model().objects.create_user(email="concurrent-quiz@example.com")
        quiz = Quiz.objects.create(title="Concurrent submissions")
        question = Question.objects.create(quiz=quiz, text="Choose the right answer")
        correct = Choice.objects.create(question=question, text="Right", is_correct=True)
        Choice.objects.create(question=question, text="Wrong")
        answers = [{"question_id": question.pk, "choice_id": correct.pk}]
        key = uuid.uuid4()
        barrier = threading.Barrier(2)

        def submit():
            close_old_connections()
            try:
                local_user = get_user_model().objects.get(pk=user.pk)
                barrier.wait(timeout=5)
                attempt, created = submit_quiz(
                    user=local_user, quiz_id=quiz.pk, answers=answers, idempotency_key=key
                )
                return attempt.pk, created
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(submit) for _ in range(2)]
            results = [future.result(timeout=10) for future in futures]
        self.assertEqual(results[0][0], results[1][0])
        self.assertEqual(sorted(created for _, created in results), [False, True])
        self.assertEqual(QuizAttempt.objects.count(), 1)
