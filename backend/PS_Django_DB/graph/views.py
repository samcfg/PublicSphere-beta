from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from PS_Graph_DB.src.language import get_language_ops
from common.api_standards import standard_response
from .serializers import (
    ClaimCreateSerializer,
    SourceCreateSerializer,
    ConnectionCreateSerializer,
    CompoundConnectionCreateSerializer,
    NodeUpdateSerializer,
    EdgeUpdateSerializer
)
from .services import DeduplicationService, SearchService


# Initialize language operations with graph
ops = get_language_ops()
ops.set_graph('test_graph')


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def claims_list(request):
    """
    GET: List all claims
    POST: Create a new claim
    """
    if request.method == 'GET':
        try:
            claims = ops.get_all_claims()
            return standard_response(data={'claims': claims}, source='graph_db')
        except Exception as e:
            return standard_response(error=str(e), status_code=500, source='graph_db')

    elif request.method == 'POST':
        serializer = ClaimCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return standard_response(error=serializer.errors, status_code=400, source='graph_db')

        # Check for duplicates before creation (Phase 2)
        content = serializer.validated_data.get('content')
        if content and content.strip():
            duplicate = DeduplicationService.check_duplicate_claim(content=content)
            if duplicate:
                return standard_response(
                    error=f"duplicate_{duplicate['duplicate_type']}",
                    data={
                        'existing_node_id': duplicate['existing_id'],
                        'existing_content': duplicate['existing_content'],
                        'similarity_score': duplicate.get('similarity_score'),
                    },
                    status_code=409,
                    source='graph_db'
                )

        try:
            user_id = request.user.id if request.user.is_authenticated else None
            claim_id = ops.create_claim(
                content=content,
                user_id=user_id
            )
            return standard_response(data={'id': claim_id}, status_code=201, source='graph_db')
        except Exception as e:
            return standard_response(error=str(e), status_code=500, source='graph_db')


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def claim_detail(request, claim_id):
    """
    GET: Retrieve claim connections
    PATCH: Update claim properties
    DELETE: Delete claim and its connections
    """
    if request.method == 'GET':
        try:
            connections = ops.get_node_connections(str(claim_id))
            return standard_response(data={'connections': connections}, source='graph_db')
        except Exception as e:
            return standard_response(error=str(e), status_code=500, source='graph_db')

    elif request.method == 'PATCH':
        if not request.user.is_authenticated:
            return standard_response(error='Authentication required', status_code=401, source='graph_db')

        try:
            user_id = request.user.id
            success = ops.edit_node(str(claim_id), user_id=user_id, **request.data)
            if success:
                return standard_response(data={'id': str(claim_id), 'updated': True}, source='graph_db')
            else:
                return standard_response(error='Claim not found', status_code=404, source='graph_db')
        except Exception as e:
            return standard_response(error=str(e), status_code=500, source='graph_db')

    elif request.method == 'DELETE':
        if not request.user.is_authenticated:
            return standard_response(error='Authentication required', status_code=401, source='graph_db')

        try:
            user_id = request.user.id
            success = ops.delete_node(str(claim_id), user_id=user_id)
            if success:
                return standard_response(data={'id': str(claim_id), 'deleted': True}, source='graph_db')
            else:
                return standard_response(error='Claim not found', status_code=404, source='graph_db')
        except Exception as e:
            return standard_response(error=str(e), status_code=500, source='graph_db')


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def sources_list(request):
    """
    GET: List all sources
    POST: Create a new source
    """
    if request.method == 'GET':
        try:
            sources = ops.get_all_sources()
            return standard_response(data={'sources': sources}, source='graph_db')
        except Exception as e:
            return standard_response(error=str(e), status_code=500, source='graph_db')

    elif request.method == 'POST':
        serializer = SourceCreateSerializer(data=request.data)
        if not serializer.is_valid():
            # Check if title validation failed and provide clear error message
            if 'title' in serializer.errors:
                return standard_response(
                    error='title_required',
                    message='Source title is required',
                    status_code=400,
                    source='graph_db'
                )
            return standard_response(error=serializer.errors, status_code=400, source='graph_db')

        # Check for duplicates before creation
        url = serializer.validated_data.get('url')
        title = serializer.validated_data.get('title')

        duplicate = DeduplicationService.check_duplicate_source(url=url, title=title)
        if duplicate:
            return standard_response(
                error=f"duplicate_{duplicate['duplicate_type']}",
                data={
                    'existing_node_id': duplicate['existing_id'],
                    'existing_title': duplicate['existing_title'],
                    'existing_url': duplicate.get('existing_url'),
                    'similarity_score': duplicate.get('similarity_score'),
                },
                status_code=409,
                source='graph_db'
            )

        try:
            user_id = request.user.id if request.user.is_authenticated else None
            source_id = ops.create_source(
                url=url,
                title=title,
                author=serializer.validated_data.get('author'),
                publication_date=serializer.validated_data.get('publication_date'),
                source_type=serializer.validated_data.get('source_type'),
                content=serializer.validated_data.get('content'),
                user_id=user_id
            )
            return standard_response(data={'id': source_id}, status_code=201, source='graph_db')
        except Exception as e:
            return standard_response(error=str(e), status_code=500, source='graph_db')


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def source_detail(request, source_id):
    """
    GET: Retrieve source connections
    PATCH: Update source properties
    DELETE: Delete source and its connections
    """
    if request.method == 'GET':
        try:
            connections = ops.get_node_connections(str(source_id))
            return standard_response(data={'connections': connections}, source='graph_db')
        except Exception as e:
            return standard_response(error=str(e), status_code=500, source='graph_db')

    elif request.method == 'PATCH':
        if not request.user.is_authenticated:
            return standard_response(error='Authentication required', status_code=401, source='graph_db')

        try:
            user_id = request.user.id
            success = ops.edit_node(str(source_id), user_id=user_id, **request.data)
            if success:
                return standard_response(data={'id': str(source_id), 'updated': True}, source='graph_db')
            else:
                return standard_response(error='Source not found', status_code=404, source='graph_db')
        except Exception as e:
            return standard_response(error=str(e), status_code=500, source='graph_db')

    elif request.method == 'DELETE':
        if not request.user.is_authenticated:
            return standard_response(error='Authentication required', status_code=401, source='graph_db')

        try:
            user_id = request.user.id
            success = ops.delete_node(str(source_id), user_id=user_id)
            if success:
                return standard_response(data={'id': str(source_id), 'deleted': True}, source='graph_db')
            else:
                return standard_response(error='Source not found', status_code=404, source='graph_db')
        except Exception as e:
            return standard_response(error=str(e), status_code=500, source='graph_db')


