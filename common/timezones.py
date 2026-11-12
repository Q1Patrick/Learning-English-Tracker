"""One timezone policy for dashboard totals and date filters."""

import logging
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ObjectDoesNotExist

DEFAULT_TIMEZONE = "Asia/Ho_Chi_Minh"
logger = logging.getLogger(__name__)


def get_user_timezone(user):
    try:
        name = user.profile.timezone or DEFAULT_TIMEZONE
    except ObjectDoesNotExist:
        name = DEFAULT_TIMEZONE
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        logger.warning("Invalid stored timezone; using default user_id=%s", user.pk)
        return ZoneInfo(DEFAULT_TIMEZONE)
