"""Registration validation, privacy and transactional integrity."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.test import APITestCase

from apps.accounts.models import UserProfile
from apps.accounts.serializers import RegisterSerializer

User = get_user_model()


class RegistrationTests(APITestCase):
    url = "/api/v1/auth/register/"

    def payload(self, **overrides):
        return {
            "email": "new-student@example.com",
            "first_name": "Learner",
            "last_name": "Example",
            "password": "UnrelatedStrongPassword!982",
            "password_confirm": "UnrelatedStrongPassword!982",
            **overrides,
        }

    def test_registration_normalizes_email_hashes_password_and_creates_profile(self):
        payload = self.payload(email="  NEW-STUDENT@EXAMPLE.COM  ")
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="new-student@example.com")
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotEqual(user.password, payload["password"])
        self.assertEqual(user.first_name, "Learner")
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertEqual(response.data["data"]["email"], user.email)
        self.assertNotIn("password", response.data["data"])
        self.assertNotIn("password_confirm", response.data["data"])
        self.assertNotIn(payload["password"], str(response.data))

    def test_duplicate_email_is_case_insensitive_and_has_stable_error_code(self):
        User.objects.create_user(email="new-student@example.com")
        for email in ("new-student@example.com", "NEW-STUDENT@EXAMPLE.COM"):
            with self.subTest(email=email):
                response = self.client.post(self.url, self.payload(email=email), format="json")
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.data["error"]["code"], "duplicate_record")
                self.assertIn("email", response.data["error"]["details"])
        self.assertEqual(User.objects.count(), 1)

    def test_password_confirmation_mismatch_does_not_create_user(self):
        response = self.client.post(
            self.url,
            self.payload(password_confirm="DifferentStrongPassword!234"),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("password_confirm", response.data["error"]["details"])
        self.assertFalse(User.objects.exists())

    def test_weak_password_is_rejected_before_account_creation(self):
        for password in ("123", "password", "12345678"):
            with self.subTest(password_type="weak"):
                response = self.client.post(
                    self.url,
                    self.payload(password=password, password_confirm=password),
                    format="json",
                )
                self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.exists())
        self.assertFalse(UserProfile.objects.exists())

    def test_invalid_email_does_not_create_user(self):
        response = self.client.post(self.url, self.payload(email="not-an-email"), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data["error"]["details"])
        self.assertFalse(User.objects.exists())

    def test_user_creation_rolls_back_when_profile_creation_fails(self):
        serializer = RegisterSerializer(data=self.payload())
        serializer.is_valid(raise_exception=True)
        with patch.object(
            UserProfile.objects, "create", side_effect=RuntimeError("profile write failed")
        ):
            with self.assertRaisesRegex(RuntimeError, "profile write failed"):
                serializer.save()
        self.assertFalse(User.objects.exists())
        self.assertFalse(UserProfile.objects.exists())

    def test_duplicate_after_validation_is_translated_and_transaction_survives(self):
        serializer = RegisterSerializer(data=self.payload())
        serializer.is_valid(raise_exception=True)
        User.objects.create_user(email="new-student@example.com")
        with self.assertRaises(serializers.ValidationError) as error:
            serializer.save()
        self.assertEqual(error.exception.get_codes()["email"][0], "duplicate_record")
        self.assertEqual(User.objects.count(), 1)
        self.assertFalse(UserProfile.objects.exists())

    def test_unrelated_integrity_error_is_not_mislabeled_as_duplicate(self):
        serializer = RegisterSerializer(data=self.payload())
        serializer.is_valid(raise_exception=True)
        with patch.object(User, "save", side_effect=IntegrityError("unrelated database failure")):
            with self.assertRaisesRegex(IntegrityError, "unrelated database failure"):
                serializer.save()
        self.assertFalse(User.objects.exists())
