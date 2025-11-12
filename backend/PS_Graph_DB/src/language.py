from typing import Dict, List, Optional, Any
from datetime import datetime
from PS_Graph_DB.src.database import get_db
from PS_Graph_DB.src.logging import get_temporal_logger
import uuid
import os
import sys
import django

# Django setup for temporal service access
django_path = os.path.join(os.path.dirname(__file__), '../../PS_Django_DB')
sys.path.insert(0, django_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from bookkeeper.services import get_temporal_service

class LanguageOperations:
    """Data operations for Claims and Connections"""

    def __init__(self):
        self.current_graph = None

    def _escape_cypher_string(self, value: str) -> str:
        """
        Escape string for safe Cypher interpolation.
        Prevents injection by escaping special characters.
        Order matters: backslash must be escaped first.

        Args:
            value: String to escape (can be None)

        Returns:
            Escaped string safe for Cypher query interpolation, or None if input is None
        """
        if value is None:
            return None
        # Escape backslashes first, then other special chars
        return (value
                .replace('\\', '\\\\')  # Escape backslashes first (prevents double-escape exploits)
                .replace("'", "\\'")     # Escape single quotes
                .replace('\n', '\\n')    # Escape newlines
                .replace('\r', '\\r'))   # Escape carriage returns

    def _execute_with_logging(self,
                             cypher_query: str,
                             columns: List[str],
                             entity_type: str,
                             operation: str,
                             entity_id: str,
                             label_or_type: str,
                             properties: Dict[str, Any],
                             source_id: Optional[str] = None,
                             target_id: Optional[str] = None,
                             changed_by: Optional[str] = None,
                             change_notes: Optional[str] = None,
                             user_id: Optional[int] = None) -> List[Dict]:
        """
        Execute Cypher with atomic logging.
        Both graph operation and version logging succeed or both rollback.

        For DELETE: log first (logger queries graph), then execute
        For CREATE/UPDATE: execute first, then log
        """
        db = get_db()
        logger = get_temporal_logger()

        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                # Set up AGE environment for this cursor
                cursor.execute("LOAD 'age'")
                cursor.execute("SET search_path = ag_catalog, '$user', public")

                try:
                    # For DELETE: log BEFORE cypher (logger needs to query intact graph)
                    if operation == 'DELETE':
                        if entity_type == 'node':
                            logger.log_node_version(
                                graph_name=self.current_graph,
                                node_id=entity_id,
                                label=label_or_type,
                                properties=properties,
                                operation=operation,
                                changed_by=changed_by,
                                change_notes=change_notes,
                                user_id=user_id
                            )
                        elif entity_type == 'edge':
                            logger.log_edge_version(
                                graph_name=self.current_graph,
                                edge_id=entity_id,
                                edge_type=label_or_type,
                                source_id=source_id,
                                target_id=target_id,
                                properties=properties,
                                operation=operation,
                                changed_by=changed_by,
                                change_notes=change_notes,
                                user_id=user_id
                            )

                    # Execute graph operation
                    result = db.execute_cypher_with_cursor(cursor, self.current_graph, cypher_query, columns)

                    # For CREATE/UPDATE: log AFTER cypher
                    if operation in ('CREATE', 'UPDATE'):
                        if entity_type == 'node':
                            logger.log_node_version(
                                graph_name=self.current_graph,
                                node_id=entity_id,
                                label=label_or_type,
                                properties=properties,
                                operation=operation,
                                changed_by=changed_by,
                                change_notes=change_notes,
                                user_id=user_id
                            )
                        elif entity_type == 'edge':
                            logger.log_edge_version(
                                graph_name=self.current_graph,
                                edge_id=entity_id,
                                edge_type=label_or_type,
                                source_id=source_id,
                                target_id=target_id,
                                properties=properties,
                                operation=operation,
                                changed_by=changed_by,
                                change_notes=change_notes,
                                user_id=user_id
                            )

                    conn.commit()
                    return result

                except Exception as e:
                    conn.rollback()
                    raise

    def set_graph(self, graph_name: str) -> bool:
        """Set the current graph, create if needed"""
        db = get_db()
        if not db.graph_exists(graph_name):
            db.create_graph(graph_name)
        self.current_graph = graph_name
        return True
    
    def create_claim(self, claim_id: Optional[str] = None, content: Optional[str] = None, user_id: Optional[int] = None) -> str:
        """Create a new Claim node with UUID and optional content"""
        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        if claim_id is None:
            claim_id = str(uuid.uuid4())

        # Build Cypher properties string
        cypher_props = f"id: '{claim_id}'"
        if content is not None:
            escaped_content = self._escape_cypher_string(content)
            cypher_props += f", content: '{escaped_content}'"

        # Build logging properties dict
        log_props = {}
        if content is not None:
            log_props['content'] = content

        self._execute_with_logging(
            cypher_query=f"CREATE (c:Claim {{{cypher_props}}}) RETURN c",
            columns=['claim'],
            entity_type='node',
            operation='CREATE',
            entity_id=claim_id,
            label_or_type='Claim',
            properties=log_props,
            user_id=user_id
        )

        return claim_id

    def create_source(self, source_id: Optional[str] = None,
                     url: Optional[str] = None,
                     title: Optional[str] = None,
                     author: Optional[str] = None,
                     publication_date: Optional[str] = None,
                     source_type: Optional[str] = None,
                     content: Optional[str] = None,
                     user_id: Optional[int] = None) -> str:
        """Create a new Source node with UUID and optional properties"""
        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        if source_id is None:
            source_id = str(uuid.uuid4())

        # Build Cypher properties string
        cypher_props = f"id: '{source_id}'"
        log_props = {}

        if url is not None:
            escaped_url = self._escape_cypher_string(url)
            cypher_props += f", url: '{escaped_url}'"
            log_props['url'] = url
        if title is not None:
            escaped_title = self._escape_cypher_string(title)
            cypher_props += f", title: '{escaped_title}'"
            log_props['title'] = title
        if author is not None:
            escaped_author = self._escape_cypher_string(author)
            cypher_props += f", author: '{escaped_author}'"
            log_props['author'] = author
        if publication_date is not None:
            escaped_date = self._escape_cypher_string(publication_date)
            cypher_props += f", publication_date: '{escaped_date}'"
            log_props['publication_date'] = publication_date
        if source_type is not None:
            escaped_type = self._escape_cypher_string(source_type)
            cypher_props += f", source_type: '{escaped_type}'"
            log_props['source_type'] = source_type
        if content is not None:
            escaped_content = self._escape_cypher_string(content)
            cypher_props += f", content: '{escaped_content}'"
            log_props['content'] = content

        self._execute_with_logging(
            cypher_query=f"CREATE (s:Source {{{cypher_props}}}) RETURN s",
            columns=['source'],
            entity_type='node',
            operation='CREATE',
            entity_id=source_id,
            label_or_type='Source',
            properties=log_props,
            user_id=user_id
        )

        return source_id

    def create_connection(self, from_node_id: str, to_node_id: str,
                         connection_id: Optional[str] = None,
                         notes: Optional[str] = None,
                         logic_type: Optional[str] = None,
                         composite_id: Optional[str] = None,
                         user_id: Optional[int] = None) -> str:
        """Create a Connection edge between any two nodes (Claims, Sources) with optional notes, logic_type, and composite_id"""
        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        # Validate logic_type
        VALID_LOGIC_TYPES = {'AND', 'OR', 'NOT', 'NAND'}
        if logic_type is not None and logic_type not in VALID_LOGIC_TYPES:
            raise ValueError(f"Invalid logic_type: '{logic_type}'. Must be one of {VALID_LOGIC_TYPES}")

        if connection_id is None:
            connection_id = str(uuid.uuid4())

        # Build Cypher properties string
        cypher_props = f"id: '{connection_id}'"
        if notes is not None:
            escaped_notes = self._escape_cypher_string(notes)
            cypher_props += f", notes: '{escaped_notes}'"
        if logic_type is not None:
            cypher_props += f", logic_type: '{logic_type}'"
        if composite_id is not None:
            cypher_props += f", composite_id: '{composite_id}'"

        # Build logging properties dict
        log_props = {}
        if notes is not None:
            log_props['notes'] = notes
        if logic_type is not None:
            log_props['logic_type'] = logic_type
        if composite_id is not None:
            log_props['composite_id'] = composite_id

        self._execute_with_logging(
            cypher_query=f"""
            MATCH (from {{id: '{from_node_id}'}})
            MATCH (to {{id: '{to_node_id}'}})
            CREATE (from)-[r:Connection {{{cypher_props}}}]->(to)
            RETURN r
            """,
            columns=['connection'],
            entity_type='edge',
            operation='CREATE',
            entity_id=connection_id,
            label_or_type='Connection',
            properties=log_props,
            source_id=from_node_id,
            target_id=to_node_id,
            user_id=user_id
        )

        return connection_id

    def create_compound_connection(self, source_node_ids: List[str], target_node_id: str,
                                   logic_type: str, notes: Optional[str] = None,
                                   composite_id: Optional[str] = None,
                                   user_id: Optional[int] = None) -> str:
        """
        Create a compound connection (multiple edges with shared composite_id, logic_type, notes).

        Args:
            source_node_ids: List of source node IDs (all edges will point to same target)
            target_node_id: Target node ID (shared by all edges)
            logic_type: 'AND', 'OR', 'NOT', 'NAND' (shared by all edges)
            notes: Optional notes (shared by all edges)
            composite_id: Optional shared group ID (auto-generated if not provided)

        Returns:
            The composite_id used for the group
        """
        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        # Validate logic_type
        VALID_LOGIC_TYPES = {'AND', 'OR', 'NOT', 'NAND'}
        if logic_type not in VALID_LOGIC_TYPES:
            raise ValueError(f"Invalid logic_type: '{logic_type}'. Must be one of {VALID_LOGIC_TYPES}")

        if composite_id is None:
            composite_id = str(uuid.uuid4())

        # Create all edges in the compound group with shared metadata
        for source_id in source_node_ids:
            self.create_connection(
                from_node_id=source_id,
                to_node_id=target_node_id,
                notes=notes,
                logic_type=logic_type,
                composite_id=composite_id,
                user_id=user_id
            )

        return composite_id

    def get_all_claims(self) -> List[Dict]:
        """Retrieve all Claim nodes"""
        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        db = get_db()
        return db.execute_cypher(
            self.current_graph,
            "MATCH (c:Claim) RETURN c",
            ['claim']
        )

    def get_all_sources(self) -> List[Dict]:
        """Retrieve all Source nodes"""
        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        db = get_db()
        return db.execute_cypher(
            self.current_graph,
            "MATCH (s:Source) RETURN s",
            ['source']
        )

    def get_node_connections(self, node_id: str) -> List[Dict]:
        """Get all connections from/to a specific node (bidirectional query)"""
        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        db = get_db()
        return db.execute_cypher(
            self.current_graph,
            f"""
            MATCH (n {{id: '{node_id}'}})-[r:Connection]-(other)
            RETURN n, r, other
            """,
            ['node', 'connection', 'other']
        )

    def delete_node(self, node_id: str, user_id: Optional[int] = None) -> bool:
        """Delete any node by UUID and all its connections"""
        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        db = get_db()

        # Query for node metadata first (needed for logging)
        node_data = db.execute_cypher(
            self.current_graph,
            f"""MATCH (n {{id: '{node_id}'}})
            RETURN labels(n) as labels, n.content as content,
                   n.url as url, n.title as title, n.author as author,
                   n.publication_date as publication_date, n.source_type as source_type""",
            ['labels', 'content', 'url', 'title', 'author', 'publication_date', 'source_type']
        )
        if not node_data:
            return False

        node_label = node_data[0]['labels'][0]

        # Build properties dict based on what exists
        properties = {}
        for prop in ['content', 'url', 'title', 'author', 'publication_date', 'source_type']:
            if node_data[0].get(prop):
                properties[prop] = node_data[0][prop]

        result = self._execute_with_logging(
            cypher_query=f"MATCH (n {{id: '{node_id}'}}) DETACH DELETE n RETURN count(n) as deleted",
            columns=['deleted'],
            entity_type='node',
            operation='DELETE',
            entity_id=node_id,
            label_or_type=node_label,
            properties=properties,
            user_id=user_id
        )

        return result[0]['deleted'] > 0 if result else False

    def delete_edge(self, edge_id: str, user_id: Optional[int] = None) -> bool:
        """
        Delete edge(s) by UUID. Accepts either individual edge ID or composite_id.
        Try-single-first: queries as individual ID first, falls back to composite query.
        """
        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        db = get_db()

        # Try-single-first: Query as individual edge ID
        edge_data = db.execute_cypher(
            self.current_graph,
            f"""
            MATCH (source)-[r {{id: '{edge_id}'}}]->(target)
            RETURN type(r) as edge_type, source.id as source_id, target.id as target_id,
                   r.notes as notes, r.logic_type as logic_type, r.composite_id as composite_id
            """,
            ['edge_type', 'source_id', 'target_id', 'notes', 'logic_type', 'composite_id']
        )

        # If no match as individual ID, try as composite_id
        if not edge_data:
            edge_data = db.execute_cypher(
                self.current_graph,
                f"""
                MATCH (source)-[r {{composite_id: '{edge_id}'}}]->(target)
                RETURN type(r) as edge_type, source.id as source_id, target.id as target_id,
                       r.notes as notes, r.logic_type as logic_type, r.composite_id as composite_id, r.id as edge_id
                """,
                ['edge_type', 'source_id', 'target_id', 'notes', 'logic_type', 'composite_id', 'edge_id']
            )
            if not edge_data:
                return False

            # Deleting compound group: log and delete each edge
            deleted_count = 0
            for edge in edge_data:
                properties = {}
                if edge.get('notes'):
                    properties['notes'] = edge['notes']
                if edge.get('logic_type'):
                    properties['logic_type'] = edge['logic_type']
                if edge.get('composite_id'):
                    properties['composite_id'] = edge['composite_id']

                result = self._execute_with_logging(
                    cypher_query=f"MATCH ()-[r {{id: '{edge['edge_id']}'}}]->() DELETE r RETURN count(r) as deleted",
                    columns=['deleted'],
                    entity_type='edge',
                    operation='DELETE',
                    entity_id=edge['edge_id'],
                    label_or_type=edge['edge_type'],
                    properties=properties,
                    source_id=edge['source_id'],
                    target_id=edge['target_id'],
                    user_id=user_id
                )
                deleted_count += result[0]['deleted'] if result else 0

            return deleted_count > 0

        # Deleting single edge
        edge_type = edge_data[0]['edge_type']
        source_id = edge_data[0]['source_id']
        target_id = edge_data[0]['target_id']
        properties = {}
        if edge_data[0].get('notes'):
            properties['notes'] = edge_data[0]['notes']
        if edge_data[0].get('logic_type'):
            properties['logic_type'] = edge_data[0]['logic_type']
        if edge_data[0].get('composite_id'):
            properties['composite_id'] = edge_data[0]['composite_id']

        result = self._execute_with_logging(
            cypher_query=f"MATCH ()-[r {{id: '{edge_id}'}}]->() DELETE r RETURN count(r) as deleted",
            columns=['deleted'],
            entity_type='edge',
            operation='DELETE',
            entity_id=edge_id,
            label_or_type=edge_type,
            properties=properties,
            source_id=source_id,
            target_id=target_id,
            user_id=user_id
        )

        return result[0]['deleted'] > 0 if result else False

    def edit_node(self, node_id: str, user_id: Optional[int] = None, **fields) -> bool:
        """Edit node properties. Accepts any valid node properties as keyword arguments"""
        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        if not fields:
            return True  # No changes requested

        db = get_db()

        # Query for node label first (needed for logging)
        node_data = db.execute_cypher(
            self.current_graph,
            f"MATCH (n {{id: '{node_id}'}}) RETURN labels(n) as labels",
            ['labels']
        )
        if not node_data:
            return False

        node_label = node_data[0]['labels'][0]

        # Build SET clause dynamically
        set_clauses = []
        for field, value in fields.items():
            if isinstance(value, str):
                escaped_value = self._escape_cypher_string(value)
                set_clauses.append(f"n.{field} = '{escaped_value}'")
            elif isinstance(value, (int, float)):
                set_clauses.append(f"n.{field} = {value}")
            else:
                escaped_value = self._escape_cypher_string(str(value))
                set_clauses.append(f"n.{field} = '{escaped_value}'")

        set_clause = ", ".join(set_clauses)

        result = self._execute_with_logging(
            cypher_query=f"MATCH (n {{id: '{node_id}'}}) SET {set_clause} RETURN count(n) as updated",
            columns=['updated'],
            entity_type='node',
            operation='UPDATE',
            entity_id=node_id,
            label_or_type=node_label,
            properties=fields,
            user_id=user_id
        )

        return result[0]['updated'] > 0 if result else False

    def edit_edge(self, edge_id: str, user_id: Optional[int] = None, **fields) -> bool:
        """
        Edit edge properties. Accepts either individual edge ID or composite_id.
        Try-single-first: queries as individual ID first, falls back to composite query.
        For compound edges, updates all edges in the group with shared metadata.
        """
        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        if not fields:
            return True  # No changes requested

        db = get_db()

        # Try-single-first: Query as individual edge ID
        edge_data = db.execute_cypher(
            self.current_graph,
            f"""
            MATCH (source)-[r {{id: '{edge_id}'}}]->(target)
            RETURN type(r) as edge_type, source.id as source_id, target.id as target_id, r.id as edge_id
            """,
            ['edge_type', 'source_id', 'target_id', 'edge_id']
        )

        # If no match as individual ID, try as composite_id
        if not edge_data:
            edge_data = db.execute_cypher(
                self.current_graph,
                f"""
                MATCH (source)-[r {{composite_id: '{edge_id}'}}]->(target)
                RETURN type(r) as edge_type, source.id as source_id, target.id as target_id, r.id as edge_id
                """,
                ['edge_type', 'source_id', 'target_id', 'edge_id']
            )
            if not edge_data:
                return False

            # Editing compound group: update all edges with shared metadata
            updated_count = 0
            for edge in edge_data:
                # Build SET clause dynamically
                set_clauses = []
                for field, value in fields.items():
                    if isinstance(value, str):
                        escaped_value = self._escape_cypher_string(value)
                        set_clauses.append(f"r.{field} = '{escaped_value}'")
                    elif isinstance(value, (int, float)):
                        set_clauses.append(f"r.{field} = {value}")
                    else:
                        escaped_value = self._escape_cypher_string(str(value))
                        set_clauses.append(f"r.{field} = '{escaped_value}'")

                set_clause = ", ".join(set_clauses)

                result = self._execute_with_logging(
                    cypher_query=f"MATCH ()-[r {{id: '{edge['edge_id']}'}}]->() SET {set_clause} RETURN count(r) as updated",
                    columns=['updated'],
                    entity_type='edge',
                    operation='UPDATE',
                    entity_id=edge['edge_id'],
                    label_or_type=edge['edge_type'],
                    properties=fields,
                    source_id=edge['source_id'],
                    target_id=edge['target_id'],
                    user_id=user_id
                )
                updated_count += result[0]['updated'] if result else 0

            return updated_count > 0

        # Editing single edge
        edge_type = edge_data[0]['edge_type']
        source_id = edge_data[0]['source_id']
        target_id = edge_data[0]['target_id']

        # Build SET clause dynamically
        set_clauses = []
        for field, value in fields.items():
            if isinstance(value, str):
                escaped_value = self._escape_cypher_string(value)
                set_clauses.append(f"r.{field} = '{escaped_value}'")
            elif isinstance(value, (int, float)):
                set_clauses.append(f"r.{field} = {value}")
            else:
                escaped_value = self._escape_cypher_string(str(value))
                set_clauses.append(f"r.{field} = '{escaped_value}'")

        set_clause = ", ".join(set_clauses)

        result = self._execute_with_logging(
            cypher_query=f"MATCH ()-[r {{id: '{edge_id}'}}]->() SET {set_clause} RETURN count(r) as updated",
            columns=['updated'],
            entity_type='edge',
            operation='UPDATE',
            entity_id=edge_id,
            label_or_type=edge_type,
            properties=fields,
            source_id=source_id,
            target_id=target_id,
            user_id=user_id
        )

        return result[0]['updated'] > 0 if result else False

    # ========== Temporal Query Methods ==========

    def get_nodes_at_timestamp(self, timestamp: datetime) -> List[Dict[str, Any]]:
        """
        Get snapshot of all nodes that existed at the given timestamp.

        Args:
            timestamp: The point in time to query

        Returns:
            List of node dicts: [{'id': '...', 'label': '...', 'properties': {...}}, ...]
        """
        service = get_temporal_service()
        return service.get_nodes_at_timestamp(timestamp)

    def get_edges_at_timestamp(self, timestamp: datetime) -> List[Dict[str, Any]]:
        """
        Get snapshot of all edges that existed at the given timestamp.
        Returns:
            List of edge dicts: [{'id': '...', 'type': '...', 'source': '...', 'target': '...', 'properties': {...}}, ...]
        """
        service = get_temporal_service()
        return service.get_edges_at_timestamp(timestamp)

    def get_graph_at_timestamp(self, timestamp: datetime) -> Dict[str, Any]:
        """
        Get complete graph state at timestamp (nodes + edges).

        Returns:
            Dict with 'nodes' and 'edges' keys: {'nodes': [...], 'edges': [...]}
        """
        service = get_temporal_service()
        return service.get_graph_at_timestamp(timestamp)


# Global operations instance
language_ops = LanguageOperations()

def get_language_ops() -> LanguageOperations:
    """Get the global language operations instance"""
    return language_ops