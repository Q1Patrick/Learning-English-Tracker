"""Bounded web sessions, kept separate from the existing JWT contract."""

from datetime import datetime, timezone

from django.conf import settings
from django.contrib.auth import get_user, login, logout
from django.utils import timezone as django_timezone
from rest_framework.authentication import CSRFCheck, SessionAuthentication
from rest_framework.exceptions import PermissionDenied

APP_SESSION_KEY = "_let_app_session"


def _now():
    return int(django_timezone.now().timestamp())


def _policy(remember_me):
    if remember_me:
        return (
            settings.APP_SESSION_REMEMBER_ABSOLUTE_SECONDS,
            settings.APP_SESSION_REMEMBER_IDLE_SECONDS,
        )
    return settings.APP_SESSION_ABSOLUTE_SECONDS, settings.APP_SESSION_IDLE_SECONDS


def session_deadline(metadata):
    _, idle_seconds = _policy(metadata["remember_me"])
    return min(metadata["absolute_expires_at"], metadata["last_activity"] + idle_seconds)


def start_app_session(request, user, remember_me):
    login(request, user)
    # Django không đổi key khi cùng user đăng nhập lại; web flow luôn xoay key.
    request.session.cycle_key()
    now = _now()
    absolute_seconds, _ = _policy(remember_me)
    metadata = {
        "version": 1,
        "started_at": now,
        "absolute_expires_at": now + absolute_seconds,
        "last_activity": now,
        "remember_me": remember_me,
    }
    request.session[APP_SESSION_KEY] = metadata
    if remember_me:
        # Deadline tuyệt đối không trượt theo mỗi lần gửi request.
        request.session.set_expiry(
            datetime.fromtimestamp(metadata["absolute_expires_at"], timezone.utc)
        )
    else:
        request.session.set_expiry(0)
    return metadata


def resolve_app_session(request, *, touch=True):
    metadata = request.session.get(APP_SESSION_KEY)
    if metadata is None:
        # Cookie admin không tự trở thành phiên ứng dụng và không bị xóa.
        return None, None

    now = _now()
    valid = isinstance(metadata, dict) and type(metadata.get("remember_me")) is bool
    if valid:
        absolute_seconds, idle_seconds = _policy(metadata["remember_me"])
        valid = metadata.get("version") == 1 and all(
            type(metadata.get(key)) is int
            for key in ("started_at", "absolute_expires_at", "last_activity")
        )
    if valid:
        valid = (
            metadata["absolute_expires_at"] == metadata["started_at"] + absolute_seconds
            and metadata["started_at"] <= metadata["last_activity"] <= now
            and now < metadata["absolute_expires_at"]
            and now - metadata["last_activity"] < idle_seconds
        )
    # Đọc raw HttpRequest, tránh đệ quy DRF request.user trong authenticate().
    user = get_user(request) if valid else None
    if not valid or user is None or not user.is_authenticated or not user.is_active:
        logout(request)
        return None, None
    if touch:
        metadata = {**metadata, "last_activity": now}
        request.session[APP_SESSION_KEY] = metadata
        # DB SessionStore chỉ UPDATE key hiện có; request cũ không INSERT lại phiên
        # đã logout. SessionMiddleware chuyển UpdateError thành SessionInterrupted.
    return user, metadata


class AppSessionAuthentication(SessionAuthentication):
    def authenticate(self, request):
        raw_request = request._request
        user, metadata = resolve_app_session(raw_request, touch=False)
        if user is None:
            return None
        self.enforce_csrf(raw_request)
        # Chỉ request đã qua CSRF mới cập nhật idle activity.
        raw_request.session[APP_SESSION_KEY] = {**metadata, "last_activity": _now()}
        return user, None

    def enforce_csrf(self, request):
        check = CSRFCheck(lambda request: None)
        check.process_request(request)
        if check.process_view(request, None, (), {}):
            raise PermissionDenied("CSRF verification failed.", code="csrf_failed")
