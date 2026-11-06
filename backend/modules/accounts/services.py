"""Verification codes: only SHA-256 digests are persisted."""
import hashlib
import hmac
import logging
import smtplib
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from django.core.mail import send_mail
from .models import (
    AccountSecurityEvent, EmailVerificationChallenge, PasswordResetChallenge, User,
)

logger = logging.getLogger(__name__)


def issue_email_verification(user):
    now = timezone.now()
    EmailVerificationChallenge.objects.filter(
        user=user, used_at__isnull=True
    ).update(used_at=now)
    raw = secrets.token_urlsafe(32)
    EmailVerificationChallenge.objects.create(
        user=user,
        token_hash=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        expires_at=now + timedelta(hours=24),
    )
    send_mail(
        "Verify your Anima account",
        "Verification token: " + raw + "\n\nExpires in 24 hours. Do not share this code.",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def redeem_email_verification(user, token):
    now = timezone.now()
    if user.email_verified_at:
        return False
    challenge = EmailVerificationChallenge.objects.filter(
        user=user,
        used_at__isnull=True,
        expires_at__gt=now,
    ).order_by("-created_at").first()
    if not challenge or not hmac.compare_digest(
        challenge.token_hash, hashlib.sha256(token.encode("utf-8")).hexdigest()
    ):
        return False
    challenge.used_at = now
    challenge.save(update_fields=["used_at"])
    user.email_verified_at = now
    user.save(update_fields=["email_verified_at"])
    EmailVerificationChallenge.objects.filter(user=user, used_at__isnull=True).update(used_at=now)
    return True


# Email-based recovery limits are enforced per account in PostgreSQL even when
# a client changes its IP address. Additional per-IP API throttles live in views.
RESET_EXPIRES_MINUTES = 20
RESET_COOLDOWN_MINUTES = 10
RESET_MAX_PER_HOUR = 3
VERIFY_COOLDOWN_MINUTES = 10
VERIFY_MAX_PER_HOUR = 3
INVALID_TOKEN_MESSAGE = "Invalid or expired recovery code"


def _digest(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _may_issue(queryset, *, now, cooldown_minutes, max_hourly):
    latest = queryset.order_by("-created_at").first()
    if latest is not None and latest.created_at > now - timedelta(minutes=cooldown_minutes):
        return False
    if queryset.filter(created_at__gte=now - timedelta(hours=1)).count() >= max_hourly:
        return False
    return True


def request_password_reset(email):
    """Always return without revealing account existence; only active users receive mail."""
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user is None:
        return
    now = timezone.now()
    try:
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user.pk)
            if not user.is_active:
                return
            challenges = PasswordResetChallenge.objects.filter(user=user)
            if not _may_issue(
                challenges, now=now, cooldown_minutes=RESET_COOLDOWN_MINUTES,
                max_hourly=RESET_MAX_PER_HOUR,
            ):
                return
            raw = secrets.token_urlsafe(32)
            challenges.filter(used_at__isnull=True).update(used_at=now)
            PasswordResetChallenge.objects.create(
                user=user, token_hash=_digest(raw),
                expires_at=now + timedelta(minutes=RESET_EXPIRES_MINUTES),
            )
            AccountSecurityEvent.objects.create(
                user=user, event=AccountSecurityEvent.Event.PASSWORD_RESET_ISSUED
            )
            # Unlike a raw password reset URL, the code cannot be replayed after use.
            # No URL to a non-existent production domain is placed in the email.
            send_mail(
                "Anima password recovery",
                "Your Anima password recovery code: " + raw +
                "\n\nExpires in 20 minutes. If you did not request this, ignore this email.",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
    
    except (OSError, smtplib.SMTPException) as exc:
        # A traceback may contain recipient addresses or SMTP payloads.
        # Log only the exception class, never tokens or account identifiers.
        logger.error("Anima password recovery mail failed (%s)", type(exc).__name__)
        return

@transaction.atomic
def redeem_password_reset(*, email, token, new_password):
    """Validate and consume a code once, change password and invalidate all JWT sessions."""
    now = timezone.now()
    user = User.objects.select_for_update().filter(email__iexact=email, is_active=True).first()
    if user is None:
        raise ValidationError({"token": [INVALID_TOKEN_MESSAGE]})
    challenge = PasswordResetChallenge.objects.select_for_update().filter(
        user=user, used_at__isnull=True, expires_at__gt=now
    ).order_by("-created_at").first()
    if challenge is None or not hmac.compare_digest(
        challenge.token_hash, _digest(token)
    ):
        raise ValidationError({"token": [INVALID_TOKEN_MESSAGE]})
    if user.check_password(new_password):
        raise ValidationError({"new_password": ["Choose a different password"]})
    try:
        validate_password(new_password, user)
    except DjangoValidationError as exc:
        raise ValidationError({"new_password": exc.messages}) from exc

    user.set_password(new_password)
    user.save(update_fields=["password"])
    PasswordResetChallenge.objects.filter(
        user=user, used_at__isnull=True
    ).update(used_at=now)
    # SimpleJWT CHECK_REVOKE_TOKEN invalidates old access and refresh claims.
    # Also blacklist any outstanding refresh tokens to prevent resurrection.
    for issued in OutstandingToken.objects.filter(user=user, expires_at__gt=now):
        BlacklistedToken.objects.get_or_create(token=issued)
    AccountSecurityEvent.objects.create(
        user=user, event=AccountSecurityEvent.Event.PASSWORD_RESET_COMPLETED
    )
    return user


def resend_email_verification(email):
    """Non-enumerating and DB rate-controlled verification resend."""
    user = User.objects.filter(
        email__iexact=email, is_active=True, email_verified_at__isnull=True
    ).first()
    if user is None:
        return
    now = timezone.now()
    try:
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user.pk)
            if not user.is_active or user.is_email_verified:
                return
            history = EmailVerificationChallenge.objects.filter(user=user)
            if not _may_issue(
                history, now=now, cooldown_minutes=VERIFY_COOLDOWN_MINUTES,
                max_hourly=VERIFY_MAX_PER_HOUR,
            ):
                return
            issue_email_verification(user)
            AccountSecurityEvent.objects.create(
                user=user, event=AccountSecurityEvent.Event.VERIFICATION_RESENT
            )
    except (OSError, smtplib.SMTPException) as exc:
        logger.error("Anima verification mail failed (%s)", type(exc).__name__)
        return
