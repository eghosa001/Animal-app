"""Controlled seller-review decisions. No direct model status writes from an API or admin form."""
import re

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .models import SellerProfile, SellerReviewEvent


ALLOWED_TRANSITIONS = {
    (SellerProfile.Status.PENDING, SellerReviewEvent.Decision.APPROVE): SellerProfile.Status.APPROVED,
    (SellerProfile.Status.PENDING, SellerReviewEvent.Decision.REJECT): SellerProfile.Status.REJECTED,
    (SellerProfile.Status.APPROVED, SellerReviewEvent.Decision.SUSPEND): SellerProfile.Status.SUSPENDED,
    (SellerProfile.Status.REJECTED, SellerReviewEvent.Decision.REOPEN): SellerProfile.Status.PENDING,
    (SellerProfile.Status.SUSPENDED, SellerReviewEvent.Decision.REOPEN): SellerProfile.Status.PENDING,
}
CASE_REFERENCE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{3,79}$")


@transaction.atomic
def review_seller(*, seller_id, reviewer, decision, reason, evidence_case_reference="", evidence_reviewed=False):
    """Transition one seller under a row lock; audit changes and invalidate risky listings.

    A case reference is an opaque, internal identifier for evidence reviewed outside
    this app. It is NOT proof that identity verification has been automated.
    """
    if not reviewer or not reviewer.is_authenticated or not reviewer.is_active:
        raise PermissionDenied("An active reviewer account is required")
    if not reviewer.is_staff or not reviewer.has_perm("accounts.review_sellerprofile"):
        raise PermissionDenied("Seller reviewer permission is required")

    reason = str(reason or "").strip()
    # Do not trim first: hidden whitespace/newlines can conceal sensitive data.
    case_ref = str(evidence_case_reference or "")

    if len(reason) < 20 or len(reason) > 2000:
        raise ValidationError({"reason": "Enter 20–2000 characters explaining the decision"})
    if case_ref and not CASE_REFERENCE_PATTERN.fullmatch(case_ref):
        raise ValidationError({
            "evidence_case_reference": "Use an opaque internal case ID (4–80 letters, digits, _ or -)"
        })

    seller = SellerProfile.objects.select_for_update().select_related("user").get(pk=seller_id)
    if seller.user_id == reviewer.pk:
        raise PermissionDenied("Reviewers may not approve or otherwise review their own seller profile")

    next_status = ALLOWED_TRANSITIONS.get((seller.status, decision))
    if not next_status:
        raise ValidationError({
            "decision": f"Cannot {decision} a seller in status {seller.status}"
        })

    if decision == SellerReviewEvent.Decision.APPROVE:
        if not case_ref:
            raise ValidationError({"evidence_case_reference": "Approval requires a documented case reference"})
        if not evidence_reviewed:
            raise ValidationError({"evidence_reviewed": "Human reviewer confirmation is required"})
        if not seller.adult_attested or not seller.user.is_active or not seller.user.is_email_verified:
            raise ValidationError({
                "seller": "An adult-attested, active, email-verified applicant is required"
            })

    previous = seller.status
    seller.status = next_status
    seller.reviewed_at = timezone.now()
    seller.save(update_fields=["status", "reviewed_at"])
    event = SellerReviewEvent.objects.create(
        seller_profile=seller,
        reviewer=reviewer,
        decision=decision,
        previous_status=previous,
        new_status=next_status,
        reason=reason,
        evidence_case_reference=case_ref,
    )

    # An immediate safety suspension removes already-published animal listings.
    # They cannot silently reappear when the account is later reopened.
    if decision == SellerReviewEvent.Decision.SUSPEND:
        from modules.listings.models import Listing, ListingEvent

        active = list(
            Listing.objects.select_for_update().filter(
                seller=seller.user, status=Listing.Status.ACTIVE
            )
        )
        for listing in active:
            listing.status = Listing.Status.REMOVED
            listing.save(update_fields=["status"])
            ListingEvent.objects.create(
                listing=listing,
                actor=reviewer,
                from_status=Listing.Status.ACTIVE,
                to_status=Listing.Status.REMOVED,
                reason=f"Seller suspended; review event {event.pk}",
            )

    return event
