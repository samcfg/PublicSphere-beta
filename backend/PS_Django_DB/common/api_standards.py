"""
Standardized API response formatting for all DRF endpoints.
Ensures consistent {data, meta, error} structure across graph/users/social/bookkeeper apps.
"""
from rest_framework import status
from rest_framework.response import Response
from django.utils import timezone


def standard_response(data=None, error=None, status_code=200, source='api'):
    """
    Standard API response envelope.

    Args:
        data: Response payload (dict, list, or None)
        error: Error message/dict (None for success)
        status_code: HTTP status code
        source: API source identifier ('graph_db', 'users', 'social', 'temporal')

    Returns:
        Response with format: {data: ..., meta: {timestamp, source}, error: ...}
    """
    return Response({
        'data': data,
        'meta': {
            'timestamp': timezone.now().isoformat(),
            'source': source
        },
        'error': error
    }, status=status_code)


class StandardResponseMixin:
    """
    Mixin for DRF generic views to automatically wrap responses in standard format.
    Overrides retrieve(), list(), create(), update(), destroy() methods.
    """

    def get_source_name(self):
        """Override in view to specify source name (defaults to app label)"""
        return getattr(self, 'source_name', self.request.resolver_match.app_name or 'api')

    def retrieve(self, request, *args, **kwargs):
        """GET single object - wrap in standard response"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return standard_response(
            data=serializer.data,
            source=self.get_source_name()
        )

    def list(self, request, *args, **kwargs):
        """GET list of objects - wrap in standard response with count"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return standard_response(
            data=serializer.data,
            source=self.get_source_name()
        )

    def create(self, request, *args, **kwargs):
        """POST create object - wrap in standard response"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return standard_response(
                data=serializer.data,
                status_code=status.HTTP_201_CREATED,
                source=self.get_source_name()
            )
        return standard_response(
            error=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST,
            source=self.get_source_name()
        )

    def update(self, request, *args, **kwargs):
        """PUT/PATCH update object - wrap in standard response"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid():
            self.perform_update(serializer)
            return standard_response(
                data=serializer.data,
                source=self.get_source_name()
            )
        return standard_response(
            error=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST,
            source=self.get_source_name()
        )

    def destroy(self, request, *args, **kwargs):
        """DELETE object - wrap in standard response"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return standard_response(
            data={'deleted': True},
            status_code=status.HTTP_204_NO_CONTENT,
            source=self.get_source_name()
        )
