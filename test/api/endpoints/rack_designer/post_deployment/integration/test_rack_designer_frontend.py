"""Integration tests for rack-designer frontend content."""
import requests


def test_rack_designer_returns_200(website_url):
    """Test that rack-designer returns 200 status code."""
    response = requests.get(f"{website_url}/rack-designer", timeout=30)
    assert response.status_code == 200


def test_rack_designer_returns_html(website_url):
    """Test that rack-designer returns HTML content type."""
    response = requests.get(f"{website_url}/rack-designer", timeout=30)
    assert 'text/html' in response.headers.get('Content-Type', '')


def test_rack_designer_trailing_slash_returns_200(website_url):
    """Test that rack-designer with trailing slash returns 200."""
    response = requests.get(f"{website_url}/rack-designer/", timeout=30)
    assert response.status_code == 200


def test_rack_designer_css_returns_200(website_url):
    """Test that rack-designer CSS returns 200 status code."""
    response = requests.get(f"{website_url}/rack-designer/css/styles.css", timeout=30)
    assert response.status_code == 200


def test_rack_designer_css_returns_css_content_type(website_url):
    """Test that rack-designer CSS returns CSS content type."""
    response = requests.get(f"{website_url}/rack-designer/css/styles.css", timeout=30)
    assert 'text/css' in response.headers.get('Content-Type', '')


def test_rack_designer_js_returns_200(website_url):
    """Test that rack-designer JS returns 200 status code."""
    response = requests.get(f"{website_url}/rack-designer/js/app.js", timeout=30)
    assert response.status_code == 200


def test_rack_designer_js_returns_javascript_content_type(website_url):
    """Test that rack-designer JS returns JavaScript content type."""
    response = requests.get(f"{website_url}/rack-designer/js/app.js", timeout=30)
    content_type = response.headers.get('Content-Type', '')
    assert 'javascript' in content_type


def test_rack_designer_config_hash_returns_200(website_url):
    """Test that rack-designer config hash URL returns 200."""
    response = requests.get(f"{website_url}/rack-designer/ABCD12345", timeout=30)
    assert response.status_code == 200


def test_rack_designer_config_hash_returns_html(website_url):
    """Test that rack-designer config hash URL returns HTML."""
    response = requests.get(f"{website_url}/rack-designer/ABCD12345", timeout=30)
    assert 'text/html' in response.headers.get('Content-Type', '')
