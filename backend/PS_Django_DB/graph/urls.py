from django.urls import path
from . import views

urlpatterns = [
    # Claims endpoints
    path('claims/', views.claims_list, name='claims-list'),
    path('claims/<uuid:claim_id>/', views.claim_detail, name='claim-detail'),

    # Sources endpoints
    path('sources/', views.sources_list, name='sources-list'),
    path('sources/<uuid:source_id>/', views.source_detail, name='source-detail'),

    # Connections endpoints
    path('connections/', views.connections_list, name='connections-list'),
    path('connections/<uuid:connection_id>/', views.connection_detail, name='connection-detail'),

    # Full graph endpoint (for Cytoscape visualization)
    path('graph/', views.graph_full, name='graph-full'),

    # Search endpoint
    path('search/', views.search_nodes, name='search-nodes'),
]
