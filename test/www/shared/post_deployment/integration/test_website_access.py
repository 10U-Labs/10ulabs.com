"""Integration tests for website infrastructure behavior (redirects, HSTS, routing)."""
import requests


def test_website_redirects_http_to_https(config):
    """Test that HTTP requests redirect to HTTPS."""
    http_url = f"http://{config['website_fqdn']}"
    response = requests.get(http_url, timeout=30, allow_redirects=False)
    assert response.status_code in [301, 302, 307, 308]


def test_website_https_redirect_location(config):
    """Test that HTTP redirect location uses HTTPS."""
    http_url = f"http://{config['website_fqdn']}"
    response = requests.get(http_url, timeout=30, allow_redirects=False)
    location = response.headers.get('Location', '')
    assert 'https://' in location


def test_website_has_strict_transport_security(website_response):
    """Test that website has HSTS header."""
    hsts = website_response.headers.get('Strict-Transport-Security', '')
    assert len(hsts) > 0


def test_apex_redirects_to_www(config):
    """Test that apex domain redirects to www."""
    apex_url = f"https://{config['apex_fqdn']}"
    response = requests.get(apex_url, timeout=30, allow_redirects=False)
    assert response.status_code == 301


def test_apex_redirect_location_is_www(config):
    """Test that apex redirect location is www domain."""
    apex_url = f"https://{config['apex_fqdn']}"
    response = requests.get(apex_url, timeout=30, allow_redirects=False)
    location = response.headers.get('Location', '')
    assert config['website_fqdn'] in location


def test_apex_redirect_preserves_path(config):
    """Test that apex redirect preserves URL path."""
    apex_url = f"https://{config['apex_fqdn']}/some/path"
    response = requests.get(apex_url, timeout=30, allow_redirects=False)
    location = response.headers.get('Location', '')
    assert '/some/path' in location


def test_rack_designer_redirects_to_trailing_slash(website_url):
    """Test that rack-designer redirects to trailing slash."""
    response = requests.get(f"{website_url}/rack-designer", timeout=30, allow_redirects=False)
    assert response.status_code == 301


def test_rack_designer_redirect_location_has_trailing_slash(website_url):
    """Test that rack-designer redirect has trailing slash."""
    response = requests.get(f"{website_url}/rack-designer", timeout=30, allow_redirects=False)
    location = response.headers.get('Location', '')
    assert location.endswith('/rack-designer/')
