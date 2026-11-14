from django.urls import path

from .views import BlocksView, ReportsView, UnblockView

urlpatterns = [
    path("blocks/", BlocksView.as_view(), name="safety-blocks"),
    path("blocks/<uuid:target_id>/", UnblockView.as_view(), name="safety-unblock"),
    path("reports/", ReportsView.as_view(), name="safety-reports"),
]
