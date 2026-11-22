from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .session_views import SessionLoginView, SessionLogoutView, SessionView
from .views import CurrentUserView, LoginView, RegisterView

app_name = "accounts"

urlpatterns = [
    path("session/", SessionView.as_view(), name="session"),
    path("session/login/", SessionLoginView.as_view(), name="session-login"),
    path("session/logout/", SessionLogoutView.as_view(), name="session-logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token-verify"),
    path("me/", CurrentUserView.as_view(), name="current-user"),
]
