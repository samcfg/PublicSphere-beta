"""
DRF API views for social interactions.
Wraps services.py business logic with REST endpoints.
"""
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django.shortcuts import get_object_or_404

from social.models import Comment, FlaggedContent, SuggestedEdit
from social.serializers import (
    RatingSerializer,
    RatingCreateSerializer,
    RatingAggregateSerializer,
    CommentSerializer,
    CommentCreateSerializer,
    CommentUpdateSerializer,
    FlagSerializer,
    FlagCreateSerializer,
    FlagResolveSerializer,
    SuggestedEditSerializer,
    SuggestedEditCreateSerializer,
)
from social.services import (
    RatingService,
    CommentService,
    ModerationService,
    SocialAnonymityService,
    SuggestionService,
)
from common.api_standards import standard_response


class RateEntityView(APIView):
    """
    Create or update a rating.
    POST /api/social/ratings/
    Body: {entity_uuid, entity_type, dimension, score}
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = RatingCreateSerializer(data=request.data)
        if serializer.is_valid():
            rating_service = RatingService()
            rating = rating_service.rate_entity(
                user_id=request.user.id,
                entity_uuid=serializer.validated_data['entity_uuid'],
                entity_type=serializer.validated_data['entity_type'],
                score=serializer.validated_data['score'],
                dimension=serializer.validated_data.get('dimension')
            )
            response_serializer = RatingSerializer(rating)
            return standard_response(
                data=response_serializer.data,
                status_code=status.HTTP_201_CREATED,
                source='social'
            )
        return standard_response(
            error={'code': 'validation_error', 'message': serializer.errors},
            status_code=status.HTTP_400_BAD_REQUEST,
            source='social'
        )


class EntityRatingsView(APIView):
    """
    Get aggregated ratings for an entity.
    GET /api/social/ratings/?entity=<uuid>&dimension=<confidence|relevance>
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        entity_uuid = request.query_params.get('entity')
        dimension = request.query_params.get('dimension')

        if not entity_uuid:
            return standard_response(
                error={'code': 'missing_parameter', 'message': 'entity parameter is required'},
                status_code=status.HTTP_400_BAD_REQUEST,
                source='social'
            )

        rating_service = RatingService()
        user_id = request.user.id if request.user.is_authenticated else None
        aggregates = rating_service.get_entity_ratings(entity_uuid, dimension, user_id)

        serializer = RatingAggregateSerializer(aggregates)
        return standard_response(data=serializer.data, source='social')


class DeleteRatingView(APIView):
    """
    Delete user's own rating.
    DELETE /api/social/ratings/?entity=<uuid>&entity_type=<type>&dimension=<dimension>
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        entity_uuid = request.query_params.get('entity')
        entity_type = request.query_params.get('entity_type')
        dimension = request.query_params.get('dimension')

        if not entity_uuid or not entity_type:
            return Response({
                'data': None,
                'meta': {'source': 'social'},
                'error': {'code': 'missing_parameter', 'message': 'entity and entity_type parameters are required'}
            }, status=status.HTTP_400_BAD_REQUEST)

        rating_service = RatingService()
        success = rating_service.delete_rating(
            user_id=request.user.id,
            entity_uuid=entity_uuid,
            entity_type=entity_type,
            dimension=dimension
        )

        if success:
            return standard_response(data={'deleted': True}, source='social')
        else:
            return standard_response(
                error={'code': 'not_found', 'message': 'Rating not found'},
                status_code=status.HTTP_404_NOT_FOUND,
                source='social'
            )


class CommentEntityView(APIView):
    """
    Create a comment.
    POST /api/social/comments/
    Body: {entity_uuid, entity_type, content, parent_comment (optional)}
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CommentCreateSerializer(data=request.data)
        if serializer.is_valid():
            comment_service = CommentService()
            comment = comment_service.create_comment(
                user_id=request.user.id,
                entity_uuid=serializer.validated_data['entity_uuid'],
                entity_type=serializer.validated_data['entity_type'],
                content=serializer.validated_data['content'],
                parent_comment_id=serializer.validated_data.get('parent_comment').id if serializer.validated_data.get('parent_comment') else None
            )
            response_serializer = CommentSerializer(comment, context={'request': request})
            return standard_response(
                data=response_serializer.data,
                status_code=status.HTTP_201_CREATED,
                source='social'
            )
        return standard_response(
            error={'code': 'validation_error', 'message': serializer.errors},
            status_code=status.HTTP_400_BAD_REQUEST,
            source='social'
        )


