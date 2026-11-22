"""OTP-protected video moderation; never write video state through model forms."""
from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from rest_framework.exceptions import PermissionDenied as ApiPermissionDenied

from modules.accounts.authentication import require_staff_mfa

from .models import VideoPost, VideoReviewEvent, VideoComment, VideoCommentReviewEvent
from .comment_moderation import review_comment
from .moderation import review_video
from .provider import StreamUnavailable


class VideoReviewForm(forms.Form):
    decision = forms.ChoiceField(choices=VideoReviewEvent.Decision.choices)
    reason = forms.CharField(
        min_length=20, max_length=800,
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    visual_review_confirmed = forms.BooleanField(
        required=False,
        label="I inspected the actual video privately in Cloudflare Stream",
    )
    policy_review_confirmed = forms.BooleanField(
        required=False,
        label="I checked animal welfare, prohibited trade, rights and safety",
    )


@admin.register(VideoPost)
class VideoPostAdmin(admin.ModelAdmin):
    list_display = (
        "id", "creator", "state", "processed_at", "visibility_sync_needed",
        "created_at", "moderation_link",
    )
    list_filter = ("state", "visibility_sync_needed", "created_at")
    search_fields = ("creator__email", "caption", "video_uid")
    readonly_fields = (
        "id", "creator", "caption", "video_uid", "listing", "state",
        "rights_attested", "animal_topic_attested", "upload_expires_at",
        "processing_error", "visibility_sync_needed",
        "processed_at", "moderated_at", "moderated_by", "created_at",
    )

    def _can_review(self, request):
        return (
            request.user.is_authenticated and request.user.is_active
            and request.user.is_staff
            and request.user.has_perm("social.review_videopost")
        )

    @admin.display(description="Review")
    def moderation_link(self, obj):
        return format_html(
            '<a href="{}">Review / privacy sync</a>',
            reverse("admin:social_videopost_review", args=[obj.pk]),
        )

    def get_urls(self):
        custom = [
            path(
                "<uuid:object_id>/review/",
                self.admin_site.admin_view(self.review_view),
                name="social_videopost_review",
            ),
        ]
        return custom + super().get_urls()

    def review_view(self, request, object_id):
        require_staff_mfa(request.user)
        if not self._can_review(request):
            raise PermissionDenied("Video moderation permission required")
        video = get_object_or_404(VideoPost.objects.select_related("creator"), pk=object_id)
        form = VideoReviewForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            try:
                review_video(
                    video_id=video.pk,
                    reviewer=request.user,
                    **form.cleaned_data,
                )
            except (ValidationError, PermissionDenied, ApiPermissionDenied) as exc:
                form.add_error(None, str(exc))
            except StreamUnavailable:
                messages.warning(
                    request,
                    "The decision was recorded but provider playback is not synchronized. "
                    "The video is hidden from Anima's public feed while review is pending. "
                    "Retry privacy sync and contact operations immediately for takedowns.",
                )
                return redirect(reverse("admin:social_videopost_changelist"))
            else:
                messages.success(request, "Video moderation decision completed and audited.")
                return redirect(reverse("admin:social_videopost_changelist"))
        return TemplateResponse(
            request, "admin/social/video_review.html",
            {
                **self.admin_site.each_context(request),
                "title": "Review animal video",
                "opts": self.model._meta,
                "video": video,
                "form": form,
            },
        )

    def has_module_permission(self, request):
        return self._can_review(request)

    def has_view_permission(self, request, obj=None):
        return self._can_review(request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(VideoReviewEvent)
class VideoReviewEventAdmin(admin.ModelAdmin):
    list_display = (
        "video", "reviewer", "decision", "previous_state", "new_state", "created_at",
    )
    readonly_fields = (
        "video", "reviewer", "decision", "previous_state", "new_state",
        "reason", "visual_review_confirmed", "policy_review_confirmed", "created_at",
    )

    def has_module_permission(self, request):
        return (
            request.user.is_active and request.user.is_staff
            and request.user.has_perm("social.review_videopost")
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class VideoCommentReviewForm(forms.Form):
    decision = forms.ChoiceField(choices=VideoCommentReviewEvent.Decision.choices)
    reason = forms.CharField(
        min_length=20, max_length=500, widget=forms.Textarea(attrs={"rows": 3}),
    )


@admin.register(VideoComment)
class VideoCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "video", "author", "status", "created_at", "review_link")
    list_filter = ("status", "created_at")
    search_fields = ("body", "author__email", "video__id")
    readonly_fields = (
        "id", "video", "author", "client_nonce", "body", "status",
        "moderated_at", "moderated_by", "created_at",
    )

    def _allowed(self, request):
        return (
            request.user.is_authenticated and request.user.is_active
            and request.user.is_staff
            and request.user.has_perm("social.review_videocomment")
        )

    @admin.display(description="Review")
    def review_link(self, obj):
        return format_html(
            '<a href="{}">Review comment</a>',
            reverse("admin:social_videocomment_review", args=[obj.pk]),
        )

    def get_urls(self):
        return [
            path(
                "<uuid:object_id>/review/",
                self.admin_site.admin_view(self.review_view),
                name="social_videocomment_review",
            ),
        ] + super().get_urls()

    def review_view(self, request, object_id):
        require_staff_mfa(request.user)
        if not self._allowed(request):
            raise PermissionDenied("Comment moderation permission required")
        comment = get_object_or_404(
            VideoComment.objects.select_related("video", "author"), pk=object_id,
        )
        form = VideoCommentReviewForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            try:
                review_comment(
                    comment_id=comment.pk, reviewer=request.user,
                    **form.cleaned_data,
                )
            except (ValidationError, PermissionDenied, ApiPermissionDenied) as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(request, "Comment review was recorded.")
                return redirect(reverse("admin:social_videocomment_changelist"))
        return TemplateResponse(
            request, "admin/social/comment_review.html",
            {
                **self.admin_site.each_context(request),
                "title": "Review animal comment", "opts": self.model._meta,
                "comment": comment, "form": form,
            },
        )

    def has_module_permission(self, request):
        return self._allowed(request)

    def has_view_permission(self, request, obj=None):
        return self._allowed(request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(VideoCommentReviewEvent)
class VideoCommentReviewEventAdmin(admin.ModelAdmin):
    list_display = ("comment", "reviewer", "decision", "previous_state", "new_state", "created_at")
    readonly_fields = (
        "comment", "reviewer", "decision", "previous_state",
        "new_state", "reason", "created_at",
    )

    def has_module_permission(self, request):
        return (
            request.user.is_active and request.user.is_staff
            and request.user.has_perm("social.review_videocomment")
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
