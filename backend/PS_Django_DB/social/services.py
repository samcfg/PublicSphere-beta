"""
Social interaction business logic.
Handles ratings, comments, moderation operations, and suggested edits.
"""
from typing import Dict, List, Optional, Tuple
from django.db.models import Avg, Count, Q, StdDev, OuterRef, Subquery, CharField
from django.db.models.functions import Cast
from django.utils import timezone
from social.models import Rating, Comment, FlaggedContent, SuggestedEdit
from users.models import User


class RatingService:
    """Service for rating operations and aggregation"""

    @staticmethod
    def rate_entity(user_id: int, entity_uuid: str, entity_type: str,
                   score: float, dimension: Optional[str] = None) -> Rating:
        """
        Create or update a rating.

        Args:
            user_id: User making the rating
            entity_uuid: UUID of entity being rated
            entity_type: 'claim', 'source', 'connection', or 'comment'
            score: Rating score (0-100)
            dimension: Optional dimension ('confidence' or 'relevance')

        Returns:
            Rating instance (created or updated)
        """
        rating, created = Rating.objects.update_or_create(
            user_id=user_id,
            entity_uuid=entity_uuid,
            entity_type=entity_type,
            dimension=dimension,
            defaults={'score': score}
        )
        return rating

    @staticmethod
    def get_entity_ratings(entity_uuid: str, dimension: Optional[str] = None, user_id: Optional[int] = None) -> Dict:
        """
        Get aggregated ratings for an entity.

        Args:
            entity_uuid: UUID of entity
            dimension: Optional filter by dimension
            user_id: Optional user ID to include their rating

        Returns:
            Dict with: avg_score, count, stddev, distribution, user_score
        """
        query = Rating.objects.filter(entity_uuid=entity_uuid)
        if dimension:
            query = query.filter(dimension=dimension)

        aggregates = query.aggregate(
            avg_score=Avg('score'),
            count=Count('id'),
            stddev=StdDev('score')
        )

        # Score distribution (0-20, 20-40, 40-60, 60-80, 80-100)
        distribution = {
            '0-20': query.filter(score__gte=0, score__lt=20).count(),
            '20-40': query.filter(score__gte=20, score__lt=40).count(),
            '40-60': query.filter(score__gte=40, score__lt=60).count(),
            '60-80': query.filter(score__gte=60, score__lt=80).count(),
            '80-100': query.filter(score__gte=80, score__lte=100).count(),
        }

        # Get current user's rating if authenticated
        user_score = None
        if user_id:
            try:
                user_rating = Rating.objects.get(
                    user_id=user_id,
                    entity_uuid=entity_uuid,
                    dimension=dimension
                )
                user_score = user_rating.score
            except Rating.DoesNotExist:
                pass

        return {
            'avg_score': round(aggregates['avg_score'], 2) if aggregates['avg_score'] else None,
            'count': aggregates['count'],
            'stddev': round(aggregates['stddev'], 2) if aggregates['stddev'] else None,
            'distribution': distribution,
            'user_score': user_score
        }

    @staticmethod
    def get_user_ratings(user_id: int, entity_type: Optional[str] = None) -> List[Rating]:
        """
        Get all ratings by a user.

        Args:
            user_id: User ID
            entity_type: Optional filter by entity type

        Returns:
            List of Rating instances
        """
        query = Rating.objects.filter(user_id=user_id)
        if entity_type:
            query = query.filter(entity_type=entity_type)
        return list(query.order_by('-timestamp'))

    @staticmethod
    def delete_rating(user_id: int, entity_uuid: str, entity_type: str,
                     dimension: Optional[str] = None) -> bool:
        """
        Delete a user's rating.

        Args:
            user_id: User who created the rating
            entity_uuid: UUID of rated entity
            entity_type: Entity type
            dimension: Optional dimension

        Returns:
            True if deleted, False if not found
        """
        try:
            rating = Rating.objects.get(
                user_id=user_id,
                entity_uuid=entity_uuid,
                entity_type=entity_type,
                dimension=dimension
            )
            rating.delete()
            return True
        except Rating.DoesNotExist:
            return False

    @staticmethod
    def get_controversial_entities(limit: int = 50) -> List[Dict]:
        """
        Find entities with high rating variance (controversial).

        Args:
            limit: Maximum number to return

        Returns:
            List of dicts with entity info and variance metrics
        """
        # Group by entity, calculate stddev
        from django.db.models import F
        controversial = (
            Rating.objects
            .values('entity_uuid', 'entity_type')
            .annotate(
                count=Count('id'),
                avg_score=Avg('score'),
                stddev=StdDev('score')
            )
            .filter(count__gte=5, stddev__isnull=False)  # At least 5 ratings
            .order_by('-stddev')[:limit]
        )

        return list(controversial)


