from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from django.utils import timezone
from django.db.models import Avg, Count, F
from PS_Graph_DB.src.language import get_language_ops
from common.api_standards import standard_response
from users.models import UserAttribution
from social.models import ViewCount, Comment, Rating
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


def check_entity_ownership(entity_uuid, entity_type, user_id):
    """
    Verify that user owns the entity.

    Args:
        entity_uuid: UUID of the entity
        entity_type: 'claim' | 'source' | 'connection'
        user_id: User ID to check

    Returns bool
    """
    try:
        attribution = UserAttribution.objects.get(
            entity_uuid=entity_uuid,
            entity_type=entity_type
        )
        return attribution.user_id == user_id
    except UserAttribution.DoesNotExist:
        return False


def calculate_engagement(entity_uuid, entity_type):
    """
    Phase 3: Calculate engagement score for an entity.

    Formula: engagement = page_views + 5*comments + 15*connections + 3*rating_count*(avg_rating - 0.5)

    Notes:
    - Page views: Total view count (GDPR-compliant, no personal data)
    - Comments: Non-deleted comments only
    - Connections: Incoming connections to this node (for nodes only)
    - Ratings: 0-100 scale, avg_rating centered at 50
      - Negative ratings (avg < 50) reduce engagement → more edit time
      - Positive ratings (avg > 50) increase engagement → less edit time

    Args:
        entity_uuid: UUID of the entity
        entity_type: 'claim' | 'source' | 'connection'

    Returns:
        float: Engagement score
    """
    # Get view count
    try:
        view_count_obj = ViewCount.objects.get(entity_uuid=entity_uuid)
        page_views = view_count_obj.count
    except ViewCount.DoesNotExist:
        page_views = 0

    # Count non-deleted comments
    comments = Comment.objects.filter(
        entity_uuid=entity_uuid,
        is_deleted=False
    ).count()

    # Count incoming connections (only for nodes, not connections themselves)
    connections = 0
    if entity_type in ['claim', 'source']:
        # Query AGE for incoming connections
        try:
            from PS_Graph_DB.src.database import get_db
            db = get_db()
            # Count incoming edges: (other)-[r:Connection]->(n {id: entity_uuid})
            result = db.execute_cypher(
                'test_graph',
                f"""
                MATCH (other)-[r:Connection]->({entity_type.capitalize()} {{id: '{entity_uuid}'}})
                RETURN count(r) as connection_count
                """,
                ['connection_count']
            )
            if result and len(result) > 0:
                connections = result[0].get('connection_count', 0)
        except Exception:
            # If AGE query fails, default to 0 connections
            connections = 0

    # Aggregate ratings: count and average
    rating_stats = Rating.objects.filter(
        entity_uuid=entity_uuid
    ).aggregate(
        count=Count('id'),
        avg=Avg('score')
    )

    rating_count = rating_stats['count'] or 0
    avg_rating = rating_stats['avg'] or 50.0  # Default to neutral (50) if no ratings

    # Calculate engagement
    # Note: avg_rating is 0-100, normalize to 0-1 range, then center at 0.5
    # Ratings below 50 (avg < 0.5) reduce engagement (negative contribution) → more edit time
    # Ratings above 50 (avg > 0.5) increase engagement (positive contribution) → less edit time
    avg_rating_normalized = avg_rating / 100.0  # Convert 0-100 to 0-1
    rating_contribution = 3 * rating_count * (avg_rating_normalized - 0.5)

    engagement = (
        page_views +
        5 * comments +
        15 * connections +
        rating_contribution
    )

    return max(0, engagement)  # Ensure non-negative


