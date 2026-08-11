from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated

from .models import DailyGoal
from .serializers import DailyGoalSerializer


class DailyGoalListCreateView(ListCreateAPIView):
    serializer_class = DailyGoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DailyGoal.objects.filter(
            user=self.request.user
        )

    def perform_create(self, serializer):
        try:
            serializer.save(
                user=self.request.user
            )
        except IntegrityError:
            raise serializers.ValidationError(
                {
                    "target_date":
                        "You already have a goal for this date."
                }
            )


class DailyGoalDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = DailyGoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DailyGoal.objects.filter(
            user=self.request.user
        )