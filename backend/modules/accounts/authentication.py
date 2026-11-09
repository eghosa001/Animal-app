"""Separate consumer JWT sessions from MFA-only staff sessions."""
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer, TokenRefreshSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


def require_staff_mfa(user):
    """Deny even superusers until a confirmed OTP device verified this session."""
    verified = getattr(user, "is_verified", None)
    if not (
        user.is_authenticated
        and user.is_active
        and user.is_staff
        and callable(verified)
        and verified()
    ):
        raise PermissionDenied("Staff authentication with a verified second factor is required")


class CustomerJWTAuthentication(JWTAuthentication):
    """No bearer token, old or new, authorizes staff actions or sensitive evidence."""

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if user.is_staff:
            raise AuthenticationFailed("Staff must use the MFA-protected admin session")
        return user


class CustomerTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        result = super().validate(attrs)
        if self.user.is_staff:
            raise AuthenticationFailed("Staff must sign in through the MFA-protected admin portal")
        return result


class CustomerTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        # A previously issued staff refresh token must never revive mobile access.
        token = RefreshToken(attrs["refresh"])
        owner_id = token.get("user_id")
        if owner_id is not None and User.objects.filter(pk=owner_id, is_staff=True).exists():
            raise AuthenticationFailed("Staff must sign in through the MFA-protected admin portal")
        return super().validate(attrs)
