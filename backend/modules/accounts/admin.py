"""Staff users may inspect accounts; seller approval requires manual evidence review."""
from django.contrib import admin
from django.utils import timezone

from .models import SellerProfile, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "display_name", "is_active", "is_staff", "email_verified_at")
    search_fields = ("email", "display_name")
    readonly_fields = ("id", "password", "email_verified_at", "last_login", "date_joined")
    list_filter = ("is_active", "is_staff")
    ordering = ("email",)

    def has_add_permission(self, request):
        # Use createsuperuser or public registration; the generic admin does not hash passwords.
        return False


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ("business_name", "user", "status", "adult_attested", "submitted_at")
    search_fields = ("business_name", "user__email")
    list_filter = ("status",)
    readonly_fields = ("user", "submitted_at", "reviewed_at")

    def save_model(self, request, obj, form, change):
        if obj.status != SellerProfile.Status.PENDING and obj.reviewed_at is None:
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)
