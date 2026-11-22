"""Real database/CSRF checks for the browser session contract, without JWT mocks."""

import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.base import UpdateError
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from apps.accounts.session_auth import APP_SESSION_KEY
from apps.vocabulary.models import Vocabulary

User = get_user_model()


@override_settings(
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
    CSRF_TRUSTED_ORIGINS=["http://localhost:5173"],
)
class SessionAuthenticationTests(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.password = secrets.token_urlsafe(24)
        self.user = User.objects.create_user(
            email="session-a@example.invalid", password=self.password
        )
        self.other_user = User.objects.create_user(
            email="session-b@example.invalid", password=secrets.token_urlsafe(24)
        )
        self.session_url = reverse("accounts:session")
        self.login_url = reverse("accounts:session-login")
        self.logout_url = reverse("accounts:session-logout")
        self.me_url = reverse("accounts:current-user")

    def bootstrap(self, client=None, **kwargs):
        response = (client or self.client).get(self.session_url, **kwargs)
        self.assertEqual(response.status_code, 200)
        return response.data["data"]["csrf_token"]

    def login(self, *, client=None, remember_me=False, **kwargs):
        client = client or self.client
        csrf_token = self.bootstrap(client)
        return client.post(
            self.login_url,
            {"email": self.user.email, "password": self.password, "remember_me": remember_me},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
            **kwargs,
        )

    def set_activity(self, *, started_ago, idle_ago, remember_me=False):
        session = self.client.session
        metadata = session[APP_SESSION_KEY]
        now = int(timezone.now().timestamp())
        absolute = (
            settings.APP_SESSION_REMEMBER_ABSOLUTE_SECONDS
            if remember_me
            else settings.APP_SESSION_ABSOLUTE_SECONDS
        )
        metadata.update(
            started_at=now - started_ago,
            absolute_expires_at=now - started_ago + absolute,
            last_activity=now - idle_ago,
        )
        session[APP_SESSION_KEY] = metadata
        session.save()
        return metadata

    def test_anonymous_bootstrap_has_http_only_csrf_and_no_auth_cookie_or_jwt(self):
        response = self.client.get(self.session_url)
        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertFalse(data["authenticated"])
        self.assertIsNone(data["user"])
        self.assertIsNone(data["expires_at"])
        self.assertIsNone(data["expires_in"])
        self.assertIsNone(data["absolute_expires_at"])
        self.assertEqual(len(data["csrf_token"]), 64)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        self.assertNotIn(settings.SESSION_COOKIE_NAME, response.cookies)
        self.assertEqual(Session.objects.count(), 0)
        cookie = response.cookies[settings.CSRF_COOKIE_NAME]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertFalse(cookie["secure"])
        self.assertIn("no-store", response["Cache-Control"])

    def test_anonymous_login_and_logout_require_csrf(self):
        for url in (self.login_url, self.logout_url):
            with self.subTest(endpoint=url):
                response = self.client.post(url, {}, format="json")
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()["error"]["code"], "csrf_failed")
                self.assertIn("no-store", response["Cache-Control"])

    def test_wrong_csrf_and_untrusted_origin_are_rejected(self):
        token = self.bootstrap()
        for extra in (
            {"HTTP_X_CSRFTOKEN": "x" * 64},
            {"HTTP_X_CSRFTOKEN": token, "HTTP_ORIGIN": "https://untrusted.example.invalid"},
        ):
            response = self.client.post(self.login_url, {}, format="json", **extra)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()["error"]["code"], "csrf_failed")

    def test_configured_frontend_origin_is_allowed(self):
        response = self.login(HTTP_ORIGIN="http://localhost:5173")
        self.assertEqual(response.status_code, 200)

    def test_bootstrap_ignores_bearer_and_failed_csrf_does_not_logout(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid")
        self.bootstrap()
        self.client.credentials()
        self.assertEqual(self.login().status_code, 200)
        old_key = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        metadata = self.set_activity(started_ago=120, idle_ago=60)
        denied = self.client.post(self.logout_url, {}, format="json")
        self.assertEqual(denied.status_code, 403)
        self.assertTrue(Session.objects.filter(session_key=old_key).exists())
        self.assertEqual(self.client.session[APP_SESSION_KEY], metadata)
        self.assertTrue(self.client.get(self.session_url).data["data"]["authenticated"])

    def test_login_sets_browser_session_and_restores_exact_user_contract(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertTrue(data["authenticated"])
        self.assertEqual(
            set(data["user"]),
            {"id", "email", "first_name", "last_name", "is_email_verified"},
        )
        self.assertEqual(data["user"]["id"], str(self.user.pk))
        self.assertFalse(data["user"]["is_email_verified"])
        self.assertEqual(len(data["csrf_token"]), 64)
        self.assertGreater(data["expires_in"], 0)
        self.assertLessEqual(data["expires_in"], settings.APP_SESSION_IDLE_SECONDS)
        self.assertLess(data["expires_at"], data["absolute_expires_at"])
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        cookie = response.cookies[settings.SESSION_COOKIE_NAME]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertEqual(cookie["domain"], "")
        self.assertEqual(cookie["expires"], "")
        self.assertEqual(cookie["max-age"], "")
        restored = self.client.get(self.session_url)
        self.assertEqual(restored.data["data"]["user"], data["user"])
        self.assertEqual(restored.data["data"]["absolute_expires_at"], data["absolute_expires_at"])
        self.assertEqual(self.client.get(self.me_url).status_code, 200)

    def test_remember_me_cookie_has_fixed_seven_day_absolute_expiry(self):
        response = self.login(remember_me=True)
        self.assertEqual(response.status_code, 200)
        cookie = response.cookies[settings.SESSION_COOKIE_NAME]
        self.assertTrue(cookie["expires"])
        self.assertGreater(int(cookie["max-age"]), 6 * 24 * 60 * 60)
        self.assertLessEqual(int(cookie["max-age"]), settings.APP_SESSION_REMEMBER_ABSOLUTE_SECONDS)
        metadata = self.client.session[APP_SESSION_KEY]
        self.assertEqual(
            metadata["absolute_expires_at"] - metadata["started_at"],
            settings.APP_SESSION_REMEMBER_ABSOLUTE_SECONDS,
        )
        self.assertLessEqual(
            response.data["data"]["expires_in"], settings.APP_SESSION_REMEMBER_IDLE_SECONDS
        )

    def test_login_default_remember_is_false_and_rejects_non_boolean_or_unknown_fields(self):
        token = self.bootstrap()
        payload = {"email": self.user.email, "password": self.password}
        response = self.client.post(self.login_url, payload, format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.client.session[APP_SESSION_KEY]["remember_me"])
        for extra in ({"remember_me": "false"}, {"remember_me": 1}, {"unexpected": True}):
            token = self.bootstrap()
            response = self.client.post(
                self.login_url, {**payload, **extra}, format="json", HTTP_X_CSRFTOKEN=token
            )
            self.assertEqual(response.status_code, 400)

    def test_invalid_and_inactive_credentials_have_same_generic_401(self):
        token = self.bootstrap()
        response = self.client.post(
            self.login_url,
            {"email": self.user.email, "password": secrets.token_urlsafe(24)},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 401)
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        inactive = self.client.post(
            self.login_url,
            {"email": self.user.email, "password": self.password},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(inactive.status_code, 401)
        self.assertEqual(inactive.data["error"], response.data["error"])

    def test_login_preserves_password_whitespace_and_rotates_existing_session(self):
        self.password = f"  {self.password}  "
        self.user.set_password(self.password)
        self.user.save(update_fields=["password"])
        first = self.login()
        self.assertEqual(first.status_code, 200)
        old_key = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        second = self.login()
        self.assertEqual(second.status_code, 200)
        self.assertNotEqual(self.client.cookies[settings.SESSION_COOKIE_NAME].value, old_key)
        self.assertFalse(Session.objects.filter(session_key=old_key).exists())
        token = second.data["data"]["csrf_token"]
        trimmed = self.client.post(
            self.login_url,
            {"email": self.user.email, "password": self.password.strip()},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(trimmed.status_code, 401)

    def test_bootstrap_does_not_touch_idle_but_protected_api_does_not_slide_absolute(self):
        self.assertEqual(self.login().status_code, 200)
        metadata = self.set_activity(started_ago=120, idle_ago=60)
        bootstrap = self.client.get(self.session_url).data["data"]
        self.assertEqual(
            self.client.session[APP_SESSION_KEY]["last_activity"], metadata["last_activity"]
        )
        self.assertEqual(
            bootstrap["expires_at"], metadata["last_activity"] + settings.APP_SESSION_IDLE_SECONDS
        )
        self.assertEqual(self.client.get(self.me_url).status_code, 200)
        touched = self.client.session[APP_SESSION_KEY]
        self.assertGreater(touched["last_activity"], metadata["last_activity"])
        self.assertEqual(touched["absolute_expires_at"], metadata["absolute_expires_at"])

    def test_absolute_and_idle_expiry_apply_to_bootstrap_and_protected_api(self):
        for remember in (False, True):
            absolute = (
                settings.APP_SESSION_REMEMBER_ABSOLUTE_SECONDS
                if remember
                else settings.APP_SESSION_ABSOLUTE_SECONDS
            )
            idle = (
                settings.APP_SESSION_REMEMBER_IDLE_SECONDS
                if remember
                else settings.APP_SESSION_IDLE_SECONDS
            )
            for started_ago, idle_ago in ((absolute + 1, 1), (idle + 1, idle + 1)):
                for endpoint in (self.session_url, self.me_url):
                    with self.subTest(remember=remember, endpoint=endpoint, idle=idle_ago):
                        self.assertEqual(self.login(remember_me=remember).status_code, 200)
                        self.set_activity(
                            started_ago=started_ago, idle_ago=idle_ago, remember_me=remember
                        )
                        old_key = self.client.cookies[settings.SESSION_COOKIE_NAME].value
                        response = self.client.get(endpoint)
                        if endpoint == self.session_url:
                            self.assertEqual(response.status_code, 200)
                            self.assertFalse(response.data["data"]["authenticated"])
                        else:
                            self.assertEqual(response.status_code, 401)
                        self.assertFalse(Session.objects.filter(session_key=old_key).exists())

    def test_inactive_user_and_changed_password_invalidate_existing_session(self):
        self.assertEqual(self.login().status_code, 200)
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        self.assertFalse(self.client.get(self.session_url).data["data"]["authenticated"])
        self.user.is_active = True
        self.user.save(update_fields=["is_active"])
        self.assertEqual(self.login().status_code, 200)
        self.user.set_password(secrets.token_urlsafe(24))
        self.user.save(update_fields=["password"])
        self.assertEqual(self.client.get(self.me_url).status_code, 401)

    def test_protected_write_requires_csrf_and_valid_token_updates_profile(self):
        self.assertEqual(self.login().status_code, 200)
        denied = self.client.patch(self.me_url, {"first_name": "Updated"}, format="json")
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(denied.data["error"]["code"], "csrf_failed")
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "")
        token = self.bootstrap()
        allowed = self.client.patch(
            self.me_url, {"first_name": "Updated"}, format="json", HTTP_X_CSRFTOKEN=token
        )
        self.assertEqual(allowed.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")

    def test_session_owner_cannot_read_or_modify_another_users_vocabulary(self):
        item = Vocabulary.objects.create(user=self.other_user, word="private", meaning="owner only")
        detail = reverse("vocabulary:detail", kwargs={"pk": item.pk})
        self.assertEqual(self.login().status_code, 200)
        self.assertEqual(self.client.get(detail).status_code, 404)
        token = self.bootstrap()
        response = self.client.patch(
            detail, {"meaning": "changed"}, format="json", HTTP_X_CSRFTOKEN=token
        )
        self.assertEqual(response.status_code, 404)
        item.refresh_from_db()
        self.assertEqual(item.meaning, "owner only")

    def test_logout_flushes_server_session_and_rotates_csrf_old_cookie_cannot_restore(self):
        login = self.login()
        old_key = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        old_csrf_cookie = self.client.cookies[settings.CSRF_COOKIE_NAME].value
        csrf_token = login.data["data"]["csrf_token"]
        response = self.client.post(self.logout_url, {}, format="json", HTTP_X_CSRFTOKEN=csrf_token)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["data"]["authenticated"])
        self.assertNotEqual(self.client.cookies[settings.CSRF_COOKIE_NAME].value, old_csrf_cookie)
        self.assertFalse(Session.objects.filter(session_key=old_key).exists())
        stale_client = APIClient(enforce_csrf_checks=True)
        stale_client.cookies[settings.SESSION_COOKIE_NAME] = old_key
        self.assertFalse(stale_client.get(self.session_url).data["data"]["authenticated"])
        self.assertEqual(stale_client.get(self.me_url).status_code, 401)

    def test_old_in_flight_session_store_cannot_recreate_logged_out_session(self):
        login = self.login()
        old_key = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        in_flight = SessionStore(session_key=old_key)
        self.assertIn(APP_SESSION_KEY, in_flight)
        response = self.client.post(
            self.logout_url, {}, format="json", HTTP_X_CSRFTOKEN=login.data["data"]["csrf_token"]
        )
        self.assertEqual(response.status_code, 200)
        in_flight["activity"] = "late request"
        with self.assertRaises(UpdateError):
            in_flight.save()
        self.assertFalse(Session.objects.filter(session_key=old_key).exists())

    def test_unmarked_django_admin_session_is_not_accepted_or_destroyed(self):
        self.client.force_login(self.user)
        old_key = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        self.assertNotIn(APP_SESSION_KEY, self.client.session)
        self.assertFalse(self.client.get(self.session_url).data["data"]["authenticated"])
        self.assertEqual(self.client.get(self.me_url).status_code, 401)
        token = self.bootstrap()
        response = self.client.post(self.logout_url, {}, format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Session.objects.filter(session_key=old_key).exists())

    def test_existing_bearer_contract_works_without_csrf_and_takes_precedence(self):
        jwt_login = self.client.post(
            reverse("accounts:login"),
            {"email": self.user.email, "password": self.password},
            format="json",
        )
        self.assertEqual(jwt_login.status_code, 200)
        self.assertNotIn(settings.SESSION_COOKIE_NAME, jwt_login.cookies)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_login.data['access']}")
        self.assertEqual(
            self.client.patch(self.me_url, {"first_name": "JWT"}, format="json").status_code, 200
        )
        self.client.credentials()
        self.assertEqual(self.login().status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid")
        self.assertEqual(self.client.get(self.me_url).status_code, 401)

    @override_settings(SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True)
    def test_https_cookie_flags_are_secure_http_only_same_site_lax(self):
        token = self.bootstrap(secure=True)
        response = self.client.post(
            self.login_url,
            {"email": self.user.email, "password": self.password, "remember_me": True},
            format="json",
            secure=True,
            HTTP_ORIGIN="https://testserver",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 200)
        for name in (settings.SESSION_COOKIE_NAME, settings.CSRF_COOKIE_NAME):
            self.assertTrue(response.cookies[name]["secure"])
            self.assertTrue(response.cookies[name]["httponly"])
            self.assertEqual(response.cookies[name]["samesite"], "Lax")
