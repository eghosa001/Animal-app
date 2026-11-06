"""Media moderation is API/service-driven and audited; asset fields are read-only."""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import MediaAccessEvent, MediaAsset, MediaReviewEvent


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("kind", "owner", "listing", "state", "uploaded_at", "secure_file_link")
    list_filter = ("kind", "state", "uploaded_at")
    search_fields = ("owner__email", "listing__title", "id")
    readonly_fields = (
        "id", "owner", "listing", "kind", "evidence_type", "state", "storage_key",
        "content_type", "size_bytes", "width", "height", "sha256", "uploaded_at",
        "reviewed_by", "reviewed_at", "review_note",
    )

    @admin.display(description="Private file")
    def secure_file_link(self, obj):
        return format_html('<a href="{}">Open authorized image</a>', reverse("media-file", kwargs={"asset_id": obj.pk}))

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if not request.user.has_perm("accounts.review_sellerprofile"):
            # Identity docs should not become discoverable by generic media moderators.
            qs = qs.exclude(kind=MediaAsset.Kind.SELLER_EVIDENCE)
        return qs


@admin.register(MediaAccessEvent)
class MediaAccessEventAdmin(admin.ModelAdmin):
    list_display = ("asset", "actor", "purpose", "accessed_at")
    readonly_fields = ("asset", "actor", "purpose", "accessed_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MediaReviewEvent)
class MediaReviewEventAdmin(admin.ModelAdmin):
    list_display = ("asset", "actor", "decision", "created_at")
    readonly_fields = ("asset", "actor", "decision", "reason", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
