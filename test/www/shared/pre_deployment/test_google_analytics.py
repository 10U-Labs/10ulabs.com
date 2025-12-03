from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
HOME_PAGE_SRC = REPO_ROOT / "src" / "www" / "paths" / "index"
GOOGLE_ANALYTICS_ID = "G-8YJFQC2EGV"
GTAG_SCRIPT_URL = f"https://www.googletagmanager.com/gtag/js?id={GOOGLE_ANALYTICS_ID}"
GTAG_CONFIG = f"gtag('config', '{GOOGLE_ANALYTICS_ID}')"


def test_index_html_has_gtag_script():
    content = (HOME_PAGE_SRC / "index.html").read_text()
    assert GTAG_SCRIPT_URL in content


def test_index_html_has_gtag_config():
    content = (HOME_PAGE_SRC / "index.html").read_text()
    assert GTAG_CONFIG in content


def test_privacy_html_has_gtag_script():
    content = (HOME_PAGE_SRC / "public" / "privacy.html").read_text()
    assert GTAG_SCRIPT_URL in content


def test_privacy_html_has_gtag_config():
    content = (HOME_PAGE_SRC / "public" / "privacy.html").read_text()
    assert GTAG_CONFIG in content
