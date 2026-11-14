"""Read-only by default; price agreements remain participant private."""
from django.contrib import admin

from .models import AnimalOffer, AnimalOfferEvent


@admin.register(AnimalOffer)
class AnimalOfferAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "created_at")
    readonly_fields = (
        "id", "conversation", "proposer", "client_nonce", "amount_minor",
        "currency", "list_price_minor_at_creation", "status", "replaces",
        "created_at", "expires_at", "responded_at",
    )

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


@admin.register(AnimalOfferEvent)
class AnimalOfferEventAdmin(AnimalOfferAdmin):
    list_display = ("id", "created_at")
    readonly_fields = (
        "id", "offer", "actor", "from_status", "to_status", "reason", "created_at",
    )