def check_edit_time_window(entity_uuid, entity_type):
    """
    Phase 3: Check if entity is within editable time window with engagement reduction.

    Logic:
    - Grace period: First 1 hour always editable (regardless of engagement)
    - Base max: 720 hours (30 days)
    - Engagement reduction: Higher engagement → shorter window
      - Steep initial dropoff: Any engagement signals "in use"
      - Gradual later reduction: High engagement asymptotes to 24hr minimum
      - Formula: max_hours = max(24, 720 / (1 + engagement/5))

    Args:
        entity_uuid: UUID of the entity
        entity_type: 'claim' | 'source' | 'connection'

    Returns:
        tuple: (can_edit: bool, reason: str|None)
    """
    try:
        attribution = UserAttribution.objects.get(
            entity_uuid=entity_uuid,
            entity_type=entity_type
        )

        now = timezone.now()
        created_at = attribution.timestamp
        hours_elapsed = (now - created_at).total_seconds() / 3600

        # Grace period: first hour always editable
        if hours_elapsed < 1:
            return True, None

        # Calculate engagement-adjusted max window
        engagement = calculate_engagement(entity_uuid, entity_type)

        # Engagement-based reduction with steep initial dropoff
        # engagement=0: 720 hours (full 30 days)
        # engagement=5: 360 hours (15 days) - 50% reduction
        # engagement=25: 120 hours (5 days)
        # engagement=100: ~35 hours
        # engagement=∞: 24 hours (minimum)
        max_hours = max(24, 720 / (1 + engagement / 5))

        if hours_elapsed >= max_hours:
            return False, f"Edit window expired (engagement-adjusted: {max_hours:.1f}h limit)"

        return True, None

    except UserAttribution.DoesNotExist:
        return False, "Entity not found"


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

        # Check ownership
        if not check_entity_ownership(str(claim_id), 'claim', request.user.id):
            return standard_response(error='Only the creator can edit this claim', status_code=403, source='graph_db')

        # Check time window
        can_edit, reason = check_edit_time_window(str(claim_id), 'claim')
        if not can_edit:
            return standard_response(error=reason or 'Cannot edit this claim', status_code=403, source='graph_db')

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

        # Check ownership
        if not check_entity_ownership(str(claim_id), 'claim', request.user.id):
            return standard_response(error='Only the creator can delete this claim', status_code=403, source='graph_db')

        # Check time window
        can_edit, reason = check_edit_time_window(str(claim_id), 'claim')
        if not can_edit:
            return standard_response(error=reason or 'Cannot delete this claim', status_code=403, source='graph_db')

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

        # Check ownership
        if not check_entity_ownership(str(source_id), 'source', request.user.id):
            return standard_response(error='Only the creator can edit this source', status_code=403, source='graph_db')

        # Check time window
        can_edit, reason = check_edit_time_window(str(source_id), 'source')
        if not can_edit:
            return standard_response(error=reason or 'Cannot edit this source', status_code=403, source='graph_db')

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

        # Check ownership
        if not check_entity_ownership(str(source_id), 'source', request.user.id):
            return standard_response(error='Only the creator can delete this source', status_code=403, source='graph_db')

        # Check time window
        can_edit, reason = check_edit_time_window(str(source_id), 'source')
        if not can_edit:
            return standard_response(error=reason or 'Cannot delete this source', status_code=403, source='graph_db')

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
        return standard_response(error='Authentication required', status_code=401, source='graph_db')

    if request.method == 'PATCH':
        # Check ownership
        if not check_entity_ownership(str(connection_id), 'connection', request.user.id):
            return standard_response(error='Only the creator can edit this connection', status_code=403, source='graph_db')

        # Check time window
        can_edit, reason = check_edit_time_window(str(connection_id), 'connection')
        if not can_edit:
            return standard_response(error=reason or 'Cannot edit this connection', status_code=403, source='graph_db')

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
        # Check ownership
        if not check_entity_ownership(str(connection_id), 'connection', request.user.id):
            return standard_response(error='Only the creator can delete this connection', status_code=403, source='graph_db')

        # Check time window
        can_edit, reason = check_edit_time_window(str(connection_id), 'connection')
        if not can_edit:
            return standard_response(error=reason or 'Cannot delete this connection', status_code=403, source='graph_db')

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


