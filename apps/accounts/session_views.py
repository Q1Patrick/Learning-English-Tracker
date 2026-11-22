"""CSRF-protected session endpoints for the browser application."""

from django.contrib.auth import logout
from django.http import JsonResponse
from django.middleware.csrf import get_token, rotate_token
from django.utils import timezone
from django.utils.cache import add_never_cache_headers
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .session_auth import APP_SESSION_KEY, resolve_app_session, session_deadline, start_app_session
from .session_serializers import SessionLoginSerializer


def csrf_failure(request, reason=""):
    # Không trả reason nội bộ, token hay request body trong lỗi CSRF.
    request_id = getattr(request, "request_id", None)
    response = JsonResponse(
        {
            "success": False,
            "error": {
                "code": "csrf_failed",
                "message": "CSRF verification failed.",
                "details": None,
            },
            "request_id": request_id,
        },
        status=403,
    )
    add_never_cache_headers(response)
    return response


def session_response(request, user=None, metadata=None):
    deadline = session_deadline(metadata) if metadata else None
    return Response(
        {
            "success": True,
            "data": {
                "authenticated": user is not None,
                "user": None
                if user is None
                else {
                    "id": str(user.pk),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_email_verified": user.is_email_verified,
                },
                "csrf_token": get_token(request),
                "expires_at": deadline,
                "expires_in": max(0, deadline - int(timezone.now().timestamp()))
                if deadline is not None
                else None,
                "absolute_expires_at": metadata["absolute_expires_at"] if metadata else None,
            },
        }
    )


@method_decorator(never_cache, name="dispatch")
class SessionView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        # Bootstrap/focus check không kéo dài idle timeout khi người dùng không hoạt động.
        user, metadata = resolve_app_session(request._request, touch=False)
        return session_response(request._request, user, metadata)


@method_decorator(csrf_protect, name="dispatch")
class SessionLoginView(SessionView):
    # Không kế thừa GET bootstrap tại URL login/logout.
    http_method_names = ["post", "options"]

    def post(self, request):
        raw_request = request._request
        serializer = SessionLoginSerializer(data=request.data, context={"request": raw_request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        metadata = start_app_session(raw_request, user, serializer.validated_data["remember_me"])
        return session_response(raw_request, user, metadata)


@method_decorator(csrf_protect, name="dispatch")
class SessionLogoutView(SessionView):
    http_method_names = ["post", "options"]

    def post(self, request):
        raw_request = request._request
        if APP_SESSION_KEY in raw_request.session:
            logout(raw_request)
        # Logout với cookie không có app marker không xóa phiên admin.
        # CSRF mới trong body giúp FE không cần đọc cookie HttpOnly.
        rotate_token(raw_request)
        return session_response(raw_request)
