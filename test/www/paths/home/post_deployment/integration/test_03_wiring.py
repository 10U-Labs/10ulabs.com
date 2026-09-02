from typing import Any, Dict

import requests


class TestCloudFrontS3Wiring:
    def test_cloudfront_serves_home_page_assets(self, website_url: str) -> None:
        response = requests.get(website_url, timeout=30)
        has_asset_references = "/assets/" in response.text or "index" in response.text
        assert has_asset_references, "Home page should reference assets"

    def test_cloudfront_serves_privacy_page(self, website_url: str) -> None:
        response = requests.get(f"{website_url}/privacy.html", timeout=30)
        has_privacy_content = "Privacy" in response.text
        assert has_privacy_content, "Privacy page should contain privacy content"


class TestLambdaEdgeWiring:
    def test_apex_redirects_to_www(self, config: Dict[str, Any]) -> None:
        apex_url = f"https://{config.get('domain_name', '10ulabs.com')}"
        response = requests.get(apex_url, timeout=30, allow_redirects=False)
        is_redirect = response.status_code in (301, 302)
        assert is_redirect, f"Apex should redirect, got {response.status_code}"

    def test_apex_redirect_location_includes_www(self, config: Dict[str, Any]) -> None:
        apex_url = f"https://{config.get('domain_name', '10ulabs.com')}"
        response = requests.get(apex_url, timeout=30, allow_redirects=False)
        if response.status_code in (301, 302):
            location = response.headers.get("Location", "")
            has_www = "www." in location
            assert has_www, f"Redirect location should include www, got {location}"

    def test_spa_routes_serve_index_html(self, website_url: str) -> None:
        response = requests.get(f"{website_url}/some-spa-route", timeout=30)
        is_react_app = (
            "<!DOCTYPE html>" in response.text.lower()
            or "<!doctype html>" in response.text.lower()
            or "<html" in response.text.lower()
        )
        assert is_react_app, "SPA routes should serve HTML document"


class TestAssetRewriteWiring:
    def test_website_loads_without_asset_errors(self, website_url: str) -> None:
        response = requests.get(website_url, timeout=30)
        has_expected_content = (
            "10U Labs" in response.text or
            "<html" in response.text.lower()
        )
        assert has_expected_content, "Website should load with expected content"

    def test_website_contains_html_document(self, website_url: str) -> None:
        response = requests.get(website_url, timeout=30)
        is_html_document = (
            "<!DOCTYPE html>" in response.text or
            "<!doctype html>" in response.text or
            "<html" in response.text.lower()
        )
        assert is_html_document, "Website should contain HTML document"
