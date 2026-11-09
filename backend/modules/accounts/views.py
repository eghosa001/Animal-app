"""Account flows and seller-application entry. Approval is staff-only."""
from django.db import IntegrityError, transaction
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import SellerProfile, User
from .serializers import (
    MeSerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer,
    RegisterSerializer, RevokeAllSessionsSerializer, SellerApplySerializer, SellerSerializer,
)
from .services import (
    issue_email_verification, redeem_email_verification, redeem_password_reset,
    request_password_reset, resend_email_verification, revoke_all_account_sessions,
)


class LoginView(TokenObtainPairView):
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth_login"


class RefreshView(TokenRefreshView):
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth_refresh"


class RegisterView(generics.CreateAPIView):
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth_register"
    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        issue_email_verification(user)
        return Response(MeSerializer(user).data, status=status.HTTP_201_CREATED)


class MeView(generics.RetrieveAPIView):
    serializer_class = MeSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class VerifyEmailView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth_verify"

    def post(self, request):
        email = str(request.data.get("email", "")).lower().strip()
        token = request.data.get("token", "")
        if not isinstance(token, str) or not token or len(token) > 256:
            raise ValidationError({"token": ["A verification token is required"]})
        with transaction.atomic():
            user = User.objects.select_for_update().filter(
                email=email, is_active=True
            ).first()
            if user is None or not redeem_email_verification(user, token):
                raise ValidationError({"token": ["Invalid or expired verification token"]})
        return Response({"verified": True})


class ResendVerificationView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth_resend"

    def post(self, request):
        email = str(request.data.get("email", "")).lower().strip()
        resend_email_verification(email)
        return Response({"message": "If this account needs verification, a message will be sent."})


class PasswordResetRequestView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth_password_request"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_password_reset(serializer.validated_data["email"])
        return Response({"message": "If an active account exists, a recovery code will be sent."})


class PasswordResetConfirmView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth_password_confirm"

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        redeem_password_reset(**serializer.validated_data)
        return Response({"password_changed": True})


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        token = request.data.get("refresh")
        if not token:
            raise ValidationError({"refresh": ["Refresh token is required"]})
        try:
            refresh = RefreshToken(token)
            # Never let an authenticated account revoke another account's token.
            if str(refresh.get("user_id", "")) != str(request.user.pk):
                raise ValidationError({"refresh": ["Token does not belong to this account"]})
            refresh.blacklist()
        except TokenError as exc:
            raise ValidationError({"refresh": ["Invalid refresh token"]}) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoutAllView(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth_logout_all"

    def post(self, request):
        serializer = RevokeAllSessionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        revoke_all_account_sessions(
            actor=request.user,
            current_password=serializer.validated_data["current_password"],
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class SellerApplicationView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        seller = getattr(request.user, "seller_profile", None)
        if seller is None:
            return Response({"status": "not_applied"})
        return Response(SellerSerializer(seller).data)

    def post(self, request):
        if not request.user.is_email_verified:
            raise PermissionDenied("Verify your email before applying as a seller")
        serializer = SellerApplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            seller = SellerProfile.objects.create(user=request.user, **serializer.validated_data)
        except IntegrityError as exc:
            raise ValidationError({"seller": ["Application already submitted"]}) from exc
        return Response(SellerSerializer(seller).data, status=status.HTTP_201_CREATED)
