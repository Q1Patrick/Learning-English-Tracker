from rest_framework import serializers, status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AIFeedback
from .serializers import (
    AIFeedbackCreateSerializer,
    AIFeedbackHistorySerializer,
    AIFeedbackSerializer,
)
from .services import submit_feedback
from .throttles import AIFeedbackThrottle


class AIFeedbackCreateView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [AIFeedbackThrottle]

    def post(self, request):
        serializer = AIFeedbackCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = request.headers.get("Idempotency-Key")
        if key is not None:
            key = serializers.UUIDField().run_validation(key)
        feedback, created = submit_feedback(
            user=request.user,
            text=serializer.validated_data["text"],
            idempotency_key=key,
        )
        return Response(
            {"success": True, "data": AIFeedbackSerializer(feedback).data},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class AIFeedbackHistoryView(ListAPIView):
    serializer_class = AIFeedbackHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AIFeedback.objects.filter(user=self.request.user).order_by("-created_at", "-id")


class AIFeedbackDetailView(RetrieveAPIView):
    serializer_class = AIFeedbackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AIFeedback.objects.filter(user=self.request.user)
