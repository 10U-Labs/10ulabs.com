import json
import subprocess
from typing import Any, Callable, Dict

import pytest

from repo_utils import REPO_ROOT

FUNCTION_FILE = REPO_ROOT / "src" / "www" / "common" / "function" / "spa_routing.js"
RUNNER = (
    "\nprocess.stdout.write(JSON.stringify("
    "handler(JSON.parse(require('fs').readFileSync(0, 'utf8')))));\n"
)

Route = Callable[[Dict[str, Any]], Dict[str, Any]]


@pytest.fixture(name="route", scope="module")
def route_fixture() -> Route:
    script = FUNCTION_FILE.read_text(encoding="utf-8") + RUNNER

    def route(event: Dict[str, Any]) -> Dict[str, Any]:
        result = subprocess.run(
            ["node", "-e", script],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        response: Dict[str, Any] = json.loads(result.stdout)
        return response

    return route


def make_event(host: str = "www.example.com", uri: str = "/") -> Dict[str, Any]:
    return {"request": {"headers": {"host": {"value": host}}, "uri": uri}}


def _event_without_host_header() -> Dict[str, Any]:
    event = make_event(uri="/about")
    event["request"]["headers"] = {}
    return event


def test_apex_returns_301_status(route: Route) -> None:
    event = make_event(host="example.com", uri="/about")
    response = route(event)
    assert response["statusCode"] == 301


def test_apex_returns_moved_permanently_description(route: Route) -> None:
    event = make_event(host="example.com", uri="/about")
    response = route(event)
    assert response["statusDescription"] == "Moved Permanently"


def test_apex_redirects_to_www_domain(route: Route) -> None:
    event = make_event(host="example.com", uri="/about")
    response = route(event)
    location = response["headers"]["location"]["value"]
    assert location == "https://www.example.com/about"


def test_apex_redirect_preserves_path(route: Route) -> None:
    event = make_event(host="10ulabs.com", uri="/rack-designer/config")
    response = route(event)
    location = response["headers"]["location"]["value"]
    assert location == "https://www.10ulabs.com/rack-designer/config"


def test_www_does_not_redirect(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/about/")
    response = route(event)
    assert "statusCode" not in response


def test_root_path_rewrites_to_home(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/")
    response = route(event)
    assert response["uri"] == "/home/index.html"


def test_empty_uri_rewrites_to_home(route: Route) -> None:
    event = make_event(host="www.example.com", uri="")
    response = route(event)
    assert response["uri"] == "/home/index.html"


@pytest.mark.parametrize("uri", [
    "/styles.css",
    "/script.js",
    "/image.png",
    "/favicon.ico",
    "/home/index.html",
    "/rack-designer/app.bundle.js",
    "/deep/nested/path/file.json",
])
def test_files_with_extensions_pass_through(route: Route, uri: str) -> None:
    event = make_event(host="www.example.com", uri=uri)
    response = route(event)
    assert response["uri"] == uri


def test_non_asset_file_uri_is_not_modified(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/images/logo.svg")
    response = route(event)
    assert response["uri"] == "/images/logo.svg"


def test_file_request_does_not_redirect(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/images/logo.svg")
    response = route(event)
    assert "statusCode" not in response


def test_assets_js_rewrites_to_home(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/assets/index-abc123.js")
    response = route(event)
    assert response["uri"] == "/home/assets/index-abc123.js"


def test_assets_css_rewrites_to_home(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/assets/index-xyz789.css")
    response = route(event)
    assert response["uri"] == "/home/assets/index-xyz789.css"


def test_assets_svg_rewrites_to_home(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/assets/logo.svg")
    response = route(event)
    assert response["uri"] == "/home/assets/logo.svg"


def test_assets_request_does_not_redirect(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/assets/file.js")
    response = route(event)
    assert "statusCode" not in response


def test_home_assets_does_not_double_rewrite(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/home/assets/file.js")
    response = route(event)
    assert response["uri"] == "/home/assets/file.js"


def test_path_without_trailing_slash_returns_301(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/rack-designer")
    response = route(event)
    assert response["statusCode"] == 301


def test_path_without_trailing_slash_redirect_location(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/rack-designer")
    response = route(event)
    location = response["headers"]["location"]["value"]
    assert location == "https://www.example.com/rack-designer/"


def test_nested_path_without_trailing_slash_returns_301(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/rack-designer/ABCD12345")
    response = route(event)
    assert response["statusCode"] == 301


def test_nested_path_without_trailing_slash_redirect_location(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/rack-designer/ABCD12345")
    response = route(event)
    location = response["headers"]["location"]["value"]
    assert location == "https://www.example.com/rack-designer/ABCD12345/"


def test_path_without_extension_redirects(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/about")
    response = route(event)
    assert response["statusCode"] == 301


def test_path_with_trailing_slash_gets_index_html(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/contact/")
    response = route(event)
    assert response["uri"] == "/contact/index.html"


def test_nested_path_without_extension_redirects(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/rack-designer/config")
    response = route(event)
    assert response["statusCode"] == 301


def test_deeply_nested_path_redirects(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/a/b/c/d")
    response = route(event)
    assert response["statusCode"] == 301


def test_missing_host_header_returns_301(route: Route) -> None:
    event = _event_without_host_header()
    response = route(event)
    assert response["statusCode"] == 301


def test_missing_host_header_redirects_to_www(route: Route) -> None:
    event = _event_without_host_header()
    response = route(event)
    location = response["headers"]["location"]["value"]
    assert location == "https://www./about"


def test_empty_host_header_returns_301(route: Route) -> None:
    event = make_event(host="", uri="/about")
    response = route(event)
    assert response["statusCode"] == 301


def test_empty_host_header_redirects_to_www(route: Route) -> None:
    event = make_event(host="", uri="/about")
    response = route(event)
    location = response["headers"]["location"]["value"]
    assert location == "https://www./about"


def test_path_with_dot_in_segment_gets_index_html(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/v1.0/api")
    response = route(event)
    assert response["uri"] == "/v1.0/api"


def test_file_with_multiple_dots_passes_through(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/app.bundle.min.js")
    response = route(event)
    assert response["uri"] == "/app.bundle.min.js"


def test_very_long_path_redirects(route: Route) -> None:
    long_path = "/" + "/".join(["segment"] * 50)
    event = make_event(host="www.example.com", uri=long_path)
    response = route(event)
    assert response["statusCode"] == 301


def test_path_with_hyphen_redirects(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/my-page-name")
    response = route(event)
    assert response["statusCode"] == 301


def test_path_with_underscore_redirects(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/my_page_name")
    response = route(event)
    assert response["statusCode"] == 301


def test_path_with_numbers_redirects(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/page123")
    response = route(event)
    assert response["statusCode"] == 301


def test_hidden_file_passes_through(route: Route) -> None:
    event = make_event(host="www.example.com", uri="/.well-known/acme-challenge")
    response = route(event)
    assert response["uri"] == "/.well-known/acme-challenge"


def test_subdomain_without_www_returns_301(route: Route) -> None:
    event = make_event(host="api.example.com", uri="/health")
    response = route(event)
    assert response["statusCode"] == 301


def test_subdomain_without_www_redirect_location(route: Route) -> None:
    event = make_event(host="api.example.com", uri="/health")
    response = route(event)
    location = response["headers"]["location"]["value"]
    assert location == "https://www.api.example.com/health"
