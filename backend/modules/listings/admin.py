"""Moderated publication; status is read-only to prevent accidental direct activation."""
from django.contrib import admin, messages
from rest_framework.exceptions import ValidationError

from .models import Animal, Listing, ListingEvent
from .services import approve_listing


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ("name", "species", "owner", "sex")
    list_filter = ("species",)
    search_fields = ("name", "owner__email")
    readonly_fields = ("owner",)


@admin.action(description="Approve selected permitted listings (review evidence first)")
def approve_selected(modeladmin, request, queryset):
    for listing in queryset:
        try:
            approve_listing(listing.id, request.user)
        except ValidationError as exc:
            modeladmin.message_user(request, f"{listing.id}: {exc}", level=messages.ERROR)
        else:
            modeladmin.message_user(request, f"Approved {listing.id}", level=messages.SUCCESS)


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "seller", "status", "region", "price_minor", "currency")
    list_filter = ("status", "currency")
    search_fields = ("title", "seller__email")
    readonly_fields = ("status", "seller", "animal", "created_at", "submitted_at", "approved_at")
    actions = (approve_selected,)


@admin.register(ListingEvent)
class ListingEventAdmin(admin.ModelAdmin):
    list_display = ("listing", "actor", "from_status", "to_status", "created_at")
    readonly_fields = ("listing", "actor", "from_status", "to_status", "reason", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
