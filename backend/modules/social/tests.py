"""Feed must never leak unprocessed, unmoderated, disabled or removed clips."""
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from modules.accounts.models import SellerProfile, User
from modules.catalog.models import Species
from modules.listings.models import Animal, Listing

from .models import VideoPost


@override_settings(VIDEO_DELIVERY_HOST="videodelivery.net")
class VideoFeedTests(APITestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            email="creator@example.com", display_name="Animal creator",
            password="A-test-password!1000",
        )
        self.staff = User.objects.create_superuser(
            email="moderator@example.com", display_name="Reviewer",
            password="A-test-password!2000",
        )

    def create_video(self, **kwargs):
        values = {
            "creator": self.creator,
            "caption": "Animal care and enrichment",
            "video_uid": "a" * 32,
        }
        values.update(kwargs)
        return VideoPost.objects.create(**values)

    def test_no_unreviewed_or_unprocessed_video_in_guest_feed(self):
        video = self.create_video()
        self.assertEqual(self.client.get("/api/v1/feed/videos/").data["count"], 0)
        video.state = VideoPost.State.APPROVED
        video.moderated_by = self.staff
        video.moderated_at = timezone.now()
        video.save()
        self.assertEqual(self.client.get("/api/v1/feed/videos/").data["count"], 0)
        video.processed_at = timezone.now()
        video.save()
        response = self.client.get("/api/v1/feed/videos/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["playback_url"],
            "https://videodelivery.net/" + ("a" * 32) + "/manifest/video.m3u8",
        )
        video.state = VideoPost.State.REMOVED
        video.save(update_fields=("state",))
        self.assertEqual(self.client.get("/api/v1/feed/videos/").data["count"], 0)

    def test_disabled_delivery_domain_means_no_public_videos(self):
        self.create_video(
            processed_at=timezone.now(), moderated_at=timezone.now(),
            moderated_by=self.staff, state=VideoPost.State.APPROVED,
        )
        with override_settings(VIDEO_DELIVERY_HOST=""):
            self.assertEqual(self.client.get("/api/v1/feed/videos/").data["count"], 0)

    def test_inactive_creator_is_hidden_and_no_public_create_endpoint(self):
        self.create_video(
            processed_at=timezone.now(), moderated_at=timezone.now(),
            moderated_by=self.staff, state=VideoPost.State.APPROVED,
        )
        self.creator.is_active = False
        self.creator.save(update_fields=("is_active",))
        self.assertEqual(self.client.get("/api/v1/feed/videos/").data["count"], 0)
        self.assertEqual(self.client.post("/api/v1/feed/videos/", {}).status_code, 405)

    def test_linked_animal_is_only_shown_while_commercially_allowed(self):
        species = Species.objects.create(
            name="Dogs", slug="dogs", category=Species.Category.COMPANION,
            trade_enabled=False,
        )
        SellerProfile.objects.create(
            user=self.creator, business_name="Animal Care",
            adult_attested=True, status=SellerProfile.Status.APPROVED,
        )
        animal = Animal.objects.create(owner=self.creator, species=species, name="River")
        listing = Listing.objects.create(
            seller=self.creator, animal=animal, title="Healthy adult pet",
            description="Example animal test listing with no trade availability",
            price_minor=125000, currency="NGN", region="Lagos",
            status=Listing.Status.ACTIVE,
        )
        self.create_video(
            listing=listing, processed_at=timezone.now(),
            moderated_at=timezone.now(), moderated_by=self.staff,
            state=VideoPost.State.APPROVED,
        )
        feed = self.client.get("/api/v1/feed/videos/")
        self.assertIsNone(feed.data["results"][0]["listing"])
        species.trade_enabled = True
        species.save(update_fields=("trade_enabled",))
        feed = self.client.get("/api/v1/feed/videos/")
        self.assertEqual(feed.data["results"][0]["listing"]["id"], str(listing.id))
        listing.status = Listing.Status.REMOVED
        listing.save(update_fields=("status",))
        feed = self.client.get("/api/v1/feed/videos/")
        self.assertIsNone(feed.data["results"][0]["listing"])
