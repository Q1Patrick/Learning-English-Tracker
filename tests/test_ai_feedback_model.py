from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.ai_feedback.models import AIFeedback

User = get_user_model()


class AIFeedbackModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="ai-test@example.com",
            password="StrongPassword123!",
        )

    def test_create_ai_feedback(self):
        feedback = AIFeedback.objects.create(
            user=self.user,
            original_text="I go to school yesterday.",
        )

        self.assertEqual(
            feedback.user,
            self.user,
        )

        self.assertEqual(
            feedback.original_text,
            "I go to school yesterday.",
        )

        self.assertEqual(
            feedback.status,
            AIFeedback.Status.PENDING,
        )
