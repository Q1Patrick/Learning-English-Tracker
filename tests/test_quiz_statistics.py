"""Person 3 statistics: retakes, ownership and local calendar-day boundaries."""

import uuid
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.accounts.models import UserProfile
from apps.quizzes.models import Quiz, QuizAttempt


class QuizStatisticsTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(email="quiz-statistics@example.com")
        cls.other_user = get_user_model().objects.create_user(
            email="other-quiz-statistics@example.com"
        )
        UserProfile.objects.create(user=cls.user, timezone="Asia/Ho_Chi_Minh")
        cls.quiz = Quiz.objects.create(title="Repeated practice")

    def setUp(self):
        self.client.force_authenticate(self.user)

    def attempt(self, score, when, *, user=None, identifier=None, total=100, correct=None):
        values = {
            "user": user or self.user,
            "quiz": self.quiz,
            "quiz_id_snapshot": self.quiz.pk,
            "quiz_title_snapshot": self.quiz.title,
            "score": score,
            "correct_answers": score if correct is None else correct,
            "total_questions": total,
        }
        if identifier is not None:
            values["id"] = identifier
        attempt = QuizAttempt.objects.create(**values)
        QuizAttempt.objects.filter(pk=attempt.pk).update(completed_at=when)
        return attempt

    def statistics(self, *, today=date(2026, 11, 10), zone="Asia/Ho_Chi_Minh"):
        from apps.statistic.quiz_services import build_quiz_statistics

        return build_quiz_statistics(self.user, today=today, user_timezone=ZoneInfo(zone))

    def test_dashboard_adds_quiz_statistics_without_removing_learning_fields(self):
        now = datetime(2026, 11, 10, 5, tzinfo=timezone.utc)
        with patch("apps.statistic.services.timezone.now", return_value=now):
            response = self.client.get("/api/v1/statistic/dashboard/")
        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertTrue(
            {"target_minutes", "studied_minutes", "week_minutes", "activity_breakdown"}
            <= data.keys()
        )
        self.assertIn("quiz_statistics", data)
        self.assertEqual(data["quiz_statistics"]["progress_over_time"][-1]["date"], "2026-11-10")

    def test_empty_history_is_distinct_from_a_zero_score(self):
        data = self.statistics()
        self.assertEqual(data["total_completed"], 0)
        self.assertEqual(data["total_correct_answers"], 0)
        for field in ("average_score", "best_score", "recent_score"):
            self.assertIsNone(data[field])
        self.assertEqual(len(data["progress_over_time"]), 30)
        self.assertEqual(data["progress_over_time"][0]["date"], date(2026, 10, 12))
        for day in data["progress_over_time"]:
            self.assertEqual(day["total_completed"], 0)
            self.assertIsNone(day["average_score"])

    def test_every_retake_counts_and_all_time_summary_includes_older_attempts(self):
        self.attempt(0, datetime(2026, 9, 1, 5, tzinfo=timezone.utc))
        self.attempt(100, datetime(2026, 11, 9, 5, tzinfo=timezone.utc))
        self.attempt(50, datetime(2026, 11, 10, 5, tzinfo=timezone.utc))
        data = self.statistics()
        self.assertEqual(data["total_completed"], 3)
        self.assertEqual(data["average_score"], 50.0)
        self.assertEqual(data["best_score"], 100)
        self.assertEqual(data["recent_score"], 50)
        self.assertEqual(data["total_correct_answers"], 150)
        self.assertEqual(sum(day["total_completed"] for day in data["progress_over_time"]), 2)

    def test_average_is_per_attempt_not_weighted_by_question_count(self):
        when = datetime(2026, 11, 10, 5, tzinfo=timezone.utc)
        self.attempt(100, when, total=1, correct=1)
        self.attempt(0, when, total=9, correct=0)
        data = self.statistics()
        self.assertEqual(data["average_score"], 50.0)
        self.assertEqual(data["total_correct_answers"], 1)

    def test_other_users_attempts_are_excluded_from_every_metric(self):
        when = datetime(2026, 11, 10, 5, tzinfo=timezone.utc)
        self.attempt(0, when)
        self.attempt(100, when, user=self.other_user)
        data = self.statistics()
        self.assertEqual(data["total_completed"], 1)
        self.assertEqual(
            (data["average_score"], data["best_score"], data["recent_score"]), (0.0, 0, 0)
        )
        self.assertEqual(data["total_correct_answers"], 0)
        self.assertEqual(data["progress_over_time"][-1]["average_score"], 0.0)

    def test_deleted_quiz_does_not_remove_its_historical_statistics(self):
        self.attempt(60, datetime(2026, 11, 10, 5, tzinfo=timezone.utc))
        self.quiz.delete()
        data = self.statistics()
        self.assertEqual((data["total_completed"], data["average_score"]), (1, 60.0))

    def test_recent_score_has_deterministic_order_when_timestamps_tie(self):
        when = datetime(2026, 11, 10, 5, tzinfo=timezone.utc)
        self.attempt(0, when, identifier=uuid.UUID(int=2))
        self.attempt(100, when, identifier=uuid.UUID(int=1))
        self.assertEqual(self.statistics()["recent_score"], 0)

    def test_progress_includes_exactly_thirty_local_calendar_days(self):
        for score, when in [
            (0, datetime(2026, 10, 11, 16, 59, tzinfo=timezone.utc)),
            (50, datetime(2026, 10, 11, 17, 0, tzinfo=timezone.utc)),
            (100, datetime(2026, 11, 10, 16, 59, tzinfo=timezone.utc)),
            (0, datetime(2026, 11, 10, 17, 0, tzinfo=timezone.utc)),
        ]:
            self.attempt(score, when)
        days = self.statistics()["progress_over_time"]
        self.assertEqual(sum(day["total_completed"] for day in days), 2)
        self.assertEqual(
            (days[0]["date"], days[-1]["date"]), (date(2026, 10, 12), date(2026, 11, 10))
        )
        self.assertEqual((days[0]["average_score"], days[-1]["average_score"]), (50.0, 100.0))

    def test_vietnam_midnight_separates_adjacent_local_days(self):
        self.attempt(50, datetime(2026, 11, 9, 16, 59, tzinfo=timezone.utc))
        self.attempt(100, datetime(2026, 11, 9, 17, 0, tzinfo=timezone.utc))
        days = self.statistics()["progress_over_time"]
        self.assertEqual((days[-2]["total_completed"], days[-1]["total_completed"]), (1, 1))
        self.assertEqual((days[-2]["average_score"], days[-1]["average_score"]), (50.0, 100.0))

    def test_dst_days_use_local_boundaries_instead_of_fixed_twenty_four_hours(self):
        for today, before, start, last, after in [
            (date(2026, 3, 8), (3, 8, 4, 59), (3, 8, 5, 0), (3, 9, 3, 59), (3, 9, 4, 0)),
            (date(2026, 11, 1), (11, 1, 3, 59), (11, 1, 4, 0), (11, 2, 4, 59), (11, 2, 5, 0)),
        ]:
            with self.subTest(today=today):
                QuizAttempt.objects.all().delete()
                for values in (before, start, last, after):
                    self.attempt(50, datetime(2026, *values, tzinfo=timezone.utc))
                days = self.statistics(today=today, zone="America/New_York")["progress_over_time"]
                self.assertEqual(days[-1]["total_completed"], 2)
                self.assertEqual(days[-2]["total_completed"], 1)
                self.assertEqual(sum(day["total_completed"] for day in days), 3)

    def test_average_rounds_half_up_to_one_decimal(self):
        when = datetime(2026, 11, 10, 5, tzinfo=timezone.utc)
        self.attempt(1, when)
        for _ in range(19):
            self.attempt(0, when)
        data = self.statistics()
        self.assertEqual(data["average_score"], 0.1)
        self.assertEqual(data["progress_over_time"][-1]["average_score"], 0.1)

    def test_query_count_does_not_grow_with_days_or_attempts(self):
        when = datetime(2026, 11, 10, 5, tzinfo=timezone.utc)
        for offset in range(35):
            self.attempt(50, when - timedelta(days=offset))
        with self.assertNumQueries(3):
            data = self.statistics()
        self.assertEqual(data["total_completed"], 35)
        self.assertEqual(sum(day["total_completed"] for day in data["progress_over_time"]), 30)
