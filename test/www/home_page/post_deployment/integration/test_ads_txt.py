import requests

ADS_TXT_CONTENT = "google.com, pub-7173129895205323, DIRECT, f08c47fec0942fa0"


def test_ads_txt_returns_200(website_url):
    response = requests.get(f"{website_url}/ads.txt", timeout=30)
    assert response.status_code == 200


def test_ads_txt_returns_text_content_type(website_url):
    response = requests.get(f"{website_url}/ads.txt", timeout=30)
    content_type = response.headers.get("Content-Type", "")
    assert "text/plain" in content_type


def test_ads_txt_contains_google_adsense_entry(website_url):
    response = requests.get(f"{website_url}/ads.txt", timeout=30)
    assert ADS_TXT_CONTENT in response.text
