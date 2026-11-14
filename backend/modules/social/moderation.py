"""Staff-MFA-only video decisions with provider visibility reconciliation."""
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from modules.accounts.authentication import require_staff_mfa

from .models import VideoPost, VideoReviewEvent
from .provider import StreamUnavailable, set_video_private


def _require_moderator(reviewer):
    require_staff_mfa(reviewer)
    if not reviewer.has_perm("social.review_videopost"):
        raise PermissionDenied("Video moderation permission required")


def reconcile_video_visibility(video_id):
    """Complete a reviewed publication or emergency takedown.

    This intentionally holds a row lock during the bounded provider operation
    to prevent publication racing with removal. The local state was committed
    before attempting the external call, so provider downtime never
    unintentionally makes an unreviewed clip visible in Anima's feed.
    """
    with transaction.atomic():
        video = VideoPost.objects.select_for_update().select_related(
            "creator"
        ).get(pk=video_id)
        if not video.visibility_sync_needed:
            return video
        if video.state == VideoPost.State.PUBLISHING:
            if not settings.STREAM_PUBLICATION_ENABLED:
                raise StreamUnavailable()
            if (
                not video.creator.is_active or not video.rights_attested
                or not video.animal_topic_attested or video.processed_at is None
                or video.moderated_by_id is None or video.moderated_at is None
            ):
                raise ValidationError("Publication eligibility changed; remove this clip")
            set_video_private(video.video_uid, private=False)
            video.state = VideoPost.State.APPROVED
        elif video.state == VideoPost.State.REMOVED:
            # A deleted/unavailable clip must require provider-signed access,
            # even if it was previously public or a publication was interrupted.
            set_video_private(video.video_uid, private=True)
        else:
            raise ValidationError("Only reviewed publishing/removal can sync provider visibility")
        video.visibility_sync_needed = False
        video.save(update_fields=("state", "visibility_sync_needed"))
        return video


def review_video(
    *, video_id, reviewer, decision, reason,
    visual_review_confirmed=False, policy_review_confirmed=False,
):
    """Review a single video. No self-review, no unreviewed publication."""
    _require_moderator(reviewer)
    reason = str(reason or "").strip()
    if not 20 <= len(reason) <= 800:
        raise ValidationError({"reason": "Explain the decision in 20–800 characters"})
    if decision not in {
        VideoReviewEvent.Decision.APPROVE, VideoReviewEvent.Decision.REJECT,
        VideoReviewEvent.Decision.REMOVE, VideoReviewEvent.Decision.RETRY_SYNC,
    }:
        raise ValidationError({"decision": "Unsupported video moderation decision"})

    needs_provider_sync = False
    with transaction.atomic():
        video = VideoPost.objects.select_for_update().select_related(
            "creator"
        ).get(pk=video_id)
        if video.creator_id == reviewer.pk:
            raise PermissionDenied("You cannot moderate your own animal video")
        previous = video.state

        if decision == VideoReviewEvent.Decision.APPROVE:
            if previous != VideoPost.State.PENDING:
                raise ValidationError("Only pending videos can be approved")
            if not (visual_review_confirmed and policy_review_confirmed):
                raise ValidationError(
                    "Confirm a full private-video visual inspection, rights and animal safety checks"
                )
            if (
                not video.rights_attested or not video.animal_topic_attested
                or video.processed_at is None or not video.creator.is_active
                or not settings.STREAM_PUBLICATION_ENABLED
            ):
                raise ValidationError("Video processing, eligibility or publication gate is incomplete")
            video.state = VideoPost.State.PUBLISHING
            video.visibility_sync_needed = True
            video.moderated_at = timezone.now()
            video.moderated_by = reviewer
            video.save(update_fields=(
                "state", "visibility_sync_needed", "moderated_at", "moderated_by",
            ))
            needs_provider_sync = True
        elif decision == VideoReviewEvent.Decision.REJECT:
            if previous != VideoPost.State.PENDING:
                raise ValidationError("Only pending videos can be rejected")
            video.state = VideoPost.State.REJECTED
            video.moderated_at = timezone.now()
            video.moderated_by = reviewer
            video.save(update_fields=("state", "moderated_at", "moderated_by"))
        elif decision == VideoReviewEvent.Decision.REMOVE:
            if previous not in (VideoPost.State.APPROVED, VideoPost.State.PUBLISHING):
                raise ValidationError("Only approved or publishing videos can be removed")
            video.state = VideoPost.State.REMOVED
            video.visibility_sync_needed = True
            video.save(update_fields=("state", "visibility_sync_needed"))
            needs_provider_sync = True
        else:
            if previous not in (VideoPost.State.PUBLISHING, VideoPost.State.REMOVED):
                raise ValidationError("Only interrupted publication/removal can be retried")
            if not video.visibility_sync_needed:
                raise ValidationError("Provider visibility is already synchronized")
            needs_provider_sync = True

        event = VideoReviewEvent.objects.create(
            video=video,
            reviewer=reviewer,
            decision=decision,
            previous_state=previous,
            new_state=video.state,
            reason=reason,
            visual_review_confirmed=bool(visual_review_confirmed),
            policy_review_confirmed=bool(policy_review_confirmed),
        )

    if needs_provider_sync:
        # If this fails, the reviewed PUBLISHING or hidden REMOVED state
        # persists with a retry flag. Never mark public success optimistically.
        reconcile_video_visibility(video_id)
    return event