@api_view(['POST'])
@permission_classes([AllowAny])  # Allow anonymous + authenticated users to track views
def track_page_view(request, entity_id):
    """
    POST: Track a page view for an entity.
    Body: { entity_type: 'claim' | 'source' | 'connection' }

    Simply increments a counter. GDPR-compliant (no personal data stored).
    """
    entity_type = request.data.get('entity_type', '').strip().lower()

    if not entity_type or entity_type not in ['claim', 'source', 'connection']:
        return standard_response(
            error='entity_type required (claim, source, or connection)',
            status_code=400,
            source='django'
        )

    try:
        # Get or create counter, increment atomically
        view_count, created = ViewCount.objects.get_or_create(
            entity_uuid=str(entity_id),
            entity_type=entity_type,
            defaults={'count': 0}
        )

        # Atomic increment
        ViewCount.objects.filter(entity_uuid=str(entity_id)).update(count=F('count') + 1)

        # Get updated count
        view_count.refresh_from_db()

        return standard_response(
            data={'count': view_count.count, 'created': created},
            source='django'
        )
    except Exception as e:
        return standard_response(error=str(e), status_code=500, source='django')


@api_view(['GET'])
def entity_engagement(request, entity_id):
    """
    GET: Calculate and return engagement metrics for an entity.
    Query params:
        - entity_type: 'claim' | 'source' | 'connection' (required)

    Returns:
        {
            engagement_score: float,
            components: {
                page_views: int,
                comments: int,
                connections: int,
                ratings: {count: int, avg: float, contribution: float}
            },
            edit_window: {
                max_hours: float,
                hours_elapsed: float,
                can_edit: bool,
                reason: str|null
            }
        }
    """
    entity_type = request.GET.get('entity_type', '').strip().lower()

    if not entity_type or entity_type not in ['claim', 'source', 'connection']:
        return standard_response(
            error='Query parameter "entity_type" required (claim, source, or connection)',
            status_code=400,
            source='django'
        )

    try:
        # Calculate engagement
        engagement = calculate_engagement(str(entity_id), entity_type)

        # Get components for display
        try:
            view_count_obj = ViewCount.objects.get(entity_uuid=str(entity_id))
            page_views = view_count_obj.count
        except ViewCount.DoesNotExist:
            page_views = 0

        comments = Comment.objects.filter(entity_uuid=str(entity_id), is_deleted=False).count()

        # Count connections
        connections = 0
        if entity_type in ['claim', 'source']:
            try:
                from PS_Graph_DB.src.database import get_db
                db = get_db()
                result = db.execute_cypher(
                    'test_graph',
                    f"""
                    MATCH (other)-[r:Connection]->({entity_type.capitalize()} {{id: '{entity_id}'}})
                    RETURN count(r) as connection_count
                    """,
                    ['connection_count']
                )
                if result and len(result) > 0:
                    connections = result[0].get('connection_count', 0)
            except Exception:
                connections = 0

        # Get rating stats
        rating_stats = Rating.objects.filter(entity_uuid=str(entity_id)).aggregate(
            count=Count('id'),
            avg=Avg('score')
        )
        rating_count = rating_stats['count'] or 0
        avg_rating = rating_stats['avg'] or 50.0
        avg_rating_normalized = avg_rating / 100.0
        rating_contribution = 3 * rating_count * (avg_rating_normalized - 0.5)

        # Get edit window info
        can_edit, reason = check_edit_time_window(str(entity_id), entity_type)

        # Calculate max hours
        max_hours = max(24, 720 / (1 + engagement / 5))

        # Calculate hours elapsed
        attribution = UserAttribution.objects.get(
            entity_uuid=str(entity_id),
            entity_type=entity_type
        )
        hours_elapsed = (timezone.now() - attribution.timestamp).total_seconds() / 3600

        return standard_response(
            data={
                'engagement_score': round(engagement, 2),
                'components': {
                    'page_views': page_views,
                    'comments': comments,
                    'connections': connections,
                    'ratings': {
                        'count': rating_count,
                        'avg': round(avg_rating, 1),
                        'contribution': round(rating_contribution, 2)
                    }
                },
                'edit_window': {
                    'max_hours': round(max_hours, 1),
                    'hours_elapsed': round(hours_elapsed, 1),
                    'can_edit': can_edit,
                    'reason': reason
                }
            },
            source='django'
        )
    except Exception as e:
        return standard_response(error=str(e), status_code=500, source='django')
