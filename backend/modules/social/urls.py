from django.urls import path

from .views import PublicVideoFeedView
from .upload_views import StreamWebhookView, VideoUploadTicketView

urlpatterns = [
    path("videos/", PublicVideoFeedView.as_view(), name="public-video-feed"),
    path("videos/upload-ticket/", VideoUploadTicketView.as_view(), name="video-upload-ticket"),
    path("stream/webhook/", StreamWebhookView.as_view(), name="stream-webhook"),
]
