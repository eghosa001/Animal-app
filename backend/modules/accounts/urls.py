"""Auth endpoints use JWT refresh rotation and a blacklist."""
from django.urls import path

from .views import (
    LoginView, LogoutView, MeView, PasswordResetConfirmView,
    PasswordResetRequestView, RefreshView, RegisterView,
    ResendVerificationView, SellerApplicationView, VerifyEmailView,
)

urlpatterns = [
    path("register", RegisterView.as_view(), name="register"),
    path("login", LoginView.as_view(), name="login"),
    path("refresh", RefreshView.as_view(), name="refresh"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("me", MeView.as_view(), name="me"),
    path("verify-email", VerifyEmailView.as_view(), name="verify-email"),
    path("resend-verification", ResendVerificationView.as_view(), name="resend-verification"),
    path("password-reset/request", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset/confirm", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("seller", SellerApplicationView.as_view(), name="seller-application"),
]
