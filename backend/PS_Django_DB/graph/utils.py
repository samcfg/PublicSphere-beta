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
