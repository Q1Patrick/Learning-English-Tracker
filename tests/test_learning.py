"""Study session API permissions and input boundaries."""

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.learning.models import StudySession

User = get_user_model()


class StudySessionAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="sessions@example.com")
        self.other = User.objects.create_user(email="other-sessions@example.com")
        self.client.force_authenticate(self.user)
        self.url = "/api/v1/study-sessions/"
        self.session = StudySession.objects.create(
            user=self.user, activity_type="reading", duration_minutes=20
        )
        self.other_session = StudySession.objects.create(
            user=self.other, activity_type="speaking", duration_minutes=30
        )

    def test_list_only_contains_owned_sessions(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(self.session.pk))

    def test_other_users_session_is_not_readable_or_editable(self):
        url = f"{self.url}{self.other_session.pk}/"
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(
            self.client.patch(url, {"duration_minutes": 99}, format="json").status_code,
            404,
        )
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.other_session.refresh_from_db()
        self.assertEqual(self.other_session.duration_minutes, 30)

    def test_create_assigns_current_user(self):
        response = self.client.post(
            self.url,
            {"user": self.other.pk, "activity_type": "writing", "duration_minutes": 15},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(StudySession.objects.get(pk=response.data["id"]).user_id, self.user.pk)

    def test_invalid_duration_and_score_are_rejected(self):
        for extra in ({"duration_minutes": 0}, {"score": 101}):
            with self.subTest(extra=extra):
                data = {"activity_type": "reading", "duration_minutes": 10, **extra}
                response = self.client.post(self.url, data, format="json")
                self.assertEqual(response.status_code, 400)
        self.assertEqual(StudySession.objects.filter(user=self.user).count(), 1)

    def test_authentication_is_required(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(self.url).status_code, 401)
