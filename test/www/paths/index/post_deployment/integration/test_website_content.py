"""Integration tests for website content."""
import requests


def test_website_returns_200(website_response):
    """Test that website returns 200 status code."""
    assert website_response.status_code == 200


def test_website_returns_html(website_response):
    """Test that website returns HTML content type."""
    assert 'text/html' in website_response.headers.get('Content-Type', '')


def test_website_has_content(website_response):
    """Test that website returns non-empty content."""
    assert len(website_response.text) > 0


def test_website_serves_over_https(website_url):
    """Test that website URL uses HTTPS."""
    assert website_url.startswith('https://')


def test_index_html_exists(website_url):
    """Test that index.html is served."""
    response = requests.get(website_url, timeout=30)
    assert response.status_code == 200


def test_website_spa_routing_returns_200(website_url):
    """Test that SPA routing returns 200 for non-existent pages."""
    response = requests.get(f"{website_url}/nonexistent-page", timeout=30)
    assert response.status_code == 200


def test_website_spa_routing_returns_html(website_url):
    """Test that SPA routing returns HTML content type."""
    response = requests.get(f"{website_url}/nonexistent-page", timeout=30)
    assert 'text/html' in response.headers.get('Content-Type', '')
