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

from bookkeeper.models import ClaimVersion, SourceVersion, EdgeVersion
from users.models import User, UserAttribution, UserModificationAttribution
from PS_Graph_DB.src.database import get_db


class TemporalLogger:
    """Logs all graph operations to relational tables for temporal reconstruction"""

    def log_node_version(self, graph_name: str, node_id: str, label: str,
                        properties: Dict[str, Any], operation: str,
                        changed_by: Optional[str] = None,
                        change_notes: Optional[str] = None,
                        user_id: Optional[int] = None) -> None:
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
            changed_by: Optional user identifier (deprecated, use user_id)
            change_notes: Optional notes about the change
            user_id: Optional User model ID for attribution tracking
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
                       r.notes as notes, r.logic_type as logic_type, r.composite_id as composite_id,
                       r.quote as quote
                """,
                ['edge_id', 'edge_type', 'source_id', 'target_id', 'notes', 'logic_type', 'composite_id', 'quote']
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
                if edge_data.get('quote'):
                    edge_properties['quote'] = edge_data['quote']
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

        # Dispatch to correct model based on node label
        if label == 'Claim':
            # For UPDATE or DELETE, close the previous version
            if operation in ('UPDATE', 'DELETE'):
                ClaimVersion.objects.filter(
                    node_id=node_id,
                    valid_to__isnull=True
                ).update(valid_to=timezone.now())

            # For CREATE and UPDATE, create new version
            if operation in ('CREATE', 'UPDATE'):
                # Get user instance if user_id provided
                user_instance = None
                if user_id is not None:
                    try:
                        user_instance = User.objects.get(id=user_id)
                    except User.DoesNotExist:
                        pass  # user_instance remains None if user not found

                # Calculate next version number
                if operation == 'CREATE':
                    version_num = 1
                else:  # UPDATE
                    # Get max version number for this entity
                    last_version = ClaimVersion.objects.filter(
                        node_id=node_id
                    ).order_by('-version_number').first()
                    version_num = (last_version.version_number + 1) if last_version else 1

                ClaimVersion.objects.create(
                    node_id=node_id,
                    version_number=version_num,
                    content=properties.get('content'),
                    operation=operation,
                    changed_by=changed_by,
                    change_notes=change_notes
                )

                # Create UserAttribution entry on CREATE only (tracks original creator)
                if operation == 'CREATE' and user_instance is not None:
                    UserAttribution.objects.create(
                        entity_uuid=node_id,
                        user=user_instance,
                        entity_type='claim',
                        is_anonymous=False  # Default to public, user can toggle later
                    )

                # Create UserModificationAttribution entry on UPDATE only (tracks editors)
                if operation == 'UPDATE' and user_instance is not None:
                    UserModificationAttribution.objects.create(
                        entity_uuid=node_id,
                        version_number=version_num,
                        user=user_instance,
                        entity_type='claim',
                        is_anonymous=False  # Default to public, user can toggle later
                    )

        elif label == 'Source':
            # For UPDATE or DELETE, close the previous version
            if operation in ('UPDATE', 'DELETE'):
                SourceVersion.objects.filter(
                    node_id=node_id,
                    valid_to__isnull=True
                ).update(valid_to=timezone.now())

            # For CREATE and UPDATE, create new version
            if operation in ('CREATE', 'UPDATE'):
                # Get user instance if user_id provided
                user_instance = None
                if user_id is not None:
                    try:
                        user_instance = User.objects.get(id=user_id)
                    except User.DoesNotExist:
                        pass  # user_instance remains None if user not found

                # Calculate next version number
                if operation == 'CREATE':
                    version_num = 1
                else:  # UPDATE
                    # Get max version number for this entity
                    last_version = SourceVersion.objects.filter(
                        node_id=node_id
                    ).order_by('-version_number').first()
                    version_num = (last_version.version_number + 1) if last_version else 1

                SourceVersion.objects.create(
                    node_id=node_id,
                    version_number=version_num,
                    # Required fields
                    title=properties.get('title'),
                    source_type=properties.get('source_type'),
                    # Universal optional fields
                    thumbnail_link=properties.get('thumbnail_link'),
                    authors=properties.get('authors'),
                    url=properties.get('url'),
                    accessed_date=properties.get('accessed_date'),
                    excerpt=properties.get('excerpt'),
                    content=properties.get('content'),
                    # Publication metadata
                    publication_date=properties.get('publication_date'),
                    container_title=properties.get('container_title'),
                    publisher=properties.get('publisher'),
                    publisher_location=properties.get('publisher_location'),
                    # Volume/Issue/Pages
                    volume=properties.get('volume'),
                    issue=properties.get('issue'),
                    pages=properties.get('pages'),
                    # Book-specific
                    edition=properties.get('edition'),
                    # Identifiers
                    doi=properties.get('doi'),
                    isbn=properties.get('isbn'),
                    issn=properties.get('issn'),
                    pmid=properties.get('pmid'),
                    pmcid=properties.get('pmcid'),
                    arxiv_id=properties.get('arxiv_id'),
                    handle=properties.get('handle'),
                    persistent_id=properties.get('persistent_id'),
                    persistent_id_type=properties.get('persistent_id_type'),
                    # Editors
                    editors=properties.get('editors'),
                    # Legal-specific
                    jurisdiction=properties.get('jurisdiction'),
                    legal_category=properties.get('legal_category'),
                    court=properties.get('court'),
                    decision_date=properties.get('decision_date'),
                    case_name=properties.get('case_name'),
                    code=properties.get('code'),
                    section=properties.get('section'),
                    # Metadata overflow
                    metadata=properties.get('metadata'),
                    # Operation tracking
                    operation=operation,
                    changed_by=changed_by,
                    change_notes=change_notes
                )

                # Create UserAttribution entry on CREATE only (tracks original creator)
                if operation == 'CREATE' and user_instance is not None:
                    UserAttribution.objects.create(
                        entity_uuid=node_id,
                        user=user_instance,
                        entity_type='source',
                        is_anonymous=False  # Default to public, user can toggle later
                    )

                # Create UserModificationAttribution entry on UPDATE only (tracks editors)
                if operation == 'UPDATE' and user_instance is not None:
                    UserModificationAttribution.objects.create(
                        entity_uuid=node_id,
                        version_number=version_num,
                        user=user_instance,
                        entity_type='source',
                        is_anonymous=False  # Default to public, user can toggle later
                    )

        else:
            raise ValueError(f"Unknown node label: {label}. Expected 'Claim' or 'Source'.")

    def log_edge_version(self, graph_name: str, edge_id: str, edge_type: str,
                        source_id: str, target_id: str,
                        properties: Dict[str, Any], operation: str,
                        changed_by: Optional[str] = None,
                        change_notes: Optional[str] = None,
                        user_id: Optional[int] = None) -> None:
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
            changed_by: Optional user identifier (deprecated, use user_id)
            change_notes: Optional notes about the change
            user_id: Optional User model ID for attribution tracking
        """
        # For UPDATE or DELETE, close the previous version
        if operation in ('UPDATE', 'DELETE'):
            EdgeVersion.objects.filter(
                edge_id=edge_id,
                valid_to__isnull=True
            ).update(valid_to=timezone.now())

        # For CREATE and UPDATE, create new version
        if operation in ('CREATE', 'UPDATE'):
            # Get user instance if user_id provided
            user_instance = None
            if user_id is not None:
                try:
                    user_instance = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    pass  # user_instance remains None if user not found

            # Calculate next version number
            if operation == 'CREATE':
                version_num = 1
            else:  # UPDATE
                # Get max version number for this entity
                last_version = EdgeVersion.objects.filter(
                    edge_id=edge_id
                ).order_by('-version_number').first()
                version_num = (last_version.version_number + 1) if last_version else 1

            EdgeVersion.objects.create(
                edge_id=edge_id,
                edge_type=edge_type,
                version_number=version_num,
                source_node_id=source_id,
                target_node_id=target_id,
                notes=properties.get('notes'),
                logic_type=properties.get('logic_type'),
                composite_id=properties.get('composite_id'),
                quote=properties.get('quote'),
                operation=operation,
                changed_by=changed_by,
                change_notes=change_notes
            )

            # Create UserAttribution entry on CREATE only (tracks original creator)
            if operation == 'CREATE' and user_instance is not None:
                UserAttribution.objects.create(
                    entity_uuid=edge_id,
                    user=user_instance,
                    entity_type='connection',
                    is_anonymous=False  # Default to public, user can toggle later
                )

            # Create UserModificationAttribution entry on UPDATE only (tracks editors)
            if operation == 'UPDATE' and user_instance is not None:
                UserModificationAttribution.objects.create(
                    entity_uuid=edge_id,
                    version_number=version_num,
                    user=user_instance,
                    entity_type='connection',
                    is_anonymous=False  # Default to public, user can toggle later
                )


# Global logger instance
temporal_logger = TemporalLogger()

def get_temporal_logger() -> TemporalLogger:
    """Get the global temporal logger instance"""
    return temporal_logger