class EntityCommentsView(APIView):
    """
    Get all comments for an entity.
    GET /api/social/comments/?entity=<uuid>
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        entity_uuid = request.query_params.get('entity')
        sort = request.query_params.get('sort', 'timestamp')

        if not entity_uuid:
            return standard_response(
                error={'code': 'missing_parameter', 'message': 'entity parameter is required'},
                status_code=status.HTTP_400_BAD_REQUEST,
                source='social'
            )

        # Validate sort parameter
        if sort not in ['timestamp', 'score']:
            sort = 'timestamp'

        comment_service = CommentService()
        comments = comment_service.get_entity_comments(entity_uuid, include_deleted=False, sort=sort)

        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return standard_response(data=serializer.data, source='social')


class CommentDetailView(APIView):
    """
    Update or delete a specific comment.
    PATCH /api/social/comments/<id>/ - Update content (own comment only)
    DELETE /api/social/comments/<id>/ - Soft delete (own comment or moderator)
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, comment_id):
        """Update comment content (own comment only)"""
        serializer = CommentUpdateSerializer(data=request.data)
        if serializer.is_valid():
            comment_service = CommentService()
            comment = comment_service.update_comment(
                comment_id=comment_id,
                user_id=request.user.id,
                new_content=serializer.validated_data['content']
            )
            if comment:
                response_serializer = CommentSerializer(comment, context={'request': request})
                return standard_response(data=response_serializer.data, source='social')
            else:
                return standard_response(
                    error={'code': 'not_found', 'message': 'Comment not found or unauthorized'},
                    status_code=status.HTTP_404_NOT_FOUND,
                    source='social'
                )
        return standard_response(
            error={'code': 'validation_error', 'message': serializer.errors},
            status_code=status.HTTP_400_BAD_REQUEST,
            source='social'
        )

    def delete(self, request, comment_id):
        """Soft delete comment (own comment or moderator)"""
        comment_service = CommentService()
        is_moderator = request.user.groups.filter(name__in=['Moderator', 'Admin']).exists() or request.user.is_staff

        success = comment_service.soft_delete_comment(
            comment_id=comment_id,
            user_id=request.user.id,
            is_moderator=is_moderator
        )

        if success:
            return standard_response(data={'deleted': True}, source='social')
        else:
            return Response({
                'data': None,
                'meta': {'source': 'social'},
                'error': {'code': 'not_found', 'message': 'Comment not found or unauthorized'}
            }, status=status.HTTP_404_NOT_FOUND)


class FlagEntityView(APIView):
    """
    Flag content for moderation review.
    POST /api/social/moderation/flag/
    Body: {entity_uuid, entity_type, reason}
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Verify user has moderator permissions
        is_moderator = request.user.groups.filter(name__in=['Moderator', 'Admin']).exists() or request.user.is_staff
        if not is_moderator:
            return standard_response(
                error={'code': 'permission_denied', 'message': 'Moderator permissions required'},
                status_code=status.HTTP_403_FORBIDDEN,
                source='social'
            )

        serializer = FlagCreateSerializer(data=request.data)
        if serializer.is_valid():
            moderation_service = ModerationService()
            flag = moderation_service.flag_entity(
                flagged_by_id=request.user.id,
                entity_uuid=serializer.validated_data['entity_uuid'],
                entity_type=serializer.validated_data['entity_type'],
                reason=serializer.validated_data['reason']
            )
            response_serializer = FlagSerializer(flag)
            return standard_response(
                data=response_serializer.data,
                status_code=status.HTTP_201_CREATED,
                source='social'
            )
        return standard_response(
            error={'code': 'validation_error', 'message': serializer.errors},
            status_code=status.HTTP_400_BAD_REQUEST,
            source='social'
        )


class PendingFlagsView(ListAPIView):
    """
    Get all pending moderation flags.
    GET /api/social/moderation/flags/pending/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FlagSerializer

    def get_queryset(self):
        # Verify user has moderator permissions
        is_moderator = self.request.user.groups.filter(name__in=['Moderator', 'Admin']).exists() or self.request.user.is_staff
        if not is_moderator:
            return FlaggedContent.objects.none()

        moderation_service = ModerationService()
        return moderation_service.get_pending_flags()

    def list(self, request, *args, **kwargs):
        """Wrap response in standard format"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return standard_response(data=serializer.data, source='social')


class ResolveFlagView(APIView):
    """
    Resolve a moderation flag (staff admin only).
    POST /api/social/moderation/flags/<id>/resolve/
    Body: {status: 'reviewed'|'action_taken'|'dismissed', resolution_notes (optional)}
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, flag_id):
        # Verify user has staff admin permissions
        if not request.user.is_staff:
            return standard_response(
                error={'code': 'permission_denied', 'message': 'Staff admin permissions required'},
                status_code=status.HTTP_403_FORBIDDEN,
                source='social'
            )

        serializer = FlagResolveSerializer(data=request.data)
        if serializer.is_valid():
            moderation_service = ModerationService()
            flag = moderation_service.resolve_flag(
                flag_id=flag_id,
                reviewed_by_id=request.user.id,
                status=serializer.validated_data['status'],
                resolution_notes=serializer.validated_data.get('resolution_notes', '')
            )
            if flag:
                response_serializer = FlagSerializer(flag)
                return standard_response(data=response_serializer.data, source='social')
            else:
                return standard_response(
                    error={'code': 'not_found', 'message': 'Flag not found'},
                    status_code=status.HTTP_404_NOT_FOUND,
                    source='social'
                )
        return standard_response(
            error={'code': 'validation_error', 'message': serializer.errors},
            status_code=status.HTTP_400_BAD_REQUEST,
            source='social'
        )


