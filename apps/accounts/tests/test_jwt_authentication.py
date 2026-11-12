"""JWT authorization is required for private API resources."""

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


class JWTAuthorizationTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email="jwt-authorization@example.com")
        self.token = RefreshToken.for_user(self.user)

    def test_access_token_authorizes_private_resource(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token.access_token}")
        response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["email"], self.user.email)

    def test_refresh_token_cannot_authorize_private_resource(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 401)

    def test_inactive_user_cannot_use_previously_issued_access_token(self):
        token = str(self.token.access_token)
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 401)
