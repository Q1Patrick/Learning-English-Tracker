from rest_framework import serializers


class ActivityBreakdownSerializer(serializers.Serializer):
    activity_type = serializers.CharField()
    minutes = serializers.IntegerField()
    sessions = serializers.IntegerField()


class DashboardStatisticsSerializer(serializers.Serializer):
    date = serializers.DateField()
    timezone = serializers.CharField()

    target_minutes = serializers.IntegerField()
    target_source = serializers.CharField()

    studied_minutes = serializers.IntegerField()
    remaining_minutes = serializers.IntegerField()
    progress_percent = serializers.FloatField()

    sessions_count = serializers.IntegerField()
    week_minutes = serializers.IntegerField()

    activity_breakdown = ActivityBreakdownSerializer(
        many=True
    )