class ControlversialEntitiesView(APIView):
    """
    Get entities with high rating variance (controversial).
    GET /api/social/controversial/?limit=50
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        limit = int(request.query_params.get('limit', 50))
        limit = min(limit, 200)  # Cap at 200

        rating_service = RatingService()
        controversial = rating_service.get_controversial_entities(limit=limit)

        return standard_response(data=controversial, source='social')


class UserSocialContributionsView(APIView):
    """
    Get authenticated user's social contributions (comments and ratings).
    GET /api/social/contributions/
    Returns: {comments: [...], ratings: [...]}
    Format matches /api/users/contributions/list/ for consistency
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        comment_service = CommentService()
        rating_service = RatingService()

        # Get user's comments (exclude soft-deleted)
        comments = comment_service.get_user_comments(request.user.id, include_deleted=False)

        # Get user's ratings
        ratings = rating_service.get_user_ratings(request.user.id)

        # Format comments similarly to graph contributions
        comments_data = []
        for comment in comments:
            comments_data.append({
                'id': comment.id,
                'entity_uuid': comment.entity_uuid,
                'entity_type': comment.entity_type,
                'content': comment.content,
                'parent_comment': comment.parent_comment_id,
                'is_anonymous': comment.is_anonymous,
                'created_at': comment.timestamp.isoformat(),
            })

        # Format ratings similarly to graph contributions
        ratings_data = []
        for rating in ratings:
            ratings_data.append({
                'id': rating.id,
                'entity_uuid': rating.entity_uuid,
                'entity_type': rating.entity_type,
                'dimension': rating.dimension,
                'score': rating.score,
                'is_anonymous': rating.is_anonymous,
                'created_at': rating.timestamp.isoformat(),
            })

        return standard_response(
            data={
                'comments': comments_data,
                'ratings': ratings_data,
            },
            source='social'
        )


