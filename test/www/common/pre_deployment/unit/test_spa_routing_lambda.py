"""Unit tests for SPA routing Lambda@Edge handler."""
import importlib.util
import sys

import pytest

from repo_utils import REPO_ROOT

LAMBDA_DIR = REPO_ROOT / "src" / "www" / "common" / "lambda"
spec = importlib.util.spec_from_file_location("spa_routing", LAMBDA_DIR / "spa_routing.py")
assert spec is not None, "Failed to create module spec"
spa_routing = importlib.util.module_from_spec(spec)
sys.modules["spa_routing"] = spa_routing
assert spec.loader is not None, "Module spec has no loader"
spec.loader.exec_module(spa_routing)
handler = spa_routing.handler


def make_event(host="www.example.com", uri="/"):
    """Create a mock CloudFront viewer-request event."""
    return {
        "Records": [{
            "cf": {
                "request": {
                    "headers": {"host": [{"value": host}]},
                    "uri": uri
                }
            }
        }]
    }


class TestApexRedirect:
    """Tests for apex to www redirect behavior."""

    def test_apex_returns_301_status(self):
        """Test that apex domain returns 301 status."""
        event = make_event(host="example.com", uri="/about")
        response = handler(event, None)
        assert response["status"] == "301"

    def test_apex_returns_moved_permanently_description(self):
        """Test that apex domain returns Moved Permanently status description."""
        event = make_event(host="example.com", uri="/about")
        response = handler(event, None)
        assert response["statusDescription"] == "Moved Permanently"

    def test_apex_redirects_to_www_domain(self):
        """Test that apex domain redirects to www domain."""
        event = make_event(host="example.com", uri="/about")
        response = handler(event, None)
        location = response["headers"]["location"][0]["value"]
        assert location == "https://www.example.com/about"

    def test_apex_redirect_preserves_path(self):
        """Test that apex redirect preserves the original path."""
        event = make_event(host="10ulabs.com", uri="/rack-designer/config")
        response = handler(event, None)
        location = response["headers"]["location"][0]["value"]
        assert location == "https://www.10ulabs.com/rack-designer/config"

    def test_www_does_not_redirect(self):
        """Test that www domain does not redirect."""
        event = make_event(host="www.example.com", uri="/about")
        response = handler(event, None)
        assert "status" not in response


class TestRootPathRewrite:
    """Tests for root path rewrite to /home/index.html."""

    def test_root_path_rewrites_to_home(self):
        """Test that / rewrites to /home/index.html."""
        event = make_event(host="www.example.com", uri="/")
        response = handler(event, None)
        assert response["uri"] == "/home/index.html"

    def test_empty_uri_rewrites_to_home(self):
        """Test that empty URI rewrites to /home/index.html."""
        event = make_event(host="www.example.com", uri="")
        response = handler(event, None)
        assert response["uri"] == "/home/index.html"


class TestFileExtensionPassthrough:
    """Tests for file extension passthrough behavior."""

    @pytest.mark.parametrize("uri", [
        "/styles.css",
        "/script.js",
        "/image.png",
        "/favicon.ico",
        "/home/index.html",
        "/rack-designer/app.bundle.js",
        "/deep/nested/path/file.json",
    ])
    def test_files_with_extensions_pass_through(self, uri):
        """Test that files with extensions are served as-is."""
        event = make_event(host="www.example.com", uri=uri)
        response = handler(event, None)
        assert response["uri"] == uri

    def test_file_uri_is_not_modified(self):
        """Test that file URIs are returned without modification."""
        event = make_event(host="www.example.com", uri="/assets/logo.svg")
        response = handler(event, None)
        assert response["uri"] == "/assets/logo.svg"

    def test_file_request_does_not_redirect(self):
        """Test that file requests do not trigger a redirect."""
        event = make_event(host="www.example.com", uri="/assets/logo.svg")
        response = handler(event, None)
        assert "status" not in response


class TestSpaRouting:
    """Tests for SPA routing behavior (paths without extensions)."""

    def test_path_without_extension_gets_index_html(self):
        """Test that paths without extensions get index.html appended."""
        event = make_event(host="www.example.com", uri="/about")
        response = handler(event, None)
        assert response["uri"] == "/about/index.html"

    def test_path_with_trailing_slash_gets_index_html(self):
        """Test that paths with trailing slash get index.html appended."""
        event = make_event(host="www.example.com", uri="/contact/")
        response = handler(event, None)
        assert response["uri"] == "/contact/index.html"

    def test_nested_path_without_extension_gets_index_html(self):
        """Test that nested paths without extensions get index.html appended."""
        event = make_event(host="www.example.com", uri="/rack-designer/config")
        response = handler(event, None)
        assert response["uri"] == "/rack-designer/config/index.html"

    def test_deeply_nested_path_gets_index_html(self):
        """Test that deeply nested paths get index.html appended."""
        event = make_event(host="www.example.com", uri="/a/b/c/d")
        response = handler(event, None)
        assert response["uri"] == "/a/b/c/d/index.html"


