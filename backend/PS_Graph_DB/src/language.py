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
                     # Required fields
                     title: Optional[str] = None,
                     source_type: Optional[str] = None,
                     # Universal optional fields
                     thumbnail_link: Optional[str] = None,
                     authors: Optional[list] = None,  # [{"name": "...", "role": "author"}]
                     url: Optional[str] = None,
                     accessed_date: Optional[str] = None,
                     excerpt: Optional[str] = None,
                     content: Optional[str] = None,
                     # Publication metadata
                     publication_date: Optional[str] = None,
                     container_title: Optional[str] = None,
                     publisher: Optional[str] = None,
                     publisher_location: Optional[str] = None,
                     # Volume/Issue/Pages
                     volume: Optional[str] = None,
                     issue: Optional[str] = None,
                     pages: Optional[str] = None,
                     # Book-specific
                     edition: Optional[str] = None,
                     # Identifiers
                     doi: Optional[str] = None,
                     isbn: Optional[str] = None,
                     issn: Optional[str] = None,
                     pmid: Optional[str] = None,
                     pmcid: Optional[str] = None,
                     arxiv_id: Optional[str] = None,
                     handle: Optional[str] = None,
                     persistent_id: Optional[str] = None,
                     persistent_id_type: Optional[str] = None,
                     # Editors
                     editors: Optional[list] = None,  # [{"name": "...", "role": "editor"}]
                     # Legal-specific
                     jurisdiction: Optional[str] = None,
                     legal_category: Optional[str] = None,
                     court: Optional[str] = None,
                     decision_date: Optional[str] = None,
                     case_name: Optional[str] = None,
                     code: Optional[str] = None,
                     section: Optional[str] = None,
                     # Flexible metadata overflow
                     metadata: Optional[dict] = None,
                     user_id: Optional[int] = None) -> str:
        """Create a new Source node with UUID and citation properties"""
        import json

        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        # Validate required fields
        if title is None:
            raise ValueError("title is required for Source nodes")
        if source_type is None:
            raise ValueError("source_type is required for Source nodes")

        # Validate source_type
        VALID_SOURCE_TYPES = {
            'journal_article', 'preprint', 'book', 'website', 'newspaper',
            'magazine', 'thesis', 'conference_paper', 'technical_report',
            'government_document', 'dataset', 'media', 'legal', 'testimony'
        }
        if source_type not in VALID_SOURCE_TYPES:
            raise ValueError(f"Invalid source_type: '{source_type}'. Must be one of {VALID_SOURCE_TYPES}")

        # Type-specific required field validation
        if source_type == 'legal':
            if jurisdiction is None:
                raise ValueError("jurisdiction is required for legal sources")
            if legal_category is None:
                raise ValueError("legal_category is required for legal sources")
            # Validate legal_category
            VALID_LEGAL_CATEGORIES = {'case', 'statute', 'regulation', 'treaty'}
            if legal_category not in VALID_LEGAL_CATEGORIES:
                raise ValueError(f"Invalid legal_category: '{legal_category}'. Must be one of {VALID_LEGAL_CATEGORIES}")

        if source_type == 'website':
            if url is None:
                raise ValueError("url is required for website sources")

        if source_id is None:
            source_id = str(uuid.uuid4())

        # Build Cypher properties string
        cypher_props = f"id: '{source_id}'"
        log_props = {}

        # Helper function to add property
        def add_prop(name: str, value, is_json: bool = False):
            nonlocal cypher_props
            if value is not None:
                if is_json:
                    # Serialize JSON to string for AGE storage
                    json_str = json.dumps(value)
                    escaped_value = self._escape_cypher_string(json_str)
                    cypher_props += f", {name}: '{escaped_value}'"
                    log_props[name] = value  # Store original object in Django
                else:
                    escaped_value = self._escape_cypher_string(str(value))
                    cypher_props += f", {name}: '{escaped_value}'"
                    log_props[name] = value

        # Add required fields
        add_prop('title', title)
        add_prop('source_type', source_type)

        # Add universal optional fields
        add_prop('thumbnail_link', thumbnail_link)
        add_prop('authors', authors, is_json=True)
        add_prop('url', url)
        add_prop('accessed_date', accessed_date)
        add_prop('excerpt', excerpt)
        add_prop('content', content)

        # Add publication metadata
        add_prop('publication_date', publication_date)
        add_prop('container_title', container_title)
        add_prop('publisher', publisher)
        add_prop('publisher_location', publisher_location)

        # Add volume/issue/pages
        add_prop('volume', volume)
        add_prop('issue', issue)
        add_prop('pages', pages)

        # Add book-specific
        add_prop('edition', edition)

        # Add identifiers
        add_prop('doi', doi)
        add_prop('isbn', isbn)
        add_prop('issn', issn)
        add_prop('pmid', pmid)
        add_prop('pmcid', pmcid)
        add_prop('arxiv_id', arxiv_id)
        add_prop('handle', handle)
        add_prop('persistent_id', persistent_id)
        add_prop('persistent_id_type', persistent_id_type)

        # Add editors
        add_prop('editors', editors, is_json=True)

        # Add legal-specific
        add_prop('jurisdiction', jurisdiction)
        add_prop('legal_category', legal_category)
        add_prop('court', court)
        add_prop('decision_date', decision_date)
        add_prop('case_name', case_name)
        add_prop('code', code)
        add_prop('section', section)

        # Add metadata overflow
        add_prop('metadata', metadata, is_json=True)

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
                         quote: Optional[str] = None,
                         user_id: Optional[int] = None) -> str:
        """Create a Connection edge between any two nodes (Claims, Sources) with optional notes, logic_type, composite_id, and quote"""
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
        if quote is not None:
            escaped_quote = self._escape_cypher_string(quote)
            cypher_props += f", quote: '{escaped_quote}'"

        # Build logging properties dict
        log_props = {}
        if notes is not None:
            log_props['notes'] = notes
        if logic_type is not None:
            log_props['logic_type'] = logic_type
        if composite_id is not None:
            log_props['composite_id'] = composite_id
        if quote is not None:
            log_props['quote'] = quote

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
                                   quote: Optional[str] = None,
                                   user_id: Optional[int] = None) -> str:
        """
        Create a compound connection (multiple edges with shared composite_id, logic_type, notes, quote).

        Args:
            source_node_ids: List of source node IDs (all edges will point to same target)
            target_node_id: Target node ID (shared by all edges)
            logic_type: 'AND', 'OR', 'NOT', 'NAND' (shared by all edges)
            notes: Optional notes (shared by all edges)
            composite_id: Optional shared group ID (auto-generated if not provided)
            quote: Optional quote excerpt (shared by all edges)

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
                quote=quote,
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
        import json

        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        if not fields:
            return True  # No changes requested

        db = get_db()

        # Query for node label and current source_type (needed for validation)
        node_data = db.execute_cypher(
            self.current_graph,
            f"MATCH (n {{id: '{node_id}'}}) RETURN labels(n) as labels, n.source_type as source_type",
            ['labels', 'source_type']
        )
        if not node_data:
            return False

        node_label = node_data[0]['labels'][0]

        # Validate Source node edits
        if node_label == 'Source':
            current_source_type = node_data[0].get('source_type')
            new_source_type = fields.get('source_type', current_source_type)

            # Validate source_type if being changed
            if 'source_type' in fields:
                VALID_SOURCE_TYPES = {
                    'journal_article', 'preprint', 'book', 'website', 'newspaper',
                    'magazine', 'thesis', 'conference_paper', 'technical_report',
                    'government_document', 'dataset', 'media', 'legal', 'testimony'
                }
                if new_source_type not in VALID_SOURCE_TYPES:
                    raise ValueError(f"Invalid source_type: '{new_source_type}'. Must be one of {VALID_SOURCE_TYPES}")

            # Type-specific required field validation
            if new_source_type == 'legal':
                # Query current values if not in fields
                if 'jurisdiction' not in fields or 'legal_category' not in fields:
                    current_data = db.execute_cypher(
                        self.current_graph,
                        f"MATCH (n {{id: '{node_id}'}}) RETURN n.jurisdiction as jurisdiction, n.legal_category as legal_category",
                        ['jurisdiction', 'legal_category']
                    )
                    current_jurisdiction = current_data[0].get('jurisdiction') if current_data else None
                    current_legal_category = current_data[0].get('legal_category') if current_data else None
                else:
                    current_jurisdiction = None
                    current_legal_category = None

                final_jurisdiction = fields.get('jurisdiction', current_jurisdiction)
                final_legal_category = fields.get('legal_category', current_legal_category)

                if final_jurisdiction is None:
                    raise ValueError("jurisdiction is required for legal sources")
                if final_legal_category is None:
                    raise ValueError("legal_category is required for legal sources")

                # Validate legal_category
                if 'legal_category' in fields:
                    VALID_LEGAL_CATEGORIES = {'case', 'statute', 'regulation', 'treaty'}
                    if final_legal_category not in VALID_LEGAL_CATEGORIES:
                        raise ValueError(f"Invalid legal_category: '{final_legal_category}'. Must be one of {VALID_LEGAL_CATEGORIES}")

            if new_source_type == 'website':
                # Query current url if not in fields
                if 'url' not in fields:
                    current_data = db.execute_cypher(
                        self.current_graph,
                        f"MATCH (n {{id: '{node_id}'}}) RETURN n.url as url",
                        ['url']
                    )
                    current_url = current_data[0].get('url') if current_data else None
                else:
                    current_url = None

                final_url = fields.get('url', current_url)
                if final_url is None:
                    raise ValueError("url is required for website sources")

        # Build SET clause dynamically
        set_clauses = []
        for field, value in fields.items():
            if isinstance(value, (list, dict)):
                # Handle JSON fields (authors, editors, metadata)
                json_str = json.dumps(value)
                escaped_value = self._escape_cypher_string(json_str)
                set_clauses.append(f"n.{field} = '{escaped_value}'")
            elif isinstance(value, str):
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