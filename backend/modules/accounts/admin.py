"""Read-only seller profiles and a separate audited review action."""
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils import timezone

from .forms import SellerReviewForm
from .models import SellerProfile, SellerReviewEvent, User
from .review_service import review_seller


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "display_name", "is_active", "is_staff", "email_verified_at")
    search_fields = ("email", "display_name")
    readonly_fields = ("id", "password", "email_verified_at", "last_login", "date_joined")
    list_filter = ("is_active", "is_staff")
    ordering = ("email",)

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        # Public registration and createsuperuser hash passwords; generic admin does not.
        return False


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "business_name", "user", "status", "adult_attested", "submitted_at",
        "reviewed_at", "review_link",
    )
    list_filter = ("status",)
    search_fields = ("business_name", "user__email")
    readonly_fields = (
        "user", "business_name", "adult_attested", "status", "submitted_at", "reviewed_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # Never allow direct status edits in the standard Django admin form.
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Audited review")
    def review_link(self, obj):
        url = reverse("admin:accounts_sellerprofile_review", args=[obj.pk])
        return format_html('<a href="{}">Review case</a>', url)

    def get_urls(self):
        custom = [
            path(
                "<int:object_id>/review/",
                self.admin_site.admin_view(self.review_view),
                name="accounts_sellerprofile_review",
            ),
        ]
        return custom + super().get_urls()

    def review_view(self, request, object_id):
        if not request.user.is_active or not request.user.is_staff or not request.user.has_perm(
            "accounts.review_sellerprofile"
        ):
            raise PermissionDenied("Seller review permission required")
        seller = get_object_or_404(
            SellerProfile.objects.select_related("user"), pk=object_id
        )
        form = SellerReviewForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            try:
                event = review_seller(
                    seller_id=seller.pk,
                    reviewer=request.user,
                    decision=form.cleaned_data["decision"],
                    reason=form.cleaned_data["reason"],
                    evidence_case_reference=form.cleaned_data.get("evidence_case_reference", ""),
                    evidence_reviewed=form.cleaned_data.get("confirm_manual_evidence_review", False),
                )
            except ValidationError as exc:
                if hasattr(exc, "message_dict"):
                    for field, messages_list in exc.message_dict.items():
                        destination = field if field in form.fields else None
                        form.add_error(destination, messages_list)
                else:
                    form.add_error(None, exc.messages)
            except PermissionDenied:
                raise
            else:
                messages.success(
                    request, f"Recorded review {event.pk}: {event.previous_status} → {event.new_status}"
                )
                return redirect(reverse("admin:accounts_sellerprofile_changelist"))

        context = {
            **self.admin_site.each_context(request),
            "title": "Review seller application",
            "opts": self.model._meta,
            "seller": seller,
            "form": form,
            "review_history": seller.review_events.select_related("reviewer").all()[:20],
        }
        return TemplateResponse(request, "admin/accounts/seller_review.html", context)


@admin.register(SellerReviewEvent)
class SellerReviewEventAdmin(admin.ModelAdmin):
    list_display = (
        "seller_profile", "decision", "previous_status", "new_status",
        "reviewer", "created_at",
    )
    list_filter = ("decision", "new_status", "created_at")
    search_fields = ("seller_profile__business_name", "reviewer__email", "evidence_case_reference")
    readonly_fields = (
        "seller_profile", "reviewer", "decision", "previous_status",
        "new_status", "reason", "evidence_case_reference", "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
