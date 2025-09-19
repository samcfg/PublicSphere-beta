# File: backend/utils/parsers/opengraph.py
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urlparse
from django.utils import timezone

class OpenGraphParser:
    """
    Parser for extracting bibliographic metadata from web pages using OpenGraph,
    Twitter Cards, Schema.org, and other metadata formats.
    """
    
    def __init__(self, url):
        self.url = url
        self.metadata = {
            'title': None,
            'author': None,
            'institution': None,
            'date_published': None,
            'date_accessed': timezone.now().date(),
            'doi': None,
            'source_type': 'other',
            'url': url
        }
        self.confidence = {
            'title': 0,
            'author': 0,
            'institution': 0,
            'date_published': 0,
            'doi': 0,
            'source_type': 0
        }
    
    def fetch_page(self):
        """Fetch the web page content"""
        headers = {
            'User-Agent': 'PublicSphere SourceExchange Metadata Parser (https://publicsphere.fyi)'
        }
        try:
            response = requests.get(self.url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch page: {str(e)}")
    
    def parse(self):
        """
        Parse the web page and extract metadata using various methods
        """
        html = self.fetch_page()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try different metadata extraction methods in order of priority
        self._extract_opengraph(soup)
        self._extract_twitter_cards(soup)
        self._extract_schema_org(soup)
        self._extract_meta_tags(soup)
        self._extract_doi(soup, html)
        self._extract_citation_meta(soup)
        self._determine_source_type(soup)
        
        # Fall back to basic HTML for any missing fields
        self._extract_basic_html(soup)
        
        return self.metadata, self.confidence
    
    def _extract_opengraph(self, soup):
        """Extract metadata from OpenGraph tags"""
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            self.metadata['title'] = og_title['content']
            self.confidence['title'] = 0.9
        
        og_site_name = soup.find('meta', property='og:site_name')
        if og_site_name and og_site_name.get('content'):
            self.metadata['institution'] = og_site_name['content']
            self.confidence['institution'] = 0.7
        
        og_type = soup.find('meta', property='og:type')
        if og_type and og_type.get('content'):
            if og_type['content'] == 'article':
                self.metadata['source_type'] = 'news'
                self.confidence['source_type'] = 0.7
            elif og_type['content'] == 'book':
                self.metadata['source_type'] = 'book'
                self.confidence['source_type'] = 0.8
    
    def _extract_twitter_cards(self, soup):
        """Extract metadata from Twitter Card tags"""
        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
        if twitter_title and twitter_title.get('content') and not self.metadata['title']:
            self.metadata['title'] = twitter_title['content']
            self.confidence['title'] = 0.8
        
        twitter_creator = soup.find('meta', attrs={'name': 'twitter:creator'})
        if twitter_creator and twitter_creator.get('content') and not self.metadata['author']:
            author = twitter_creator['content']
            if author.startswith('@'):
                author = author[1:]
            self.metadata['author'] = author
            self.confidence['author'] = 0.6
    
    def _extract_schema_org(self, soup):
        """Extract metadata from Schema.org JSON-LD"""
        schema_tags = soup.find_all('script', type='application/ld+json')
        for tag in schema_tags:
            try:
                schema_data = json.loads(tag.string)
                if isinstance(schema_data, list):
                    schema_data = schema_data[0]
                
                # Extract data based on Schema.org type
                if '@type' in schema_data:
                    # Handle different types
                    if schema_data['@type'] in ['Article', 'NewsArticle', 'BlogPosting']:
                        if 'headline' in schema_data and not self.metadata['title']:
                            self.metadata['title'] = schema_data['headline']
                            self.confidence['title'] = 0.9
                        
                        if 'author' in schema_data and not self.metadata['author']:
                            author = schema_data['author']
                            if isinstance(author, dict) and 'name' in author:
                                self.metadata['author'] = author['name']
                                self.confidence['author'] = 0.9
                            elif isinstance(author, list) and len(author) > 0:
                                if isinstance(author[0], dict) and 'name' in author[0]:
                                    self.metadata['author'] = author[0]['name']
                                    self.confidence['author'] = 0.9
                                elif isinstance(author[0], str):
                                    self.metadata['author'] = author[0]
                                    self.confidence['author'] = 0.8
                        
                        if 'publisher' in schema_data and not self.metadata['institution']:
                            publisher = schema_data['publisher']
                            if isinstance(publisher, dict) and 'name' in publisher:
                                self.metadata['institution'] = publisher['name']
                                self.confidence['institution'] = 0.9
                        
                        if 'datePublished' in schema_data and not self.metadata['date_published']:
                            try:
                                date_str = schema_data['datePublished']
                                # Convert ISO format to date object
                                date = timezone.datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
                                self.metadata['date_published'] = date
                                self.confidence['date_published'] = 0.9
                            except ValueError:
                                pass
                        
                        self.metadata['source_type'] = 'news'
                        self.confidence['source_type'] = 0.9
                    
                    elif schema_data['@type'] == 'Book':
                        if 'name' in schema_data and not self.metadata['title']:
                            self.metadata['title'] = schema_data['name']
                            self.confidence['title'] = 0.9
                        
                        if 'author' in schema_data and not self.metadata['author']:
                            author = schema_data['author']
                            if isinstance(author, dict) and 'name' in author:
                                self.metadata['author'] = author['name']
                                self.confidence['author'] = 0.9
                        
                        if 'publisher' in schema_data and not self.metadata['institution']:
                            publisher = schema_data['publisher']
                            if isinstance(publisher, dict) and 'name' in publisher:
                                self.metadata['institution'] = publisher['name']
                                self.confidence['institution'] = 0.9
                        
                        self.metadata['source_type'] = 'book'
                        self.confidence['source_type'] = 0.9
                    
                    elif schema_data['@type'] == 'ScholarlyArticle':
                        if 'name' in schema_data and not self.metadata['title']:
                            self.metadata['title'] = schema_data['name']
                            self.confidence['title'] = 0.9
                        elif 'headline' in schema_data and not self.metadata['title']:
                            self.metadata['title'] = schema_data['headline']
                            self.confidence['title'] = 0.9
                        
                        if 'author' in schema_data and not self.metadata['author']:
                            author = schema_data['author']
                            if isinstance(author, dict) and 'name' in author:
                                self.metadata['author'] = author['name']
                                self.confidence['author'] = 0.9
                            elif isinstance(author, list) and len(author) > 0:
                                if isinstance(author[0], dict) and 'name' in author[0]:
                                    authors = [a['name'] for a in author if 'name' in a]
                                    self.metadata['author'] = ', '.join(authors[:3])
                                    if len(authors) > 3:
                                        self.metadata['author'] += ', et al.'
                                    self.confidence['author'] = 0.9
                        
                        if 'publisher' in schema_data and not self.metadata['institution']:
                            publisher = schema_data['publisher']
                            if isinstance(publisher, dict) and 'name' in publisher:
                                self.metadata['institution'] = publisher['name']
                                self.confidence['institution'] = 0.9
                        
                        if 'datePublished' in schema_data and not self.metadata['date_published']:
                            try:
                                date_str = schema_data['datePublished']
                                date = timezone.datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
                                self.metadata['date_published'] = date
                                self.confidence['date_published'] = 0.9
                            except ValueError:
                                pass
                        
                        self.metadata['source_type'] = 'paper'
                        self.confidence['source_type'] = 0.9
            except (json.JSONDecodeError, TypeError):
                continue
    
    def _extract_meta_tags(self, soup):
        """Extract metadata from standard meta tags"""
        # Title from meta tags
        if not self.metadata['title']:
            meta_title = soup.find('meta', attrs={'name': 'title'})
            if meta_title and meta_title.get('content'):
                self.metadata['title'] = meta_title['content']
                self.confidence['title'] = 0.7
        
        # Author from meta tags
        if not self.metadata['author']:
            meta_author = soup.find('meta', attrs={'name': ['author', 'citation_author']})
            if meta_author and meta_author.get('content'):
                self.metadata['author'] = meta_author['content']
                self.confidence['author'] = 0.8
        
        # Date from meta tags
        if not self.metadata['date_published']:
            meta_date = soup.find('meta', attrs={'name': ['date', 'pubdate', 'publication_date', 'citation_publication_date']})
            if meta_date and meta_date.get('content'):
                try:
                    date_str = meta_date['content']
                    # Try different date formats
                    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y', '%B %d, %Y', '%b %d, %Y']:
                        try:
                            date = timezone.datetime.strptime(date_str, fmt).date()
                            self.metadata['date_published'] = date
                            self.confidence['date_published'] = 0.8
                            break
                        except ValueError:
                            continue
                except Exception:
                    pass
    
    def _extract_doi(self, soup, html):
        """Extract DOI from the page"""
        # Check meta tags first
        meta_doi = soup.find('meta', attrs={'name': ['doi', 'citation_doi']})
        if meta_doi and meta_doi.get('content'):
            self.metadata['doi'] = meta_doi['content']
            self.confidence['doi'] = 0.9
            return
        
        # Try to find DOI in the page content
        doi_patterns = [
            r'(?:DOI|doi):\s*(10\.\d{4,9}/[-.;()/:A-Z0-9]+)',
            r'(?:https?://)?(?:dx\.)?doi\.org/(10\.\d{4,9}/[-.;()/:A-Z0-9]+)'
        ]
        
        for pattern in doi_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                self.metadata['doi'] = match.group(1)
                self.confidence['doi'] = 0.8
                break
    
    def _extract_citation_meta(self, soup):
        """Extract metadata from citation-specific meta tags"""
        # These tags are commonly used in academic publishing platforms
        citation_title = soup.find('meta', attrs={'name': 'citation_title'})
        if citation_title and citation_title.get('content') and not self.metadata['title']:
            self.metadata['title'] = citation_title['content']
            self.confidence['title'] = 0.9
        
        citation_authors = soup.find_all('meta', attrs={'name': 'citation_author'})
        if citation_authors and not self.metadata['author']:
            authors = [author['content'] for author in citation_authors if 'content' in author.attrs]
            if authors:
                if len(authors) <= 3:
                    self.metadata['author'] = ', '.join(authors)
                else:
                    self.metadata['author'] = f"{authors[0]}, et al."
                self.confidence['author'] = 0.9
        
        citation_publication = soup.find('meta', attrs={'name': 'citation_journal_title'})
        if citation_publication and citation_publication.get('content') and not self.metadata['institution']:
            self.metadata['institution'] = citation_publication['content']
            self.confidence['institution'] = 0.9
        
        citation_date = soup.find('meta', attrs={'name': 'citation_date'})
        if not citation_date:
            citation_date = soup.find('meta', attrs={'name': 'citation_publication_date'})
        
        if citation_date and citation_date.get('content') and not self.metadata['date_published']:
            try:
                date_str = citation_date['content']
                # Try different date formats
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y']:
                    try:
                        date = timezone.datetime.strptime(date_str, fmt).date()
                        self.metadata['date_published'] = date
                        self.confidence['date_published'] = 0.9
                        break
                    except ValueError:
                        continue
            except Exception:
                pass
        
        # If we have citation metadata, this is likely a scholarly article
        if citation_title or citation_authors or citation_publication:
            self.metadata['source_type'] = 'paper'
            self.confidence['source_type'] = 0.9
    
    def _extract_basic_html(self, soup):
        """
        Extract metadata from basic HTML elements as a fallback
        """
        # Title from title tag
        if not self.metadata['title']:
            title_tag = soup.find('title')
            if title_tag and title_tag.string:
                # Clean up title - remove site name if present
                title = title_tag.string.strip()
                pipe_split = title.split('|')
                if len(pipe_split) > 1:
                    title = pipe_split[0].strip()
                dash_split = title.split('-')
                if len(dash_split) > 1 and len(dash_split[-1]) < 30:
                    title = ' '.join(dash_split[:-1]).strip()
                
                self.metadata['title'] = title
                self.confidence['title'] = 0.5
        
        # Try to extract author from byline or article metadata
        if not self.metadata['author']:
            author_candidates = [
                soup.find('span', class_=lambda c: c and ('author' in c.lower() or 'byline' in c.lower())),
                soup.find('div', class_=lambda c: c and ('author' in c.lower() or 'byline' in c.lower())),
                soup.find('a', class_=lambda c: c and ('author' in c.lower() or 'byline' in c.lower())),
                soup.find('p', class_=lambda c: c and ('author' in c.lower() or 'byline' in c.lower()))
            ]
            
            for candidate in author_candidates:
                if candidate and candidate.string:
                    text = candidate.string.strip()
                    # Clean up author text (remove "By" prefix)
                    if text.lower().startswith('by '):
                        text = text[3:].strip()
                    self.metadata['author'] = text
                    self.confidence['author'] = 0.5
                    break
    
    def _determine_source_type(self, soup):
        """Determine the source type based on URL and page content"""
        if self.confidence['source_type'] >= 0.7:
            return  # Already determined with high confidence
        
        # Check URL patterns
        domain = urlparse(self.url).netloc.lower()
        
        # Academic domains
        academic_domains = ['.edu', '.ac.', 'arxiv.org', 'researchgate.net', 'academia.edu', 'ssrn.com']
        if any(domain.endswith(d) or d in domain for d in academic_domains):
            self.metadata['source_type'] = 'paper'
            self.confidence['source_type'] = 0.7
            return
        
        # News domains
        news_domains = [
            'news', 'nytimes.com', 'washingtonpost.com', 'bbc.', 'cnn.com', 
            'reuters.com', 'bloomberg.com', 'guardian.'
        ]
        if any(d in domain for d in news_domains):
            self.metadata['source_type'] = 'news'
            self.confidence['source_type'] = 0.7
            return
        
        # Video sites
        video_domains = ['youtube.com', 'vimeo.com', 'dailymotion.com', 'twitch.tv']
        if any(d in domain for d in video_domains):
            self.metadata['source_type'] = 'video'
            self.confidence['source_type'] = 0.8
            return
        
        # Check page content
        # Academic indicators
        academic_indicators = [
            'abstract', 'methodology', 'conclusion', 'references', 'bibliography',
            'journal', 'volume', 'issue', 'peer-reviewed', 'doi:', 'cite this'
        ]
        content_text = ' '.join([p.get_text().lower() for p in soup.find_all('p')])
        if sum(1 for word in academic_indicators if word in content_text) >= 3:
            self.metadata['source_type'] = 'paper'
            self.confidence['source_type'] = 0.6
            return
        
        # News indicators
        news_indicators = ['article', 'editorial', 'op-ed', 'reported', 'journalist']
        if sum(1 for word in news_indicators if word in content_text) >= 2:
            self.metadata['source_type'] = 'news'
            self.confidence['source_type'] = 0.6
            return