"""Tests to validate asset path alignment between build output and deployment.

This test prevents the bug where:
- Vite builds index.html with /assets/* references
- Files are deployed to S3 at /home/assets/*
- Lambda@Edge must rewrite /assets/* to /home/assets/*

If any of these are misaligned, the React app fails to load.
"""

import re
from pathlib import Path

from repo_utils import REPO_ROOT

DIST_DIR = REPO_ROOT / "src" / "www" / "paths" / "home" / "dist"
LAMBDA_FILE = REPO_ROOT / "src" / "www" / "common" / "lambda" / "spa_routing.py"


class TestAssetPathAlignment:
    """Verify asset paths in index.html align with dist structure."""

    def test_dist_index_html_exists(self):
        """Verify dist/index.html exists (build has run)."""
        index_path = DIST_DIR / "index.html"
        assert index_path.exists(), (
            f"dist/index.html not found at {index_path}. "
            "Run 'npm run build --prefix src/www/paths/home' first."
        )

    def test_asset_js_files_exist(self):
        """Verify JS files referenced in index.html exist in dist/assets/."""
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

    def test_asset_css_files_exist(self):
        """Verify CSS files referenced in index.html exist in dist/assets/."""
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
    """Verify Lambda@Edge rewrites /assets/* to /home/assets/*."""

    def test_lambda_file_exists(self):
        """Verify spa_routing.py Lambda exists."""
        assert LAMBDA_FILE.exists(), (
            f"Lambda file not found at {LAMBDA_FILE}"
        )

    def test_lambda_has_assets_prefix_check(self):
        """Verify Lambda checks for /assets/ prefix."""
        if not LAMBDA_FILE.exists():
            return
        content = LAMBDA_FILE.read_text()
        assert 'uri.startswith("/assets/")' in content

    def test_lambda_has_home_rewrite(self):
        """Verify Lambda rewrites to /home prefix."""
        if not LAMBDA_FILE.exists():
            return
        content = LAMBDA_FILE.read_text()
        assert '"/home"' in content or "/home" in content

    def test_lambda_rewrite_before_extension_passthrough(self):
        """Verify /assets/ rewrite happens before generic extension passthrough."""
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
