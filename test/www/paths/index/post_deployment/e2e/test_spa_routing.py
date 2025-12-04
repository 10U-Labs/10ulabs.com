def test_spa_handles_nonexistent_routes(nonexistent_page_response):
    assert nonexistent_page_response.status_code == 200


def test_spa_returns_html_for_nonexistent_routes(nonexistent_page_response):
    assert 'text/html' in nonexistent_page_response.headers.get('Content-Type', '')


def test_spa_has_content_for_nonexistent_routes(nonexistent_page_response):
    assert len(nonexistent_page_response.text) > 0


def test_privacy_page_returns_200(privacy_page_response):
    assert privacy_page_response.status_code == 200


def test_privacy_page_returns_html(privacy_page_response):
    assert 'text/html' in privacy_page_response.headers.get('Content-Type', '')


def test_privacy_page_has_content(privacy_page_response):
    assert len(privacy_page_response.text) > 0


def test_privacy_page_contains_privacy_content(privacy_page_response):
    assert 'Privacy' in privacy_page_response.text
