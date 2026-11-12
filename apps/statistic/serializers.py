from rest_framework import serializers


class ActivityBreakdownSerializer(serializers.Serializer):
    activity_type = serializers.CharField()
    minutes = serializers.IntegerField()
    sessions = serializers.IntegerField()


class QuizProgressDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    total_completed = serializers.IntegerField()
    average_score = serializers.FloatField(allow_null=True)


class QuizStatisticsSerializer(serializers.Serializer):
    total_completed = serializers.IntegerField()
    average_score = serializers.FloatField(allow_null=True)
    best_score = serializers.IntegerField(allow_null=True)
    recent_score = serializers.IntegerField(allow_null=True)
    total_correct_answers = serializers.IntegerField()
    progress_over_time = QuizProgressDaySerializer(many=True)


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

    activity_breakdown = ActivityBreakdownSerializer(many=True)
    quiz_statistics = QuizStatisticsSerializer()
