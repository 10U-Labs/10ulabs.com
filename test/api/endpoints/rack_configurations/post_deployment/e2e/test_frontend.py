import requests


GOOGLE_ANALYTICS_ID = "G-8YJFQC2EGV"
GTAG_SCRIPT_URL = f"https://www.googletagmanager.com/gtag/js?id={GOOGLE_ANALYTICS_ID}"


def test_rack_designer_page_returns_200(website_url: str) -> None:
    response = requests.get(f"{website_url}/rack-designer", timeout=30)
    assert response.status_code == 200


def test_rack_designer_page_returns_html(website_url: str) -> None:
    response = requests.get(f"{website_url}/rack-designer", timeout=30)
    assert 'text/html' in response.headers.get('Content-Type', '')


def test_rack_designer_trailing_slash_returns_200(website_url: str) -> None:
    response = requests.get(f"{website_url}/rack-designer/", timeout=30)
    assert response.status_code == 200


def test_rack_designer_config_hash_url_returns_200(website_url: str) -> None:
    response = requests.get(f"{website_url}/rack-designer/ABCD12345", timeout=30)
    assert response.status_code == 200


def test_rack_designer_config_hash_url_returns_html(website_url: str) -> None:
    response = requests.get(f"{website_url}/rack-designer/ABCD12345", timeout=30)
    assert 'text/html' in response.headers.get('Content-Type', '')


def test_rack_designer_css_returns_200(website_url: str) -> None:
    response = requests.get(
        f"{website_url}/rack-designer/css/styles.css", timeout=30
    )
    assert response.status_code == 200


def test_rack_designer_css_returns_css_content_type(website_url: str) -> None:
    response = requests.get(
        f"{website_url}/rack-designer/css/styles.css", timeout=30
    )
    assert 'text/css' in response.headers.get('Content-Type', '')


def test_rack_designer_js_returns_200(website_url: str) -> None:
    response = requests.get(
        f"{website_url}/rack-designer/js/app.js", timeout=30
    )
    assert response.status_code == 200


def test_rack_designer_js_returns_javascript_content_type(website_url: str) -> None:
    response = requests.get(
        f"{website_url}/rack-designer/js/app.js", timeout=30
    )
    content_type = response.headers.get('Content-Type', '')
    assert 'javascript' in content_type


def test_rack_designer_page_has_gtag_script(website_url: str) -> None:
    response = requests.get(f"{website_url}/rack-designer/", timeout=30)
    assert GTAG_SCRIPT_URL in response.text


def test_rack_designer_page_has_gtag_config(website_url: str) -> None:
    response = requests.get(f"{website_url}/rack-designer/", timeout=30)
    assert f"gtag('config', '{GOOGLE_ANALYTICS_ID}')" in response.text
