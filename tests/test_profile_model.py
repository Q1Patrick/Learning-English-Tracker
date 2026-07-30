from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import UserProfile


User = get_user_model()


class UserProfileModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="patrick@example.com",
            password="StrongPassword123!",
        )

    def test_create_user_profile(self):
        profile = UserProfile.objects.create(
            user=self.user,
            display_name="Patrick",
            english_level=UserProfile.EnglishLevel.INTERMEDIATE,
            daily_target_minutes=60,
            learning_goal="Speak English confidently.",
            timezone="Asia/Ho_Chi_Minh",
        )

        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.display_name, "Patrick")
        self.assertEqual(profile.english_level, "B1")
        self.assertEqual(profile.daily_target_minutes, 60)

    def test_profile_has_default_values(self):
        profile = UserProfile.objects.create(user=self.user)

        self.assertEqual(
            profile.english_level,
            UserProfile.EnglishLevel.BEGINNER,
        )
        self.assertEqual(profile.daily_target_minutes, 30)
        self.assertEqual(profile.timezone, "UTC")

    def test_user_can_have_only_one_profile(self):
        UserProfile.objects.create(user=self.user)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UserProfile.objects.create(user=self.user)

    def test_profile_is_deleted_when_user_is_deleted(self):
        profile = UserProfile.objects.create(user=self.user)
        profile_id = profile.id

        self.user.delete()

        self.assertFalse(
            UserProfile.objects.filter(id=profile_id).exists()
        )

    def test_daily_target_must_be_at_least_five_minutes(self):
        profile = UserProfile(
            user=self.user,
            daily_target_minutes=0,
        )

        with self.assertRaises(ValidationError):
            profile.full_clean()

    def test_user_profile_string_representation(self):
        profile = UserProfile.objects.create(user=self.user)

        self.assertEqual(
            str(profile),
            "Profile of patrick@example.com",
        )