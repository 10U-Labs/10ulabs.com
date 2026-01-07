"""Layer 2: Configuration tests for www home page post-deployment.

Test that deployed resources are configured correctly. Assumes existence passed.
"""
import requests


class TestHomePageConfiguration:
    """Layer 2: Verify home page content configuration."""

    def test_home_page_returns_html_content_type(self, website_url):
        """Verify home page returns HTML content type."""
        response = requests.get(website_url, timeout=30)
        content_type = response.headers.get("Content-Type", "")
        is_html = "text/html" in content_type
        assert is_html, f"Expected text/html, got {content_type}"

    def test_home_page_uses_https(self, website_url):
        """Verify website URL uses HTTPS."""
        uses_https = website_url.startswith("https://")
        assert uses_https, f"Expected https://, got {website_url}"


class TestStaticFilesConfiguration:
    """Layer 2: Verify static files configuration."""

    def test_ads_txt_returns_text_content_type(self, website_url):
        """Verify ads.txt returns text/plain content type."""
        response = requests.get(f"{website_url}/ads.txt", timeout=30)
        content_type = response.headers.get("Content-Type", "")
        is_text_plain = "text/plain" in content_type
        assert is_text_plain, f"Expected text/plain, got {content_type}"

    def test_ads_txt_contains_google_adsense_entry(self, website_url):
        """Verify ads.txt contains Google AdSense entry."""
        response = requests.get(f"{website_url}/ads.txt", timeout=30)
        expected_content = "google.com, pub-7173129895205323, DIRECT, f08c47fec0942fa0"
        has_adsense_entry = expected_content in response.text
        assert has_adsense_entry, "ads.txt missing Google AdSense entry"


class TestGoogleAnalyticsConfiguration:
    """Layer 2: Verify Google Analytics is configured."""

    def test_home_page_has_gtag_script(self, website_url):
        """Verify home page includes Google Analytics script."""
        response = requests.get(website_url, timeout=30)
        gtag_script_url = "https://www.googletagmanager.com/gtag/js?id=G-8YJFQC2EGV"
        has_gtag_script = gtag_script_url in response.text
        assert has_gtag_script, "Home page missing Google Analytics script"

    def test_home_page_has_gtag_config(self, website_url):
        """Verify home page has Google Analytics config."""
        response = requests.get(website_url, timeout=30)
        gtag_config = "gtag('config', 'G-8YJFQC2EGV')"
        has_gtag_config = gtag_config in response.text
        assert has_gtag_config, "Home page missing Google Analytics config"

    def test_privacy_page_has_gtag_script(self, website_url):
        """Verify privacy page includes Google Analytics script."""
        response = requests.get(f"{website_url}/privacy.html", timeout=30)
        gtag_script_url = "https://www.googletagmanager.com/gtag/js?id=G-8YJFQC2EGV"
        has_gtag_script = gtag_script_url in response.text
        assert has_gtag_script, "Privacy page missing Google Analytics script"

    def test_privacy_page_has_gtag_config(self, website_url):
        """Verify privacy page has Google Analytics config."""
        response = requests.get(f"{website_url}/privacy.html", timeout=30)
        gtag_config = "gtag('config', 'G-8YJFQC2EGV')"
        has_gtag_config = gtag_config in response.text
        assert has_gtag_config, "Privacy page missing Google Analytics config"


class TestSPARoutingConfiguration:
    """Layer 2: Verify SPA routing is configured correctly."""

    def test_spa_routing_returns_html_content_type(self, website_url):
        """Verify SPA routing returns HTML content type."""
        response = requests.get(f"{website_url}/nonexistent-page-test", timeout=30)
        content_type = response.headers.get("Content-Type", "")
        is_html = "text/html" in content_type
        assert is_html, f"Expected text/html for SPA route, got {content_type}"

    def test_spa_routing_returns_non_empty_content(self, website_url):
        """Verify SPA routing returns non-empty content."""
        response = requests.get(f"{website_url}/some-spa-route", timeout=30)
        has_content = len(response.text) > 0
        assert has_content, "SPA route should return content"
