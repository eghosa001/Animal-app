"""Versioned, minimal public API routes."""
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from config.views import live, ready
from modules.listings.views import ListingViewSet

router = DefaultRouter()
router.register("listings", ListingViewSet, basename="listing")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/live", live, name="health-live"),
    path("health/ready", ready, name="health-ready"),
    path("api/v1/auth/", include("modules.accounts.urls")),
    path("api/v1/catalog/", include("modules.catalog.urls")),
    path("api/v1/media/", include("modules.media.urls")),
    path("api/v1/", include(router.urls)),
]
