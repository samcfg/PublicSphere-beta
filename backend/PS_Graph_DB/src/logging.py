"""
Temporal logging
Tracks all node and edge changes in the relational database for temporal reconstruction.
"""
import os
import sys
import django
from typing import Dict, Any, Optional, List
from datetime import datetime
from django.utils import timezone

# Django setup for model access
django_path = os.path.join(os.path.dirname(__file__), '../../PS_Django_DB')
sys.path.insert(0, django_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from bookkeeper.models import NodeVersion, EdgeVersion
from PS_Graph_DB.src.database import get_db


class TemporalLogger:
    """Logs all graph operations to relational tables for temporal reconstruction"""

    def log_node_version(self, graph_name: str, node_id: str, label: str,
                        properties: Dict[str, Any], operation: str,
                        changed_by: Optional[str] = None,
                        change_notes: Optional[str] = None) -> None:
        """
        Log a node version to the temporal database.

        For CREATE: Insert new version with valid_to = NULL (open interval)
        For UPDATE: Close previous version, create new version with valid_to = NULL
        For DELETE: Query connected edges, log their deletions, then close node version

        Args:
            graph_name: Name of the graph to query (needed for DELETE cascade)
            node_id: UUID of the node
            label: Node label (e.g., 'Claim')
            properties: Dict of node properties (e.g., {'content': '...'})
            operation: 'CREATE', 'UPDATE', or 'DELETE'
            changed_by: Optional user identifier
            change_notes: Optional notes about the change
        """
        # For DELETE, log all connected edges first (cascade logging)
        if operation == 'DELETE':
            db = get_db()
            # Query for all edges connected to this node
            edges = db.execute_cypher(
                graph_name,
                f"""
                MATCH (n {{id: '{node_id}'}})-[r]-()
                RETURN r.id as edge_id, type(r) as edge_type,
                       startNode(r).id as source_id, endNode(r).id as target_id,
                       r.notes as notes, r.logic_type as logic_type, r.composite_id as composite_id
                """,
                ['edge_id', 'edge_type', 'source_id', 'target_id', 'notes', 'logic_type', 'composite_id']
            )
            # Log each edge deletion
            for edge_data in edges:
                edge_properties = {}
                if edge_data.get('notes'):
                    edge_properties['notes'] = edge_data['notes']
                if edge_data.get('logic_type'):
                    edge_properties['logic_type'] = edge_data['logic_type']
                if edge_data.get('composite_id'):
                    edge_properties['composite_id'] = edge_data['composite_id']
                self.log_edge_version(
                    graph_name=graph_name,
                    edge_id=edge_data['edge_id'],
                    edge_type=edge_data['edge_type'],
                    source_id=edge_data['source_id'],
                    target_id=edge_data['target_id'],
                    properties=edge_properties,
                    operation='DELETE',
                    changed_by=changed_by,
                    change_notes=f"Cascade delete from node {node_id}"
                )

        # For UPDATE or DELETE, close the previous version
        if operation in ('UPDATE', 'DELETE'):
            NodeVersion.objects.filter(
                node_id=node_id,
                valid_to__isnull=True
            ).update(valid_to=timezone.now())

        # For CREATE and UPDATE, create new version
        if operation in ('CREATE', 'UPDATE'):
            NodeVersion.objects.create(
                node_id=node_id,
                node_label=label,
                content=properties.get('content'),
                operation=operation,
                changed_by=changed_by,
                change_notes=change_notes
            )

    def log_edge_version(self, graph_name: str, edge_id: str, edge_type: str,
                        source_id: str, target_id: str,
                        properties: Dict[str, Any], operation: str,
                        changed_by: Optional[str] = None,
                        change_notes: Optional[str] = None) -> None:
        """
        Log an edge version to the temporal database.

        For CREATE: Insert new version with valid_to = NULL (open interval)
        For UPDATE: Close previous version, create new version with valid_to = NULL
        For DELETE: Close previous version only (no new record created)

        Args:
            graph_name: Name of the graph (for consistency with node logging)
            edge_id: UUID of the edge
            edge_type: Edge type (e.g., 'Connection')
            source_id: UUID of source node
            target_id: UUID of target node
            properties: Dict of edge properties (e.g., {'notes': '...'})
            operation: 'CREATE', 'UPDATE', or 'DELETE'
            changed_by: Optional user identifier
            change_notes: Optional notes about the change
        """
        # For UPDATE or DELETE, close the previous version
        if operation in ('UPDATE', 'DELETE'):
            EdgeVersion.objects.filter(
                edge_id=edge_id,
                valid_to__isnull=True
            ).update(valid_to=timezone.now())

        # For CREATE and UPDATE, create new version
        if operation in ('CREATE', 'UPDATE'):
            EdgeVersion.objects.create(
                edge_id=edge_id,
                edge_type=edge_type,
                source_node_id=source_id,
                target_node_id=target_id,
                notes=properties.get('notes'),
                logic_type=properties.get('logic_type'),
                composite_id=properties.get('composite_id'),
                operation=operation,
                changed_by=changed_by,
                change_notes=change_notes
            )


# Global logger instance
temporal_logger = TemporalLogger()

def get_temporal_logger() -> TemporalLogger:
    """Get the global temporal logger instance"""
    return temporal_logger
