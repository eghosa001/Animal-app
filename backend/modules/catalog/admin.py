from django.contrib import admin

from .models import Species


@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "category", "trade_enabled")
    list_filter = ("category", "trade_enabled")
    search_fields = ("name", "slug")
    # Trade-enabled changes must be made only by staff with legal approval.
