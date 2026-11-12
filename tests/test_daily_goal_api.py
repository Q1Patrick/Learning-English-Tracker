"""Daily-goal API regression and ownership tests."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from rest_framework import serializers
from rest_framework.test import APITestCase

from apps.goals.models import DailyGoal
from apps.goals.serializers import DailyGoalSerializer

User = get_user_model()


class DailyGoalAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="goals@example.com")
        self.other = User.objects.create_user(email="other-goals@example.com")
        self.client.force_authenticate(self.user)
        self.url = "/api/v1/goals/"
        self.goal = DailyGoal.objects.create(
            user=self.user, target_date=date(2026, 11, 9), target_minutes=30
        )
        self.other_goal = DailyGoal.objects.create(
            user=self.other, target_date=date(2026, 11, 10), target_minutes=60
        )

    def test_duplicate_create_returns_field_error(self):
        response = self.client.post(
            self.url,
            {"target_date": "2026-11-09", "target_minutes": 60},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "duplicate_record")
        self.assertIn("target_date", response.data["error"]["details"])

    def test_duplicate_update_returns_field_error(self):
        second = DailyGoal.objects.create(
            user=self.user, target_date=date(2026, 11, 10), target_minutes=45
        )
        response = self.client.patch(
            f"{self.url}{second.pk}/", {"target_date": "2026-11-09"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "duplicate_record")
        second.refresh_from_db()
        self.assertEqual(second.target_date, date(2026, 11, 10))

    def test_unchanged_date_can_be_saved(self):
        response = self.client.patch(
            f"{self.url}{self.goal.pk}/",
            {"target_date": "2026-11-09", "target_minutes": 45},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.target_minutes, 45)

    def test_same_date_is_allowed_for_different_users(self):
        response = self.client.post(
            self.url,
            {"target_date": "2026-11-10", "target_minutes": 30},
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_list_is_scoped_to_current_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(self.goal.pk))

    def test_other_users_goal_is_not_readable_or_editable(self):
        url = f"{self.url}{self.other_goal.pk}/"
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(
            self.client.patch(url, {"target_minutes": 90}, format="json").status_code,
            404,
        )
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.other_goal.refresh_from_db()
        self.assertEqual(self.other_goal.target_minutes, 60)

    def test_invalid_target_is_rejected(self):
        response = self.client.post(
            self.url,
            {"target_date": "2026-11-11", "target_minutes": 481},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_authentication_is_required(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(self.url).status_code, 401)


class DailyGoalWriteRaceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="goal-race@example.com")
        self.context = {"request": SimpleNamespace(user=self.user)}

    def test_duplicate_after_validation_is_translated_and_transaction_survives(self):
        serializer = DailyGoalSerializer(
            data={"target_date": "2026-11-09", "target_minutes": 30},
            context=self.context,
        )
        serializer.is_valid(raise_exception=True)
        DailyGoal.objects.create(user=self.user, target_date=date(2026, 11, 9), target_minutes=60)
        with self.assertRaises(serializers.ValidationError) as error:
            serializer.save(user=self.user)
        self.assertEqual(error.exception.get_codes()["target_date"][0], "duplicate_record")
        self.assertEqual(DailyGoal.objects.filter(user=self.user).count(), 1)

    def test_unrelated_integrity_error_is_not_mislabeled(self):
        serializer = DailyGoalSerializer(
            data={"target_date": "2026-11-09", "target_minutes": 30},
            context=self.context,
        )
        serializer.is_valid(raise_exception=True)
        with patch.object(
            DailyGoal, "save", side_effect=IntegrityError("unrelated database failure")
        ):
            with self.assertRaisesRegex(IntegrityError, "unrelated database failure"):
                serializer.save(user=self.user)
        self.assertEqual(DailyGoal.objects.count(), 0)
