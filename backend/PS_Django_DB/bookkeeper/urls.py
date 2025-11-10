from django.urls import path
from . import views

urlpatterns = [
    # Version history endpoints for specific entities
    path('claims/<str:node_id>/versions/', views.ClaimVersionListView.as_view(), name='claim-versions'),
    path('sources/<str:node_id>/versions/', views.SourceVersionListView.as_view(), name='source-versions'),
    path('edges/<str:edge_id>/versions/', views.EdgeVersionListView.as_view(), name='edge-versions'),
    path('ratings/<int:rating_id>/versions/', views.RatingVersionListView.as_view(), name='rating-versions'),
    path('comments/<int:comment_id>/versions/', views.CommentVersionListView.as_view(), name='comment-versions'),

    # Temporal query endpoints
    path('snapshot/', views.graph_snapshot, name='graph-snapshot'),
    path('history/', views.entity_history, name='entity-history'),
]
