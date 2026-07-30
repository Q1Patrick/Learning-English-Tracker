from django.contrib.auth import get_user_model
from django.test import TestCase


User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user_with_email(self):
        user = User.objects.create_user(
            email="patrick@example.com",
            password="StrongPassword123!",
        )

        self.assertEqual(user.email, "patrick@example.com")
        self.assertTrue(user.check_password("StrongPassword123!"))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_email_is_required(self):
        with self.assertRaisesMessage(
            ValueError,
            "Users must provide an email address.",
        ):
            User.objects.create_user(
                email="",
                password="StrongPassword123!",
            )

    def test_email_is_normalized(self):
        user = User.objects.create_user(
            email="Patrick@EXAMPLE.COM",
            password="StrongPassword123!",
        )

        self.assertEqual(user.email, "patrick@example.com")

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="StrongPassword123!",
        )

        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_active)

    def test_user_string_representation(self):
        user = User.objects.create_user(
            email="patrick@example.com",
            password="StrongPassword123!",
        )

        self.assertEqual(str(user), "patrick@example.com")