import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Tuple
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AGEDatabase:
    def __init__(self, 
                 user: str = "sam",
                 host: str = "localhost", 
                 database: str = "postgres",
                 password: str = "124141",
                 port: int = 5432,
                 minconn: int = 1,
                 maxconn: int = 10):
        
        self.connection_params = {
            'user': user,
            'host': host,
            'database': database,
            'password': password,
            'port': port
        }
        
        try:
            self.pool = psycopg2.pool.ThreadedConnectionPool(
                minconn, maxconn, **self.connection_params
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager for database connections with AGE setup"""
        conn = None
        try:
            conn = self.pool.getconn()
            
            # Set autocommit first, then set up AGE environment
            conn.autocommit = False

            # Set up AGE environment
            with conn.cursor() as cursor:
                cursor.execute("LOAD 'age'")
                cursor.execute("SET search_path = ag_catalog, '$user', public")
            yield conn
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if conn:
                self.pool.putconn(conn)

    @contextmanager
    def get_cursor(self, autocommit: bool = False):
        """Context manager for cursor operations"""
        conn = None
        try:
            conn = self.pool.getconn()

            # Set autocommit before any operations
            conn.autocommit = autocommit

            # Set up AGE environment
            with conn.cursor() as setup_cursor:
                setup_cursor.execute("LOAD 'age'")
                setup_cursor.execute("SET search_path = ag_catalog, '$user', public")

            cursor = conn.cursor()
            try:
                yield cursor
                if not autocommit:
                    conn.commit()
            except Exception as e:
                if not autocommit:
                    conn.rollback()
                raise
            finally:
                cursor.close()
        except Exception as e:
            if conn and not autocommit:
                conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if conn:
                self.pool.putconn(conn)

    def execute_cypher(self, graph_name: str, cypher_query: str, 
                      return_columns: List[str] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return parsed results"""
        
        if return_columns is None:
            return_columns = ['result']
            
        column_spec = ', '.join([f"{col} agtype" for col in return_columns])
        
        sql_query = f"""
        SELECT * FROM cypher('{graph_name}', $$
        {cypher_query}
        $$) AS ({column_spec})
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                parsed_row = {}
                for i, col_name in enumerate(return_columns):
                    agtype_value = row[i]
                    if agtype_value:
                        # Strip AGE type suffixes and parse JSON
                        clean_value = str(agtype_value).replace('::vertex', '').replace('::edge', '').replace('::path', '')
                        try:
                            parsed_row[col_name] = json.loads(clean_value)
                        except json.JSONDecodeError:
                            # Handle scalar values
                            parsed_row[col_name] = clean_value.strip('"')
                    else:
                        parsed_row[col_name] = None
                        
                results.append(parsed_row)
                
            return results

    def graph_exists(self, graph_name: str) -> bool:
        """Check if a graph exists"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT name FROM ag_graph WHERE name = %s", (graph_name,))
            return cursor.fetchone() is not None

    def create_graph(self, graph_name: str) -> bool:
        """Create a new graph"""
        if self.graph_exists(graph_name):
            logger.warning(f"Graph '{graph_name}' already exists")
            return False
            
        with self.get_cursor() as cursor:
            cursor.execute(f"SELECT create_graph('{graph_name}')")
            logger.info(f"Created graph '{graph_name}'")
            return True

    def drop_graph(self, graph_name: str, cascade: bool = True) -> bool:
        """Drop a graph"""
        if not self.graph_exists(graph_name):
            logger.warning(f"Graph '{graph_name}' does not exist")
            return False
            
        cascade_str = "true" if cascade else "false"
        with self.get_cursor() as cursor:
            cursor.execute(f"SELECT drop_graph('{graph_name}', {cascade_str})")
            logger.info(f"Dropped graph '{graph_name}'")
            return True

    def get_graph_stats(self, graph_name: str) -> Dict[str, int]:
        """Get node and edge counts for a graph"""
        if not self.graph_exists(graph_name):
            return {'nodes': 0, 'edges': 0}
            
        # Count nodes
        node_result = self.execute_cypher(graph_name, "MATCH (n) RETURN count(n)", ['count'])
        node_count = node_result[0]['count'] if node_result else 0
        
        # Count edges  
        edge_result = self.execute_cypher(graph_name, "MATCH ()-[r]->() RETURN count(r)", ['count'])
        edge_count = edge_result[0]['count'] if edge_result else 0
        
        return {'nodes': node_count, 'edges': edge_count}

    def get_node_labels(self, graph_name: str) -> List[str]:
        """Get all unique node labels in a graph"""
        if not self.graph_exists(graph_name):
            return []
            
        result = self.execute_cypher(graph_name, "MATCH (n) RETURN DISTINCT labels(n)", ['labels'])
        
        # Flatten and deduplicate labels
        all_labels = set()
        for row in result:
            labels = row['labels']
            if isinstance(labels, list):
                all_labels.update(labels)
        
        return sorted(list(all_labels))

    def get_edge_types(self, graph_name: str) -> List[str]:
        """Get all unique edge types in a graph"""
        if not self.graph_exists(graph_name):
            return []
            
        result = self.execute_cypher(graph_name, "MATCH ()-[r]->() RETURN DISTINCT type(r)", ['type'])
        return [row['type'] for row in result if row['type']]

    def close(self):
        """Close all connections in the pool"""
        if hasattr(self, 'pool'):
            self.pool.closeall()
            logger.info("Database connection pool closed")

# Global database instance
db = AGEDatabase()

def get_db() -> AGEDatabase:
    """Get the global database instance"""
    return db