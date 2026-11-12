from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import UserProfile
from apps.accounts.serializers import CurrentUserSerializer

User = get_user_model()


class CurrentUserProfileTests(APITestCase):
    def setUp(self):
        self.password = "StrongPassword123!"

        self.user = User.objects.create_user(
            email="patrick@example.com",
            password=self.password,
            first_name="Patrick",
            last_name="Chau",
        )

        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name="Patrick",
            english_level="A2",
            daily_target_minutes=30,
            timezone="Asia/Ho_Chi_Minh",
        )

        self.url = reverse("accounts:current-user")

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_authenticated_user_can_view_profile(self):
        self.authenticate()

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["data"]["email"],
            self.user.email,
        )
        self.assertEqual(
            response.data["data"]["profile"]["english_level"],
            "A2",
        )

    def test_unauthenticated_user_cannot_view_profile(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_user_can_update_profile(self):
        self.authenticate()

        response = self.client.patch(
            self.url,
            {
                "first_name": "Updated",
                "profile": {
                    "english_level": "B1",
                    "daily_target_minutes": 60,
                },
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.refresh_from_db()
        self.profile.refresh_from_db()

        self.assertEqual(
            self.user.first_name,
            "Updated",
        )
        self.assertEqual(
            self.profile.english_level,
            "B1",
        )
        self.assertEqual(
            self.profile.daily_target_minutes,
            60,
        )

    def test_invalid_daily_target_is_rejected(self):
        self.authenticate()

        response = self.client.patch(
            self.url,
            {
                "profile": {
                    "daily_target_minutes": 0,
                }
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_user_cannot_change_email_through_profile_endpoint(self):
        self.authenticate()

        response = self.client.patch(
            self.url,
            {
                "email": "hacker@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.email,
            "patrick@example.com",
        )

    def test_invalid_timezone_is_rejected_without_updating_profile(self):
        self.authenticate()
        response = self.client.patch(
            self.url,
            {"profile": {"timezone": "Invalid/Timezone"}},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "invalid_timezone")
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.timezone, "Asia/Ho_Chi_Minh")

    def test_valid_timezone_can_be_updated(self):
        self.authenticate()
        response = self.client.patch(
            self.url, {"profile": {"timezone": "Europe/London"}}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.timezone, "Europe/London")

    def test_account_update_rolls_back_when_profile_save_fails(self):
        serializer = CurrentUserSerializer(
            self.user,
            data={"first_name": "New name", "profile": {"display_name": "New display"}},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        with patch.object(UserProfile, "save", side_effect=RuntimeError("write failed")):
            with self.assertRaisesRegex(RuntimeError, "write failed"):
                serializer.save()
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, "Patrick")
        self.assertEqual(self.profile.display_name, "Patrick")
