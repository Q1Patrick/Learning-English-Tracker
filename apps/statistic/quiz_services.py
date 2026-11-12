"""Quiz metrics count every attempt; the chart covers thirty local calendar days."""

from datetime import datetime, time, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Avg, Count, Max, Sum
from django.db.models.functions import TruncDate

from apps.quizzes.models import QuizAttempt

PROGRESS_DAYS = 30


def _average(value):
    if value is None:
        return None
    return float(Decimal(str(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def build_quiz_statistics(user, *, today, user_timezone):
    """Return all-time totals plus a zero-filled, timezone-aware daily series.

    Aggregate attempts directly so deleting/inactivating source quizzes cannot
    erase historical metrics. Three queries are used regardless of chart length.
    """
    attempts = QuizAttempt.objects.filter(user=user)
    totals = attempts.aggregate(
        total_completed=Count("id"),
        average_score=Avg("score"),
        best_score=Max("score"),
        total_correct_answers=Sum("correct_answers"),
    )
    recent_score = attempts.order_by("-completed_at", "-id").values_list("score", flat=True).first()
    first_date = today - timedelta(days=PROGRESS_DAYS - 1)
    start = datetime.combine(first_date, time.min, tzinfo=user_timezone).astimezone(timezone.utc)
    end = datetime.combine(today + timedelta(days=1), time.min, tzinfo=user_timezone).astimezone(
        timezone.utc
    )
    daily_rows = (
        attempts.filter(completed_at__gte=start, completed_at__lt=end)
        .annotate(local_date=TruncDate("completed_at", tzinfo=user_timezone))
        .values("local_date")
        .annotate(total_completed=Count("id"), average_score=Avg("score"))
        .order_by("local_date")
    )
    daily = {row["local_date"]: row for row in daily_rows}
    progress = []
    for offset in range(PROGRESS_DAYS):
        day = first_date + timedelta(days=offset)
        values = daily.get(day, {})
        progress.append(
            {
                "date": day,
                "total_completed": values.get("total_completed", 0),
                "average_score": _average(values.get("average_score")),
            }
        )
    return {
        "total_completed": totals["total_completed"],
        "average_score": _average(totals["average_score"]),
        "best_score": totals["best_score"],
        "recent_score": recent_score,
        "total_correct_answers": totals["total_correct_answers"] or 0,
        "progress_over_time": progress,
    }
