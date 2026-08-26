import importlib.util
import sys

import pytest

from repo_utils import REPO_ROOT

LAMBDA_DIR = REPO_ROOT / "src" / "www" / "common" / "lambda"
spec = importlib.util.spec_from_file_location("spa_routing", LAMBDA_DIR / "handler.py")
assert spec is not None, "Failed to create module spec"
spa_routing = importlib.util.module_from_spec(spec)
sys.modules["spa_routing"] = spa_routing
assert spec.loader is not None, "Module spec has no loader"
spec.loader.exec_module(spa_routing)
handler = spa_routing.lambda_handler


def make_event(host="www.example.com", uri="/"):
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
    def test_apex_returns_301_status(self):
        event = make_event(host="example.com", uri="/about")
        response = handler(event, None)
        assert response["status"] == "301"

    def test_apex_returns_moved_permanently_description(self):
        event = make_event(host="example.com", uri="/about")
        response = handler(event, None)
        assert response["statusDescription"] == "Moved Permanently"

    def test_apex_redirects_to_www_domain(self):
        event = make_event(host="example.com", uri="/about")
        response = handler(event, None)
        location = response["headers"]["location"][0]["value"]
        assert location == "https://www.example.com/about"

    def test_apex_redirect_preserves_path(self):
        event = make_event(host="10ulabs.com", uri="/rack-designer/config")
        response = handler(event, None)
        location = response["headers"]["location"][0]["value"]
        assert location == "https://www.10ulabs.com/rack-designer/config"

    def test_www_does_not_redirect(self):
        event = make_event(host="www.example.com", uri="/about/")
        response = handler(event, None)
        assert "status" not in response


class TestRootPathRewrite:
    def test_root_path_rewrites_to_home(self):
        event = make_event(host="www.example.com", uri="/")
        response = handler(event, None)
        assert response["uri"] == "/home/index.html"

    def test_empty_uri_rewrites_to_home(self):
        event = make_event(host="www.example.com", uri="")
        response = handler(event, None)
        assert response["uri"] == "/home/index.html"


class TestFileExtensionPassthrough:
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
        event = make_event(host="www.example.com", uri=uri)
        response = handler(event, None)
        assert response["uri"] == uri

    def test_non_asset_file_uri_is_not_modified(self):
        event = make_event(host="www.example.com", uri="/images/logo.svg")
        response = handler(event, None)
        assert response["uri"] == "/images/logo.svg"

    def test_file_request_does_not_redirect(self):
        event = make_event(host="www.example.com", uri="/images/logo.svg")
        response = handler(event, None)
        assert "status" not in response


class TestAssetsRewrite:
    def test_assets_js_rewrites_to_home(self):
        event = make_event(host="www.example.com", uri="/assets/index-abc123.js")
        response = handler(event, None)
        assert response["uri"] == "/home/assets/index-abc123.js"

    def test_assets_css_rewrites_to_home(self):
        event = make_event(host="www.example.com", uri="/assets/index-xyz789.css")
        response = handler(event, None)
        assert response["uri"] == "/home/assets/index-xyz789.css"

    def test_assets_svg_rewrites_to_home(self):
        event = make_event(host="www.example.com", uri="/assets/logo.svg")
        response = handler(event, None)
        assert response["uri"] == "/home/assets/logo.svg"

    def test_assets_request_does_not_redirect(self):
        event = make_event(host="www.example.com", uri="/assets/file.js")
        response = handler(event, None)
        assert "status" not in response

    def test_home_assets_does_not_double_rewrite(self):
        event = make_event(host="www.example.com", uri="/home/assets/file.js")
        response = handler(event, None)
        assert response["uri"] == "/home/assets/file.js"


class TestTrailingSlashRedirect:
    def test_path_without_trailing_slash_returns_301(self):
        event = make_event(host="www.example.com", uri="/rack-designer")
        response = handler(event, None)
        assert response["status"] == "301"

    def test_path_without_trailing_slash_redirect_location(self):
        event = make_event(host="www.example.com", uri="/rack-designer")
        response = handler(event, None)
        location = response["headers"]["location"][0]["value"]
        assert location == "https://www.example.com/rack-designer/"

    def test_nested_path_without_trailing_slash_returns_301(self):
        event = make_event(host="www.example.com", uri="/rack-designer/ABCD12345")
        response = handler(event, None)
        assert response["status"] == "301"

    def test_nested_path_without_trailing_slash_redirect_location(self):
        event = make_event(host="www.example.com", uri="/rack-designer/ABCD12345")
        response = handler(event, None)
        location = response["headers"]["location"][0]["value"]
        assert location == "https://www.example.com/rack-designer/ABCD12345/"


class TestSpaRouting:
    def test_path_without_extension_redirects(self):
        event = make_event(host="www.example.com", uri="/about")
        response = handler(event, None)
        assert response["status"] == "301"

    def test_path_with_trailing_slash_gets_index_html(self):
        event = make_event(host="www.example.com", uri="/contact/")
        response = handler(event, None)
        assert response["uri"] == "/contact/index.html"

    def test_nested_path_without_extension_redirects(self):
        event = make_event(host="www.example.com", uri="/rack-designer/config")
        response = handler(event, None)
        assert response["status"] == "301"

    def test_deeply_nested_path_redirects(self):
        event = make_event(host="www.example.com", uri="/a/b/c/d")
        response = handler(event, None)
        assert response["status"] == "301"


class TestEdgeCases:
    def test_missing_host_header_returns_301(self):
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
        event = make_event(host="www.example.com", uri="/v1.0/api")
        response = handler(event, None)
        assert response["uri"] == "/v1.0/api"

    def test_file_with_multiple_dots_passes_through(self):
        event = make_event(host="www.example.com", uri="/app.bundle.min.js")
        response = handler(event, None)
        assert response["uri"] == "/app.bundle.min.js"

    def test_very_long_path_redirects(self):
        long_path = "/" + "/".join(["segment"] * 50)
        event = make_event(host="www.example.com", uri=long_path)
        response = handler(event, None)
        assert response["status"] == "301"

    def test_path_with_hyphen_redirects(self):
        event = make_event(host="www.example.com", uri="/my-page-name")
        response = handler(event, None)
        assert response["status"] == "301"

    def test_path_with_underscore_redirects(self):
        event = make_event(host="www.example.com", uri="/my_page_name")
        response = handler(event, None)
        assert response["status"] == "301"

    def test_path_with_numbers_redirects(self):
        event = make_event(host="www.example.com", uri="/page123")
        response = handler(event, None)
        assert response["status"] == "301"

    def test_hidden_file_passes_through(self):
        event = make_event(host="www.example.com", uri="/.well-known/acme-challenge")
        response = handler(event, None)
        assert response["uri"] == "/.well-known/acme-challenge"

    def test_subdomain_without_www_returns_301(self):
        event = make_event(host="api.example.com", uri="/health")
        response = handler(event, None)
        assert response["status"] == "301"

    def test_subdomain_without_www_redirect_location(self):
        event = make_event(host="api.example.com", uri="/health")
        response = handler(event, None)
        location = response["headers"]["location"][0]["value"]
        assert location == "https://www.api.example.com/health"
