from datetime import date, datetime
from datetime import timezone as dt_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import UserProfile
from apps.goals.models import DailyGoal
from apps.learning.models import StudySession

User = get_user_model()


class DashboardStatisticsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="student@example.com",
            password="StrongPassword123!",
        )

        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)

        self.profile.timezone = "Asia/Ho_Chi_Minh"
        self.profile.daily_target_minutes = 30
        self.profile.save()

        self.client.force_authenticate(user=self.user)

        self.url = "/api/v1/statistic/dashboard/"

    def test_dashboard_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            401,
        )

    @patch("apps.statistic.services.timezone.now")
    def test_dashboard_calculates_today_progress(self, mock_now):
        # Fixed UTC instant is noon in Vietnam; independent of machine timezone.
        studied_at = datetime(2026, 11, 9, 5, 0, tzinfo=dt_timezone.utc)
        mock_now.return_value = studied_at
        today = date(2026, 11, 9)

        DailyGoal.objects.create(
            user=self.user,
            target_date=today,
            target_minutes=60,
        )

        StudySession.objects.create(
            user=self.user,
            activity_type="speaking",
            duration_minutes=20,
            studied_at=studied_at,
        )

        StudySession.objects.create(
            user=self.user,
            activity_type="listening",
            duration_minutes=25,
            studied_at=studied_at,
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.data["data"]

        self.assertEqual(
            data["target_minutes"],
            60,
        )

        self.assertEqual(
            data["studied_minutes"],
            45,
        )

        self.assertEqual(
            data["remaining_minutes"],
            15,
        )

        self.assertEqual(
            data["progress_percent"],
            75.0,
        )

        self.assertEqual(
            data["sessions_count"],
            2,
        )
