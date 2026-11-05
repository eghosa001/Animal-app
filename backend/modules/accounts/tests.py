"""End-to-end API tests for registration, verification, JWT and seller review."""
from django.core import mail
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import SellerProfile, User


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AccountApiTests(APITestCase):
    def setUp(self):
        self.register_payload = {
            "email": "breeder@example.com",
            "display_name": "Example Breeder",
            "password": "ExampleSafePassword!72",
        }

    def test_registration_verification_and_login(self):
        registration = self.client.post("/api/v1/auth/register", self.register_payload, format="json")
        self.assertEqual(registration.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="breeder@example.com")
        self.assertFalse(user.is_email_verified)
        self.assertEqual(len(mail.outbox), 1)
        token = mail.outbox[0].body.split("Verification token: ")[1].split("\n")[0]
        verified = self.client.post("/api/v1/auth/verify-email", {
            "email": user.email, "token": token,
        }, format="json")
        self.assertEqual(verified.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        login = self.client.post("/api/v1/auth/login", {
            "email": user.email, "password": self.register_payload["password"],
        }, format="json")
        self.assertEqual(login.status_code, 200)
        self.assertIn("refresh", login.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        me = self.client.get("/api/v1/auth/me")
        self.assertEqual(me.status_code, 200)
        self.assertTrue(me.data["email_verified"])
        logout = self.client.post("/api/v1/auth/logout", {"refresh": login.data["refresh"]}, format="json")
        self.assertEqual(logout.status_code, 204)

    def test_seller_application_does_not_self_approve(self):
        self.client.post("/api/v1/auth/register", self.register_payload, format="json")
        login = self.client.post("/api/v1/auth/login", {
            "email": "breeder@example.com", "password": self.register_payload["password"],
        }, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        denied = self.client.post("/api/v1/auth/seller", {
            "business_name": "Animal Friends", "adult_attested": True,
        }, format="json")
        self.assertEqual(denied.status_code, 403)
        user = User.objects.get(email="breeder@example.com")
        user.email_verified_at = timezone.now()
        user.save(update_fields=["email_verified_at"])
        applied = self.client.post("/api/v1/auth/seller", {
            "business_name": "Animal Friends", "adult_attested": True,
        }, format="json")
        self.assertEqual(applied.status_code, 201)
        self.assertEqual(SellerProfile.objects.get(user=user).status, SellerProfile.Status.PENDING)
        duplicate = self.client.post("/api/v1/auth/seller", {
            "business_name": "Animal Friends 2", "adult_attested": True,
        }, format="json")
        self.assertEqual(duplicate.status_code, 400)

    def test_password_validation_rejects_weak_password(self):
        response = self.client.post("/api/v1/auth/register", {
            **self.register_payload, "password": "1234567890",
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.exists())
