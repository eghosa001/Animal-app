from django.urls import path

from .views import PublicVideoFeedView
from .upload_views import (
    MyVideoPostsView, StreamWebhookView, VideoUploadCapabilitiesView,
    VideoUploadTicketView,
)

urlpatterns = [
    path("videos/", PublicVideoFeedView.as_view(), name="public-video-feed"),
    path("videos/upload-ticket/", VideoUploadTicketView.as_view(), name="video-upload-ticket"),
    path("videos/upload-capabilities/", VideoUploadCapabilitiesView.as_view(), name="video-upload-capabilities"),
    path("videos/mine/", MyVideoPostsView.as_view(), name="my-video-posts"),
    path("stream/webhook/", StreamWebhookView.as_view(), name="stream-webhook"),
]
