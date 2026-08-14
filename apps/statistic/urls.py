from django.urls import path

from .views import DashboardStatisticsView

app_name = "statistic"


urlpatterns = [
    path("dashboard/",DashboardStatisticsView.as_view(),name="dashboard",),
]