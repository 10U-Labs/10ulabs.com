import re

from repo_utils import REPO_ROOT

DIST_DIR = REPO_ROOT / "src" / "www" / "paths" / "home" / "dist"
LAMBDA_FILE = REPO_ROOT / "src" / "www" / "common" / "lambda" / "handler.py"


class TestAssetPathAlignment:
    def test_dist_directory_structure_valid(self) -> None:
        index_path = DIST_DIR / "index.html"
        if not index_path.exists():
            return
        content = index_path.read_text()
        is_html = "<!DOCTYPE html>" in content or "<html" in content.lower()
        assert is_html, "dist/index.html should be valid HTML"

    def test_asset_js_files_exist(self) -> None:
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

    def test_asset_css_files_exist(self) -> None:
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


class TestLambdaAssetRewrite:
    def test_lambda_file_exists(self) -> None:
        assert LAMBDA_FILE.exists(), (
            f"Lambda file not found at {LAMBDA_FILE}"
        )

    def test_lambda_has_assets_prefix_check(self) -> None:
        if not LAMBDA_FILE.exists():
            return
        content = LAMBDA_FILE.read_text()
        assert 'uri.startswith("/assets/")' in content

    def test_lambda_has_home_rewrite(self) -> None:
        if not LAMBDA_FILE.exists():
            return
        content = LAMBDA_FILE.read_text()
        assert '"/home"' in content or "/home" in content

    def test_lambda_rewrite_before_extension_passthrough(self) -> None:
        if not LAMBDA_FILE.exists():
            return
        content = LAMBDA_FILE.read_text()
        assets_pos = content.find('uri.startswith("/assets/")')
        extension_pos = content.find('if "." in uri:')
        if assets_pos == -1 or extension_pos == -1:
            return
        assert assets_pos < extension_pos, (
            "Lambda /assets/ rewrite must come BEFORE the generic extension passthrough. "
            "Otherwise /assets/*.js would pass through unrewritten."
        )
