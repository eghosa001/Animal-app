"""MFA boundaries are mandatory for every privileged Admin and review action."""
import uuid
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.utils import timezone
from django_otp.oath import totp
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from modules.accounts.staff_auth_test_utils import verify_staff_test_session
from modules.media.models import MediaAsset

from .models import User


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class StaffMfaSecurityTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(
            email="security-moderator@example.com",
            password="LongStaffPassword!2026",
            display_name="Staff Moderator",
            is_staff=True,
            email_verified_at=timezone.now(),
        )
        self.staff.user_permissions.add(Permission.objects.get(
            content_type__app_label="accounts", codename="review_sellerprofile"
        ))
        self.staff.user_permissions.add(Permission.objects.get(
            content_type__app_label="accounts", codename="view_sellerprofile"
        ))
        self.staff.user_permissions.add(Permission.objects.get(
            content_type__app_label="animal_media", codename="review_mediaasset"
        ))

    def test_password_only_staff_session_denied_admin(self):
        self.client.force_login(self.staff)
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_verified_device_allows_admin_and_revocation_closes_it(self):
        device = verify_staff_test_session(self.client, self.staff)
        self.assertEqual(self.client.get("/admin/").status_code, 200)
        self.assertEqual(self.client.get("/admin/accounts/sellerprofile/").status_code, 200)

        device.confirmed = False
        device.save(update_fields=["confirmed"])
        denied = self.client.get("/admin/")
        self.assertEqual(denied.status_code, 302)

    def test_staff_app_login_and_old_jwt_refresh_are_rejected(self):
        attempt = self.client.post("/api/v1/auth/login", {
            "email": self.staff.email,
            "password": "LongStaffPassword!2026",
        }, format="json")
        self.assertEqual(attempt.status_code, 401)
        self.assertNotIn("access", attempt.data)

        # A JWT minted by an old version must not be accepted after this change.
        legacy = RefreshToken.for_user(self.staff)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {legacy.access_token}")
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 401)
        self.client.credentials()
        denied = self.client.post(
            "/api/v1/auth/refresh", {"refresh": str(legacy)}, format="json",
        )
        self.assertEqual(denied.status_code, 401)

    def test_customer_jwt_still_works_after_staff_hardening(self):
        buyer = User.objects.create_user(
            email="ordinary-buyer@example.com",
            password="BuyerPassword!2026",
            display_name="Buyer",
            email_verified_at=timezone.now(),
        )
        response = self.client.post("/api/v1/auth/login", {
            "email": buyer.email, "password": "BuyerPassword!2026"
        }, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 200)

    def test_staff_media_review_requires_verified_browser_session(self):
        target = f"/api/v1/media/{uuid.uuid4()}/review/"
        self.client.force_login(self.staff)
        no_otp = self.client.post(
            target, {"decision": "reject", "reason": "Blocked without an OTP verified staff session."},
            format="json",
        )
        self.assertEqual(no_otp.status_code, 403)
        verify_staff_test_session(self.client, self.staff)
        with_otp = self.client.post(
            target, {"decision": "reject", "reason": "Invalid media record under a real staff session."},
            format="json",
        )
        self.assertEqual(with_otp.status_code, 404)

        self.client.force_authenticate(user=None)
        old_token = RefreshToken.for_user(self.staff)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {old_token.access_token}")
        via_jwt = self.client.post(
            target, {"decision": "reject", "reason": "Bearer tokens cannot authorize staff."},
            format="json",
        )
        self.assertEqual(via_jwt.status_code, 403)

    def test_staff_evidence_access_requires_otp_not_legacy_jwt(self):
        seller = User.objects.create_user(
            email="mfa-evidence-seller@example.com",
            password="SellerPassword!2026",
            display_name="Seller",
            email_verified_at=timezone.now(),
        )
        # No file reads should occur for unverified staff, so storage is not needed.
        asset = MediaAsset.objects.create(
            owner=seller,
            kind=MediaAsset.Kind.SELLER_EVIDENCE,
            evidence_type=MediaAsset.EvidenceType.IDENTITY,
            storage_key="seller-evidence/test-placeholder.jpg",
            size_bytes=32, width=3, height=3, sha256="a" * 64,
        )
        endpoint = f"/api/v1/media/{asset.pk}/file/"
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(endpoint).status_code, 404)
        self.client.logout()

        legacy = RefreshToken.for_user(self.staff)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {legacy.access_token}")
        self.assertEqual(self.client.get(endpoint).status_code, 401)

    def test_otp_token_cannot_be_replayed_on_same_device(self):
        device = TOTPDevice.objects.create(user=self.staff, name="Primary", confirmed=True)
        code = str(totp(device.bin_key, step=device.step, t0=device.t0, digits=device.digits)).zfill(6)
        self.assertTrue(device.verify_token(code))
        self.assertFalse(device.verify_token(code))

    def test_bootstrap_command_requires_private_tty(self):
        with patch("sys.stdin.isatty", return_value=False):
            with self.assertRaisesMessage(CommandError, "private interactive TTY"):
                call_command("bootstrap_staff_totp", email=self.staff.email)

    def test_bootstrap_command_refuses_second_confirmed_device(self):
        TOTPDevice.objects.create(user=self.staff, confirmed=True, name="Primary")
        with patch("sys.stdin.isatty", return_value=True), patch("sys.stdout.isatty", return_value=True):
            with self.assertRaisesMessage(CommandError, "already exists"):
                call_command("bootstrap_staff_totp", email=self.staff.email)
