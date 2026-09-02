import requests


GOOGLE_ANALYTICS_ID = "G-8YJFQC2EGV"
GTAG_SCRIPT_URL = f"https://www.googletagmanager.com/gtag/js?id={GOOGLE_ANALYTICS_ID}"


class TestRackDesignerPageAccessJourney:
    def test_page_returns_200(self, website_url: str) -> None:
        response = requests.get(f"{website_url}/rack-designer", timeout=30)
        assert response.status_code == 200

    def test_page_returns_html(self, website_url: str) -> None:
        response = requests.get(f"{website_url}/rack-designer", timeout=30)
        assert 'text/html' in response.headers.get('Content-Type', '')

    def test_trailing_slash_returns_200(self, website_url: str) -> None:
        response = requests.get(f"{website_url}/rack-designer/", timeout=30)
        assert response.status_code == 200

    def test_config_hash_url_returns_200(self, website_url: str) -> None:
        response = requests.get(f"{website_url}/rack-designer/ABCD12345", timeout=30)
        assert response.status_code == 200

    def test_config_hash_url_returns_html(self, website_url: str) -> None:
        response = requests.get(f"{website_url}/rack-designer/ABCD12345", timeout=30)
        assert 'text/html' in response.headers.get('Content-Type', '')


class TestRackDesignerAssetsJourney:
    def test_css_returns_200(self, website_url: str) -> None:
        response = requests.get(
            f"{website_url}/rack-designer/css/styles.css", timeout=30
        )
        assert response.status_code == 200

    def test_css_returns_css_content_type(self, website_url: str) -> None:
        response = requests.get(
            f"{website_url}/rack-designer/css/styles.css", timeout=30
        )
        assert 'text/css' in response.headers.get('Content-Type', '')

    def test_js_returns_200(self, website_url: str) -> None:
        response = requests.get(
            f"{website_url}/rack-designer/js/app.js", timeout=30
        )
        assert response.status_code == 200

    def test_js_returns_javascript_content_type(self, website_url: str) -> None:
        response = requests.get(
            f"{website_url}/rack-designer/js/app.js", timeout=30
        )
        content_type = response.headers.get('Content-Type', '')
        assert 'javascript' in content_type


class TestGoogleAnalyticsJourney:
    def test_page_has_gtag_script(self, website_url: str) -> None:
        response = requests.get(f"{website_url}/rack-designer/", timeout=30)
        assert GTAG_SCRIPT_URL in response.text

    def test_page_has_gtag_config(self, website_url: str) -> None:
        response = requests.get(f"{website_url}/rack-designer/", timeout=30)
        assert f"gtag('config', '{GOOGLE_ANALYTICS_ID}')" in response.text
