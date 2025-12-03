from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
RACK_DESIGNER_SRC = REPO_ROOT / "src" / "www" / "paths" / "rack_designer"
GOOGLE_ANALYTICS_ID = "G-8YJFQC2EGV"
GTAG_SCRIPT_URL = f"https://www.googletagmanager.com/gtag/js?id={GOOGLE_ANALYTICS_ID}"
GTAG_CONFIG = f"gtag('config', '{GOOGLE_ANALYTICS_ID}')"


def test_index_html_has_gtag_script():
    content = (RACK_DESIGNER_SRC / "index.html").read_text()
    assert GTAG_SCRIPT_URL in content


def test_index_html_has_gtag_config():
    content = (RACK_DESIGNER_SRC / "index.html").read_text()
    assert GTAG_CONFIG in content
