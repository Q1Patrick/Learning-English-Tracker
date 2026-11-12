"""A complete backend journey using real JWT login and a disposable test database."""

from datetime import datetime, timezone
from io import StringIO
from unittest.mock import patch
from uuid import uuid4

from django.core.management import call_command
from django.utils.dateparse import parse_datetime
from rest_framework.test import APIClient, APITestCase

from apps.quizzes.seed_data import QUIZ_SEEDS, seed_uuid


class Person3JourneyTests(APITestCase):
    def register_and_login(self, client, email):
        password = "Person3FlowPass!7192"
        response = client.post(
            "/api/v1/auth/register/",
            {"email": email, "password": password, "password_confirm": password},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        login = client.post(
            "/api/v1/auth/login/", {"email": email, "password": password}, format="json"
        )
        self.assertEqual(login.status_code, 200)
        client.credentials(HTTP_AUTHORIZATION="Bearer " + login.data["access"])

    @patch("django.utils.timezone.now", return_value=datetime(2026, 11, 10, 5, tzinfo=timezone.utc))
    def test_seed_login_submit_replay_history_and_dashboard(self, mock_now):
        fixed_now = mock_now.return_value
        call_command("seed_quizzes", stdout=StringIO())
        self.register_and_login(self.client, "person3-flow@example.com")
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/quizzes/").data["count"], 5)

        seed = QUIZ_SEEDS[0]
        quiz_id = seed_uuid(seed, "quiz")
        detail = self.client.get(f"/api/v1/quizzes/{quiz_id}/")
        self.assertEqual(detail.status_code, 200)
        for question in detail.data["data"]["questions"]:
            self.assertNotIn("explanation", question)
            for choice in question["choices"]:
                self.assertNotIn("is_correct", choice)
        # The test harness knows fixture answers; the public endpoint does not expose them.
        answers = []
        for question in seed.questions:
            position = next(i for i, choice in enumerate(question.choices, 1) if choice.is_correct)
            answers.append(
                {
                    "question_id": str(seed_uuid(seed, "question", question.slug)),
                    "choice_id": str(seed_uuid(seed, "choice", question.slug, str(position))),
                }
            )
        key = str(uuid4())
        first = self.client.post(
            f"/api/v1/quizzes/{quiz_id}/submit/",
            {"answers": answers},
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
        )
        self.assertEqual(first.status_code, 201)
        attempt = first.data["data"]
        self.assertEqual(
            (attempt["score"], attempt["correct_answers"], attempt["total_questions"]), (100, 3, 3)
        )
        self.assertEqual(len(attempt["answers"]), 3)
        self.assertEqual(parse_datetime(attempt["completed_at"]), fixed_now)
        replay = self.client.post(
            f"/api/v1/quizzes/{quiz_id}/submit/",
            {"answers": answers},
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
        )
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.data, first.data)
        history = self.client.get("/api/v1/quizzes/history/")
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.data["count"], 1)
        self.assertEqual(history.data, self.client.get("/api/v1/quizzes/attempts/").data)

        # The model's default callable was bound before timezone.now was patched.
        study_session = self.client.post(
            "/api/v1/study-sessions/",
            {
                "activity_type": "reading",
                "duration_minutes": 20,
                "studied_at": fixed_now.isoformat(),
            },
            format="json",
        )
        self.assertEqual(study_session.status_code, 201)
        self.assertEqual(parse_datetime(study_session.data["studied_at"]), fixed_now)
        self.assertEqual(
            self.client.post(
                "/api/v1/goals/",
                {"target_date": fixed_now.date().isoformat(), "target_minutes": 60},
                format="json",
            ).status_code,
            201,
        )
        dashboard = self.client.get("/api/v1/statistic/dashboard/")
        self.assertEqual(dashboard.status_code, 200)
        data = dashboard.data["data"]
        self.assertEqual((data["studied_minutes"], data["remaining_minutes"]), (20, 40))
        metrics = data["quiz_statistics"]
        self.assertEqual(
            (
                metrics["total_completed"],
                metrics["average_score"],
                metrics["total_correct_answers"],
            ),
            (1, 100.0, 3),
        )
        self.assertEqual(metrics["progress_over_time"][-1]["total_completed"], 1)

        other = APIClient()
        self.register_and_login(other, "person3-other-flow@example.com")
        self.assertEqual(other.get("/api/v1/quizzes/history/").data["count"], 0)
        self.assertEqual(other.get(f"/api/v1/quizzes/attempts/{attempt['id']}/").status_code, 404)
        self.assertEqual(
            other.get("/api/v1/statistic/dashboard/").data["data"]["quiz_statistics"][
                "total_completed"
            ],
            0,
        )
