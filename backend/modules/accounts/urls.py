"""Auth endpoints use JWT refresh rotation and a blacklist."""
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    LogoutView, MeView, RegisterView, ResendVerificationView,
    SellerApplicationView, VerifyEmailView,
)

urlpatterns = [
    path("register", RegisterView.as_view(), name="register"),
    path("login", TokenObtainPairView.as_view(), name="login"),
    path("refresh", TokenRefreshView.as_view(), name="refresh"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("me", MeView.as_view(), name="me"),
    path("verify-email", VerifyEmailView.as_view(), name="verify-email"),
    path("resend-verification", ResendVerificationView.as_view(), name="resend-verification"),
    path("seller", SellerApplicationView.as_view(), name="seller-application"),
]
