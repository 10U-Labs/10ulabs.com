"""Integration tests for rack designer Google Analytics."""
import requests

GOOGLE_ANALYTICS_ID = "G-8YJFQC2EGV"
GTAG_SCRIPT_URL = f"https://www.googletagmanager.com/gtag/js?id={GOOGLE_ANALYTICS_ID}"


def test_rack_designer_has_gtag_script(website_url):
    """Test rack designer page includes Google Analytics script."""
    response = requests.get(f"{website_url}/rack-designer/", timeout=30)
    assert GTAG_SCRIPT_URL in response.text


def test_rack_designer_has_gtag_config(website_url):
    """Test rack designer page includes Google Analytics config."""
    response = requests.get(f"{website_url}/rack-designer/", timeout=30)
    assert f"gtag('config', '{GOOGLE_ANALYTICS_ID}')" in response.text
