"""Private media security checks against the real Django API and Postgres in CI."""
import io
import tempfile
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APITestCase

from modules.accounts.models import SellerProfile, User
from modules.catalog.models import Species
from modules.listings.models import Animal, Listing

from .models import MediaAccessEvent, MediaAsset, MediaReviewEvent
from .storage import MediaStorageError, _local_path, backend_name, read_object


def photo_file(*, format="PNG", declared=None, size=(32, 24)):
    image = Image.new("RGB", size, color=(38, 126, 75))
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    payload = buffer.getvalue()
    return SimpleUploadedFile(
        "user-provided-untrusted-file.png", payload,
        content_type=declared or ("image/png" if format == "PNG" else "image/jpeg"),
    )


@override_settings(DEBUG=True, MEDIA_STORAGE_BACKEND="local")
class PrivateMediaApiTests(APITestCase):
    def setUp(self):
        # DRF's anonymous/user throttles use a shared cache across test cases.
        # Reset between cases to test object access, not unrelated rate-limit history.
        cache.clear()
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root_override = override_settings(PRIVATE_MEDIA_ROOT=self.tempdir.name)
        self.root_override.enable()
        self.addCleanup(self.root_override.disable)

        self.seller = User.objects.create_user(
            email="seller-media@example.com", password="LongStrong!2026",
            display_name="Seller", email_verified_at=timezone.now(),
        )
        self.buyer = User.objects.create_user(
            email="buyer-media@example.com", password="LongStrong!2026",
            display_name="Buyer", email_verified_at=timezone.now(),
        )
        self.reviewer = User.objects.create_user(
            email="media-moderator@example.com", password="LongStrong!2026",
            display_name="Media Reviewer", email_verified_at=timezone.now(), is_staff=True,
        )
        self.identity_reviewer = User.objects.create_user(
            email="verification-staff@example.com", password="LongStrong!2026",
            display_name="Identity Reviewer", email_verified_at=timezone.now(), is_staff=True,
        )
        self.reviewer.user_permissions.add(Permission.objects.get(
            content_type__app_label="animal_media", codename="review_mediaasset",
        ))
        self.identity_reviewer.user_permissions.add(Permission.objects.get(
            content_type__app_label="accounts", codename="review_sellerprofile",
        ))
        SellerProfile.objects.create(
            user=self.seller, business_name="Animal Supplier",
            adult_attested=True, status=SellerProfile.Status.PENDING,
        )
        self.species = Species.objects.create(
            name="Dogs", slug="dogs-media", category=Species.Category.COMPANION,
            trade_enabled=True,
        )
        animal = Animal.objects.create(owner=self.seller, species=self.species, name="Fido")
        self.listing = Listing.objects.create(
            animal=animal, seller=self.seller, title="Sample dog animal photo",
            description="Private photo upload test listing, not a live commercial animal.",
            price_minor=5000000, region="Lagos", status=Listing.Status.DRAFT,
        )
        self.client.force_authenticate(user=self.seller)

    def upload_photo(self, *, file=None, listing_id=None):
        return self.client.post(
            "/api/v1/media/listing-photos/",
            {"listing_id": str(listing_id or self.listing.pk), "file": file or photo_file()},
            format="multipart",
        )

    def upload_evidence(self, *, file=None, consent="true", evidence_type="identity"):
        return self.client.post(
            "/api/v1/media/seller-evidence/",
            {"file": file or photo_file(), "evidence_type": evidence_type, "consent": consent},
            format="multipart",
        )

    def test_photo_bytes_are_normalized_and_private_until_approved(self):
        response = self.upload_photo()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["state"], "pending")
        self.assertEqual(response.data["content_type"], "image/jpeg")
        self.assertNotIn("storage_key", response.data)
        self.assertNotIn("sha256", response.data)
        asset = MediaAsset.objects.get(pk=response.data["id"])
        self.assertEqual(asset.kind, MediaAsset.Kind.LISTING_PHOTO)
        self.assertEqual(asset.owner, self.seller)
        self.assertEqual(asset.listing, self.listing)
        self.assertTrue(asset.storage_key.startswith("listing-photos/"))
        content = read_object(kind=asset.kind, key=asset.storage_key)
        self.assertTrue(content.startswith(b"\xff\xd8"))
        with Image.open(io.BytesIO(content)) as image:
            self.assertEqual(image.format, "JPEG")
            self.assertFalse(bool(image.getexif()))

        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(response.data["file_url"]).status_code, 404)
        self.client.force_authenticate(user=self.buyer)
        self.assertEqual(self.client.get(response.data["file_url"]).status_code, 404)
        self.client.force_authenticate(user=self.seller)
        self.assertEqual(self.client.get(response.data["file_url"]).status_code, 200)
        self.assertEqual(MediaAccessEvent.objects.count(), 1)

    def test_photo_approval_visibility_and_seller_suspension(self):
        result = self.upload_photo()
        asset = MediaAsset.objects.get(pk=result.data["id"])
        self.client.force_authenticate(user=self.reviewer)
        approval = self.client.post(f"/api/v1/media/{asset.id}/review/", {
            "decision": "approve", "reason": "Image was inspected and matches platform content rules.",
        }, format="json")
        self.assertEqual(approval.status_code, 400)  # Seller still pending.
        self.assertEqual(MediaReviewEvent.objects.count(), 0)

        profile = self.seller.seller_profile
        profile.status = SellerProfile.Status.APPROVED
        profile.save(update_fields=["status"])
        approval = self.client.post(f"/api/v1/media/{asset.id}/review/", {
            "decision": "approve", "reason": "Animal photo reviewed manually; no policy violations identified.",
        }, format="json")
        self.assertEqual(approval.status_code, 200, approval.data)
        self.assertEqual(MediaReviewEvent.objects.count(), 1)
        again = self.client.post(f"/api/v1/media/{asset.id}/review/", {
            "decision": "approve", "reason": "This review should fail because the image was already approved.",
        }, format="json")
        self.assertEqual(again.status_code, 400)
        self.assertEqual(MediaReviewEvent.objects.count(), 1)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(f"/api/v1/media/{asset.id}/file/").status_code, 404)
        self.listing.status = Listing.Status.ACTIVE
        self.listing.save(update_fields=["status"])
        public = self.client.get(f"/api/v1/media/{asset.id}/file/")
        self.assertEqual(public.status_code, 200)
        self.assertEqual(public["Content-Type"], "image/jpeg")
        self.assertEqual(public["Cache-Control"], "private, no-store")
        self.assertEqual(MediaAccessEvent.objects.count(), 0)  # Anonymous access not logged as PII.

        profile.status = SellerProfile.Status.SUSPENDED
        profile.save(update_fields=["status"])
        self.assertEqual(self.client.get(f"/api/v1/media/{asset.id}/file/").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/listings/").data["count"], 0)

    def test_evidence_upload_requires_consent_and_is_never_public(self):
        self.assertEqual(self.upload_evidence(consent="false").status_code, 400)
        self.assertEqual(MediaAsset.objects.count(), 0)
        uploaded = self.upload_evidence()
        self.assertEqual(uploaded.status_code, 201, uploaded.data)
        self.assertEqual(uploaded.data["evidence_type"], "identity")
        self.assertEqual(uploaded.data["state"], "pending")
        self.assertNotIn("storage_key", uploaded.data)
        self.assertNotIn("bucket", uploaded.data)
        asset = MediaAsset.objects.get(pk=uploaded.data["id"])
        self.assertTrue(asset.storage_key.startswith("seller-evidence/"))
        uri = uploaded.data["file_url"]

        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(uri).status_code, 404)
        self.client.force_authenticate(user=self.buyer)
        self.assertEqual(self.client.get(uri).status_code, 404)
        self.client.force_authenticate(user=self.reviewer)
        self.assertEqual(self.client.get(uri).status_code, 404)  # Media reviewer != KYC reviewer.
        self.client.force_authenticate(user=self.identity_reviewer)
        allowed = self.client.get(uri)
        self.assertEqual(allowed.status_code, 200)
        self.assertIn("attachment;", allowed["Content-Disposition"])
        self.assertEqual(allowed["Cache-Control"], "private, no-store")
        self.assertEqual(MediaAccessEvent.objects.count(), 1)
        self.assertEqual(MediaAccessEvent.objects.first().purpose, "evidence_review")
        self.client.force_authenticate(user=self.seller)
        self.assertEqual(self.client.get(uri).status_code, 200)
        self.assertEqual(MediaAccessEvent.objects.count(), 2)

    def test_file_spoofing_and_corrupt_images_are_rejected(self):
        mismatched = photo_file(format="PNG", declared="image/jpeg")
        self.assertEqual(self.upload_photo(file=mismatched).status_code, 400)
        html = SimpleUploadedFile("image.jpg", b"<script>alert(1)</script>", content_type="image/jpeg")
        self.assertEqual(self.upload_photo(file=html).status_code, 400)
        gif = SimpleUploadedFile("animation.gif", b"GIF89a", content_type="image/gif")
        self.assertEqual(self.upload_photo(file=gif).status_code, 400)
        pdf = SimpleUploadedFile("identity.pdf", b"%PDF-1.7", content_type="application/pdf")
        self.assertEqual(self.upload_evidence(file=pdf).status_code, 400)
        self.assertEqual(MediaAsset.objects.count(), 0)

    def test_oversized_evidence_rejected_before_storage(self):
        large = SimpleUploadedFile(
            "oversized.jpg", b"x" * (5 * 1024 * 1024 + 1), content_type="image/jpeg"
        )
        response = self.upload_evidence(file=large)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(MediaAsset.objects.count(), 0)

    def test_cross_seller_and_unauthenticated_uploads_forbidden(self):
        self.client.force_authenticate(user=self.buyer)
        self.assertIn(self.upload_photo().status_code, (403, 404))
        self.assertEqual(self.upload_evidence().status_code, 403)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.upload_photo().status_code, 401)
        self.assertEqual(self.upload_evidence().status_code, 401)
        self.assertEqual(MediaAsset.objects.count(), 0)

    def test_only_draft_listings_receive_photos_and_uploads_are_limited(self):
        self.listing.status = Listing.Status.PENDING
        self.listing.save(update_fields=["status"])
        self.assertEqual(self.upload_photo().status_code, 400)
        self.listing.status = Listing.Status.DRAFT
        self.listing.save(update_fields=["status"])
        for _ in range(8):
            self.assertEqual(self.upload_photo().status_code, 201)
        self.assertEqual(self.upload_photo().status_code, 400)
        self.assertEqual(MediaAsset.objects.count(), 8)

    def test_reviewer_cannot_approve_own_photo_or_unreviewable_listing(self):
        result = self.upload_photo()
        uri = f"/api/v1/media/{result.data['id']}/review/"
        profile = self.seller.seller_profile
        profile.status = SellerProfile.Status.APPROVED
        profile.save(update_fields=["status"])
        self.client.force_authenticate(user=self.seller)
        self.assertEqual(self.client.post(uri, {
            "decision": "approve", "reason": "I should not be allowed to approve my own photo.",
        }, format="json").status_code, 403)
        self.client.force_authenticate(user=self.identity_reviewer)
        self.assertEqual(self.client.post(uri, {
            "decision": "approve", "reason": "My permission must not allow photo moderation.",
        }, format="json").status_code, 403)
        self.client.force_authenticate(user=self.reviewer)
        self.species.trade_enabled = False
        self.species.save(update_fields=["trade_enabled"])
        self.assertEqual(self.client.post(uri, {
            "decision": "approve", "reason": "This category is no longer allowed for trade.",
        }, format="json").status_code, 400)
        self.assertEqual(MediaReviewEvent.objects.count(), 0)

    def test_owner_media_list_does_not_leak_other_users(self):
        self.upload_photo()
        self.upload_evidence()
        self.client.force_authenticate(user=self.buyer)
        data = self.client.get("/api/v1/media/mine/")
        self.assertEqual(data.status_code, 200)
        self.assertEqual(data.data, [])
        self.client.force_authenticate(user=self.seller)
        data = self.client.get("/api/v1/media/mine/")
        self.assertEqual(len(data.data), 2)
        self.assertTrue(all("storage_key" not in item for item in data.data))

    def test_django_admin_session_access_to_seller_evidence_is_audited(self):
        self.upload_evidence()
        asset = MediaAsset.objects.get(kind=MediaAsset.Kind.SELLER_EVIDENCE)
        self.client.force_authenticate(user=None)
        self.client.force_login(self.identity_reviewer)
        file_response = self.client.get(f"/api/v1/media/{asset.pk}/file/")
        self.assertEqual(file_response.status_code, 200)
        self.assertEqual(MediaAccessEvent.objects.count(), 1)
        self.assertEqual(MediaAccessEvent.objects.first().actor, self.identity_reviewer)
        self.client.force_login(self.reviewer)
        self.assertEqual(self.client.get(f"/api/v1/media/{asset.pk}/file/").status_code, 404)

    def test_django_admin_photo_review_and_permission_gate(self):
        from django.urls import reverse

        photo = self.upload_photo()
        asset = MediaAsset.objects.get(pk=photo.data["id"])
        profile = self.seller.seller_profile
        profile.status = SellerProfile.Status.APPROVED
        profile.save(update_fields=["status"])
        url = reverse("admin:animal_media_mediaasset_review", args=[asset.pk])
        self.client.force_authenticate(user=None)
        self.client.force_login(self.identity_reviewer)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.reviewer)
        self.assertEqual(self.client.get(url).status_code, 200)
        decision = self.client.post(url, {
            "decision": "approve",
            "reason": "Photo content manually checked against the animal listing moderation rules.",
        })
        self.assertEqual(decision.status_code, 302)
        asset.refresh_from_db()
        self.assertEqual(asset.state, MediaAsset.State.APPROVED)
        self.assertEqual(MediaReviewEvent.objects.count(), 1)

    def test_seller_can_remove_draft_photo_and_public_access_stays_closed(self):
        uploaded = self.upload_photo()
        self.assertEqual(uploaded.status_code, 201)
        aid = uploaded.data["id"]
        target = f"/api/v1/media/{aid}/"
        self.assertEqual(self.client.delete(target).status_code, 204)
        asset = MediaAsset.objects.get(pk=aid)
        self.assertEqual(asset.state, MediaAsset.State.REMOVED)
        self.assertTrue(MediaReviewEvent.objects.filter(asset=asset, decision="removed").exists())
        self.assertEqual(self.client.get(uploaded.data["file_url"]).status_code, 404)
        self.assertEqual(self.client.get("/api/v1/media/mine/").data, [])
        self.assertEqual(self.client.delete(target).status_code, 404)
        # Removal frees the user's slot, but retained bytes await privacy cleanup.
        self.assertEqual(self.upload_photo().status_code, 201)
        # The anonymous throttle is intentionally shared across tests; use an
        # authenticated, unrelated user to assert object-level access.
        self.client.force_authenticate(user=self.buyer)
        self.assertEqual(self.client.get(uploaded.data["file_url"]).status_code, 404)

    def test_full_draft_gallery_can_replace_removed_photo(self):
        for _ in range(8):
            self.assertEqual(self.upload_photo().status_code, 201)
        ninth = self.upload_photo()
        self.assertEqual(ninth.status_code, 400)
        asset = MediaAsset.objects.filter(
            listing=self.listing, kind=MediaAsset.Kind.LISTING_PHOTO
        ).first()
        self.assertEqual(
            self.client.delete(f"/api/v1/media/{asset.pk}/").status_code, 204
        )
        self.assertEqual(self.upload_photo().status_code, 201)
        self.assertEqual(MediaAsset.objects.filter(
            listing=self.listing
        ).exclude(state=MediaAsset.State.REMOVED).count(), 8)

    def test_other_account_cannot_remove_photo_and_submitted_photo_is_locked(self):
        uploaded = self.upload_photo()
        aid = uploaded.data["id"]
        target = f"/api/v1/media/{aid}/"
        self.client.force_authenticate(user=self.buyer)
        self.assertEqual(self.client.delete(target).status_code, 404)
        self.client.force_authenticate(user=self.seller)
        self.listing.status = Listing.Status.PENDING
        self.listing.save(update_fields=["status"])
        denied = self.client.delete(target)
        self.assertEqual(denied.status_code, 400)
        self.assertEqual(MediaAsset.objects.get(pk=aid).state, MediaAsset.State.PENDING)

    def test_unsafe_local_storage_disabled_outside_debug(self):
        with override_settings(DEBUG=False, MEDIA_STORAGE_BACKEND="local"):
            with self.assertRaises(MediaStorageError):
                backend_name()

    def test_local_storage_rejects_path_traversal(self):
        with self.assertRaises(MediaStorageError):
            _local_path("seller-evidence/../../etc/password.jpg")

    @override_settings(
        DEBUG=False, MEDIA_STORAGE_BACKEND="r2",
        R2_BUCKET_PHOTOS="private-test-photos", R2_BUCKET_EVIDENCE="private-test-evidence",
    )
    @patch("modules.media.storage.r2_client")
    def test_r2_bucket_separation_and_no_public_acl(self, mock_client):
        from .storage import put_object

        boto = MagicMock()
        mock_client.return_value = boto
        put_object(kind=MediaAsset.Kind.LISTING_PHOTO, key="listing-photos/xyz.jpg", body=b"hello")
        put_object(kind=MediaAsset.Kind.SELLER_EVIDENCE, key="seller-evidence/xyz.jpg", body=b"hello")
        self.assertEqual(boto.put_object.call_count, 2)
        args1 = boto.put_object.call_args_list[0].kwargs
        args2 = boto.put_object.call_args_list[1].kwargs
        self.assertEqual(args1["Bucket"], "private-test-photos")
        self.assertEqual(args2["Bucket"], "private-test-evidence")
        self.assertEqual(args1["CacheControl"], "private, no-store")
        self.assertNotIn("ACL", args1)
        self.assertNotIn("ACL", args2)
