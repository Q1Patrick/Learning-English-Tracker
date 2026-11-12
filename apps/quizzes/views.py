from django.db.models import Count, Prefetch
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Choice, Question, Quiz, QuizAttempt
from .serializers import (
    QuizAttemptDetailSerializer,
    QuizAttemptListSerializer,
    QuizDetailSerializer,
    QuizListSerializer,
    QuizSubmissionSerializer,
)
from .services import parse_idempotency_key, submit_quiz


class QuizListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = QuizListSerializer

    def get_queryset(self):
        return (
            Quiz.objects.filter(is_active=True)
            .annotate(question_count=Count("questions"))
            .order_by("-created_at", "-id")
        )


class QuizDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = QuizDetailSerializer

    def get_queryset(self):
        questions = Question.objects.order_by("order", "id").prefetch_related(
            Prefetch("choices", queryset=Choice.objects.order_by("order", "id"))
        )
        return Quiz.objects.filter(is_active=True).prefetch_related(
            Prefetch("questions", queryset=questions)
        )

    def retrieve(self, request, *args, **kwargs):
        return Response({"success": True, "data": self.get_serializer(self.get_object()).data})


class QuizSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        serializer = QuizSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = parse_idempotency_key(request.headers.get("Idempotency-Key"))
        attempt, created = submit_quiz(
            user=request.user,
            quiz_id=pk,
            answers=serializer.validated_data["answers"],
            idempotency_key=key,
        )
        return Response(
            {"success": True, "data": QuizAttemptDetailSerializer(attempt).data},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class QuizAttemptListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = QuizAttemptListSerializer

    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user)


class QuizAttemptDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = QuizAttemptDetailSerializer

    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user).prefetch_related("answers")

    def retrieve(self, request, *args, **kwargs):
        return Response({"success": True, "data": self.get_serializer(self.get_object()).data})
