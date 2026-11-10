"""Read-only staff video inventory until upload and moderation flows are shipped."""
from django.contrib import admin

from .models import VideoPost


@admin.register(VideoPost)
class VideoPostAdmin(admin.ModelAdmin):
    list_display = ("id", "creator", "state", "processed_at", "moderated_at", "created_at")
    list_filter = ("state", "created_at")
    search_fields = ("creator__email", "caption", "video_uid")
    readonly_fields = (
        "id", "creator", "caption", "video_uid", "listing", "state",
        "processed_at", "moderated_at", "moderated_by", "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
