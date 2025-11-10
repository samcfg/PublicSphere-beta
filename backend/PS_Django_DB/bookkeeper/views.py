from rest_framework import generics, status
from rest_framework.decorators import api_view
from django.db import models
from django.utils.dateparse import parse_datetime
from common.api_standards import standard_response, StandardResponseMixin
from .models import ClaimVersion, SourceVersion, EdgeVersion, RatingVersion, CommentVersion
from .serializers import (
    ClaimVersionSerializer,
    SourceVersionSerializer,
    EdgeVersionSerializer,
    RatingVersionSerializer,
    CommentVersionSerializer,
)


class ClaimVersionListView(StandardResponseMixin, generics.ListAPIView):
    """
    GET /api/temporal/claims/<node_id>/versions/
    Returns all versions for a specific Claim node
    """
    serializer_class = ClaimVersionSerializer

    def get_queryset(self):
        node_id = self.kwargs['node_id']
        return ClaimVersion.objects.filter(node_id=node_id).order_by('version_number')


class SourceVersionListView(StandardResponseMixin, generics.ListAPIView):
    """
    GET /api/temporal/sources/<node_id>/versions/
    Returns all versions for a specific Source node
    """
    serializer_class = SourceVersionSerializer

    def get_queryset(self):
        node_id = self.kwargs['node_id']
        return SourceVersion.objects.filter(node_id=node_id).order_by('version_number')


class EdgeVersionListView(StandardResponseMixin, generics.ListAPIView):
    """
    GET /api/temporal/edges/<edge_id>/versions/
    Returns all versions for a specific Edge
    """
    serializer_class = EdgeVersionSerializer

    def get_queryset(self):
        edge_id = self.kwargs['edge_id']
        return EdgeVersion.objects.filter(edge_id=edge_id).order_by('version_number')


class RatingVersionListView(StandardResponseMixin, generics.ListAPIView):
    """
    GET /api/temporal/ratings/<rating_id>/versions/
    Returns all versions for a specific Rating
    """
    serializer_class = RatingVersionSerializer

    def get_queryset(self):
        rating_id = self.kwargs['rating_id']
        return RatingVersion.objects.filter(rating_id=rating_id).order_by('version_number')


class CommentVersionListView(StandardResponseMixin, generics.ListAPIView):
    """
    GET /api/temporal/comments/<comment_id>/versions/
    Returns all versions for a specific Comment
    """
    serializer_class = CommentVersionSerializer

    def get_queryset(self):
        comment_id = self.kwargs['comment_id']
        return CommentVersion.objects.filter(comment_id=comment_id).order_by('version_number')


@api_view(['GET'])
def graph_snapshot(request):
    """
    GET /api/temporal/snapshot/?timestamp=<ISO8601>
    Returns graph state at a specific point in time
    Query all nodes/edges valid at the timestamp (valid_from <= timestamp < valid_to)
    """
    timestamp_str = request.query_params.get('timestamp')
    if not timestamp_str:
        return standard_response(
            error='Missing required parameter: timestamp (ISO8601 format)',
            status_code=status.HTTP_400_BAD_REQUEST,
            source='temporal'
        )

    timestamp = parse_datetime(timestamp_str)
    if not timestamp:
        return standard_response(
            error='Invalid timestamp format. Use ISO8601 (e.g., 2024-01-15T10:30:00Z)',
            status_code=status.HTTP_400_BAD_REQUEST,
            source='temporal'
        )

    # Query all entities valid at this timestamp
    # valid_from <= timestamp AND (valid_to IS NULL OR valid_to > timestamp)
    claims = ClaimVersion.objects.filter(
        valid_from__lte=timestamp
    ).filter(
        models.Q(valid_to__isnull=True) | models.Q(valid_to__gt=timestamp)
    ).exclude(operation='DELETE')

    sources = SourceVersion.objects.filter(
        valid_from__lte=timestamp
    ).filter(
        models.Q(valid_to__isnull=True) | models.Q(valid_to__gt=timestamp)
    ).exclude(operation='DELETE')

    edges = EdgeVersion.objects.filter(
        valid_from__lte=timestamp
    ).filter(
        models.Q(valid_to__isnull=True) | models.Q(valid_to__gt=timestamp)
    ).exclude(operation='DELETE')

    return standard_response(data={
        'timestamp': timestamp_str,
        'claims': ClaimVersionSerializer(claims, many=True).data,
        'sources': SourceVersionSerializer(sources, many=True).data,
        'edges': EdgeVersionSerializer(edges, many=True).data,
    }, source='temporal')


@api_view(['GET'])
def entity_history(request):
    """
    GET /api/temporal/history/?entity_uuid=<uuid>&entity_type=<claim|source|connection>
    Returns complete edit history for any entity
    """
    entity_uuid = request.query_params.get('entity_uuid')
    entity_type = request.query_params.get('entity_type')

    if not entity_uuid or not entity_type:
        return standard_response(
            error='Missing required parameters: entity_uuid, entity_type',
            status_code=status.HTTP_400_BAD_REQUEST,
            source='temporal'
        )

    if entity_type == 'claim':
        versions = ClaimVersion.objects.filter(node_id=entity_uuid).order_by('version_number')
        serializer = ClaimVersionSerializer(versions, many=True)
    elif entity_type == 'source':
        versions = SourceVersion.objects.filter(node_id=entity_uuid).order_by('version_number')
        serializer = SourceVersionSerializer(versions, many=True)
    elif entity_type == 'connection':
        versions = EdgeVersion.objects.filter(edge_id=entity_uuid).order_by('version_number')
        serializer = EdgeVersionSerializer(versions, many=True)
    else:
        return standard_response(
            error='Invalid entity_type. Must be: claim, source, or connection',
            status_code=status.HTTP_400_BAD_REQUEST,
            source='temporal'
        )

    return standard_response(data={
        'entity_uuid': entity_uuid,
        'entity_type': entity_type,
        'versions': serializer.data,
    }, source='temporal')
