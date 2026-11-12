from django.conf import settings
from rest_framework.throttling import UserRateThrottle


class AIFeedbackThrottle(UserRateThrottle):
    scope = "ai_feedback"

    def get_rate(self):
        return settings.AI_FEEDBACK_THROTTLE_RATE
