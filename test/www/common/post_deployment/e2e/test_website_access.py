"""E2E tests for website access (HTTP requests to live endpoints).

Per tenets: If the test sends an HTTP request, it's an e2e test.
"""
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


def test_rack_designer_serves_content_directly(website_url):
    """Test that rack-designer serves content without redirect."""
    response = requests.get(f"{website_url}/rack-designer", timeout=30, allow_redirects=False)
    assert response.status_code == 200


def test_rack_designer_returns_html_content(website_url):
    """Test that rack-designer returns HTML content."""
    response = requests.get(f"{website_url}/rack-designer", timeout=30, allow_redirects=False)
    content_type = response.headers.get('Content-Type', '')
    assert 'text/html' in content_type


def test_homepage_returns_200(website_response):
    """Test that homepage returns 200 status."""
    assert website_response.status_code == 200


def test_homepage_returns_html_content(website_response):
    """Test that homepage returns HTML content type."""
    content_type = website_response.headers.get('Content-Type', '')
    assert 'text/html' in content_type


def test_hsts_max_age_is_reasonable(website_response):
    """Test that HSTS max-age is at least one year."""
    hsts = website_response.headers.get('Strict-Transport-Security', '')
    assert 'max-age=' in hsts


def test_hsts_includes_subdomains(website_response):
    """Test that HSTS includes includeSubDomains."""
    hsts = website_response.headers.get('Strict-Transport-Security', '')
    assert 'includeSubDomains' in hsts


def test_hsts_includes_preload(website_response):
    """Test that HSTS includes preload directive."""
    hsts = website_response.headers.get('Strict-Transport-Security', '')
    assert 'preload' in hsts


def test_website_served_by_cloudfront(website_response):
    """Test that website is served by CloudFront."""
    server = website_response.headers.get('Server', '')
    x_cache = website_response.headers.get('X-Cache', '')
    has_cloudfront_marker = 'CloudFront' in server or 'cloudfront' in x_cache.lower()
    assert has_cloudfront_marker


def test_privacy_page_accessible(website_url):
    """Test that privacy page is accessible."""
    response = requests.get(f"{website_url}/privacy", timeout=30)
    assert response.status_code == 200


def test_robots_txt_accessible(website_url):
    """Test that robots.txt is accessible."""
    response = requests.get(f"{website_url}/robots.txt", timeout=30)
    assert response.status_code == 200


def test_ads_txt_accessible(website_url):
    """Test that ads.txt is accessible."""
    response = requests.get(f"{website_url}/ads.txt", timeout=30)
    assert response.status_code == 200


def test_assets_js_returns_200_status(website_response, website_url):
    """Test that /assets/*.js returns 200 status code."""
    import re
    html = website_response.text
    js_match = re.search(r'src="(/assets/[^"]+\.js)"', html)
    if js_match:
        js_path = js_match.group(1)
        response = requests.get(f"{website_url}{js_path}", timeout=30)
        assert response.status_code == 200


def test_assets_js_returns_javascript_content_type(website_response, website_url):
    """Test that /assets/*.js returns JavaScript content-type, not HTML fallback."""
    import re
    html = website_response.text
    js_match = re.search(r'src="(/assets/[^"]+\.js)"', html)
    if js_match:
        js_path = js_match.group(1)
        response = requests.get(f"{website_url}{js_path}", timeout=30)
        content_type = response.headers.get("Content-Type", "")
        assert "javascript" in content_type.lower()


def test_assets_css_returns_200_status(website_response, website_url):
    """Test that /assets/*.css returns 200 status code."""
    import re
    html = website_response.text
    css_match = re.search(r'href="(/assets/[^"]+\.css)"', html)
    if css_match:
        css_path = css_match.group(1)
        response = requests.get(f"{website_url}{css_path}", timeout=30)
        assert response.status_code == 200


def test_assets_css_returns_css_content_type(website_response, website_url):
    """Test that /assets/*.css returns CSS content-type, not HTML fallback."""
    import re
    html = website_response.text
    css_match = re.search(r'href="(/assets/[^"]+\.css)"', html)
    if css_match:
        css_path = css_match.group(1)
        response = requests.get(f"{website_url}{css_path}", timeout=30)
        content_type = response.headers.get("Content-Type", "")
        assert "css" in content_type.lower()