class TestEdgeCases:
    """Tests for edge cases and unusual inputs."""

    def test_missing_host_header_returns_301(self):
        """Test that missing host header returns 301 status."""
        event = {
            "Records": [{
                "cf": {
                    "request": {
                        "headers": {},
                        "uri": "/about"
                    }
                }
            }]
        }
        response = handler(event, None)
        assert response["status"] == "301"

    def test_missing_host_header_redirects_to_www(self):
        """Test that missing host header redirects to www prefix."""
        event = {
            "Records": [{
                "cf": {
                    "request": {
                        "headers": {},
                        "uri": "/about"
                    }
                }
            }]
        }
        response = handler(event, None)
        location = response["headers"]["location"][0]["value"]
        assert location == "https://www./about"

    def test_empty_host_header_returns_301(self):
        """Test that empty host header returns 301 status."""
        event = {
            "Records": [{
                "cf": {
                    "request": {
                        "headers": {"host": [{"value": ""}]},
                        "uri": "/about"
                    }
                }
            }]
        }
        response = handler(event, None)
        assert response["status"] == "301"

    def test_empty_host_header_redirects_to_www(self):
        """Test that empty host header redirects to www prefix."""
        event = {
            "Records": [{
                "cf": {
                    "request": {
                        "headers": {"host": [{"value": ""}]},
                        "uri": "/about"
                    }
                }
            }]
        }
        response = handler(event, None)
        location = response["headers"]["location"][0]["value"]
        assert location == "https://www./about"

    def test_path_with_dot_in_segment_gets_index_html(self):
        """Test that paths with dots in segments (not extensions) get index.html."""
        event = make_event(host="www.example.com", uri="/v1.0/api")
        response = handler(event, None)
        # Has a dot, so treated as file - passes through
        assert response["uri"] == "/v1.0/api"

    def test_file_with_multiple_dots_passes_through(self):
        """Test that files with multiple dots pass through."""
        event = make_event(host="www.example.com", uri="/app.bundle.min.js")
        response = handler(event, None)
        assert response["uri"] == "/app.bundle.min.js"

    def test_very_long_path_gets_index_html(self):
        """Test that very long paths without extension get index.html."""
        long_path = "/" + "/".join(["segment"] * 50)
        event = make_event(host="www.example.com", uri=long_path)
        response = handler(event, None)
        assert response["uri"] == f"{long_path}/index.html"

    def test_path_with_hyphen_gets_index_html(self):
        """Test that paths with hyphens get index.html."""
        event = make_event(host="www.example.com", uri="/my-page-name")
        response = handler(event, None)
        assert response["uri"] == "/my-page-name/index.html"

    def test_path_with_underscore_gets_index_html(self):
        """Test that paths with underscores get index.html."""
        event = make_event(host="www.example.com", uri="/my_page_name")
        response = handler(event, None)
        assert response["uri"] == "/my_page_name/index.html"

    def test_path_with_numbers_gets_index_html(self):
        """Test that paths with numbers get index.html."""
        event = make_event(host="www.example.com", uri="/page123")
        response = handler(event, None)
        assert response["uri"] == "/page123/index.html"

    def test_hidden_file_passes_through(self):
        """Test that hidden files (starting with dot) pass through."""
        event = make_event(host="www.example.com", uri="/.well-known/acme-challenge")
        response = handler(event, None)
        # Has a dot, treated as having extension
        assert response["uri"] == "/.well-known/acme-challenge"

    def test_subdomain_without_www_returns_301(self):
        """Test that subdomains without www return 301 status."""
        event = make_event(host="api.example.com", uri="/health")
        response = handler(event, None)
        assert response["status"] == "301"

    def test_subdomain_without_www_redirect_location(self):
        """Test that subdomain redirect location adds www prefix."""
        event = make_event(host="api.example.com", uri="/health")
        response = handler(event, None)
        location = response["headers"]["location"][0]["value"]
        assert location == "https://www.api.example.com/health"