@api_view(['POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def connections_list(request):
    """
    POST: Create a new connection (single or compound)
    """
    # Check if compound connection request
    if 'source_node_ids' in request.data:
        serializer = CompoundConnectionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return standard_response(error=serializer.errors, status_code=400, source='graph_db')

        try:
            user_id = request.user.id if request.user.is_authenticated else None
            composite_id = ops.create_compound_connection(
                source_node_ids=[str(sid) for sid in serializer.validated_data['source_node_ids']],
                target_node_id=str(serializer.validated_data['target_node_id']),
                logic_type=serializer.validated_data['logic_type'],
                notes=serializer.validated_data.get('notes'),
                composite_id=str(serializer.validated_data['composite_id']) if serializer.validated_data.get('composite_id') else None,
                user_id=user_id
            )
            return standard_response(data={'composite_id': composite_id}, status_code=201, source='graph_db')
        except Exception as e:
            return standard_response(error=str(e), status_code=500, source='graph_db')

    # Single connection
    else:
        serializer = ConnectionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return standard_response(error=serializer.errors, status_code=400, source='graph_db')

        try:
            user_id = request.user.id if request.user.is_authenticated else None
            connection_id = ops.create_connection(
                from_node_id=str(serializer.validated_data['from_node_id']),
                to_node_id=str(serializer.validated_data['to_node_id']),
                notes=serializer.validated_data.get('notes'),
                logic_type=serializer.validated_data.get('logic_type'),
                composite_id=str(serializer.validated_data['composite_id']) if serializer.validated_data.get('composite_id') else None,
                user_id=user_id
            )
            return standard_response(data={'id': connection_id}, status_code=201, source='graph_db')
        except Exception as e:
            return standard_response(error=str(e), status_code=500, source='graph_db')


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def connection_detail(request, connection_id):
    """
    PATCH: Update connection properties (supports individual or composite_id)
    DELETE: Delete connection (supports individual or composite_id)
    """
    if not request.user.is_authenticated:
        return _standard_response(error='Authentication required', status_code=401, source='graph_db')

    if request.method == 'PATCH':
        try:
            user_id = request.user.id
            success = ops.edit_edge(str(connection_id), user_id=user_id, **request.data)
            if success:
                return standard_response(data={'id': str(connection_id), 'updated': True}, source='graph_db')
            else:
                return standard_response(error='Connection not found', status_code=404, source='graph_db')
        except Exception as e:
            return standard_response(error=str(e), status_code=500, source='graph_db')

    elif request.method == 'DELETE':
        try:
            user_id = request.user.id
            success = ops.delete_edge(str(connection_id), user_id=user_id)
            if success:
                return standard_response(data={'id': str(connection_id), 'deleted': True}, source='graph_db')
            else:
                return standard_response(error='Connection not found', status_code=404, source='graph_db')
        except Exception as e:
            return standard_response(error=str(e), status_code=500, source='graph_db')


@api_view(['GET'])
def graph_full(request):
    """
    GET: Retrieve complete graph (all claims, sources, and connections)
    Returns raw AGE format for frontend formatting
    """
    try:
        claims = ops.get_all_claims()
        sources = ops.get_all_sources()

        # Get all connections by querying each node
        # This is inefficient but works with current language.py API
        # TODO: Add get_all_connections() method to language.py
        edges = []
        all_node_ids = [c['claim']['properties']['id'] for c in claims] + \
                       [s['source']['properties']['id'] for s in sources]

        seen_edges = set()
        for node_id in all_node_ids:
            connections = ops.get_node_connections(node_id)
            for conn in connections:
                edge_id = conn.get('connection', {}).get('properties', {}).get('id')
                if edge_id and edge_id not in seen_edges:
                    edges.append(conn)
                    seen_edges.add(edge_id)

        return standard_response(data={
            'claims': claims,
            'sources': sources,
            'edges': edges
        }, source='graph_db')
    except Exception as e:
        return _standard_response(error=str(e), status_code=500, source='graph_db')


@api_view(['GET'])
def search_nodes(request):
    """
    GET: Search nodes by content (Phase 3 - full-text search)
    Query params:
        - q: search query string (required)
        - type: 'claim' or 'source' to filter by node type (optional)
    """
    query = request.GET.get('q', '').strip()
    node_type = request.GET.get('type', '').strip().lower()

    if not query:
        return standard_response(error='Query parameter "q" is required', status_code=400, source='graph_db')

    # Validate node_type if provided
    if node_type and node_type not in ['claim', 'source']:
        return standard_response(error='Invalid type parameter. Must be "claim" or "source"', status_code=400, source='graph_db')

    try:
        # Use Django SearchService instead of AGE (Phase 3)
        results = SearchService.search_nodes(query=query, node_type=node_type if node_type else None)
        return standard_response(data={'results': results}, source='django')
    except Exception as e:
        return standard_response(error=str(e), status_code=500, source='django')
