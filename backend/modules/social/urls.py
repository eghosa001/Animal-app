from django.urls import path

from .views import PublicVideoFeedView

urlpatterns = [
    path("videos/", PublicVideoFeedView.as_view(), name="public-video-feed"),
]