class CommentService:
    """Service for comment operations"""

    @staticmethod
    def create_comment(user_id: int, entity_uuid: str, entity_type: str,
                      content: str, parent_comment_id: Optional[int] = None) -> Comment:
        """
        Create a new comment.

        Args:
            user_id: User creating comment
            entity_uuid: UUID of entity being commented on
            entity_type: 'claim', 'source', 'connection', or 'comment'
            content: Comment text
            parent_comment_id: If set, this is a reply

        Returns:
            Comment instance
        """
        comment = Comment.objects.create(
            user_id=user_id,
            entity_uuid=entity_uuid,
            entity_type=entity_type,
            content=content,
            parent_comment_id=parent_comment_id
        )
        return comment

    @staticmethod
    def get_entity_comments(entity_uuid: str, include_deleted: bool = False, sort: str = 'timestamp') -> List[Comment]:
        """
        Get all comments for an entity (flat list, sorted by timestamp or score).

        Args:
            entity_uuid: UUID of entity
            include_deleted: If True, include soft-deleted comments
            sort: 'timestamp' (default) or 'score'

        Returns:
            List of Comment instances
        """
        query = Comment.objects.filter(entity_uuid=entity_uuid)
        if not include_deleted:
            query = query.filter(is_deleted=False)

        if sort == 'score':
            # Cast comment.id to string to match Rating.entity_uuid
            # Subquery to get average rating for each comment
            rating_subquery = Rating.objects.filter(
                entity_uuid=Cast(OuterRef('id'), CharField()),
                entity_type='comment'
            ).values('entity_uuid').annotate(
                avg=Avg('score')
            ).values('avg')

            query = query.annotate(
                avg_score=Subquery(rating_subquery)
            ).order_by('-avg_score', '-timestamp')  # Nulls (unrated) go last, then by timestamp
        else:
            query = query.order_by('timestamp')

        return list(query)

    @staticmethod
    def get_comment_thread(comment_id: int, include_deleted: bool = False) -> List[Comment]:
        """
        Get all replies to a comment (nested thread).

        Args:
            comment_id: Parent comment ID
            include_deleted: If True, include soft-deleted comments

        Returns:
            List of Comment instances (replies)
        """
        query = Comment.objects.filter(parent_comment_id=comment_id)
        if not include_deleted:
            query = query.filter(is_deleted=False)
        return list(query.order_by('timestamp'))

    @staticmethod
    def update_comment(comment_id: int, user_id: int, new_content: str) -> Optional[Comment]:
        """
        Update comment content (must be own comment).

        Args:
            comment_id: Comment ID
            user_id: User making the request
            new_content: New comment text

        Returns:
            Updated Comment instance or None if not found/unauthorized
        """
        try:
            comment = Comment.objects.get(id=comment_id, user_id=user_id)
            comment.content = new_content
            comment.save()
            return comment
        except Comment.DoesNotExist:
            return None

    @staticmethod
    def soft_delete_comment(comment_id: int, user_id: int, is_moderator: bool = False) -> bool:
        """
        Soft-delete a comment (user or moderator action).

        Args:
            comment_id: Comment ID
            user_id: User making the request
            is_moderator: If True, allows deleting others' comments

        Returns:
            True if deleted, False if not found/unauthorized
        """
        try:
            if is_moderator:
                comment = Comment.objects.get(id=comment_id)
            else:
                comment = Comment.objects.get(id=comment_id, user_id=user_id)

            comment.is_deleted = True
            comment.save()
            return True
        except Comment.DoesNotExist:
            return False

    @staticmethod
    def hard_delete_comment(comment_id: int) -> bool:
        """
        Permanently delete a comment (staff admin only).

        Args:
            comment_id: Comment ID

        Returns:
            True if deleted, False if not found
        """
        try:
            comment = Comment.objects.get(id=comment_id)
            comment.delete()
            return True
        except Comment.DoesNotExist:
            return False

    @staticmethod
    def get_user_comments(user_id: int, include_deleted: bool = False) -> List[Comment]:
        """
        Get all comments by a user.

        Args:
            user_id: User ID
            include_deleted: If True, include soft-deleted comments

        Returns:
            List of Comment instances
        """
        query = Comment.objects.filter(user_id=user_id)
        if not include_deleted:
            query = query.filter(is_deleted=False)
        return list(query.order_by('-timestamp'))


