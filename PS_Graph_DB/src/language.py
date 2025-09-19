from typing import Dict, List, Optional
from .database import get_db
import uuid

class LanguageOperations:
    """Data operations for Claims and Connections"""

    def __init__(self):
        self.current_graph = None

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

        db = get_db()

        if claim_id is None:
            claim_id = str(uuid.uuid4())

        # Build properties dynamically
        properties = f"id: '{claim_id}'"
        if content is not None:
            # Escape single quotes in content
            escaped_content = content.replace("'", "\\'")
            properties += f", content: '{escaped_content}'"

        db.execute_cypher(
            self.current_graph,
            f"CREATE (c:Claim {{{properties}}}) RETURN c",
            ['claim']
        )

        return claim_id
    
    def create_connection(self, from_claim_id: str, to_claim_id: str,
                         connection_id: Optional[str] = None, notes: Optional[str] = None) -> str:
        """Create a Connection edge between two Claims with optional notes"""
        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        db = get_db()

        if connection_id is None:
            connection_id = str(uuid.uuid4())

        # Build properties dynamically
        properties = f"id: '{connection_id}'"
        if notes is not None:
            # Escape single quotes in notes
            escaped_notes = notes.replace("'", "\\'")
            properties += f", notes: '{escaped_notes}'"

        db.execute_cypher(
            self.current_graph,
            f"""
            MATCH (from:Claim {{id: '{from_claim_id}'}})
            MATCH (to:Claim {{id: '{to_claim_id}'}})
            CREATE (from)-[r:Connection {{{properties}}}]->(to)
            RETURN r
            """,
            ['connection']
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
        result = db.execute_cypher(
            self.current_graph,
            f"MATCH (n {{id: '{node_id}'}}) DETACH DELETE n RETURN count(n) as deleted",
            ['deleted']
        )
        return result[0]['deleted'] > 0 if result else False

    def delete_edge(self, edge_id: str) -> bool:
        """Delete a specific edge by UUID"""
        if not self.current_graph:
            raise ValueError("No graph set. Call set_graph() first")

        db = get_db()
        result = db.execute_cypher(
            self.current_graph,
            f"MATCH ()-[r {{id: '{edge_id}'}}]->() DELETE r RETURN count(r) as deleted",
            ['deleted']
        )
        return result[0]['deleted'] > 0 if result else False

# Global operations instance
language_ops = LanguageOperations()

def get_language_ops() -> LanguageOperations:
    """Get the global language operations instance"""
    return language_ops