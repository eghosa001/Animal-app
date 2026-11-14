"""Minimal safety staff queue; messages themselves are never publicly browsable."""
from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from rest_framework.exceptions import PermissionDenied as ApiPermissionDenied

from modules.accounts.authentication import require_staff_mfa

from .models import SafetyReport, SafetyReportReviewEvent, UserBlock
from .moderation import review_report


class ReportDecisionForm(forms.Form):
    to_status = forms.ChoiceField(choices=(
        (SafetyReport.Status.IN_REVIEW, "Investigating"),
        (SafetyReport.Status.ACTIONED, "Action taken and documented"),
        (SafetyReport.Status.DISMISSED, "Dismissed after review"),
    ))
    reason = forms.CharField(
        min_length=20, max_length=800,
        widget=forms.Textarea(attrs={"rows": 4}),
    )


@admin.register(SafetyReport)
class SafetyReportAdmin(admin.ModelAdmin):
    list_display = (
        "id", "category", "status", "created_at", "reviewed_at", "review_link",
    )
    list_filter = ("category", "status", "created_at")
    search_fields = ("id", "reporter__email")
    readonly_fields = (
        "id", "reporter", "category", "detail", "status",
        "video", "listing", "message", "subject_user", "created_at",
        "reviewed_at", "reviewed_by",
    )

    def _allowed(self, request):
        return (
            request.user.is_authenticated and request.user.is_active
            and request.user.is_staff
            and request.user.has_perm("safety.review_safetyreport")
        )

    @admin.display(description="Review")
    def review_link(self, obj):
        return format_html(
            '<a href="{}">Review case</a>',
            reverse("admin:safety_safetyreport_review", args=[obj.pk]),
        )

    def get_urls(self):
        urls = [path(
            "<uuid:object_id>/review/",
            self.admin_site.admin_view(self.review_view),
            name="safety_safetyreport_review",
        )]
        return urls + super().get_urls()

    def review_view(self, request, object_id):
        require_staff_mfa(request.user)
        if not self._allowed(request):
            raise PermissionDenied("Safety reviewer permission required")
        report = get_object_or_404(SafetyReport, pk=object_id)
        form = ReportDecisionForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            try:
                review_report(
                    report_id=report.pk, reviewer=request.user,
                    **form.cleaned_data,
                )
            except (ValidationError, PermissionDenied, ApiPermissionDenied) as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(request, "Safety review decision audited.")
                return redirect(reverse("admin:safety_safetyreport_changelist"))
        return TemplateResponse(request, "admin/safety/report_review.html", {
            **self.admin_site.each_context(request),
            "title": "Review animal safety report",
            "opts": self.model._meta,
            "report": report,
            "form": form,
        })

    def has_module_permission(self, request):
        return self._allowed(request)

    def has_view_permission(self, request, obj=None):
        return self._allowed(request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SafetyReportReviewEvent)
class SafetyReviewEventAdmin(admin.ModelAdmin):
    list_display = ("report", "reviewer", "from_status", "to_status", "created_at")
    readonly_fields = (
        "report", "reviewer", "from_status", "to_status", "reason", "created_at",
    )

    def has_module_permission(self, request):
        return (
            request.user.is_active and request.user.is_staff
            and request.user.has_perm("safety.review_safetyreport")
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UserBlock)
class UserBlockAdmin(admin.ModelAdmin):
    """User blocks are private personal decisions, inaccessible to general staff."""
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
