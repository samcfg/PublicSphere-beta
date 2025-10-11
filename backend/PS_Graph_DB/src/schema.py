from dataclasses import dataclass, field
from typing import Dict, List, Type, Any
from .database import get_db

@dataclass
class NodeSchema:
    label: str
    required_properties: Dict[str, Type[Any]]
    optional_properties: Dict[str, Type[Any]] = field(default_factory=dict)
    
@dataclass
class EdgeSchema:
    type: str
    from_labels: List[str]
    to_labels: List[str]
    required_properties: Dict[str, Type[Any]] = field(default_factory=dict)
    optional_properties: Dict[str, Type[Any]] = field(default_factory=dict)

class BasicSchema:
    """Elementary schema with Claim nodes and Connection edges"""
    
    def __init__(self):
        self.nodes = {
            'Claim': NodeSchema(
                label='Claim',
                required_properties={'id': str},
                optional_properties={'content': str}
            )
        }
        
        self.edges = {
            'Connection': EdgeSchema(
                type='Connection',
                from_labels=['Claim'],
                to_labels=['Claim'],
                required_properties={'id': str},
                optional_properties={
                    'notes': str,
                    'logic_type': str,    # 'AND' or 'OR' for compound edges
                    'composite_id': str   # UUID shared across compound edge group
                }
            )
        }
    
    def apply_to_graph(self, graph_name: str) -> bool:
        """Apply the basic schema to a graph"""
        db = get_db()
        
        if not db.graph_exists(graph_name):
            db.create_graph(graph_name)
        
        # Note: AGE doesn't support traditional Cypher index syntax
        # Indexing would need to be done at PostgreSQL level if needed
        return True

# Global schema instance
schema = BasicSchema()

def get_schema() -> BasicSchema:
    """Get the global schema instance"""
    return schema