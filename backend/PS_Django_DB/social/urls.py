"""
URL routing for social API endpoints.
Maps /api/social/* paths to view classes.
"""
from django.urls import path
from social.views import (
    RateEntityView,
    EntityRatingsView,
    DeleteRatingView,
    CommentEntityView,
    EntityCommentsView,
    CommentDetailView,
    FlagEntityView,
    PendingFlagsView,
    ResolveFlagView,
    ControlversialEntitiesView,
    UserSocialContributionsView,
    ToggleSocialAnonymityView,
    CreateSuggestionView,
    EntitySuggestionsView,
    SuggestionDetailView,
    CheckSuggestionThresholdView,
)

app_name = 'social'

urlpatterns = [
    # Rating endpoints
    path('ratings/', RateEntityView.as_view(), name='rate_entity'),  # POST: create/update rating
    path('ratings/entity/', EntityRatingsView.as_view(), name='entity_ratings'),  # GET: aggregated ratings
    path('ratings/delete/', DeleteRatingView.as_view(), name='delete_rating'),  # DELETE: remove own rating

    # Comment endpoints
    path('comments/', CommentEntityView.as_view(), name='comment_entity'),  # POST: create comment
    path('comments/entity/', EntityCommentsView.as_view(), name='entity_comments'),  # GET: entity comments
    path('comments/<int:comment_id>/', CommentDetailView.as_view(), name='comment_detail'),  # PATCH/DELETE: update/delete comment

    # Moderation endpoints
    path('moderation/flag/', FlagEntityView.as_view(), name='flag_entity'),  # POST: flag content
    path('moderation/flags/pending/', PendingFlagsView.as_view(), name='pending_flags'),  # GET: pending flags
    path('moderation/flags/<int:flag_id>/resolve/', ResolveFlagView.as_view(), name='resolve_flag'),  # POST: resolve flag

    # Analytics endpoints
    path('controversial/', ControlversialEntitiesView.as_view(), name='controversial'),  # GET: controversial entities

    # User contributions
    path('contributions/', UserSocialContributionsView.as_view(), name='user_social_contributions'),  # GET: user's comments and ratings
    path('toggle-anonymity/', ToggleSocialAnonymityView.as_view(), name='toggle_social_anonymity'),  # POST: toggle anonymity for comments/ratings

    # Suggestion endpoints
    path('suggestions/', CreateSuggestionView.as_view(), name='create_suggestion'),  # POST: create suggestion
    path('suggestions/entity/', EntitySuggestionsView.as_view(), name='entity_suggestions'),  # GET: suggestions for entity
    path('suggestions/<uuid:suggestion_id>/', SuggestionDetailView.as_view(), name='suggestion_detail'),  # GET: suggestion detail
    path('suggestions/<uuid:suggestion_id>/check-threshold/', CheckSuggestionThresholdView.as_view(), name='check_suggestion_threshold'),  # GET: check if meets threshold
]
