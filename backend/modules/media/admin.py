"""Media moderation is API/service-driven and audited; asset fields are read-only."""
from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from rest_framework.exceptions import ValidationError

from .services import review_listing_photo
from django.utils.html import format_html

from .models import MediaAccessEvent, MediaAsset, MediaReviewEvent


class PhotoReviewForm(forms.Form):
    decision = forms.ChoiceField(choices=(("approve", "Approve"), ("reject", "Reject")))
    reason = forms.CharField(
        min_length=20, max_length=500, widget=forms.Textarea(attrs={"rows": 4}),
    )


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("kind", "owner", "listing", "state", "uploaded_at", "secure_file_link", "review_link")
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

    @admin.display(description="Photo moderation")
    def review_link(self, obj):
        if obj.kind != MediaAsset.Kind.LISTING_PHOTO or obj.state != MediaAsset.State.PENDING:
            return "—"
        return format_html(
            '<a href="{}">Review photo</a>',
            reverse("admin:animal_media_mediaasset_review", args=[obj.pk]),
        )

    def get_urls(self):
        urls = [
            path(
                "<uuid:object_id>/review/",
                self.admin_site.admin_view(self.review_view),
                name="animal_media_mediaasset_review",
            ),
        ]
        return urls + super().get_urls()

    def review_view(self, request, object_id):
        if not request.user.is_active or not request.user.is_staff or not request.user.has_perm(
            "animal_media.review_mediaasset"
        ):
            raise PermissionDenied("Photo review permission required")
        asset = get_object_or_404(
            MediaAsset.objects.filter(kind=MediaAsset.Kind.LISTING_PHOTO), pk=object_id
        )
        form = PhotoReviewForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            try:
                review_listing_photo(
                    asset_id=asset.pk,
                    reviewer=request.user,
                    decision=form.cleaned_data["decision"],
                    reason=form.cleaned_data["reason"],
                )
            except ValidationError as exc:
                form.add_error(None, str(exc.detail))
            else:
                messages.success(request, "Photo review decision recorded.")
                return redirect(reverse("admin:animal_media_mediaasset_changelist"))
        context = {
            **self.admin_site.each_context(request),
            "title": "Moderate animal photograph",
            "opts": self.model._meta,
            "asset": asset,
            "form": form,
        }
        return TemplateResponse(request, "admin/animal_media/photo_review.html", context)

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_staff and (
            request.user.has_perm("animal_media.review_mediaasset")
            or request.user.has_perm("accounts.review_sellerprofile")
            or super().has_module_permission(request)
        )

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff and (
            request.user.has_perm("animal_media.review_mediaasset")
            or request.user.has_perm("accounts.review_sellerprofile")
            or super().has_view_permission(request, obj)
        )

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
            qs = qs.exclude(kind=MediaAsset.Kind.SELLER_EVIDENCE)
        if not request.user.has_perm("animal_media.review_mediaasset"):
            qs = qs.exclude(kind=MediaAsset.Kind.LISTING_PHOTO)
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
