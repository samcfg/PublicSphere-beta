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
            ),
            'Source': NodeSchema(
                label='Source',
                required_properties={
                    'id': str,
                    'title': str,
                    'source_type': str  # 'journal_article', 'preprint', 'book', 'website',
                                        # 'newspaper', 'magazine', 'thesis', 'conference_paper',
                                        # 'technical_report', 'government_document', 'dataset',
                                        # 'media', 'legal', 'testimony'
                },
                optional_properties={
                    # Universal optional fields (all types)
                    'thumbnail_link': str,
                    'authors': str,  # JSONB string: [{"name": "...", "role": "author"}]
                    'url': str,
                    'accessed_date': str,
                    'excerpt': str,
                    'content': str,

                    # Publication metadata
                    'publication_date': str,
                    'container_title': str,  # Journal/book/website/conference name
                    'publisher': str,
                    'publisher_location': str,

                    # Volume/Issue/Pages
                    'volume': str,
                    'issue': str,
                    'pages': str,

                    # Book-specific
                    'edition': str,

                    # Identifiers
                    'doi': str,
                    'isbn': str,
                    'issn': str,
                    'pmid': str,
                    'pmcid': str,
                    'arxiv_id': str,
                    'handle': str,
                    'persistent_id': str,
                    'persistent_id_type': str,

                    # Editors
                    'editors': str,  # JSONB string: [{"name": "...", "role": "editor"}]

                    # Legal-specific
                    'jurisdiction': str,
                    'legal_category': str,  # 'case', 'statute', 'regulation', 'treaty'
                    'court': str,
                    'decision_date': str,
                    'case_name': str,
                    'code': str,
                    'section': str,

                    # Flexible overflow for type-specific edge cases
                    'metadata': str  # JSONB string for additional fields
                }
            )
        }
        
        self.edges = {
            'Connection': EdgeSchema(
                type='Connection',
                from_labels=['Claim', 'Source'],
                to_labels=['Claim', 'Source'],
                required_properties={'id': str},
                optional_properties={
                    'notes': str,
                    'logic_type': str,    # 'AND', 'OR', 'NOT', 'NAND'
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