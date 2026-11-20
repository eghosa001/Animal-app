"""Order intentions are not financial records and cannot be altered via Admin."""
from django.contrib import admin

from .models import OrderIntent, OrderIntentEvent


@admin.register(OrderIntent)
class OrderIntentAdmin(admin.ModelAdmin):
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


@admin.register(OrderIntentEvent)
class OrderIntentEventAdmin(OrderIntentAdmin):
    pass
