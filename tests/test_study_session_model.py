from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.learning.models import StudySession


User = get_user_model()


class StudySessionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="student@example.com",
            password="StrongPassword123!",
        )

    def test_create_study_session(self):
        session = StudySession.objects.create(
            user=self.user,
            activity_type=StudySession.ActivityType.SPEAKING,
            duration_minutes=30,
            score=80,
        )

        self.assertEqual(session.user, self.user)
        self.assertEqual(
            session.activity_type,
            StudySession.ActivityType.SPEAKING,
        )
        self.assertEqual(session.duration_minutes, 30)
        self.assertEqual(session.score, 80)

    def test_user_can_have_multiple_sessions(self):
        StudySession.objects.create(
            user=self.user,
            activity_type=StudySession.ActivityType.SPEAKING,
            duration_minutes=30,
        )

        StudySession.objects.create(
            user=self.user,
            activity_type=StudySession.ActivityType.LISTENING,
            duration_minutes=45,
        )

        self.assertEqual(
            self.user.study_sessions.count(),
            2,
        )

    def test_duration_cannot_be_zero(self):
        session = StudySession(
            user=self.user,
            activity_type=StudySession.ActivityType.READING,
            duration_minutes=0,
        )

        with self.assertRaises(ValidationError):
            session.full_clean()

    def test_score_cannot_exceed_100(self):
        session = StudySession(
            user=self.user,
            activity_type=StudySession.ActivityType.WRITING,
            duration_minutes=30,
            score=101,
        )

        with self.assertRaises(ValidationError):
            session.full_clean()

    def test_score_is_optional(self):
        session = StudySession.objects.create(
            user=self.user,
            activity_type=StudySession.ActivityType.VOCABULARY,
            duration_minutes=20,
        )

        self.assertIsNone(session.score)

    def test_delete_user_deletes_sessions(self):
        StudySession.objects.create(
            user=self.user,
            activity_type=StudySession.ActivityType.LISTENING,
            duration_minutes=30,
        )

        self.user.delete()

        self.assertEqual(
            StudySession.objects.count(),
            0,
        )