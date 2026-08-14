from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.test import SimpleTestCase

User = get_user_model()


class JWTAuthenticationTests(APITestCase):
    def setUp(self):
        self.password = "StrongPassword123!"

        self.user = User.objects.create_user(
            email="patrick@example.com",
            password=self.password,
            first_name="Patrick",
            last_name="Chau",
        )

        self.login_url = reverse("accounts:login")
        self.refresh_url = reverse("accounts:token-refresh")
        self.current_user_url = reverse("accounts:current-user")

    def test_user_can_login_with_email(self):
        response = self.client.post(
            self.login_url,
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        print("LOGIN RESPONSE:", response.data)

        self.assertEqual(
            response.data["user"]["email"],
            self.user.email,
        )

    def test_login_rejects_incorrect_password(self):
        response = self.client.post(
            self.login_url,
            {
                "email": self.user.email,
                "password": "IncorrectPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_authenticated_user_can_access_me_endpoint(self):
        login_response = self.client.post(
            self.login_url,
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
        )

        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.get(self.current_user_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["data"]["email"],
            self.user.email,
        )

    def test_unauthenticated_user_cannot_access_me_endpoint(self):
        response = self.client.get(self.current_user_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_refresh_token_returns_new_access_token(self):
        login_response = self.client.post(
            self.login_url,
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
        )

        refresh_token = login_response.data["refresh"]

        response = self.client.post(
            self.refresh_url,
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn("access", response.data)



class JWTTestDiscoveryTests(SimpleTestCase):
    def test_jwt_test_file_is_discovered(self):
        self.assertTrue(True)