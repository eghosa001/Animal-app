"""MFA-gated human report triage with an immutable decision audit."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from modules.accounts.authentication import require_staff_mfa

from .models import SafetyReport, SafetyReportReviewEvent


ALLOWED_TRANSITIONS = {
    SafetyReport.Status.OPEN: (
        SafetyReport.Status.IN_REVIEW,
        SafetyReport.Status.ACTIONED,
        SafetyReport.Status.DISMISSED,
    ),
    SafetyReport.Status.IN_REVIEW: (
        SafetyReport.Status.ACTIONED,
        SafetyReport.Status.DISMISSED,
    ),
}


@transaction.atomic
def review_report(*, report_id, reviewer, to_status, reason):
    require_staff_mfa(reviewer)
    if not reviewer.has_perm("safety.review_safetyreport"):
        raise PermissionDenied("Safety reviewer permission required")
    reason = str(reason or "").strip()
    if len(reason) < 20 or len(reason) > 800:
        raise ValidationError({"reason": "Explain the decision in 20–800 characters"})
    report = SafetyReport.objects.select_for_update(of=("self",)).get(pk=report_id)
    if report.reporter_id == reviewer.pk:
        raise PermissionDenied("Reviewers cannot decide their own reports")
    if to_status not in ALLOWED_TRANSITIONS.get(report.status, ()):
        raise ValidationError({"to_status": "Unsupported report status transition"})
    before = report.status
    report.status = to_status
    report.reviewed_at = timezone.now()
    report.reviewed_by = reviewer
    report.save(update_fields=("status", "reviewed_at", "reviewed_by"))
    return SafetyReportReviewEvent.objects.create(
        report=report, reviewer=reviewer, from_status=before,
        to_status=to_status, reason=reason,
    )
