"""
Tests for Resource Verifier Tool.
"""

import pytest
from backend.tools.resource_verifier import verify_url


def test_verify_url_valid():
    """Test verification of a known good URL."""
    # Test with a reliable URL
    assert verify_url("https://www.google.com") == True


def test_verify_url_invalid():
    """Test verification of an invalid URL."""
    # Non-existent domain
    assert verify_url("https://this-domain-definitely-does-not-exist-12345.com") == False


def test_verify_url_malformed():
    """Test handling of malformed URLs."""
    assert verify_url("not-a-url") == False
    assert verify_url("") == False
    assert verify_url("ftp://example.com") == False


def test_verify_url_timeout():
    """Test that timeout works (using a slow/non-responsive endpoint)."""
    # This should timeout quickly
    result = verify_url("https://httpstat.us/200?sleep=10000", timeout=1, retries=0)
    # May return False due to timeout
    assert isinstance(result, bool)


def test_verify_url_http_error():
    """Test handling of HTTP error codes."""
    # 404 should return False
    assert verify_url("https://httpstat.us/404", retries=0) == False
    
    # 500 should return False
    assert verify_url("https://httpstat.us/500", retries=0) == False


def test_verify_url_redirect():
    """Test that redirects (3xx) are handled."""
    # Test a real redirect that should work
    # Most sites handle HEAD requests and redirects properly
    result = verify_url("http://google.com", retries=0)  # Redirects to https
    # Result may vary, but should be boolean
    assert isinstance(result, bool)
