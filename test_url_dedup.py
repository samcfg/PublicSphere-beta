#!/usr/bin/env python3
"""
Test script for URL deduplication (Phase 1)

Tests the complete flow:
1. Create a source with a URL
2. Attempt to create duplicate sources with variations of the same URL
3. Verify deduplication works correctly
"""

import os
import sys

# Setup Django environment - must be in backend/PS_Django_DB directory
backend_dir = os.path.join(os.path.dirname(__file__), 'backend', 'PS_Django_DB')
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PS_Django_DB.settings')

import django
django.setup()

from PS_Graph_DB.src.language import get_language_ops
from bookkeeper.models import SourceVersion
from graph.services import DeduplicationService
from graph.utils import normalize_url

# Initialize language operations
ops = get_language_ops()
ops.set_graph('test_graph')

def test_url_normalization():
    """Test that URL normalization works correctly"""
    print("\n=== Testing URL Normalization ===")

    test_cases = [
        ("https://example.com/article", "example.com/article"),
        ("http://www.example.com/article/", "example.com/article"),
        ("HTTPS://WWW.Example.COM/Article/", "example.com/article"),
        ("https://example.com/page?utm_source=facebook", "example.com/page"),
        ("https://example.com/article#section2", "example.com/article"),
    ]

    for input_url, expected in test_cases:
        result = normalize_url(input_url)
        status = "✓" if result == expected else "✗"
        print(f"{status} {input_url}")
        print(f"  → {result} (expected: {expected})")
        if result != expected:
            print(f"  ERROR: Normalization mismatch!")
            return False

    print("\nAll normalization tests passed ✓")
    return True


def test_duplicate_detection():
    """Test that duplicate detection catches URL variations"""
    print("\n=== Testing Duplicate Detection ===")

    # Clean up any previous test sources
    print("\nCleaning up previous test sources...")
    SourceVersion.objects.filter(title__startswith="[TEST]").delete()

    # Create initial source
    original_url = "https://www.example.com/test-article"
    original_title = "[TEST] Example Article for Deduplication Testing"

    print(f"\n1. Creating original source:")
    print(f"   URL: {original_url}")
    print(f"   Title: {original_title}")

    try:
        source_id = ops.create_source(
            url=original_url,
            title=original_title,
            content="This is a test source for URL deduplication",
            user_id=None
        )
        print(f"   ✓ Created source: {source_id}")
    except Exception as e:
        print(f"   ✗ ERROR: Failed to create source: {e}")
        return False

    # Test duplicate detection with URL variations
    test_urls = [
        "http://example.com/test-article",      # Different protocol, no www
        "https://example.com/test-article/",    # Trailing slash
        "HTTPS://WWW.EXAMPLE.COM/TEST-ARTICLE", # Different case
        "https://example.com/test-article?ref=123", # Query params
    ]

    print("\n2. Testing duplicate detection with URL variations:")
    for test_url in test_urls:
        duplicate = DeduplicationService.check_duplicate_source(
            url=test_url,
            title="[TEST] Different Title"
        )

        if duplicate and duplicate['duplicate_type'] == 'url':
            print(f"   ✓ Correctly detected duplicate: {test_url}")
            print(f"     Found existing: {duplicate['existing_title']}")
        else:
            print(f"   ✗ FAILED to detect duplicate: {test_url}")
            return False

    # Test that different URLs are NOT flagged as duplicates
    print("\n3. Testing that different URLs are allowed:")
    different_url = "https://different-site.com/article"
    duplicate = DeduplicationService.check_duplicate_source(
        url=different_url,
        title="[TEST] Different Article"
    )

    if duplicate:
        print(f"   ✗ ERROR: False positive - flagged different URL as duplicate")
        return False
    else:
        print(f"   ✓ Correctly allowed different URL: {different_url}")

    # Cleanup
    print("\n4. Cleaning up test data...")
    SourceVersion.objects.filter(node_id=source_id).delete()
    print("   ✓ Test data cleaned up")

    print("\n=== All duplicate detection tests passed ✓ ===")
    return True


def test_api_integration():
    """Test API-level duplicate rejection"""
    print("\n=== Testing API Integration ===")
    print("(This requires manual testing via HTTP requests or frontend)")
    print("Steps to test:")
    print("1. Start Django server: uv run python manage.py runserver")
    print("2. Create a source with URL via frontend or API")
    print("3. Try to create another source with same URL (different protocol/case)")
    print("4. Verify 409 error is returned with duplicate info")
    print("5. Verify frontend shows duplicate error message with link")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 1: URL Deduplication Testing")
    print("=" * 60)

    success = True

    # Run tests
    success = success and test_url_normalization()
    success = success and test_duplicate_detection()
    test_api_integration()

    print("\n" + "=" * 60)
    if success:
        print("✓ All automated tests PASSED")
    else:
        print("✗ Some tests FAILED")
    print("=" * 60)

    sys.exit(0 if success else 1)
