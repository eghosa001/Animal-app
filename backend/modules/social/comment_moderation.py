"""Audited, MFA-only review of text comments; never auto-publish."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from modules.accounts.authentication import require_staff_mfa

from .models import VideoComment, VideoCommentReviewEvent, VideoPost


def review_comment(*, comment_id, reviewer, decision, reason):
    require_staff_mfa(reviewer)
    if not reviewer.is_active or not reviewer.is_staff or not reviewer.has_perm(
        "social.review_videocomment"
    ):
        raise PermissionDenied("Comment moderation permission required")
    reason = reason.strip()
    if not 20 <= len(reason) <= 500:
        raise ValidationError("Explain the comment decision in 20–500 characters")
    if decision not in VideoCommentReviewEvent.Decision.values:
        raise ValidationError("Unsupported comment moderation action")
    with transaction.atomic():
        comment = VideoComment.objects.select_for_update().select_related(
            "video__creator", "author",
        ).get(pk=comment_id)
        if reviewer.pk in (comment.author_id, comment.video.creator_id):
            raise PermissionDenied("You cannot moderate your own content")
        previous = comment.status
        if decision == VideoCommentReviewEvent.Decision.APPROVE:
            if previous != VideoComment.Status.PENDING:
                raise ValidationError("Only pending comments can be approved")
            video = comment.video
            if not (
                comment.author.is_active and video.creator.is_active
                and video.state == VideoPost.State.APPROVED
                and video.processed_at and video.moderated_at
                and video.moderated_by_id
            ):
                raise ValidationError("Comment or video is no longer eligible")
            new_state = VideoComment.Status.APPROVED
        elif decision == VideoCommentReviewEvent.Decision.REJECT:
            if previous != VideoComment.Status.PENDING:
                raise ValidationError("Only pending comments can be rejected")
            new_state = VideoComment.Status.REJECTED
        else:
            if previous != VideoComment.Status.APPROVED:
                raise ValidationError("Only published comments can be removed")
            new_state = VideoComment.Status.REMOVED
        comment.status = new_state
        comment.moderated_by = reviewer
        comment.moderated_at = timezone.now()
        comment.save(update_fields=("status", "moderated_by", "moderated_at"))
        return VideoCommentReviewEvent.objects.create(
            comment=comment, reviewer=reviewer, decision=decision,
            previous_state=previous, new_state=new_state, reason=reason,
        )
