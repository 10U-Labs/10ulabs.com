import requests


def test_website_returns_200(website_response):
    assert website_response.status_code == 200


def test_website_returns_html(website_response):
    assert 'text/html' in website_response.headers.get('Content-Type', '')


def test_website_has_content(website_response):
    assert len(website_response.text) > 0


def test_website_serves_over_https(website_url):
    assert website_url.startswith('https://')


def test_website_redirects_http_to_https(config):
    http_url = f"http://{config['website_fqdn']}"
    response = requests.get(http_url, timeout=30, allow_redirects=False)
    assert response.status_code in [301, 302, 307, 308]


def test_website_https_redirect_location(config):
    http_url = f"http://{config['website_fqdn']}"
    response = requests.get(http_url, timeout=30, allow_redirects=False)
    location = response.headers.get('Location', '')
    assert 'https://' in location


def test_website_has_strict_transport_security(website_response):
    hsts = website_response.headers.get('Strict-Transport-Security', '')
    assert len(hsts) > 0


def test_website_spa_routing_returns_200(website_url):
    response = requests.get(f"{website_url}/nonexistent-page", timeout=30)
    assert response.status_code == 200


def test_website_spa_routing_returns_html(website_url):
    response = requests.get(f"{website_url}/nonexistent-page", timeout=30)
    assert 'text/html' in response.headers.get('Content-Type', '')


def test_apex_redirects_to_www(config):
    apex_url = f"https://{config['apex_fqdn']}"
    response = requests.get(apex_url, timeout=30, allow_redirects=False)
    assert response.status_code == 301


def test_apex_redirect_location_is_www(config):
    apex_url = f"https://{config['apex_fqdn']}"
    response = requests.get(apex_url, timeout=30, allow_redirects=False)
    location = response.headers.get('Location', '')
    assert config['website_fqdn'] in location


def test_apex_redirect_preserves_path(config):
    apex_url = f"https://{config['apex_fqdn']}/some/path"
    response = requests.get(apex_url, timeout=30, allow_redirects=False)
    location = response.headers.get('Location', '')
    assert '/some/path' in location


def test_rack_designer_returns_200(website_url):
    response = requests.get(f"{website_url}/rack-designer", timeout=30)
    assert response.status_code == 200


def test_rack_designer_returns_html(website_url):
    response = requests.get(f"{website_url}/rack-designer", timeout=30)
    assert 'text/html' in response.headers.get('Content-Type', '')


def test_rack_designer_trailing_slash_returns_200(website_url):
    response = requests.get(f"{website_url}/rack-designer/", timeout=30)
    assert response.status_code == 200


def test_rack_designer_css_returns_200(website_url):
    response = requests.get(f"{website_url}/rack-designer/css/styles.css", timeout=30)
    assert response.status_code == 200


def test_rack_designer_css_returns_css_content_type(website_url):
    response = requests.get(f"{website_url}/rack-designer/css/styles.css", timeout=30)
    assert 'text/css' in response.headers.get('Content-Type', '')


def test_rack_designer_js_returns_200(website_url):
    response = requests.get(f"{website_url}/rack-designer/js/app.js", timeout=30)
    assert response.status_code == 200


def test_rack_designer_js_returns_javascript_content_type(website_url):
    response = requests.get(f"{website_url}/rack-designer/js/app.js", timeout=30)
    content_type = response.headers.get('Content-Type', '')
    assert 'javascript' in content_type
