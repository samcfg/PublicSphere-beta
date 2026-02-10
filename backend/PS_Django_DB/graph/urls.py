from django.urls import path
from . import views

urlpatterns = [
    # Claims endpoints
    path('claims/', views.claims_list, name='claims-list'),
    path('claims/<uuid:claim_id>/', views.claim_detail, name='claim-detail'),

    # Sources endpoints
    path('sources/', views.sources_list, name='sources-list'),
    path('sources/<uuid:source_id>/', views.source_detail, name='source-detail'),

    # Citation metadata fetching
    path('fetch-citation-metadata/', views.fetch_citation_metadata, name='fetch-citation-metadata'),

    # Connections endpoints
    path('connections/', views.connections_list, name='connections-list'),
    path('connections/<uuid:connection_id>/', views.connection_detail, name='connection-detail'),

    # Full graph endpoint (for Cytoscape visualization)
    path('graph/', views.graph_full, name='graph-full'),

    # Search endpoint
    path('search/', views.search_nodes, name='search-nodes'),

    # Engagement metrics endpoint
    path('engagement/<uuid:entity_id>/', views.entity_engagement, name='entity-engagement'),

    # Page view tracking endpoint
    path('pageview/<uuid:entity_id>/', views.track_page_view, name='track-page-view'),
]
