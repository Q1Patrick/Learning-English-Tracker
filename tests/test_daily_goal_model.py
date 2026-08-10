from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.goals.models import DailyGoal


User = get_user_model()


class DailyGoalModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="student@example.com",
            password="StrongPassword123!",
        )

    def test_create_daily_goal(self):
        goal = DailyGoal.objects.create(
            user=self.user,
            target_date=date(2026, 8, 10),
            target_minutes=60,
        )

        self.assertEqual(goal.user, self.user)
        self.assertEqual(
            goal.target_date,
            date(2026, 8, 10),
        )
        self.assertEqual(goal.target_minutes, 60)

    def test_user_can_have_goals_for_different_dates(self):
        DailyGoal.objects.create(
            user=self.user,
            target_date=date(2026, 8, 10),
            target_minutes=60,
        )

        DailyGoal.objects.create(
            user=self.user,
            target_date=date(2026, 8, 11),
            target_minutes=90,
        )

        self.assertEqual(
            self.user.daily_goals.count(),
            2,
        )

    def test_user_cannot_have_two_goals_for_same_date(self):
        DailyGoal.objects.create(
            user=self.user,
            target_date=date(2026, 8, 10),
            target_minutes=60,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                DailyGoal.objects.create(
                    user=self.user,
                    target_date=date(2026, 8, 10),
                    target_minutes=90,
                )

    def test_different_users_can_have_goal_on_same_date(self):
        second_user = User.objects.create_user(
            email="second@example.com",
            password="StrongPassword123!",
        )

        DailyGoal.objects.create(
            user=self.user,
            target_date=date(2026, 8, 10),
            target_minutes=60,
        )

        DailyGoal.objects.create(
            user=second_user,
            target_date=date(2026, 8, 10),
            target_minutes=45,
        )

        self.assertEqual(
            DailyGoal.objects.count(),
            2,
        )

    def test_target_minutes_cannot_be_less_than_five(self):
        goal = DailyGoal(
            user=self.user,
            target_date=date(2026, 8, 10),
            target_minutes=0,
        )

        with self.assertRaises(ValidationError):
            goal.full_clean()

    def test_target_minutes_cannot_exceed_480(self):
        goal = DailyGoal(
            user=self.user,
            target_date=date(2026, 8, 10),
            target_minutes=481,
        )

        with self.assertRaises(ValidationError):
            goal.full_clean()

    def test_deleting_user_deletes_daily_goals(self):
        DailyGoal.objects.create(
            user=self.user,
            target_date=date(2026, 8, 10),
            target_minutes=60,
        )

        self.user.delete()

        self.assertEqual(
            DailyGoal.objects.count(),
            0,
        )