import re

import pytest
from repo_utils import REPO_ROOT

DIST_DIR = REPO_ROOT / "src" / "www" / "paths" / "home" / "dist"
SPA_ROUTING_FILE = REPO_ROOT / "src" / "www" / "common" / "function" / "spa_routing.js"


def test_dist_directory_structure_valid() -> None:
    index_path = DIST_DIR / "index.html"
    if not index_path.exists():
        return
    content = index_path.read_text()
    is_html = "<!DOCTYPE html>" in content or "<html" in content.lower()
    assert is_html, "dist/index.html should be valid HTML"


def test_asset_js_files_exist() -> None:
    index_path = DIST_DIR / "index.html"
    if not index_path.exists():
        return
    content = index_path.read_text()
    js_refs = re.findall(r'src="(/assets/[^"]+\.js)"', content)
    for ref in js_refs:
        asset_path = DIST_DIR / ref.lstrip("/")
        assert asset_path.exists(), (
            f"index.html references {ref} but file not found at {asset_path}"
        )


def test_asset_css_files_exist() -> None:
    index_path = DIST_DIR / "index.html"
    if not index_path.exists():
        return
    content = index_path.read_text()
    css_refs = re.findall(r'href="(/assets/[^"]+\.css)"', content)
    for ref in css_refs:
        asset_path = DIST_DIR / ref.lstrip("/")
        assert asset_path.exists(), (
            f"index.html references {ref} but file not found at {asset_path}"
        )


@pytest.fixture(name="spa_routing_source", scope="module")
def spa_routing_source_fixture() -> str:
    return SPA_ROUTING_FILE.read_text()


def test_spa_routing_file_exists() -> None:
    assert SPA_ROUTING_FILE.exists(), (
        f"SPA routing function not found at {SPA_ROUTING_FILE}"
    )


def test_spa_routing_has_assets_prefix_check(spa_routing_source: str) -> None:
    assert "uri.startsWith('/assets/')" in spa_routing_source


def test_spa_routing_has_home_rewrite(spa_routing_source: str) -> None:
    assert "`/home${uri}`" in spa_routing_source


def test_spa_routing_rewrite_before_extension_passthrough(spa_routing_source: str) -> None:
    assets_pos = spa_routing_source.find("uri.startsWith('/assets/')")
    extension_pos = spa_routing_source.find("uri.includes('.')")
    assert assets_pos != -1 and extension_pos != -1, (
        "SPA routing function must check /assets/ and the extension passthrough"
    )
    assert assets_pos < extension_pos, (
        "SPA routing /assets/ rewrite must come BEFORE the generic extension passthrough. "
        "Otherwise /assets/*.js would pass through unrewritten."
    )
