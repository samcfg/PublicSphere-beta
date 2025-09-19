# File: backend/utils/referrer.py
from urllib.parse import urlparse
import re

def validate_referrer(referrer_url, article_url):
    """
    Validate if a referrer URL is legitimate for an article URL
    
    Args:
        referrer_url: The HTTP referrer URL
        article_url: The original article URL
        
    Returns:
        bool: True if the referrer is valid, False otherwise
    """
    if not referrer_url or not article_url:
        return False
    
    try:
        # Parse URLs
        ref_parsed = urlparse(referrer_url)
        art_parsed = urlparse(article_url)
        
        # Extract domains
        ref_domain = ref_parsed.netloc.lower()
        art_domain = art_parsed.netloc.lower()
        
        # Remove 'www.' prefix if present
        if ref_domain.startswith('www.'):
            ref_domain = ref_domain[4:]
        if art_domain.startswith('www.'):
            art_domain = art_domain[4:]
        
        # Domain matching - article domain should be part of referrer domain
        # or they should be the same domain
        if ref_domain == art_domain:
            return True
        
        # Check if article domain is a subdomain of referrer domain
        if art_domain.endswith('.' + ref_domain):
            return True
        
        # Check if referrer domain is a subdomain of article domain
        if ref_domain.endswith('.' + art_domain):
            return True
        
        # Special case for AMP and mobile versions
        if (ref_domain.startswith('amp.') and ref_domain[4:] == art_domain) or \
           (ref_domain.startswith('m.') and ref_domain[2:] == art_domain):
            return True
        
        # Check for CDN domains or common blog platforms
        cdn_patterns = [
            r'cdn\.', r'media\.', r'static\.', r'assets\.',
            r'blog\.', r'blogs\.', r'medium\.com', r'substack\.com'
        ]
        
        for pattern in cdn_patterns:
            if re.match(pattern, ref_domain) and art_domain in referrer_url:
                return True
        
        # Path matching - check if the article path is in the referrer path
        # This handles cases where the article URL is embedded in the referrer
        article_path = art_parsed.path.rstrip('/')
        if article_path and article_path in ref_parsed.path:
            return True
        
        # Check for common social media and news aggregator domains
        # These should not be considered valid referrers for article access
        social_domains = [
            'facebook.com', 'twitter.com', 'linkedin.com', 'reddit.com',
            'news.google.com', 'news.yahoo.com', 't.co', 'bit.ly'
        ]
        if any(domain in ref_domain for domain in social_domains):
            return False
        
        # More sophisticated checks could be added here
        # e.g., checking for article title in referrer HTML, etc.
        
        return False
        
    except Exception as e:
        print(f"Error validating referrer: {e}")
        return False


def get_publisher_domains(article_url):
    """
    Extract potential publisher domains from an article URL
    
    Args:
        article_url: The original article URL
        
    Returns:
        list: A list of potential publisher domains
    """
    if not article_url:
        return []
    
    try:
        # Parse URL
        parsed = urlparse(article_url)
        domain = parsed.netloc.lower()
        
        # Remove 'www.' prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # List of potential publisher domains
        domains = [domain]
        
        # Add parent domain if this is a subdomain
        parts = domain.split('.')
        if len(parts) > 2:
            parent_domain = '.'.join(parts[-2:])
            domains.append(parent_domain)
        
        return domains
        
    except Exception as e:
        print(f"Error extracting publisher domains: {e}")
        return []


def is_valid_domain(domain):
    """
    Check if a domain is a valid hostname
    
    Args:
        domain: The domain to check
        
    Returns:
        bool: True if the domain is valid, False otherwise
    """
    if not domain:
        return False
    
    # Check for valid domain pattern
    pattern = r'^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$'
    return bool(re.match(pattern, domain.lower()))