"""Private messages are intentionally inaccessible through generic staff admin."""
from django.contrib import admin

from .models import ChatMessage, Conversation


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "updated_at")
    readonly_fields = ("id", "created_at", "updated_at")

    def has_module_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ChatMessage)
class ChatMessageAdmin(ConversationAdmin):
    list_display = ("id", "created_at")
    readonly_fields = ("id", "created_at")
