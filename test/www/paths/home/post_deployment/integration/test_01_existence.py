import requests


class TestHomePageExists:
    def test_home_page_returns_200(self, website_url: str) -> None:
        response = requests.get(website_url, timeout=30)
        status_is_200 = response.status_code == 200
        assert status_is_200, f"Home page returned {response.status_code}"

    def test_home_page_has_content(self, website_url: str) -> None:
        response = requests.get(website_url, timeout=30)
        has_content = len(response.text) > 0
        assert has_content, "Home page returned empty content"


class TestStaticFilesExist:
    def test_robots_txt_exists(self, website_url: str) -> None:
        response = requests.get(f"{website_url}/robots.txt", timeout=30)
        file_exists = response.status_code == 200
        assert file_exists, f"robots.txt returned {response.status_code}"

    def test_ads_txt_exists(self, website_url: str) -> None:
        response = requests.get(f"{website_url}/ads.txt", timeout=30)
        file_exists = response.status_code == 200
        assert file_exists, f"ads.txt returned {response.status_code}"

    def test_privacy_page_exists(self, website_url: str) -> None:
        response = requests.get(f"{website_url}/privacy.html", timeout=30)
        page_exists = response.status_code == 200
        assert page_exists, f"privacy.html returned {response.status_code}"


class TestSPARoutingExists:
    def test_nonexistent_path_returns_200(self, website_url: str) -> None:
        response = requests.get(f"{website_url}/nonexistent-page-test", timeout=30)
        status_is_200 = response.status_code == 200
        assert status_is_200, (
            f"SPA routing returned {response.status_code} for nonexistent path"
        )

    def test_deeply_nested_nonexistent_path_returns_200(self, website_url: str) -> None:
        response = requests.get(f"{website_url}/a/b/c/d/nonexistent", timeout=30)
        status_is_200 = response.status_code == 200
        assert status_is_200, (
            f"SPA routing returned {response.status_code} for nested path"
        )
