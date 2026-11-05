"""Verification codes: only SHA-256 digests are persisted."""
import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailVerificationChallenge


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
        return True
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
