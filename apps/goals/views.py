from rest_framework.filters import SearchFilter
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated

from common.filters import filter_dates

from .models import DailyGoal
from .serializers import DailyGoalSerializer


class DailyGoalListCreateView(ListCreateAPIView):
    serializer_class = DailyGoalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ["notes"]

    def get_queryset(self):
        return filter_dates(
            DailyGoal.objects.filter(user=self.request.user), self.request, "target_date"
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DailyGoalDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = DailyGoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DailyGoal.objects.filter(user=self.request.user)
