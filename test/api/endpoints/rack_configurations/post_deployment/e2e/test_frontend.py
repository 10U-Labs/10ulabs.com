"""E2E frontend tests for rack designer endpoint.

Tests critical frontend user journeys from end to end.
These tests make real HTTP requests to the deployed frontend.

User Journeys:
- Page access journey: User accesses the rack designer page
- Asset loading journey: User loads page assets (CSS, JS)
- Google Analytics journey: Analytics tracking is configured
"""
import requests


GOOGLE_ANALYTICS_ID = "G-8YJFQC2EGV"
GTAG_SCRIPT_URL = f"https://www.googletagmanager.com/gtag/js?id={GOOGLE_ANALYTICS_ID}"


class TestRackDesignerPageAccessJourney:
    """User Journey: User accesses rack designer page.

    Critical path: User navigates to the rack designer.
    Failure impact: Users cannot access the application.
    """

    def test_page_returns_200(self, website_url):
        """Verify rack-designer page returns 200 status code."""
        response = requests.get(f"{website_url}/rack-designer", timeout=30)
        assert response.status_code == 200

    def test_page_returns_html(self, website_url):
        """Verify rack-designer page returns HTML content type."""
        response = requests.get(f"{website_url}/rack-designer", timeout=30)
        assert 'text/html' in response.headers.get('Content-Type', '')

    def test_trailing_slash_returns_200(self, website_url):
        """Verify rack-designer with trailing slash returns 200."""
        response = requests.get(f"{website_url}/rack-designer/", timeout=30)
        assert response.status_code == 200

    def test_config_hash_url_returns_200(self, website_url):
        """Verify rack-designer config hash URL returns 200."""
        response = requests.get(f"{website_url}/rack-designer/ABCD12345", timeout=30)
        assert response.status_code == 200

    def test_config_hash_url_returns_html(self, website_url):
        """Verify rack-designer config hash URL returns HTML."""
        response = requests.get(f"{website_url}/rack-designer/ABCD12345", timeout=30)
        assert 'text/html' in response.headers.get('Content-Type', '')


class TestRackDesignerAssetsJourney:
    """User Journey: User loads page assets.

    Critical path: Browser loads CSS and JS files.
    Failure impact: Broken styling or non-functional page.
    """

    def test_css_returns_200(self, website_url):
        """Verify rack-designer CSS returns 200 status code."""
        response = requests.get(
            f"{website_url}/rack-designer/css/styles.css", timeout=30
        )
        assert response.status_code == 200

    def test_css_returns_css_content_type(self, website_url):
        """Verify rack-designer CSS returns CSS content type."""
        response = requests.get(
            f"{website_url}/rack-designer/css/styles.css", timeout=30
        )
        assert 'text/css' in response.headers.get('Content-Type', '')

    def test_js_returns_200(self, website_url):
        """Verify rack-designer JS returns 200 status code."""
        response = requests.get(
            f"{website_url}/rack-designer/js/app.js", timeout=30
        )
        assert response.status_code == 200

    def test_js_returns_javascript_content_type(self, website_url):
        """Verify rack-designer JS returns JavaScript content type."""
        response = requests.get(
            f"{website_url}/rack-designer/js/app.js", timeout=30
        )
        content_type = response.headers.get('Content-Type', '')
        assert 'javascript' in content_type


class TestGoogleAnalyticsJourney:
    """User Journey: Analytics tracking is configured.

    Critical path: Page load triggers analytics tracking.
    Failure impact: No visibility into user behavior.
    """

    def test_page_has_gtag_script(self, website_url):
        """Verify rack designer page includes Google Analytics script."""
        response = requests.get(f"{website_url}/rack-designer/", timeout=30)
        assert GTAG_SCRIPT_URL in response.text

    def test_page_has_gtag_config(self, website_url):
        """Verify rack designer page includes Google Analytics config."""
        response = requests.get(f"{website_url}/rack-designer/", timeout=30)
        assert f"gtag('config', '{GOOGLE_ANALYTICS_ID}')" in response.text
