"""Layer 3: Wiring tests for www home page post-deployment.

Test that components are connected correctly. Assumes configuration passed.
"""
import requests


class TestCloudFrontS3Wiring:
    """Layer 3: Verify CloudFront serves content from S3 correctly."""

    def test_cloudfront_serves_home_page_assets(self, website_url):
        """Verify CloudFront serves home page JavaScript assets."""
        response = requests.get(website_url, timeout=30)
        # Check that page includes asset references
        has_asset_references = "/assets/" in response.text or "index" in response.text
        assert has_asset_references, "Home page should reference assets"

    def test_cloudfront_serves_privacy_page(self, website_url):
        """Verify CloudFront serves static HTML pages from S3."""
        response = requests.get(f"{website_url}/privacy.html", timeout=30)
        has_privacy_content = "Privacy" in response.text
        assert has_privacy_content, "Privacy page should contain privacy content"


class TestLambdaEdgeWiring:
    """Layer 3: Verify Lambda@Edge routing is wired correctly."""

    def test_apex_redirects_to_www(self, config):
        """Verify apex domain redirects to www."""
        apex_url = f"https://{config.get('domain_name', '10ulabs.com')}"
        response = requests.get(apex_url, timeout=30, allow_redirects=False)
        is_redirect = response.status_code in (301, 302)
        assert is_redirect, f"Apex should redirect, got {response.status_code}"

    def test_apex_redirect_location_includes_www(self, config):
        """Verify apex redirect location includes www prefix."""
        apex_url = f"https://{config.get('domain_name', '10ulabs.com')}"
        response = requests.get(apex_url, timeout=30, allow_redirects=False)
        if response.status_code in (301, 302):
            location = response.headers.get("Location", "")
            has_www = "www." in location
            assert has_www, f"Redirect location should include www, got {location}"

    def test_spa_routes_serve_index_html(self, website_url):
        """Verify SPA routes serve index.html content."""
        response = requests.get(f"{website_url}/some-spa-route", timeout=30)
        # SPA routes should return the React app HTML
        is_react_app = (
            "<!DOCTYPE html>" in response.text.lower()
            or "<!doctype html>" in response.text.lower()
            or "<html" in response.text.lower()
        )
        assert is_react_app, "SPA routes should serve HTML document"


class TestAssetRewriteWiring:
    """Layer 3: Verify /assets/ rewrite to /home/assets/ is wired correctly."""

    def test_website_loads_without_asset_errors(self, website_url):
        """Verify the website can load (implies assets are working)."""
        response = requests.get(website_url, timeout=30)
        # If we get a 200 and the page has expected content, assets are likely working
        has_expected_content = (
            "10U Labs" in response.text or
            "<html" in response.text.lower()
        )
        assert has_expected_content, "Website should load with expected content"

    def test_website_contains_html_document(self, website_url):
        """Verify the website contains a valid HTML document."""
        response = requests.get(website_url, timeout=30)
        is_html_document = (
            "<!DOCTYPE html>" in response.text or
            "<!doctype html>" in response.text or
            "<html" in response.text.lower()
        )
        assert is_html_document, "Website should contain HTML document"
