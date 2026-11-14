from django.urls import path

from .views import ConversationOffersView, OfferDecisionView

urlpatterns = [
    path("conversations/<uuid:conversation_id>/",
         ConversationOffersView.as_view(), name="conversation-offers"),
    path("<uuid:offer_id>/decision/",
         OfferDecisionView.as_view(), name="offer-decision"),
]
