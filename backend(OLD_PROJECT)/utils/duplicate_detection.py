# File: backend/utils/duplicate_detection.py
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import F, Q, Value
from django.db.models.functions import Greatest
import re
import string
from urllib.parse import urlparse, unquote

def normalize_url(url):
    """
    Normalize a URL for comparison by removing query parameters,
    standardizing protocol, etc.
    """
    if not url:
        return None
    
    try:
        # Parse the URL
        parsed = urlparse(url)
        
        # Normalize the hostname (lowercase, remove www.)
        hostname = parsed.netloc.lower()
        if hostname.startswith('www.'):
            hostname = hostname[4:]
        
        # Rebuild URL without query parameters and fragments
        normalized = f"{parsed.scheme}://{hostname}{parsed.path}"
        
        # Remove trailing slashes
        normalized = normalized.rstrip('/')
        
        return normalized
    except Exception:
        return url


def normalize_doi(doi):
    """
    Normalize a DOI for comparison
    """
    if not doi:
        return None
    
    # Extract DOI from various formats
    if doi.startswith('https://doi.org/'):
        doi = doi[16:]
    elif doi.startswith('http://doi.org/'):
        doi = doi[15:]
    elif doi.startswith('doi:'):
        doi = doi[4:]
    
    # Convert to lowercase
    return doi.lower().strip()


def normalize_title(title):
    """
    Normalize a title for comparison by removing punctuation,
    extra whitespace, stop words, etc.
    """
    if not title:
        return ""
    
    # Convert to lowercase
    title = title.lower()
    
    # Remove punctuation
    translator = str.maketrans('', '', string.punctuation)
    title = title.translate(translator)
    
    # Remove common stop words
    stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with'}
    words = title.split()
    words = [word for word in words if word not in stop_words]
    
    # Rejoin and normalize whitespace
    title = ' '.join(words)
    title = re.sub(r'\s+', ' ', title).strip()
    
    return title


def find_potential_duplicates(source_area, threshold=0.8):
    """
    Find potential duplicate source areas using a combination of
    exact matching and fuzzy matching.
    
    Args:
        source_area: A SourceArea object or dictionary with title, url, doi, etc.
        threshold: Similarity threshold (0.0 to 1.0) for considering a match
        
    Returns:
        A list of potential duplicate SourceArea objects with similarity scores
    """
    from apps.sources.models import SourceArea
    
    # Skip if the source area has no title, url, or doi
    if not source_area.get('title') and not source_area.get('url') and not source_area.get('doi'):
        return []
    
    # Start with an empty queryset
    duplicates = SourceArea.objects.none()
    exact_match_ids = set()
    
    # Check for exact URL match
    if source_area.get('url'):
        normalized_url = normalize_url(source_area['url'])
        if normalized_url:
            url_matches = SourceArea.objects.filter(url__isnull=False).exclude(id=source_area.get('id'))
            
            for match in url_matches:
                match_normalized = normalize_url(match.url)
                if match_normalized and match_normalized == normalized_url:
                    exact_match_ids.add(match.id)
    
    # Check for exact DOI match
    if source_area.get('doi'):
        normalized_doi = normalize_doi(source_area['doi'])
        if normalized_doi:
            doi_matches = SourceArea.objects.filter(doi__isnull=False).exclude(id=source_area.get('id'))
            
            for match in doi_matches:
                match_normalized = normalize_doi(match.doi)
                if match_normalized and match_normalized == normalized_doi:
                    exact_match_ids.add(match.id)
    
    # Filter out exact matches
    if exact_match_ids:
        duplicates = SourceArea.objects.filter(id__in=exact_match_ids)
    
    # Only perform fuzzy matching if no exact matches found
    if not duplicates.exists() and source_area.get('title'):
        normalized_title = normalize_title(source_area['title'])
        if normalized_title:
            # Filter sources that could be duplicates
            potential_matches = SourceArea.objects.exclude(id=source_area.get('id'))
            
            # Filter based on author or publication year if available
            if source_area.get('author'):
                author_words = source_area['author'].split()[:2]  # First two words of author
                author_filters = Q()
                for word in author_words:
                    if len(word) > 3:  # Avoid short words
                        author_filters |= Q(author__icontains=word)
                potential_matches = potential_matches.filter(author_filters)
            
            if source_area.get('date_published'):
                year = source_area['date_published'].year
                potential_matches = potential_matches.filter(
                    date_published__year__range=(year-1, year+1)
                )
            
            # Calculate similarity scores using trigram similarity
            similarity_threshold = threshold
            similar_titles = potential_matches.annotate(
                similarity=TrigramSimilarity('title', normalized_title)
            ).filter(similarity__gte=similarity_threshold)
            
            # Sort by similarity score
            similar_titles = similar_titles.order_by('-similarity')
            
            # Add to duplicates queryset
            duplicates = duplicates.union(similar_titles)
    
    # Return results with similarity scores
    return duplicates


def format_duplicate_suggestions(duplicates):
    """
    Format duplicate suggestions for display to the user.
    
    Args:
        duplicates: QuerySet of potential duplicates with similarity scores
        
    Returns:
        A list of dictionaries with formatted duplicate information
    """
    suggestions = []
    
    for duplicate in duplicates:
        # Create a dictionary with basic info
        suggestion = {
            'id': duplicate.id,
            'title': duplicate.title,
            'similarity': getattr(duplicate, 'similarity', 1.0),  # Default to 1.0 for exact matches
            'highlight': {}
        }
        
        # Add author if available
        if duplicate.author:
            suggestion['author'] = duplicate.author
        
        # Add URL if available
        if duplicate.url:
            suggestion['url'] = duplicate.url
        
        # Add DOI if available
        if duplicate.doi:
            suggestion['doi'] = duplicate.doi
        
        # Add date published if available
        if duplicate.date_published:
            suggestion['date_published'] = duplicate.date_published
        
        # Highlight matching fields
        if hasattr(duplicate, 'similarity') and duplicate.similarity < 1.0:
            suggestion['highlight']['title'] = True
        
        suggestions.append(suggestion)
    
    return suggestions