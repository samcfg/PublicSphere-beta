"""
Utilities for graph operations: normalization, deduplication, search helpers.
"""

from urllib.parse import urlparse, parse_qs
import re


def normalize_url(url: str) -> str | None:
    """
    Canonical URL form for duplicate detection.

    Examples:
        'HTTPS://WWW.Example.com/Article/' -> 'example.com/article'
        'http://example.com/page?utm=fb' -> 'example.com/page'

    Rules:
        - Lowercase
        - Remove protocol (http/https)
        - Remove www prefix
        - Remove trailing slashes
        - Remove query params (tracking parameters)
        - Remove fragments (#anchors)

    Returns:
        Normalized URL string, or None if input is empty/invalid
    """
    if not url or not url.strip():
        return None

    url = url.strip().lower()

    # Add protocol if missing (urlparse needs it)
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        path = parsed.path.rstrip('/')

        # Return canonical form: domain + path (no protocol, query, or fragment)
        return f"{domain}{path}" if domain else None
    except Exception:
        # Invalid URL format
        return None


def normalize_content(content: str) -> str:
    """
    Canonical content form for exact duplicate detection.

    Used for both claim content and source titles.

    Rules:
        - Lowercase
        - Trim whitespace
        - Collapse multiple spaces to single space

    Returns:
        Normalized content string
    """
    if not content:
        return ""

    # Collapse whitespace and lowercase
    return re.sub(r'\s+', ' ', content.strip().lower())


def normalize_doi(doi: str) -> str | None:
    """
    Canonical DOI form for duplicate detection.

    Examples:
        'https://doi.org/10.1126/science.169.3946.635' -> '10.1126/science.169.3946.635'
        'DOI: 10.1234/foo' -> '10.1234/foo'
        '10.1234/FOO' -> '10.1234/foo'

    Rules:
        - Lowercase
        - Strip 'https://doi.org/' prefix
        - Strip 'https://dx.doi.org/' prefix
        - Strip 'doi:' prefix
        - Trim whitespace

    Returns:
        Normalized DOI string (e.g., '10.1234/foo'), or None if invalid
    """
    if not doi or not doi.strip():
        return None

    doi = doi.strip().lower()

    # Remove common prefixes
    prefixes = [
        'https://doi.org/',
        'https://dx.doi.org/',
        'http://doi.org/',
        'http://dx.doi.org/',
        'doi.org/',
        'dx.doi.org/',
        'doi:',
        'doi ',
    ]

    for prefix in prefixes:
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
            break

    # Validate basic DOI structure (starts with 10.)
    if not doi.startswith('10.'):
        return None

    return doi.strip()
