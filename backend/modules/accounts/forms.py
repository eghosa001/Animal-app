"""Human reviewer form. Do not collect ID numbers or identity photos in Django Admin."""
from django import forms

from .models import SellerReviewEvent


class SellerReviewForm(forms.Form):
    decision = forms.ChoiceField(choices=SellerReviewEvent.Decision.choices)
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 4, "cols": 70}),
        help_text="State the evidence and policy reasons without personal identity numbers.",
    )
    evidence_case_reference = forms.RegexField(
        regex=r"^[A-Za-z0-9][A-Za-z0-9_-]{3,79}$",
        required=False,
        max_length=80,
        help_text="Opaque case ID kept outside this system (e.g. CASE-2026-001). Do not enter sensitive documents.",
    )
    confirm_manual_evidence_review = forms.BooleanField(
        required=False,
        help_text="I have actually reviewed required evidence in an approved secure process.",
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("decision") == SellerReviewEvent.Decision.APPROVE:
            if not cleaned.get("evidence_case_reference"):
                self.add_error("evidence_case_reference", "Approval requires an external evidence case ID.")
            if not cleaned.get("confirm_manual_evidence_review"):
                self.add_error("confirm_manual_evidence_review", "Confirm the evidence was reviewed.")
        return cleaned
