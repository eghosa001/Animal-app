from django.urls import path

from .views import OrderIntentCancelView, OrderIntentDetailView, OrderIntentsView

urlpatterns = [
    path("intents/", OrderIntentsView.as_view(), name="order-intents"),
    path("intents/<uuid:intent_id>/", OrderIntentDetailView.as_view(), name="order-intent-detail"),
    path("intents/<uuid:intent_id>/cancel/", OrderIntentCancelView.as_view(),
         name="order-intent-cancel"),
]
