# File: backend/utils/parsers/doi.py
import requests
import json
from django.utils import timezone

class DOIResolver:
    """
    Class for resolving DOIs and retrieving metadata from CrossRef and DataCite
    """
    
    def __init__(self, doi):
        self.doi = doi.strip()
        if self.doi.startswith('https://doi.org/'):
            self.doi = self.doi[16:]
        elif self.doi.startswith('doi:'):
            self.doi = self.doi[4:]
    
    def get_metadata(self):
        """
        Try to get metadata from CrossRef or DataCite
        """
        # First try CrossRef
        crossref_data = self._query_crossref()
        if crossref_data:
            return self._parse_crossref(crossref_data)
        
        # If not found, try DataCite
        datacite_data = self._query_datacite()
        if datacite_data:
            return self._parse_datacite(datacite_data)
        
        return None
    
    def _query_crossref(self):
        """Query the CrossRef API for DOI metadata"""
        url = f"https://api.crossref.org/works/{self.doi}"
        headers = {
            'User-Agent': 'PublicSphere SourceExchange (https://publicsphere.fyi; mailto:support@publicsphere.fyi)'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException:
            pass
        
        return None
    
    def _query_datacite(self):
        """Query the DataCite API for DOI metadata"""
        url = f"https://api.datacite.org/dois/{self.doi}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException:
            pass
        
        return None
    
    def _parse_crossref(self, data):
        """Parse CrossRef response into metadata dictionary"""
        try:
            work = data.get('message', {})
            metadata = {
                'title': None,
                'author': None,
                'institution': None,
                'date_published': None,
                'date_accessed': timezone.now().date(),
                'doi': self.doi,
                'source_type': 'paper',
                'url': f"https://doi.org/{self.doi}"
            }
            
            # Extract title
            if 'title' in work and work['title']:
                metadata['title'] = work['title'][0]
            
            # Extract authors
            if 'author' in work and work['author']:
                authors = []
                for author in work['author'][:3]:  # Limit to first 3 authors
                    name_parts = []
                    if 'given' in author:
                        name_parts.append(author['given'])
                    if 'family' in author:
                        name_parts.append(author['family'])
                    if name_parts:
                        authors.append(' '.join(name_parts))
                
                if authors:
                    if len(work['author']) > 3:
                        metadata['author'] = f"{', '.join(authors)}, et al."
                    else:
                        metadata['author'] = ', '.join(authors)
            
            # Extract publisher/institution
            if 'publisher' in work:
                metadata['institution'] = work['publisher']
            
            # Extract publication date
            if 'published-print' in work and 'date-parts' in work['published-print']:
                date_parts = work['published-print']['date-parts'][0]
                if len(date_parts) >= 3:
                    metadata['date_published'] = timezone.datetime(
                        date_parts[0], date_parts[1], date_parts[2]
                    ).date()
                elif len(date_parts) == 2:
                    metadata['date_published'] = timezone.datetime(
                        date_parts[0], date_parts[1], 1
                    ).date()
                elif len(date_parts) == 1:
                    metadata['date_published'] = timezone.datetime(
                        date_parts[0], 1, 1
                    ).date()
            
            # Determine source type
            if 'type' in work:
                work_type = work['type'].lower()
                if work_type in ['journal-article', 'proceedings-article']:
                    metadata['source_type'] = 'paper'
                elif work_type in ['book', 'monograph']:
                    metadata['source_type'] = 'book'
                elif work_type in ['posted-content', 'web-content']:
                    metadata['source_type'] = 'news'
            
            return metadata
            
        except (KeyError, IndexError, TypeError) as e:
            print(f"Error parsing CrossRef data: {e}")
            return None
    
    def _parse_datacite(self, data):
        """Parse DataCite response into metadata dictionary"""
        try:
            attributes = data.get('data', {}).get('attributes', {})
            metadata = {
                'title': None,
                'author': None,
                'institution': None,
                'date_published': None,
                'date_accessed': timezone.now().date(),
                'doi': self.doi,
                'source_type': 'paper',
                'url': f"https://doi.org/{self.doi}"
            }
            
            # Extract title
            if 'titles' in attributes and attributes['titles']:
                for title in attributes['titles']:
                    if 'title' in title:
                        metadata['title'] = title['title']
                        break
            
            # Extract authors
            if 'creators' in attributes and attributes['creators']:
                authors = []
                for creator in attributes['creators'][:3]:  # Limit to first 3
                    if 'name' in creator:
                        authors.append(creator['name'])
                    elif 'givenName' in creator and 'familyName' in creator:
                        authors.append(f"{creator['givenName']} {creator['familyName']}")
                
                if authors:
                    if len(attributes['creators']) > 3:
                        metadata['author'] = f"{', '.join(authors)}, et al."
                    else:
                        metadata['author'] = ', '.join(authors)
            
            # Extract publisher/institution
            if 'publisher' in attributes:
                metadata['institution'] = attributes['publisher']
            
            # Extract publication date
            if 'publicationYear' in attributes:
                try:
                    year = int(attributes['publicationYear'])
                    metadata['date_published'] = timezone.datetime(year, 1, 1).date()
                except (ValueError, TypeError):
                    pass
            
            # Extract more precise date if available
            if 'dates' in attributes:
                for date_entry in attributes['dates']:
                    if date_entry.get('dateType') == 'Issued' and 'date' in date_entry:
                        date_str = date_entry['date']
                        try:
                            # Try parsing as YYYY-MM-DD
                            if len(date_str) >= 10:
                                date = timezone.datetime.strptime(date_str[:10], '%Y-%m-%d').date()
                                metadata['date_published'] = date
                                break
                        except ValueError:
                            pass
            
            # Determine source type
            if 'resourceType' in attributes:
                resource_type = attributes['resourceType'].get('resourceTypeGeneral', '').lower()
                if resource_type in ['text', 'journalarticle', 'article']:
                    metadata['source_type'] = 'paper'
                elif resource_type in ['book', 'monograph']:
                    metadata['source_type'] = 'book'
                elif resource_type in ['audiovisual', 'video']:
                    metadata['source_type'] = 'video'
            
            return metadata
            
        except (KeyError, IndexError, TypeError) as e:
            print(f"Error parsing DataCite data: {e}")
            return None