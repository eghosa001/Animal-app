"""Session revocation regression tests against PostgreSQL and the real API."""
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import AccountSecurityEvent, User


class LogoutAllTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.password = "CorrectPassword!2026"
        self.user = User.objects.create_user(
            email="sessions-owner@example.com",
            password=self.password,
            display_name="Session Owner",
            email_verified_at=timezone.now(),
        )
        self.other = User.objects.create_user(
            email="sessions-other@example.com",
            password="OtherPassword!2026",
            display_name="Other User",
            email_verified_at=timezone.now(),
        )
        self.endpoint = "/api/v1/auth/logout-all"

    def _login(self, user, password):
        response = self.client.post("/api/v1/auth/login", {
            "email": user.email,
            "password": password,
        }, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        return response.data

    def test_logout_all_revokes_all_access_refresh_and_admin_cookie_hash(self):
        first = self._login(self.user, self.password)
        second = self._login(self.user, self.password)
        original_hash = self.user.password
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {first['access']}")
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 200)

        result = self.client.post(
            self.endpoint, {"current_password": self.password}, format="json",
        )
        self.assertEqual(result.status_code, 204)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.password))
        self.assertNotEqual(self.user.password, original_hash)

        # The access token used to revoke itself is no longer valid.
        for login in (first, second):
            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login['access']}")
            self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 401)
            self.client.credentials()
            self.assertEqual(self.client.post(
                "/api/v1/auth/refresh", {"refresh": login["refresh"]}, format="json",
            ).status_code, 401)

        self.assertEqual(AccountSecurityEvent.objects.filter(
            user=self.user, event=AccountSecurityEvent.Event.ALL_SESSIONS_REVOKED,
        ).count(), 1)
        self.assertEqual(self.user.security_events.count(), 1)

        # A new login with the exact same password succeeds after re-authentication.
        newly_signed_in = self._login(self.user, self.password)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {newly_signed_in['access']}"
        )
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 200)

    def test_wrong_password_keeps_all_sessions_valid_and_does_not_audit(self):
        login = self._login(self.user, self.password)
        original_hash = self.user.password
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login['access']}")
        denied = self.client.post(
            self.endpoint, {"current_password": "IncorrectPassword!000"},
            format="json",
        )
        self.assertEqual(denied.status_code, 400)
        self.assertIn("current_password", denied.data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.password, original_hash)
        self.assertEqual(AccountSecurityEvent.objects.count(), 0)
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 200)
        self.client.credentials()
        self.assertEqual(self.client.post(
            "/api/v1/auth/refresh", {"refresh": login["refresh"]},
            format="json",
        ).status_code, 200)

    def test_missing_password_and_unauthenticated_request_rejected(self):
        self.assertEqual(self.client.post(
            self.endpoint, {"current_password": self.password}, format="json",
        ).status_code, 401)
        login = self._login(self.user, self.password)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login['access']}")
        self.assertEqual(self.client.post(self.endpoint, {}, format="json").status_code, 400)
        self.assertEqual(AccountSecurityEvent.objects.count(), 0)

    def test_other_users_sessions_survive_logout_all(self):
        user1 = self._login(self.user, self.password)
        user2 = self._login(self.other, "OtherPassword!2026")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {user1['access']}")
        self.assertEqual(self.client.post(
            self.endpoint, {"current_password": self.password},
            format="json",
        ).status_code, 204)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {user2['access']}")
        me = self.client.get("/api/v1/auth/me")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data["email"], self.other.email)
        self.client.credentials()
        self.assertEqual(self.client.post(
            "/api/v1/auth/refresh", {"refresh": user2["refresh"]},
            format="json",
        ).status_code, 200)

    def test_single_logout_rejects_refresh_token_owned_by_other_account(self):
        user1 = self._login(self.user, self.password)
        user2 = self._login(self.other, "OtherPassword!2026")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {user1['access']}")
        result = self.client.post("/api/v1/auth/logout", {
            "refresh": user2["refresh"],
        }, format="json")
        self.assertEqual(result.status_code, 400)
        self.assertIn("refresh", result.data)
        self.client.credentials()
        self.assertEqual(self.client.post(
            "/api/v1/auth/refresh", {"refresh": user2["refresh"]},
            format="json",
        ).status_code, 200)

    def test_single_logout_still_accepts_account_owned_refresh(self):
        user1 = self._login(self.user, self.password)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {user1['access']}")
        self.assertEqual(self.client.post("/api/v1/auth/logout", {
            "refresh": user1["refresh"],
        }, format="json").status_code, 204)
        self.client.credentials()
        self.assertEqual(self.client.post(
            "/api/v1/auth/refresh", {"refresh": user1["refresh"]},
            format="json",
        ).status_code, 401)