class ToggleSocialAnonymityView(APIView):
    """
    Toggle anonymity for user's social contributions (comments/ratings).
    POST /api/social/toggle-anonymity/
    Body: {entity_id: int, entity_type: 'comment'|'rating'}
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        entity_id = request.data.get('entity_id')
        entity_type = request.data.get('entity_type')

        if not entity_id or not entity_type:
            return standard_response(
                error={'code': 'validation_error', 'message': 'entity_id and entity_type are required'},
                status_code=status.HTTP_400_BAD_REQUEST,
                source='social'
            )

        if entity_type not in ['comment', 'rating']:
            return standard_response(
                error={'code': 'validation_error', 'message': 'entity_type must be comment or rating'},
                status_code=status.HTTP_400_BAD_REQUEST,
                source='social'
            )

        anonymity_service = SocialAnonymityService()

        if entity_type == 'comment':
            success = anonymity_service.toggle_comment_anonymity(entity_id, request.user.id)
        else:  # rating
            success = anonymity_service.toggle_rating_anonymity(entity_id, request.user.id)

        if success:
            return standard_response(
                data={'toggled': True},
                source='social'
            )
        else:
            return standard_response(
                error={'code': 'not_found', 'message': 'Entity not found or unauthorized'},
                status_code=status.HTTP_404_NOT_FOUND,
                source='social'
            )


class CreateSuggestionView(APIView):
    """
    Create a suggested edit for a node.
    POST /api/social/suggestions/
    Body: {entity_uuid, entity_type, proposed_changes, rationale}
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SuggestedEditCreateSerializer(data=request.data)
        if serializer.is_valid():
            suggestion_service = SuggestionService()
            suggestion = suggestion_service.create_suggestion(
                user_id=request.user.id,
                entity_uuid=serializer.validated_data['entity_uuid'],
                entity_type=serializer.validated_data['entity_type'],
                proposed_changes=serializer.validated_data['proposed_changes'],
                rationale=serializer.validated_data['rationale']
            )
            response_serializer = SuggestedEditSerializer(suggestion)
            return standard_response(
                data=response_serializer.data,
                status_code=status.HTTP_201_CREATED,
                source='social'
            )
        return standard_response(
            error={'code': 'validation_error', 'message': serializer.errors},
            status_code=status.HTTP_400_BAD_REQUEST,
            source='social'
        )


class EntitySuggestionsView(APIView):
    """
    Get all suggestions for an entity.
    GET /api/social/suggestions/?entity=<uuid>&status=<pending|accepted|rejected>
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        entity_uuid = request.query_params.get('entity')
        status_filter = request.query_params.get('status')

        if not entity_uuid:
            return standard_response(
                error={'code': 'missing_parameter', 'message': 'entity parameter is required'},
                status_code=status.HTTP_400_BAD_REQUEST,
                source='social'
            )

        # Validate status if provided
        if status_filter and status_filter not in ['pending', 'accepted', 'rejected']:
            return standard_response(
                error={'code': 'validation_error', 'message': 'status must be pending, accepted, or rejected'},
                status_code=status.HTTP_400_BAD_REQUEST,
                source='social'
            )

        suggestion_service = SuggestionService()
        suggestions = suggestion_service.get_entity_suggestions(entity_uuid, status=status_filter)

        serializer = SuggestedEditSerializer(suggestions, many=True)
        return standard_response(data=serializer.data, source='social')


class SuggestionDetailView(APIView):
    """
    Get details of a specific suggestion.
    GET /api/social/suggestions/<suggestion_id>/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, suggestion_id):
        suggestion_service = SuggestionService()
        suggestion = suggestion_service.get_suggestion(str(suggestion_id))

        if not suggestion:
            return standard_response(
                error={'code': 'not_found', 'message': 'Suggestion not found'},
                status_code=status.HTTP_404_NOT_FOUND,
                source='social'
            )

        serializer = SuggestedEditSerializer(suggestion)
        return standard_response(data=serializer.data, source='social')


class CheckSuggestionThresholdView(APIView):
    """
    Check if a suggestion meets acceptance threshold.
    GET /api/social/suggestions/<suggestion_id>/check-threshold/
    Returns: {can_accept: bool, reason: str|null, rating_stats: {...}}
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, suggestion_id):
        suggestion_service = SuggestionService()
        suggestion = suggestion_service.get_suggestion(str(suggestion_id))

        if not suggestion:
            return standard_response(
                error={'code': 'not_found', 'message': 'Suggestion not found'},
                status_code=status.HTTP_404_NOT_FOUND,
                source='social'
            )

        # Calculate engagement for target node
        from graph.views import calculate_engagement
        engagement = calculate_engagement(suggestion.entity_uuid, suggestion.entity_type)

        # Check threshold
        can_accept, reason = suggestion_service.check_acceptance_threshold(
            str(suggestion_id),
            engagement
        )

        # Get rating stats
        from django.db.models import Avg, Count
        from social.models import Rating
        stats = Rating.objects.filter(
            entity_uuid=str(suggestion_id),
            entity_type='suggested_edit'
        ).aggregate(
            count=Count('id'),
            avg=Avg('score')
        )

        return standard_response(
            data={
                'can_accept': can_accept,
                'reason': reason,
                'rating_stats': {
                    'count': stats['count'] or 0,
                    'avg': round(stats['avg'], 1) if stats['avg'] is not None else None
                },
                'node_engagement': round(engagement, 2)
            },
            source='social'
        )
