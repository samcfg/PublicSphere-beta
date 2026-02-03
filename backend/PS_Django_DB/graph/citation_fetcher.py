"""
Citation metadata extraction from URLs, identifiers, and PDFs.

Waterfall strategy:
1. Identifier extraction (DOI, ISBN, ISSN, arXiv, bioRxiv, etc.)
2. API lookup (CrossRef, OpenLibrary, arXiv API)
3. HTML metadata tags (Highwire Press, Dublin Core, OpenGraph)
4. PDF metadata (XMP, DOI extraction, structure parsing)
5. Fallback: basic web page metadata
"""

import re
import requests
from bs4 import BeautifulSoup
from datetime import date
from typing import Optional
from urllib.parse import urlparse
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class CitationFetcher:
    """Extract citation metadata from URLs, identifiers, and PDFs"""

    # User agent for HTTP requests (identify as PublicSphere)
    USER_AGENT = 'PublicSphere/1.0 (https://publicsphere.org; mailto:contact@publicsphere.org)'

    # API endpoints
    CROSSREF_API = 'https://api.crossref.org/works/'
    ARXIV_API = 'https://export.arxiv.org/api/query'
    OPENLIBRARY_API = 'https://openlibrary.org/api/books'

    @classmethod
    def fetch_from_url(cls, url: str) -> dict:
        """
        Main entry point: extract citation metadata from URL.

        Returns:
            {
                'success': bool,
                'source': str,  # 'crossref', 'arxiv', 'html_meta', 'fallback'
                'confidence': str,  # 'high', 'medium', 'low'
                'metadata': {
                    'title': str,
                    'authors': [{'name': str, 'role': 'author'}],
                    'url': str,
                    'doi': str,
                    'source_type': str,
                    'container_title': str,
                    'publication_date': str,
                    'volume': str,
                    'issue': str,
                    'pages': str,
                    'publisher': str,
                    'isbn': str,
                    'issn': str,
                    'accessed_date': str,
                    # ... other fields
                }
            }
        """
        # 1. Try identifier extraction + API lookup
        doi = cls._extract_doi(url)
        if doi:
            result = cls._fetch_crossref(doi)
            if result:
                return {
                    'success': True,
                    'source': 'crossref',
                    'confidence': 'high',
                    'metadata': result
                }

        # Check for bioRxiv/medRxiv (they use DOIs but need special handling)
        biorxiv_doi = cls._extract_biorxiv_id(url)
        if biorxiv_doi:
            result = cls._fetch_crossref(biorxiv_doi)
            if result:
                result['source_type'] = 'preprint'  # Override to preprint
                if 'metadata' not in result:
                    result['metadata'] = {}
                result['metadata']['archive'] = 'bioRxiv' if 'biorxiv' in url else 'medRxiv'
                return {
                    'success': True,
                    'source': 'crossref',
                    'confidence': 'high',
                    'metadata': result
                }

        arxiv_id = cls._extract_arxiv_id(url)
        if arxiv_id:
            result = cls._fetch_arxiv(arxiv_id)
            if result:
                return {
                    'success': True,
                    'source': 'arxiv',
                    'confidence': 'high',
                    'metadata': result
                }

        # 2. HTML metadata extraction
        try:
            html_metadata = cls._fetch_html_metadata(url)
            if html_metadata.get('title'):
                confidence = html_metadata.pop('_confidence', 'medium')
                return {
                    'success': True,
                    'source': 'html_meta',
                    'confidence': confidence,
                    'metadata': html_metadata
                }
        except Exception as e:
            # Log error but continue to fallback
            print(f"HTML metadata extraction failed: {e}")

        # 3. Fallback: minimal metadata
        return {
            'success': True,
            'source': 'fallback',
            'confidence': 'low',
            'metadata': {
                'url': url,
                'accessed_date': date.today().isoformat(),
                'source_type': 'website',
            }
        }

    @classmethod
    def fetch_from_pdf(cls, pdf_file) -> dict:
        """
        Extract metadata from uploaded PDF file.

        Args:
            pdf_file: Django UploadedFile object

        Returns: Same format as fetch_from_url()
        """
        if not PDF_AVAILABLE:
            return {
                'success': False,
                'source': 'pdf_unavailable',
                'confidence': 'low',
                'metadata': {'error': 'PDF extraction not available (PyPDF2 not installed)'}
            }

        # 1. Extract XMP metadata (embedded by publishers)
        metadata = cls._extract_pdf_xmp(pdf_file)
        if metadata.get('doi'):
            # If we found DOI in PDF, fetch from CrossRef
            crossref_data = cls._fetch_crossref(metadata['doi'])
            if crossref_data:
                return {
                    'success': True,
                    'source': 'pdf_xmp_crossref',
                    'confidence': 'high',
                    'metadata': crossref_data
                }

        # 2. Pattern match for DOI in PDF text
        doi = cls._extract_doi_from_pdf_text(pdf_file)
        if doi:
            crossref_data = cls._fetch_crossref(doi)
            if crossref_data:
                return {
                    'success': True,
                    'source': 'pdf_text_crossref',
                    'confidence': 'high',
                    'metadata': crossref_data
                }

        # 3. Return whatever we extracted from PDF metadata
        if metadata:
            return {
                'success': True,
                'source': 'pdf_metadata',
                'confidence': 'medium',
                'metadata': metadata
            }

        # Fallback: no metadata found
        return {
            'success': False,
            'source': 'pdf_fallback',
            'confidence': 'low',
            'metadata': {'source_type': 'unknown'}
        }

    # ========== IDENTIFIER EXTRACTION ==========

    @staticmethod
    def _extract_doi(url: str) -> Optional[str]:
        """
        Extract DOI from URL.

        Patterns:
            https://doi.org/10.1126/science.169.3946.635
            https://dx.doi.org/10.1234/foo
            http://www.nature.com/articles/10.1038/nature12345
        """
        # Direct DOI URL
        doi_pattern = r'doi\.org/(10\.\d{4,}/[^\s]+)'
        match = re.search(doi_pattern, url, re.IGNORECASE)
        if match:
            return match.group(1).rstrip('/')

        # DOI embedded in other URLs
        embedded_pattern = r'\b(10\.\d{4,}/[^\s]+)'
        match = re.search(embedded_pattern, url)
        if match:
            potential_doi = match.group(1)
            # Validate it looks like a real DOI (basic check)
            if '/' in potential_doi:
                return potential_doi.rstrip('/')

        return None

    @staticmethod
    def _extract_arxiv_id(url: str) -> Optional[str]:
        """
        Extract arXiv ID from URL.

        Patterns:
            https://arxiv.org/abs/2301.12345
            https://arxiv.org/pdf/2301.12345.pdf
        """
        patterns = [
            r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})',  # New format: 2301.12345
            r'arxiv\.org/(?:abs|pdf)/([a-z-]+/\d{7})',   # Old format: cs/0701123
        ]

        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    @staticmethod
    def _extract_biorxiv_id(url: str) -> Optional[str]:
        """
        Extract bioRxiv/medRxiv DOI from URL.

        Patterns:
            https://www.biorxiv.org/content/10.1101/2021.01.15.426820v1
            https://www.medrxiv.org/content/10.1101/2020.12.22.20248679v2
        """
        pattern = r'(?:bio|med)rxiv\.org/content/(10\.1101/[^\s]+)'
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            doi = match.group(1).rstrip('/')
            # Remove version suffix (v1, v2, etc.)
            doi = re.sub(r'v\d+$', '', doi)
            return doi
        return None

    @staticmethod
    def _extract_isbn(text: str) -> Optional[str]:
        """
        Extract ISBN from text (ISBN-10 or ISBN-13).

        Note: Usually extracted from HTML meta tags, not URL
        """
        # ISBN-13: 978-0-123-45678-9 (with or without hyphens)
        isbn13_pattern = r'978[-\s]?\d{1,5}[-\s]?\d{1,7}[-\s]?\d{1,7}[-\s]?\d'
        match = re.search(isbn13_pattern, text)
        if match:
            return re.sub(r'[-\s]', '', match.group(0))

        # ISBN-10: 0-123-45678-X
        isbn10_pattern = r'\d{1,5}[-\s]?\d{1,7}[-\s]?\d{1,7}[-\s]?[\dX]'
        match = re.search(isbn10_pattern, text)
        if match:
            return re.sub(r'[-\s]', '', match.group(0))

        return None

    @staticmethod
    def _extract_issn(text: str) -> Optional[str]:
        """Extract ISSN from text (format: 1234-5678)"""
        pattern = r'\d{4}-\d{3}[\dX]'
        match = re.search(pattern, text)
        return match.group(0) if match else None

    # ========== API FETCHERS ==========

    @classmethod
    def _fetch_crossref(cls, doi: str) -> Optional[dict]:
        """
        Fetch metadata from CrossRef API.

        Returns structured metadata dict or None if not found.
        """
        try:
            response = requests.get(
                f'{cls.CROSSREF_API}{doi}',
                headers={'User-Agent': cls.USER_AGENT},
                timeout=5
            )

            if response.status_code != 200:
                return None

            data = response.json()['message']

            # Parse CrossRef response into our schema
            authors = []
            for author in data.get('author', []):
                name_parts = []
                if author.get('family'):
                    name_parts.append(author['family'])
                if author.get('given'):
                    name_parts.append(author['given'])

                author_entry = {
                    'name': ', '.join(name_parts) if name_parts else 'Unknown',
                    'role': 'author'
                }

                # Add affiliation if available
                if author.get('affiliation') and len(author['affiliation']) > 0:
                    affiliation_name = author['affiliation'][0].get('name')
                    if affiliation_name:
                        author_entry['affiliation'] = affiliation_name

                authors.append(author_entry)

            # Determine source type from CrossRef type
            crossref_type = data.get('type', '')
            source_type_map = {
                'journal-article': 'journal_article',
                'book': 'book',
                'book-chapter': 'book_chapter',
                'proceedings-article': 'conference_paper',
                'posted-content': 'preprint',
            }
            source_type = source_type_map.get(crossref_type, 'journal_article')

            # Parse date (CrossRef provides as array: [[2021, 1, 15]])
            pub_date = None
            date_parts = data.get('published-print', data.get('published-online', {})).get('date-parts', [[]])
            if date_parts and date_parts[0]:
                # Convert [2021, 1, 15] to "2021-01-15" or "2021" if only year
                parts = date_parts[0]
                if len(parts) == 3:
                    pub_date = f"{parts[0]:04d}-{parts[1]:02d}-{parts[2]:02d}"
                elif len(parts) == 2:
                    pub_date = f"{parts[0]:04d}-{parts[1]:02d}"
                elif len(parts) == 1:
                    pub_date = f"{parts[0]:04d}"

            metadata = {
                'title': data.get('title', [''])[0] if data.get('title') else None,
                'authors': authors if authors else None,
                'doi': doi,
                'source_type': source_type,
                'container_title': data.get('container-title', [''])[0] if data.get('container-title') else None,
                'publication_date': pub_date,
                'volume': data.get('volume'),
                'issue': data.get('issue'),
                'pages': data.get('page'),
                'publisher': data.get('publisher'),
                'issn': data.get('ISSN', [None])[0],
                'url': data.get('URL'),
                'accessed_date': date.today().isoformat(),
            }

            # Clean None values
            return {k: v for k, v in metadata.items() if v is not None}

        except Exception as e:
            print(f"CrossRef fetch failed for DOI {doi}: {e}")
            return None

    @classmethod
    def _fetch_arxiv(cls, arxiv_id: str) -> Optional[dict]:
        """Fetch metadata from arXiv API"""
        try:
            response = requests.get(
                cls.ARXIV_API,
                params={'id_list': arxiv_id},
                headers={'User-Agent': cls.USER_AGENT},
                timeout=5
            )

            if response.status_code != 200:
                return None

            # Parse XML response
            from xml.etree import ElementTree as ET
            root = ET.fromstring(response.content)

            # arXiv uses Atom namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entry = root.find('atom:entry', ns)

            if entry is None:
                return None

            # Extract authors
            authors = []
            for author_elem in entry.findall('atom:author', ns):
                name_elem = author_elem.find('atom:name', ns)
                if name_elem is not None:
                    authors.append({'name': name_elem.text, 'role': 'author'})

            # Extract DOI if present
            doi_elem = entry.find('atom:doi', ns)
            doi = doi_elem.text if doi_elem is not None else None

            # Extract title
            title_elem = entry.find('atom:title', ns)
            title = title_elem.text.strip() if title_elem is not None else None

            # Extract publication date
            published_elem = entry.find('atom:published', ns)
            pub_date = published_elem.text[:10] if published_elem is not None else None  # YYYY-MM-DD

            metadata = {
                'title': title,
                'authors': authors if authors else None,
                'publication_date': pub_date,
                'source_type': 'preprint',
                'url': f'https://arxiv.org/abs/{arxiv_id}',
                'container_title': 'arXiv',
                'accessed_date': date.today().isoformat(),
                'metadata': {
                    'arxiv_id': arxiv_id,
                    'archive': 'arXiv',
                }
            }

            if doi:
                metadata['doi'] = doi

            return {k: v for k, v in metadata.items() if v is not None}

        except Exception as e:
            print(f"arXiv fetch failed for ID {arxiv_id}: {e}")
            return None

    @classmethod
    def _fetch_openlibrary(cls, isbn: str) -> Optional[dict]:
        """Fetch book metadata from OpenLibrary API"""
        try:
            response = requests.get(
                cls.OPENLIBRARY_API,
                params={'bibkeys': f'ISBN:{isbn}', 'format': 'json', 'jscmd': 'data'},
                headers={'User-Agent': cls.USER_AGENT},
                timeout=5
            )

            if response.status_code != 200:
                return None

            data = response.json().get(f'ISBN:{isbn}')
            if not data:
                return None

            authors = [{'name': author['name'], 'role': 'author'}
                      for author in data.get('authors', [])]

            publishers = data.get('publishers', [])
            publisher = publishers[0].get('name') if publishers else None

            metadata = {
                'title': data.get('title'),
                'authors': authors if authors else None,
                'isbn': isbn,
                'source_type': 'book',
                'publisher': publisher,
                'publication_date': data.get('publish_date'),
                'url': data.get('url'),
                'accessed_date': date.today().isoformat(),
            }

            return {k: v for k, v in metadata.items() if v is not None}

        except Exception as e:
            print(f"OpenLibrary fetch failed for ISBN {isbn}: {e}")
            return None

    # ========== HTML METADATA EXTRACTION ==========

    @classmethod
    def _fetch_html_metadata(cls, url: str) -> dict:
        """
        Extract metadata from HTML meta tags.

        Priority: schema.org > Highwire Press > Dublin Core > OpenGraph > Basic HTML
        """
        try:
            response = requests.get(
                url,
                headers={'User-Agent': cls.USER_AGENT},
                timeout=10
            )

            if response.status_code != 200:
                return {}

            soup = BeautifulSoup(response.content, 'html.parser')

            # Try extraction methods in order of reliability
            # 1. schema.org JSON-LD (most structured, increasingly common)
            metadata = cls._extract_schema_org(soup, url)
            if metadata.get('title'):
                metadata['_confidence'] = 'high'
                return metadata

            # 2. Highwire Press (academic publishers)
            metadata = cls._extract_highwire_metadata(soup, url)
            if metadata.get('title'):
                metadata['_confidence'] = 'high'
                return metadata

            # 3. Dublin Core (libraries, repositories)
            metadata = cls._extract_dublin_core_metadata(soup, url)
            if metadata.get('title'):
                metadata['_confidence'] = 'medium'
                return metadata

            # 4. OpenGraph (social sharing)
            metadata = cls._extract_opengraph_metadata(soup, url)
            if metadata.get('title'):
                metadata['_confidence'] = 'medium'
                return metadata

            # Fallback: basic HTML
            title_tag = soup.find('title')
            return {
                'title': title_tag.string.strip() if title_tag and title_tag.string else None,
                'url': url,
                'accessed_date': date.today().isoformat(),
                'source_type': 'website',
                '_confidence': 'low',
            }

        except Exception as e:
            print(f"HTML metadata extraction failed: {e}")
            return {}

    @staticmethod
    def _extract_schema_org(soup: BeautifulSoup, url: str) -> dict:
        """
        Extract schema.org JSON-LD metadata (NewsArticle, ScholarlyArticle, Book, etc.).

        Common types: NewsArticle, Article, ScholarlyArticle, Book, Report
        """
        import json

        # Find all JSON-LD script tags
        json_ld_tags = soup.find_all('script', type='application/ld+json')

        for tag in json_ld_tags:
            try:
                data = json.loads(tag.string)

                # Handle @graph arrays (some sites wrap multiple schemas)
                if isinstance(data, dict) and '@graph' in data:
                    # Search for article/creative work types in graph
                    for item in data['@graph']:
                        if CitationFetcher._is_schema_creative_work(item.get('@type')):
                            data = item
                            break

                # Skip if not a creative work type
                if not CitationFetcher._is_schema_creative_work(data.get('@type')):
                    continue

                # Extract authors
                authors = []
                author_data = data.get('author', [])
                if not isinstance(author_data, list):
                    author_data = [author_data]

                for author in author_data:
                    if isinstance(author, dict):
                        name = author.get('name')
                        if name:
                            author_entry = {'name': name, 'role': 'author'}
                            # Add affiliation if present
                            if author.get('affiliation'):
                                affiliation = author['affiliation']
                                if isinstance(affiliation, dict):
                                    affiliation = affiliation.get('name')
                                if affiliation:
                                    author_entry['affiliation'] = affiliation
                            authors.append(author_entry)
                    elif isinstance(author, str):
                        authors.append({'name': author, 'role': 'author'})

                # Extract publication date
                pub_date = (
                    data.get('datePublished') or
                    data.get('dateCreated') or
                    data.get('publicationDate')
                )
                if pub_date:
                    # Truncate to YYYY-MM-DD if longer
                    pub_date = pub_date[:10] if len(pub_date) >= 10 else pub_date

                # Extract publisher
                publisher_data = data.get('publisher')
                publisher = None
                if isinstance(publisher_data, dict):
                    publisher = publisher_data.get('name')
                elif isinstance(publisher_data, str):
                    publisher = publisher_data

                # Extract container (journal, newspaper, website name)
                container = None
                if data.get('isPartOf'):
                    part_of = data['isPartOf']
                    if isinstance(part_of, dict):
                        container = part_of.get('name')

                # Map schema.org type to our source_type
                schema_type = data.get('@type', '')
                source_type = CitationFetcher._map_schema_type_to_source_type(schema_type)

                # Extract additional fields
                volume = data.get('volumeNumber')
                issue = data.get('issueNumber')
                pages = data.get('pagination')

                # Build metadata dict
                metadata = {
                    'title': data.get('headline') or data.get('name'),
                    'authors': authors if authors else None,
                    'publication_date': pub_date,
                    'container_title': container or publisher,
                    'publisher': publisher,
                    'url': data.get('url') or url,
                    'source_type': source_type,
                    'accessed_date': date.today().isoformat(),
                }

                # Add optional fields if present
                if volume:
                    metadata['volume'] = str(volume)
                if issue:
                    metadata['issue'] = str(issue)
                if pages:
                    metadata['pages'] = str(pages)

                # Extract DOI if present
                doi = data.get('doi')
                if doi:
                    metadata['doi'] = doi

                # Extract ISBN if present (books)
                isbn = data.get('isbn')
                if isbn:
                    metadata['isbn'] = isbn

                # Store article section in metadata overflow
                section = data.get('articleSection')
                if section:
                    if 'metadata' not in metadata:
                        metadata['metadata'] = {}
                    metadata['metadata']['section'] = section

                # Clean None values
                return {k: v for k, v in metadata.items() if v is not None}

            except (json.JSONDecodeError, AttributeError, KeyError) as e:
                # Skip malformed JSON-LD, try next script tag
                continue

        # No valid schema.org data found
        return {}

    @staticmethod
    def _is_schema_creative_work(schema_type) -> bool:
        """Check if schema.org @type is a creative work we can cite"""
        if not schema_type:
            return False

        # Handle both string and list types
        if isinstance(schema_type, list):
            schema_type = schema_type[0] if schema_type else ''

        creative_work_types = [
            'Article', 'NewsArticle', 'ScholarlyArticle', 'BlogPosting',
            'Book', 'Report', 'Thesis', 'CreativeWork',
            'WebPage',  # Sometimes used for articles
        ]

        return any(t in schema_type for t in creative_work_types)

    @staticmethod
    def _map_schema_type_to_source_type(schema_type: str) -> str:
        """Map schema.org @type to our source_type vocabulary"""
        if not schema_type:
            return 'website'

        # Handle list types (take first)
        if isinstance(schema_type, list):
            schema_type = schema_type[0] if schema_type else ''

        # Map to our types
        type_map = {
            'ScholarlyArticle': 'journal_article',
            'NewsArticle': 'newspaper',
            'BlogPosting': 'website',
            'Book': 'book',
            'Report': 'report',
            'Thesis': 'thesis',
            'Article': 'website',  # Generic, could be magazine/blog
            'WebPage': 'website',
        }

        for schema_t, our_type in type_map.items():
            if schema_t in schema_type:
                return our_type

        return 'website'

    @staticmethod
    def _extract_highwire_metadata(soup: BeautifulSoup, url: str) -> dict:
        """
        Extract Highwire Press meta tags (used by academic publishers).

        Tags: citation_title, citation_author, citation_journal_title, etc.
        """
        def get_meta(name):
            tag = soup.find('meta', attrs={'name': name})
            return tag.get('content') if tag else None

        # Get all authors
        authors = []
        for tag in soup.find_all('meta', attrs={'name': 'citation_author'}):
            content = tag.get('content')
            if content:
                authors.append({'name': content, 'role': 'author'})

        # Extract DOI and check for rxiv
        doi = get_meta('citation_doi')
        source_type = 'journal_article'

        if doi and '10.1101' in doi:
            source_type = 'preprint'

        # Parse pages
        first_page = get_meta('citation_firstpage')
        last_page = get_meta('citation_lastpage')
        pages = None
        if first_page and last_page:
            pages = f"{first_page}-{last_page}"
        elif first_page:
            pages = first_page

        metadata = {
            'title': get_meta('citation_title'),
            'authors': authors if authors else None,
            'container_title': get_meta('citation_journal_title'),
            'publication_date': get_meta('citation_publication_date') or get_meta('citation_date'),
            'volume': get_meta('citation_volume'),
            'issue': get_meta('citation_issue'),
            'pages': pages,
            'doi': doi,
            'issn': get_meta('citation_issn'),
            'isbn': get_meta('citation_isbn'),
            'publisher': get_meta('citation_publisher'),
            'url': url,
            'source_type': source_type,
            'accessed_date': date.today().isoformat(),
        }

        return {k: v for k, v in metadata.items() if v is not None}

    @staticmethod
    def _extract_dublin_core_metadata(soup: BeautifulSoup, url: str) -> dict:
        """Extract Dublin Core meta tags (used by libraries, repositories)"""
        def get_meta(name):
            tag = soup.find('meta', attrs={'name': f'DC.{name}'})
            if not tag:
                tag = soup.find('meta', attrs={'name': f'dc.{name}'})
            return tag.get('content') if tag else None

        # Authors (can be multiple DC.creator tags)
        authors = []
        for tag in soup.find_all('meta', attrs={'name': re.compile(r'^DC\.creator$', re.IGNORECASE)}):
            content = tag.get('content')
            if content:
                authors.append({'name': content, 'role': 'author'})

        metadata = {
            'title': get_meta('title'),
            'authors': authors if authors else None,
            'publication_date': get_meta('date'),
            'publisher': get_meta('publisher'),
            'url': url,
            'source_type': 'website',
            'accessed_date': date.today().isoformat(),
        }

        return {k: v for k, v in metadata.items() if v is not None}

    @staticmethod
    def _extract_opengraph_metadata(soup: BeautifulSoup, url: str) -> dict:
        """Extract OpenGraph meta tags (social sharing)"""
        def get_og_meta(prop):
            """Get og:property"""
            tag = soup.find('meta', attrs={'property': f'og:{prop}'})
            return tag.get('content') if tag else None

        def get_article_meta(prop):
            """Get article:property"""
            tag = soup.find('meta', attrs={'property': f'article:{prop}'})
            return tag.get('content') if tag else None

        # Authors from article:author tags
        authors = []
        for tag in soup.find_all('meta', attrs={'property': 'article:author'}):
            content = tag.get('content')
            if content:
                authors.append({'name': content, 'role': 'author'})

        # Publication date (truncate to YYYY-MM-DD if longer)
        pub_date = get_article_meta('published_time') or get_article_meta('published')
        if pub_date and len(pub_date) >= 10:
            pub_date = pub_date[:10]

        # Container title (site name)
        container = get_og_meta('site_name')

        # Publisher (less common, but sometimes present)
        publisher = get_article_meta('publisher')

        # Determine source_type from og:type
        og_type = get_og_meta('type') or ''
        source_type = 'website'
        if 'article' in og_type.lower():
            # Could be article, article:opinion, etc.
            source_type = 'newspaper'  # Assume news article unless we know better

        metadata = {
            'title': get_og_meta('title'),
            'authors': authors if authors else None,
            'publication_date': pub_date,
            'container_title': container,
            'publisher': publisher,
            'url': get_og_meta('url') or url,
            'source_type': source_type,
            'accessed_date': date.today().isoformat(),
        }

        # Store article section in metadata overflow if present
        section = get_article_meta('section')
        if section:
            metadata['metadata'] = {'section': section}

        return {k: v for k, v in metadata.items() if v is not None}

    # ========== PDF METADATA EXTRACTION ==========

    @staticmethod
    def _extract_pdf_xmp(pdf_file) -> dict:
        """Extract XMP metadata embedded in PDF"""
        if not PDF_AVAILABLE:
            return {}

        try:
            # Reset file pointer to beginning
            pdf_file.seek(0)
            reader = PyPDF2.PdfReader(pdf_file)
            info = reader.metadata

            if not info:
                return {}

            # Parse PDF date format (D:20210115120000) to ISO 8601
            creation_date = info.get('/CreationDate', '')
            pub_date = None
            if creation_date and creation_date.startswith('D:'):
                date_str = creation_date[2:10]  # Extract YYYYMMDD
                if len(date_str) == 8:
                    pub_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"

            authors = []
            author_str = info.get('/Author')
            if author_str:
                authors.append({'name': author_str, 'role': 'author'})

            metadata = {
                'title': info.get('/Title'),
                'authors': authors if authors else None,
                'publication_date': pub_date,
                'source_type': 'unknown',
            }

            return {k: v for k, v in metadata.items() if v is not None}

        except Exception as e:
            print(f"PDF XMP extraction failed: {e}")
            return {}

    @staticmethod
    def _extract_doi_from_pdf_text(pdf_file) -> Optional[str]:
        """
        Extract DOI by pattern matching in PDF text.

        Checks first 2 pages and last page (common DOI locations).
        """
        if not PDF_AVAILABLE:
            return None

        try:
            # Reset file pointer
            pdf_file.seek(0)
            reader = PyPDF2.PdfReader(pdf_file)

            # Check first 2 pages and last page
            pages_to_check = [0, 1]
            if len(reader.pages) > 2:
                pages_to_check.append(len(reader.pages) - 1)

            for page_num in pages_to_check:
                if page_num < len(reader.pages):
                    text = reader.pages[page_num].extract_text()

                    # Pattern: doi: 10.1234/foo or DOI: 10.1234/foo
                    pattern = r'doi:?\s*(10\.\d{4,}/[^\s]+)'
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        return match.group(1).rstrip('.')

            return None

        except Exception as e:
            print(f"PDF DOI extraction failed: {e}")
            return None
