"""Regression tests for recovery token secrecy, account enumeration and JWT revocation."""
from datetime import timedelta
from unittest.mock import patch

from django.core import mail
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from .models import (
    AccountSecurityEvent, EmailVerificationChallenge, PasswordResetChallenge, User,
)
from .services import issue_email_verification


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AccountRecoveryTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.email = "recovery@example.com"
        self.old_password = "InitialSafePassword!2026"
        self.new_password = "NewStrongPassword!2026"
        self.user = User.objects.create_user(
            email=self.email, password=self.old_password,
            display_name="Recovery Example", email_verified_at=timezone.now(),
        )
        self.request_url = "/api/v1/auth/password-reset/request"
        self.confirm_url = "/api/v1/auth/password-reset/confirm"

    def request_reset(self, email=None):
        return self.client.post(
            self.request_url, {"email": email or self.email}, format="json",
        )

    def emailed_code(self):
        return mail.outbox[-1].body.split("Your Anima password recovery code: ")[1].split("\n")[0]

    def confirm(self, token, *, password=None, email=None):
        return self.client.post(self.confirm_url, {
            "email": email or self.email,
            "token": token,
            "new_password": password or self.new_password,
        }, format="json")

    def test_unknown_and_known_email_share_generic_success_shape(self):
        missing = self.request_reset(email="missing@example.com")
        self.assertEqual(missing.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        disabled = User.objects.create_user(
            email="disabled@example.com", password="DisabledPass!2026",
            display_name="Disabled", is_active=False,
        )
        blocked = self.request_reset(email=disabled.email)
        self.assertEqual(blocked.status_code, 200)
        self.assertEqual(blocked.data, missing.data)
        self.assertEqual(len(mail.outbox), 0)
        known = self.request_reset()
        self.assertEqual(known.status_code, 200)
        self.assertEqual(known.data, missing.data)
        self.assertEqual(len(mail.outbox), 1)

    def test_code_is_random_hashed_and_email_contains_no_raw_password(self):
        self.request_reset()
        code = self.emailed_code()
        challenge = PasswordResetChallenge.objects.get(user=self.user)
        self.assertGreater(len(code), 40)
        self.assertEqual(len(challenge.token_hash), 64)
        self.assertNotEqual(challenge.token_hash, code)
        self.assertNotIn(self.old_password, mail.outbox[0].body)
        self.assertNotIn(self.new_password, mail.outbox[0].body)
        self.assertEqual(challenge.expires_at.minute, (challenge.created_at + timedelta(minutes=20)).minute)
        self.assertEqual(AccountSecurityEvent.objects.filter(
            user=self.user, event=AccountSecurityEvent.Event.PASSWORD_RESET_ISSUED
        ).count(), 1)

    def test_mail_transport_failure_returns_generic_response_without_token_row(self):
        with patch("modules.accounts.services.send_mail", side_effect=OSError("mail unavailable")):
            response = self.request_reset()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {"message": "If an active account exists, a recovery code will be sent."},
        )
        self.assertFalse(PasswordResetChallenge.objects.filter(user=self.user).exists())
        self.assertFalse(AccountSecurityEvent.objects.filter(user=self.user).exists())

    def test_repeated_requests_do_not_send_extra_mail_or_invalidate_first_code(self):
        self.request_reset()
        first = self.emailed_code()
        repeat = self.request_reset()
        self.assertEqual(repeat.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(PasswordResetChallenge.objects.filter(user=self.user).count(), 1)
        self.assertEqual(self.confirm(first).status_code, 200)

    def test_expired_invalid_and_replayed_codes_are_rejected(self):
        self.request_reset()
        code = self.emailed_code()
        invalid = self.confirm("wrong-code")
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(invalid.data["token"], ["Invalid or expired recovery code"])
        other = self.confirm(code, email="missing@example.com")
        self.assertEqual(other.status_code, 400)
        self.assertEqual(other.data, invalid.data)
        self.assertTrue(self.user.check_password(self.old_password))
        completed = self.confirm(code)
        self.assertEqual(completed.status_code, 200)
        self.assertTrue(completed.data["password_changed"])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.new_password))
        replay = self.confirm(code, password="AnotherVeryStrong!2026")
        self.assertEqual(replay.status_code, 400)
        self.assertEqual(replay.data["token"], invalid.data["token"])
        self.assertEqual(AccountSecurityEvent.objects.filter(
            user=self.user, event=AccountSecurityEvent.Event.PASSWORD_RESET_COMPLETED
        ).count(), 1)

        # The next distinct code must be rejected after its TTL.
        PasswordResetChallenge.objects.filter(user=self.user).update(
            created_at=timezone.now() - timedelta(hours=2)
        )
        self.request_reset()
        next_code = self.emailed_code()
        PasswordResetChallenge.objects.filter(
            user=self.user, used_at__isnull=True
        ).update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.confirm(next_code).status_code, 400)

    def test_weak_or_reused_password_does_not_consume_recovery_code(self):
        self.request_reset()
        code = self.emailed_code()
        weak = self.confirm(code, password="1234567890")
        self.assertEqual(weak.status_code, 400)
        self.assertIn("new_password", weak.data)
        same = self.confirm(code, password=self.old_password)
        self.assertEqual(same.status_code, 400)
        self.assertIn("new_password", same.data)
        self.assertIsNone(PasswordResetChallenge.objects.get(user=self.user).used_at)
        self.assertEqual(self.confirm(code).status_code, 200)

    def test_password_reset_revokes_old_access_and_refresh_sessions(self):
        login = self.client.post("/api/v1/auth/login", {
            "email": self.email, "password": self.old_password,
        }, format="json")
        self.assertEqual(login.status_code, 200)
        access, refresh = login.data["access"], login.data["refresh"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 200)
        self.client.credentials()
        self.request_reset()
        self.assertEqual(self.confirm(self.emailed_code()).status_code, 200)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 401)
        self.client.credentials()
        old_refresh = self.client.post(
            "/api/v1/auth/refresh", {"refresh": refresh}, format="json",
        )
        self.assertEqual(old_refresh.status_code, 401)
        old_login = self.client.post("/api/v1/auth/login", {
            "email": self.email, "password": self.old_password,
        }, format="json")
        self.assertEqual(old_login.status_code, 401)
        new_login = self.client.post("/api/v1/auth/login", {
            "email": self.email, "password": self.new_password,
        }, format="json")
        self.assertEqual(new_login.status_code, 200)
        self.assertTrue(BlacklistedToken.objects.filter(token__user=self.user).exists())
        self.assertTrue(OutstandingToken.objects.filter(user=self.user).exists())

    def test_resend_verification_has_cooldown_and_old_code_is_invalidated(self):
        self.user.email_verified_at = None
        self.user.save(update_fields=["email_verified_at"])
        issue_email_verification(self.user)
        first = mail.outbox[-1].body.split("Verification token: ")[1].split("\n")[0]
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(self.client.post(
            "/api/v1/auth/resend-verification", {"email": self.email}, format="json",
        ).status_code, 200)
        self.assertEqual(len(mail.outbox), 1)  # 10-minute account cooldown.

        EmailVerificationChallenge.objects.filter(user=self.user).update(
            created_at=timezone.now() - timedelta(minutes=12)
        )
        self.assertEqual(self.client.post(
            "/api/v1/auth/resend-verification", {"email": self.email}, format="json",
        ).status_code, 200)
        self.assertEqual(len(mail.outbox), 2)
        second = mail.outbox[-1].body.split("Verification token: ")[1].split("\n")[0]
        self.assertNotEqual(first, second)
        self.assertEqual(self.client.post(
            "/api/v1/auth/verify-email",
            {"email": self.email, "token": first}, format="json",
        ).status_code, 400)
        self.assertEqual(self.client.post(
            "/api/v1/auth/verify-email",
            {"email": self.email, "token": second}, format="json",
        ).status_code, 200)
        self.assertEqual(self.client.post(
            "/api/v1/auth/verify-email",
            {"email": self.email, "token": "not-a-valid-token"}, format="json",
        ).status_code, 400)

    def test_password_request_and_login_are_limited_per_ip(self):
        for _ in range(5):
            response = self.request_reset(email="unknown@example.com")
            self.assertEqual(response.status_code, 200)
        self.assertEqual(self.request_reset(email="unknown@example.com").status_code, 429)
        cache.clear()
        for _ in range(10):
            denied = self.client.post("/api/v1/auth/login", {
                "email": "missing@example.com", "password": "any-password",
            }, format="json")
            self.assertEqual(denied.status_code, 401)
        self.assertEqual(self.client.post("/api/v1/auth/login", {
            "email": "missing@example.com", "password": "any-password",
        }, format="json").status_code, 429)