class ModerationService:
    """Service for moderation operations"""

    @staticmethod
    def flag_entity(flagged_by_id: int, entity_uuid: str, entity_type: str,
                   reason: str) -> FlaggedContent:
        """
        Flag content for moderator review.

        Args:
            flagged_by_id: User/moderator flagging the content
            entity_uuid: UUID of flagged entity
            entity_type: Entity type
            reason: Explanation for flag

        Returns:
            FlaggedContent instance
        """
        flag = FlaggedContent.objects.create(
            flagged_by_id=flagged_by_id,
            entity_uuid=entity_uuid,
            entity_type=entity_type,
            reason=reason
        )
        return flag

    @staticmethod
    def get_pending_flags(limit: Optional[int] = None) -> List[FlaggedContent]:
        """
        Get all pending moderation flags.

        Args:
            limit: Optional limit on results

        Returns:
            List of FlaggedContent instances
        """
        query = FlaggedContent.objects.filter(status='pending').order_by('timestamp')
        if limit:
            query = query[:limit]
        return list(query)

    @staticmethod
    def resolve_flag(flag_id: int, reviewed_by_id: int, status: str,
                    resolution_notes: str = '') -> Optional[FlaggedContent]:
        """
        Resolve a moderation flag (staff admin action).

        Args:
            flag_id: FlaggedContent ID
            reviewed_by_id: Staff admin resolving the flag
            status: New status ('reviewed', 'action_taken', 'dismissed')
            resolution_notes: Optional notes from reviewer

        Returns:
            Updated FlaggedContent instance or None if not found
        """
        try:
            flag = FlaggedContent.objects.get(id=flag_id)
            flag.status = status
            flag.reviewed_by_id = reviewed_by_id
            flag.resolution_notes = resolution_notes
            flag.reviewed_at = timezone.now()
            flag.save()
            return flag
        except FlaggedContent.DoesNotExist:
            return None

    @staticmethod
    def get_entity_flags(entity_uuid: str) -> List[FlaggedContent]:
        """
        Get all flags for a specific entity.

        Args:
            entity_uuid: UUID of entity

        Returns:
            List of FlaggedContent instances
        """
        return list(FlaggedContent.objects.filter(entity_uuid=entity_uuid).order_by('-timestamp'))


def get_rating_service() -> RatingService:
    """Get rating service instance"""
    return RatingService()


def get_comment_service() -> CommentService:
    """Get comment service instance"""
    return CommentService()


def get_moderation_service() -> ModerationService:
    """Get moderation service instance"""
    return ModerationService()


class SocialAnonymityService:
    """Service for toggling anonymity on comments and ratings"""

    @staticmethod
    def toggle_comment_anonymity(comment_id: int, user_id: int) -> bool:
        """
        Toggle is_anonymous for a user's own comment.

        Args:
            comment_id: Comment ID
            user_id: User making the request (must own the comment)

        Returns:
            True if toggled, False if not found or unauthorized
        """
        try:
            comment = Comment.objects.get(id=comment_id, user_id=user_id)
            comment.is_anonymous = not comment.is_anonymous
            comment.save()
            return True
        except Comment.DoesNotExist:
            return False

    @staticmethod
    def toggle_rating_anonymity(rating_id: int, user_id: int) -> bool:
        """
        Toggle is_anonymous for a user's own rating.

        Args:
            rating_id: Rating ID
            user_id: User making the request (must own the rating)

        Returns:
            True if toggled, False if not found or unauthorized
        """
        try:
            rating = Rating.objects.get(id=rating_id, user_id=user_id)
            rating.is_anonymous = not rating.is_anonymous
            rating.save()
            return True
        except Rating.DoesNotExist:
            return False


def get_social_anonymity_service() -> SocialAnonymityService:
    """Get social anonymity service instance"""
    return SocialAnonymityService()


