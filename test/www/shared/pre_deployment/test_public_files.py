from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
PUBLIC_DIR = REPO_ROOT / "src" / "www" / "home_page" / "react" / "public"
GOOGLE_ANALYTICS_ID = "G-8YJFQC2EGV"
ADS_TXT_CONTENT = "google.com, pub-7173129895205323, DIRECT, f08c47fec0942fa0"


def test_ads_txt_file_exists():
    assert (PUBLIC_DIR / "ads.txt").exists()


def test_ads_txt_contains_google_adsense_entry():
    content = (PUBLIC_DIR / "ads.txt").read_text()
    assert ADS_TXT_CONTENT in content


def test_robots_txt_file_exists():
    assert (PUBLIC_DIR / "robots.txt").exists()


def test_privacy_html_file_exists():
    assert (PUBLIC_DIR / "privacy.html").exists()
