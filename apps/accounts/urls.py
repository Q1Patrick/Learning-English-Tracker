from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

from .views import CurrentUserView, LoginView, RegisterView


app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/",TokenRefreshView.as_view(),name="token-refresh",),
    path("token/verify/",TokenVerifyView.as_view(),name="token-verify",),
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path("me/",CurrentUserView.as_view(),name="current-user",),
    
]