class SuggestionService:
    """Service for suggested edit operations"""

    @staticmethod
    def create_suggestion(user_id: int, entity_uuid: str, entity_type: str,
                         proposed_changes: Dict, rationale: str) -> SuggestedEdit:
        """
        Create a new suggested edit.

        Args:
            user_id: User making the suggestion
            entity_uuid: UUID of target node
            entity_type: 'claim' or 'source'
            proposed_changes: Dict of property: new_value pairs
            rationale: Why this change improves the node

        Returns:
            SuggestedEdit instance
        """
        suggestion = SuggestedEdit.objects.create(
            entity_uuid=entity_uuid,
            entity_type=entity_type,
            suggested_by_id=user_id,
            proposed_changes=proposed_changes,
            rationale=rationale
        )
        return suggestion

    @staticmethod
    def get_entity_suggestions(entity_uuid: str, status: Optional[str] = None) -> List[SuggestedEdit]:
        """
        Get all suggestions for an entity.

        Args:
            entity_uuid: UUID of target node
            status: Optional filter by status ('pending', 'accepted', 'rejected')

        Returns:
            List of SuggestedEdit instances
        """
        query = SuggestedEdit.objects.filter(entity_uuid=entity_uuid)
        if status:
            query = query.filter(status=status)
        return list(query.order_by('-created_at'))

    @staticmethod
    def get_suggestion(suggestion_id: str) -> Optional[SuggestedEdit]:
        """
        Get a specific suggestion by ID.

        Args:
            suggestion_id: UUID of suggestion

        Returns:
            SuggestedEdit instance or None
        """
        try:
            return SuggestedEdit.objects.get(suggestion_id=suggestion_id)
        except SuggestedEdit.DoesNotExist:
            return None

    @staticmethod
    def check_acceptance_threshold(suggestion_id: str, node_engagement: float) -> Tuple[bool, Optional[str]]:
        """
        Check if suggestion meets acceptance threshold based on ratings and node engagement.

        Logic:
        - Base requirements: MIN_VOTES=5, MIN_AVG=70
        - Higher engagement → more votes required
        - Formula: required_votes = MIN_VOTES * (1 + node_engagement/50)

        Args:
            suggestion_id: UUID of suggestion
            node_engagement: Engagement score of target node

        Returns:
            Tuple (can_accept: bool, reason: str|None)
        """
        stats = Rating.objects.filter(
            entity_uuid=str(suggestion_id),
            entity_type='suggested_edit'
        ).aggregate(count=Count('id'), avg=Avg('score'))

        rating_count = stats['count'] or 0
        avg_rating = stats['avg'] or 50.0

        # Base thresholds
        MIN_VOTES = 5
        MIN_AVG = 70

        # Scale with node engagement
        engagement_multiplier = 1 + (node_engagement / 50)
        required_votes = MIN_VOTES * engagement_multiplier

        # Accept if: positive consensus + sufficient participation
        if avg_rating >= MIN_AVG and rating_count >= required_votes:
            return True, None

        return False, f"Need {required_votes:.0f} votes at {MIN_AVG}+ avg (currently: {rating_count} votes, {avg_rating:.1f} avg)"

    @staticmethod
    def accept_suggestion(suggestion_id: str, resolved_by_id: int,
                         resolution_notes: str = '', auto_accepted: bool = False) -> Optional[SuggestedEdit]:
        """
        Accept a suggestion and apply changes to target node.

        Args:
            suggestion_id: UUID of suggestion
            resolved_by_id: User accepting (moderator or system)
            resolution_notes: Optional notes
            auto_accepted: True if threshold auto-triggered, False if moderator action

        Returns:
            Updated SuggestedEdit instance or None if not found

        Note: Actual node modification happens in the view layer via ops.edit_node()
        """
        try:
            suggestion = SuggestedEdit.objects.get(suggestion_id=suggestion_id)
            if suggestion.status != 'pending':
                return None  # Already resolved

            suggestion.status = 'accepted'
            suggestion.resolved_by_id = resolved_by_id
            suggestion.resolved_at = timezone.now()
            suggestion.resolution_notes = resolution_notes or ('Auto-accepted via threshold' if auto_accepted else 'Accepted by moderator')
            suggestion.save()
            return suggestion
        except SuggestedEdit.DoesNotExist:
            return None

    @staticmethod
    def reject_suggestion(suggestion_id: str, resolved_by_id: int,
                         resolution_notes: str = '') -> Optional[SuggestedEdit]:
        """
        Reject a suggestion (moderator only).

        Args:
            suggestion_id: UUID of suggestion
            resolved_by_id: Moderator rejecting
            resolution_notes: Reason for rejection

        Returns:
            Updated SuggestedEdit instance or None if not found
        """
        try:
            suggestion = SuggestedEdit.objects.get(suggestion_id=suggestion_id)
            if suggestion.status != 'pending':
                return None  # Already resolved

            suggestion.status = 'rejected'
            suggestion.resolved_by_id = resolved_by_id
            suggestion.resolved_at = timezone.now()
            suggestion.resolution_notes = resolution_notes or 'Rejected by moderator'
            suggestion.save()
            return suggestion
        except SuggestedEdit.DoesNotExist:
            return None

    @staticmethod
    def get_user_suggestions(user_id: int, status: Optional[str] = None) -> List[SuggestedEdit]:
        """
        Get all suggestions by a user.

        Args:
            user_id: User ID
            status: Optional filter by status

        Returns:
            List of SuggestedEdit instances
        """
        query = SuggestedEdit.objects.filter(suggested_by_id=user_id)
        if status:
            query = query.filter(status=status)
        return list(query.order_by('-created_at'))


def get_suggestion_service() -> SuggestionService:
    """Get suggestion service instance"""
    return SuggestionService()
