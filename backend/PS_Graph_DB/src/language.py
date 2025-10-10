from typing import Dict, List, Optional, Any
from database import get_db
from logging import get_temporal_logger
import uuid

class LanguageOperations:
    """Data operations for Claims and Connections"""

    def __init__(self):
        self.current_graph = None

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
                             change_notes: Optional[str] = None) -> List[Dict]:
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
                                change_notes=change_notes
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
                                change_notes=change_notes
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
                                change_notes=change_notes
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
                                change_notes=change_notes
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
    
    def create_claim(self, claim_id: Optional[str] = None, content: Optional[str] = None) -> str:
        """Create a new Claim node with UUID and optional content"""
        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        if claim_id is None:
            claim_id = str(uuid.uuid4())

        # Build Cypher properties string
        cypher_props = f"id: '{claim_id}'"
        if content is not None:
            escaped_content = content.replace("'", "\\'")
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
            properties=log_props
        )

        return claim_id
    
    def create_connection(self, from_claim_id: str, to_claim_id: str,
                         connection_id: Optional[str] = None, notes: Optional[str] = None) -> str:
        """Create a Connection edge between two Claims with optional notes"""
        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        if connection_id is None:
            connection_id = str(uuid.uuid4())

        # Build Cypher properties string
        cypher_props = f"id: '{connection_id}'"
        if notes is not None:
            escaped_notes = notes.replace("'", "\\'")
            cypher_props += f", notes: '{escaped_notes}'"

        # Build logging properties dict
        log_props = {}
        if notes is not None:
            log_props['notes'] = notes

        self._execute_with_logging(
            cypher_query=f"""
            MATCH (from:Claim {{id: '{from_claim_id}'}})
            MATCH (to:Claim {{id: '{to_claim_id}'}})
            CREATE (from)-[r:Connection {{{cypher_props}}}]->(to)
            RETURN r
            """,
            columns=['connection'],
            entity_type='edge',
            operation='CREATE',
            entity_id=connection_id,
            label_or_type='Connection',
            properties=log_props,
            source_id=from_claim_id,
            target_id=to_claim_id
        )

        return connection_id
    
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
    
    def get_claim_connections(self, claim_id: str) -> List[Dict]:
        """Get all connections from a specific claim"""
        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        db = get_db()
        return db.execute_cypher(
            self.current_graph,
            f"""
            MATCH (c:Claim {{id: '{claim_id}'}})-[r:Connection]->(target:Claim)
            RETURN c, r, target
            """,
            ['source', 'connection', 'target']
        )

    def delete_node(self, node_id: str) -> bool:
        """Delete any node by UUID and all its connections"""
        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        db = get_db()

        # Query for node metadata first (needed for logging)
        node_data = db.execute_cypher(
            self.current_graph,
            f"MATCH (n {{id: '{node_id}'}}) RETURN labels(n) as labels, n.content as content",
            ['labels', 'content']
        )
        if not node_data:
            return False

        node_label = node_data[0]['labels'][0]
        content = node_data[0].get('content')
        properties = {'content': content} if content else {}

        result = self._execute_with_logging(
            cypher_query=f"MATCH (n {{id: '{node_id}'}}) DETACH DELETE n RETURN count(n) as deleted",
            columns=['deleted'],
            entity_type='node',
            operation='DELETE',
            entity_id=node_id,
            label_or_type=node_label,
            properties=properties
        )

        return result[0]['deleted'] > 0 if result else False

    def delete_edge(self, edge_id: str) -> bool:
        """Delete a specific edge by UUID"""
        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        db = get_db()

        # Query for edge metadata first (needed for logging)
        edge_data = db.execute_cypher(
            self.current_graph,
            f"""
            MATCH (source)-[r {{id: '{edge_id}'}}]->(target)
            RETURN type(r) as edge_type, source.id as source_id, target.id as target_id, r.notes as notes
            """,
            ['edge_type', 'source_id', 'target_id', 'notes']
        )
        if not edge_data:
            return False

        edge_type = edge_data[0]['edge_type']
        source_id = edge_data[0]['source_id']
        target_id = edge_data[0]['target_id']
        notes = edge_data[0].get('notes')
        properties = {'notes': notes} if notes else {}

        result = self._execute_with_logging(
            cypher_query=f"MATCH ()-[r {{id: '{edge_id}'}}]->() DELETE r RETURN count(r) as deleted",
            columns=['deleted'],
            entity_type='edge',
            operation='DELETE',
            entity_id=edge_id,
            label_or_type=edge_type,
            properties=properties,
            source_id=source_id,
            target_id=target_id
        )

        return result[0]['deleted'] > 0 if result else False

    def edit_node(self, node_id: str, **fields) -> bool:
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
                escaped_value = value.replace("'", "\\'")
                set_clauses.append(f"n.{field} = '{escaped_value}'")
            elif isinstance(value, (int, float)):
                set_clauses.append(f"n.{field} = {value}")
            else:
                escaped_value = str(value).replace("'", "\\'")
                set_clauses.append(f"n.{field} = '{escaped_value}'")

        set_clause = ", ".join(set_clauses)

        result = self._execute_with_logging(
            cypher_query=f"MATCH (n {{id: '{node_id}'}}) SET {set_clause} RETURN count(n) as updated",
            columns=['updated'],
            entity_type='node',
            operation='UPDATE',
            entity_id=node_id,
            label_or_type=node_label,
            properties=fields
        )

        return result[0]['updated'] > 0 if result else False

    def edit_edge(self, edge_id: str, **fields) -> bool:
        """Edit edge properties. Accepts any valid edge properties as keyword arguments"""
        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        if not fields:
            return True  # No changes requested

        db = get_db()

        # Query for edge metadata first (needed for logging)
        edge_data = db.execute_cypher(
            self.current_graph,
            f"""
            MATCH (source)-[r {{id: '{edge_id}'}}]->(target)
            RETURN type(r) as edge_type, source.id as source_id, target.id as target_id
            """,
            ['edge_type', 'source_id', 'target_id']
        )
        if not edge_data:
            return False

        edge_type = edge_data[0]['edge_type']
        source_id = edge_data[0]['source_id']
        target_id = edge_data[0]['target_id']

        # Build SET clause dynamically
        set_clauses = []
        for field, value in fields.items():
            if isinstance(value, str):
                escaped_value = value.replace("'", "\\'")
                set_clauses.append(f"r.{field} = '{escaped_value}'")
            elif isinstance(value, (int, float)):
                set_clauses.append(f"r.{field} = {value}")
            else:
                escaped_value = str(value).replace("'", "\\'")
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
            target_id=target_id
        )

        return result[0]['updated'] > 0 if result else False

# Global operations instance
language_ops = LanguageOperations()

def get_language_ops() -> LanguageOperations:
    """Get the global language operations instance"""
    return language_ops