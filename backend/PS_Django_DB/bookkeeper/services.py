"""
Temporal query services for graph history reconstruction.
Passed to language.py
"""
from typing import List, Dict, Any
from datetime import datetime
from django.db.models import Q
from .models import ClaimVersion, SourceVersion, EdgeVersion


class TemporalQueryService:
    """Service for querying temporal graph snapshots"""

    def get_nodes_at_timestamp(self, timestamp: datetime) -> List[Dict[str, Any]]:
        """
        Get all nodes (Claims and Sources) that were valid at the given timestamp.

        A node is valid at timestamp T if:
        - valid_from <= T AND (valid_to > T OR valid_to IS NULL)

        Returns:
            List of dicts with structure:
            {
                'id': node_id (UUID),
                'label': node_label (e.g., 'Claim', 'Source'),
                'properties': {'content': '...', ...}
            }
        """
        nodes = []

        # Query for Claim nodes valid at timestamp
        claim_versions = ClaimVersion.objects.filter(
            Q(valid_from__lte=timestamp) &
            (Q(valid_to__gt=timestamp) | Q(valid_to__isnull=True))
        )

        for cv in claim_versions:
            node_dict = {
                'id': cv.node_id,
                'label': 'Claim',
                'properties': {}
            }
            if cv.content:
                node_dict['properties']['content'] = cv.content
            nodes.append(node_dict)

        # Query for Source nodes valid at timestamp
        source_versions = SourceVersion.objects.filter(
            Q(valid_from__lte=timestamp) &
            (Q(valid_to__gt=timestamp) | Q(valid_to__isnull=True))
        )

        for sv in source_versions:
            node_dict = {
                'id': sv.node_id,
                'label': 'Source',
                'properties': {}
            }
            # Add Source-specific properties if they exist
            if sv.url:
                node_dict['properties']['url'] = sv.url
            if sv.title:
                node_dict['properties']['title'] = sv.title
            if sv.author:
                node_dict['properties']['author'] = sv.author
            if sv.publication_date:
                node_dict['properties']['publication_date'] = sv.publication_date
            if sv.source_type:
                node_dict['properties']['source_type'] = sv.source_type
            if sv.content:
                node_dict['properties']['content'] = sv.content
            nodes.append(node_dict)

        return nodes

    def get_edges_at_timestamp(self, timestamp: datetime) -> List[Dict[str, Any]]:
        """
        Get all edges that were valid at the given timestamp.

        An edge is valid at timestamp T if:
        - valid_from <= T AND (valid_to > T OR valid_to IS NULL)

        Returns:
            List of dicts with structure:
            {
                'id': edge_id (UUID),
                'type': edge_type (e.g., 'Connection'),
                'source': source_node_id,
                'target': target_node_id,
                'properties': {'notes': '...', ...}
            }
        """
        # Query for edges valid at timestamp
        edge_versions = EdgeVersion.objects.filter(
            Q(valid_from__lte=timestamp) &
            (Q(valid_to__gt=timestamp) | Q(valid_to__isnull=True))
        )

        # Transform to dict format
        edges = []
        for ev in edge_versions:
            edge_dict = {
                'id': ev.edge_id,
                'type': ev.edge_type,
                'source': ev.source_node_id,
                'target': ev.target_node_id,
                'properties': {}
            }

            # Add properties if they exist
            if ev.notes:
                edge_dict['properties']['notes'] = ev.notes
            if ev.logic_type:
                edge_dict['properties']['logic_type'] = ev.logic_type
            if ev.composite_id:
                edge_dict['properties']['composite_id'] = ev.composite_id

            edges.append(edge_dict)

        return edges

    def get_graph_at_timestamp(self, timestamp: datetime) -> Dict[str, Any]:
        """
        Get complete graph state at timestamp.
        Returns both nodes and edges in a single dict.

        Returns:
            Dict with 'nodes' and 'edges' keys containing lists
        """
        return {
            'nodes': self.get_nodes_at_timestamp(timestamp),
            'edges': self.get_edges_at_timestamp(timestamp)
        }


# Global service instance (singleton pattern)
_temporal_service = None


def get_temporal_service() -> TemporalQueryService:
    """Get the global temporal query service instance"""
    global _temporal_service
    if _temporal_service is None:
        _temporal_service = TemporalQueryService()
    return _temporal_service
