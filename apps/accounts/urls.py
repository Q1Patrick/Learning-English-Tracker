from django.urls import path
# Add login with JWT
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from .views import CurrentUserView, LoginView, RegisterView
app_name = "accounts"


urlpatterns = [
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("register/",RegisterView.as_view(), name="register",),
    path("token/verify/",TokenVerifyView.as_view(),name="token-verify",),
    path("me/",CurrentUserView.as_view(),name="current-user",),
    
]