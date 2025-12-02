import requests

GOOGLE_ANALYTICS_ID = "G-8YJFQC2EGV"
GTAG_SCRIPT_URL = f"https://www.googletagmanager.com/gtag/js?id={GOOGLE_ANALYTICS_ID}"


def test_home_page_has_gtag_script(website_url):
    response = requests.get(website_url, timeout=30)
    assert GTAG_SCRIPT_URL in response.text


def test_home_page_has_gtag_config(website_url):
    response = requests.get(website_url, timeout=30)
    assert f"gtag('config', '{GOOGLE_ANALYTICS_ID}')" in response.text


def test_privacy_page_has_gtag_script(website_url):
    response = requests.get(f"{website_url}/privacy.html", timeout=30)
    assert GTAG_SCRIPT_URL in response.text


def test_privacy_page_has_gtag_config(website_url):
    response = requests.get(f"{website_url}/privacy.html", timeout=30)
    assert f"gtag('config', '{GOOGLE_ANALYTICS_ID}')" in response.text
