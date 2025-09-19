# File: backend/utils/parsers/schema.py
import json
from bs4 import BeautifulSoup
from django.utils import timezone
import re

class SchemaParser:
    """
    Parser for extracting structured data from Schema.org JSON-LD metadata
    embedded in web pages.
    """
    
    def __init__(self, html_content):
        self.html_content = html_content
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.schemas = []
    
    def parse(self):
        """
        Extract and parse all Schema.org JSON-LD metadata from the page
        """
        self._extract_jsonld()
        return self.schemas
    
    def _extract_jsonld(self):
        """Extract Schema.org JSON-LD data from script tags"""
        script_tags = self.soup.find_all('script', type='application/ld+json')
        
        for tag in script_tags:
            try:
                data = json.loads(tag.string)
                if isinstance(data, list):
                    for item in data:
                        if self._is_valid_schema(item):
                            self.schemas.append(item)
                elif isinstance(data, dict):
                    if self._is_valid_schema(data):
                        self.schemas.append(data)
                
                # Handle @graph structure which contains multiple items
                if isinstance(data, dict) and '@graph' in data and isinstance(data['@graph'], list):
                    for item in data['@graph']:
                        if self._is_valid_schema(item):
                            self.schemas.append(item)
            except (json.JSONDecodeError, AttributeError):
                continue
    
    def _is_valid_schema(self, data):
        """Check if data is a valid Schema.org object"""
        return isinstance(data, dict) and ('@type' in data or '@type' in data)
    
    def get_metadata(self):
        """
        Extract bibliographic metadata from parsed Schema.org data
        """
        if not self.schemas:
            self.parse()
        
        metadata = {
            'title': None,
            'author': None,
            'institution': None,
            'date_published': None,
            'date_accessed': timezone.now().date(),
            'doi': None,
            'source_type': 'other'
        }
        
        # Process schemas in order of relevance
        priority_types = [
            'ScholarlyArticle', 'Article', 'NewsArticle', 'BlogPosting',
            'Book', 'WebPage', 'WebSite', 'CreativeWork'
        ]
        
        # Sort schemas by priority
        schemas_by_priority = []
        for schema_type in priority_types:
            for schema in self.schemas:
                if schema.get('@type') == schema_type:
                    schemas_by_priority.append(schema)
        
        # Add any remaining schemas
        for schema in self.schemas:
            if schema not in schemas_by_priority:
                schemas_by_priority.append(schema)
        
        # Process schemas to extract metadata
        for schema in schemas_by_priority:
            schema_type = schema.get('@type')
            
            # Extract title
            if not metadata['title']:
                if 'headline' in schema:
                    metadata['title'] = schema['headline']
                elif 'name' in schema:
                    metadata['title'] = schema['name']
                elif 'title' in schema:
                    metadata['title'] = schema['title']
            
            # Extract author
            if not metadata['author']:
                if 'author' in schema:
                    author = schema['author']
                    if isinstance(author, dict):
                        if 'name' in author:
                            metadata['author'] = author['name']
                    elif isinstance(author, list):
                        authors = []
                        for auth in author[:3]:  # Limit to first 3 authors
                            if isinstance(auth, dict) and 'name' in auth:
                                authors.append(auth['name'])
                            elif isinstance(auth, str):
                                authors.append(auth)
                        
                        if authors:
                            if len(author) > 3:
                                metadata['author'] = f"{', '.join(authors)}, et al."
                            else:
                                metadata['author'] = ', '.join(authors)
                elif 'creator' in schema:
                    creator = schema['creator']
                    if isinstance(creator, dict) and 'name' in creator:
                        metadata['author'] = creator['name']
                    elif isinstance(creator, str):
                        metadata['author'] = creator
            
            # Extract institution/publisher
            if not metadata['institution']:
                if 'publisher' in schema:
                    publisher = schema['publisher']
                    if isinstance(publisher, dict) and 'name' in publisher:
                        metadata['institution'] = publisher['name']
                    elif isinstance(publisher, str):
                        metadata['institution'] = publisher
                elif 'sourceOrganization' in schema:
                    org = schema['sourceOrganization']
                    if isinstance(org, dict) and 'name' in org:
                        metadata['institution'] = org['name']
                    elif isinstance(org, str):
                        metadata['institution'] = org
            
            # Extract publication date
            if not metadata['date_published']:
                if 'datePublished' in schema:
                    date_str = schema['datePublished']
                    try:
                        if 'T' in date_str:  # ISO format
                            date = timezone.datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
                        else:
                            date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
                        metadata['date_published'] = date
                    except (ValueError, TypeError):
                        pass
                elif 'dateCreated' in schema:
                    date_str = schema['dateCreated']
                    try:
                        if 'T' in date_str:  # ISO format
                            date = timezone.datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
                        else:
                            date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
                        metadata['date_published'] = date
                    except (ValueError, TypeError):
                        pass
            
            # Extract DOI
            if not metadata['doi']:
                if 'sameAs' in schema:
                    same_as = schema['sameAs']
                    if isinstance(same_as, str):
                        doi_match = re.search(r'doi\.org/(10\.\d{4,9}/[-.;()/:A-Z0-9]+)', same_as, re.IGNORECASE)
                        if doi_match:
                            metadata['doi'] = doi_match.group(1)
                    elif isinstance(same_as, list):
                        for url in same_as:
                            doi_match = re.search(r'doi\.org/(10\.\d{4,9}/[-.;()/:A-Z0-9]+)', url, re.IGNORECASE)
                            if doi_match:
                                metadata['doi'] = doi_match.group(1)
                                break
                elif 'identifier' in schema:
                    identifier = schema['identifier']
                    if isinstance(identifier, dict) and identifier.get('@type') == 'PropertyValue':
                        if identifier.get('propertyID') == 'DOI' and 'value' in identifier:
                            metadata['doi'] = identifier['value']
                    elif isinstance(identifier, list):
                        for id_item in identifier:
                            if isinstance(id_item, dict) and id_item.get('@type') == 'PropertyValue':
                                if id_item.get('propertyID') == 'DOI' and 'value' in id_item:
                                    metadata['doi'] = id_item['value']
                                    break
            
            # Determine source type
            if schema_type in ['ScholarlyArticle', 'AcademicArticle']:
                metadata['source_type'] = 'paper'
            elif schema_type in ['Article', 'NewsArticle', 'BlogPosting']:
                metadata['source_type'] = 'news'
            elif schema_type == 'Book':
                metadata['source_type'] = 'book'
            elif schema_type == 'VideoObject':
                metadata['source_type'] = 'video'
            
            # Once we've found enough metadata, stop processing
            if (metadata['title'] and metadata['author'] and 
                metadata['institution'] and metadata['date_published']):
                break
        
        return metadata