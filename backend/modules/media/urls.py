from django.urls import path

from .views import (
    DraftPhotoDeleteView, ListingPhotoUploadView, MediaFileView, MediaReviewView,
    MyMediaView, SellerEvidenceUploadView,
)

urlpatterns = [
    path("listing-photos/", ListingPhotoUploadView.as_view(), name="media-listing-photo-upload"),
    path("seller-evidence/", SellerEvidenceUploadView.as_view(), name="media-seller-evidence-upload"),
    path("mine/", MyMediaView.as_view(), name="media-mine"),
    path("<uuid:asset_id>/file/", MediaFileView.as_view(), name="media-file"),
    path("<uuid:asset_id>/", DraftPhotoDeleteView.as_view(), name="media-draft-photo-delete"),
    path("<uuid:asset_id>/review/", MediaReviewView.as_view(), name="media-review"),
]
