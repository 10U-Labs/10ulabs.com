import requests

GOOGLE_ANALYTICS_ID = "G-8YJFQC2EGV"
GTAG_SCRIPT_URL = f"https://www.googletagmanager.com/gtag/js?id={GOOGLE_ANALYTICS_ID}"
CONFIG_HASH_URL = "/rack-designer/ABCD12345"


def test_rack_designer_redirects_to_trailing_slash(website_url: str) -> None:
    response = requests.get(f"{website_url}/rack-designer", timeout=30, allow_redirects=False)
    assert response.status_code == 301


def test_rack_designer_redirect_location_has_trailing_slash(website_url: str) -> None:
    response = requests.get(f"{website_url}/rack-designer", timeout=30, allow_redirects=False)
    location = response.headers.get('Location', '')
    assert location.endswith('/rack-designer/')


def test_rack_designer_trailing_slash_returns_200(website_url: str) -> None:
    response = requests.get(f"{website_url}/rack-designer/", timeout=30)
    assert response.status_code == 200


def test_rack_designer_returns_html_content(website_url: str) -> None:
    response = requests.get(f"{website_url}/rack-designer/", timeout=30, allow_redirects=False)
    content_type = response.headers.get('Content-Type', '')
    assert 'text/html' in content_type


def test_rack_designer_config_hash_url_returns_200(website_url: str) -> None:
    url = f"{website_url}{CONFIG_HASH_URL}"
    assert requests.get(url, timeout=30).status_code == 200


def test_rack_designer_config_hash_url_returns_html(website_url: str) -> None:
    url = f"{website_url}{CONFIG_HASH_URL}"
    content_type = requests.get(url, timeout=30).headers.get('Content-Type', '')
    assert 'text/html' in content_type


def test_rack_designer_css_returns_200(website_url: str) -> None:
    response = requests.get(f"{website_url}/rack-designer/css/styles.css", timeout=30)
    assert response.status_code == 200


def test_rack_designer_css_returns_css_content_type(website_url: str) -> None:
    response = requests.get(f"{website_url}/rack-designer/css/styles.css", timeout=30)
    content_type = response.headers.get('Content-Type', '')
    assert 'text/css' in content_type


def test_rack_designer_js_returns_200(website_url: str) -> None:
    response = requests.get(f"{website_url}/rack-designer/js/app.js", timeout=30)
    assert response.status_code == 200


def test_rack_designer_js_returns_javascript_content_type(website_url: str) -> None:
    response = requests.get(f"{website_url}/rack-designer/js/app.js", timeout=30)
    assert 'javascript' in response.headers.get('Content-Type', '')


def test_rack_designer_page_has_gtag_script(website_url: str) -> None:
    response = requests.get(f"{website_url}/rack-designer/", timeout=30)
    assert GTAG_SCRIPT_URL in response.text


def test_rack_designer_page_has_gtag_config(website_url: str) -> None:
    response = requests.get(f"{website_url}/rack-designer/", timeout=30)
    assert f"gtag('config', '{GOOGLE_ANALYTICS_ID}')" in response.text
