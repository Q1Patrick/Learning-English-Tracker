from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import DashboardStatisticsSerializer
from .services import build_dashboard_statistics


class DashboardStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        statistics = build_dashboard_statistics(
            request.user
        )

        serializer = DashboardStatisticsSerializer(
            statistics
        )

        return Response(
            {
                "success": True,
                "data": serializer.data,
            }
        )