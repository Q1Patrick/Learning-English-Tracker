from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Sum
from django.utils import timezone

from apps.goals.models import DailyGoal
from apps.learning.models import StudySession


DEFAULT_TIMEZONE = "Asia/Ho_Chi_Minh"


def get_user_timezone(user):
    timezone_name = DEFAULT_TIMEZONE

    try:
        profile_timezone = getattr(
            user.profile,
            "timezone",
            None,
        )

        if profile_timezone:
            timezone_name = profile_timezone

    except ObjectDoesNotExist:
        pass

    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return ZoneInfo(DEFAULT_TIMEZONE)


def get_day_range(target_date, user_timezone):
    """
    Return the start and end datetime for one local day.
    """
    start = datetime.combine(
        target_date,
        time.min,
        tzinfo=user_timezone,
    )

    end = start + timedelta(days=1)

    return start, end


def build_dashboard_statistics(user):
    user_timezone = get_user_timezone(user)

    now = timezone.now().astimezone(user_timezone)
    today = now.date()

    today_start, tomorrow_start = get_day_range(
        today,
        user_timezone,
    )

    # -------------------------
    # Daily goal
    # -------------------------

    goal = DailyGoal.objects.filter(
        user=user,
        target_date=today,
    ).first()

    if goal:
        target_minutes = goal.target_minutes
        target_source = "daily_goal"
    else:
        try:
            target_minutes = user.profile.daily_target_minutes
            target_source = "profile_default"
        except ObjectDoesNotExist:
            target_minutes = 30
            target_source = "system_default"

    # -------------------------
    # Today's StudySessions
    # -------------------------

    today_sessions = StudySession.objects.filter(
        user=user,
        studied_at__gte=today_start,
        studied_at__lt=tomorrow_start,
    )

    today_aggregate = today_sessions.aggregate(
        total_minutes=Sum("duration_minutes"),
        sessions_count=Count("id"),
    )

    studied_minutes = (
        today_aggregate["total_minutes"] or 0
    )

    sessions_count = (
        today_aggregate["sessions_count"] or 0
    )

    # -------------------------
    # Progress
    # -------------------------

    remaining_minutes = max(
        target_minutes - studied_minutes,
        0,
    )

    if target_minutes > 0:
        progress_percent = round(
            studied_minutes / target_minutes * 100,
            1,
        )
    else:
        progress_percent = 0

    # Don't display progress above 100%
    progress_percent = min(
        progress_percent,
        100,
    )

    # -------------------------
    # Activity breakdown
    # -------------------------

    activity_breakdown = list(
        today_sessions
        .values("activity_type")
        .annotate(
            minutes=Sum("duration_minutes"),
            sessions=Count("id"),
        )
        .order_by("activity_type")
    )

    # -------------------------
    # This week's statistics
    # Monday -> today
    # -------------------------

    week_start_date = today - timedelta(
        days=today.weekday()
    )

    week_start, _ = get_day_range(
        week_start_date,
        user_timezone,
    )

    week_sessions = StudySession.objects.filter(
        user=user,
        studied_at__gte=week_start,
        studied_at__lt=tomorrow_start,
    )

    week_minutes = (
        week_sessions.aggregate(
            total=Sum("duration_minutes")
        )["total"]
        or 0
    )

    return {
        "date": today,
        "timezone": str(user_timezone),

        "target_minutes": target_minutes,
        "target_source": target_source,

        "studied_minutes": studied_minutes,
        "remaining_minutes": remaining_minutes,
        "progress_percent": progress_percent,

        "sessions_count": sessions_count,
        "week_minutes": week_minutes,

        "activity_breakdown": activity_breakdown,
    }