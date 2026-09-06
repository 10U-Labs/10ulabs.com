from unittest.mock import MagicMock, patch

from test_fixtures.website import create_website_fixtures


def test_returns_tuple() -> None:
    result = create_website_fixtures()
    assert isinstance(result, tuple)


def test_returns_two_fixtures() -> None:
    result = create_website_fixtures()
    assert len(result) == 2


def test_website_url_fixture_is_callable() -> None:
    website_url, _ = create_website_fixtures()
    assert callable(website_url)


def test_website_response_fixture_is_callable() -> None:
    _, website_response = create_website_fixtures()
    assert callable(website_response)


def test_website_url_constructs_https_url() -> None:
    website_url_fixture, _ = create_website_fixtures()
    mock_config = {'website_fqdn': 'www.example.com'}
    result = website_url_fixture.__wrapped__(mock_config)
    assert result == 'https://www.example.com'


def test_website_url_uses_config_fqdn() -> None:
    website_url_fixture, _ = create_website_fixtures()
    mock_config = {'website_fqdn': 'www.test-site.org'}
    result = website_url_fixture.__wrapped__(mock_config)
    assert 'www.test-site.org' in result


def test_website_url_has_https_prefix() -> None:
    website_url_fixture, _ = create_website_fixtures()
    mock_config = {'website_fqdn': 'any-domain.com'}
    result = website_url_fixture.__wrapped__(mock_config)
    assert result.startswith('https://')


@patch('test_fixtures.website.requests.get')
def test_website_response_calls_requests_get(mock_get: MagicMock) -> None:
    _, website_response_fixture = create_website_fixtures()
    mock_response = MagicMock()
    mock_get.return_value = mock_response
    website_response_fixture.__wrapped__('https://www.example.com')
    assert mock_get.call_count == 1


@patch('test_fixtures.website.requests.get')
def test_website_response_passes_url(mock_get: MagicMock) -> None:
    _, website_response_fixture = create_website_fixtures()
    mock_response = MagicMock()
    mock_get.return_value = mock_response
    website_response_fixture.__wrapped__('https://www.test.com')
    assert mock_get.call_args[0][0] == 'https://www.test.com'


@patch('test_fixtures.website.requests.get')
def test_website_response_uses_30_second_timeout(mock_get: MagicMock) -> None:
    _, website_response_fixture = create_website_fixtures()
    mock_response = MagicMock()
    mock_get.return_value = mock_response
    website_response_fixture.__wrapped__('https://www.example.com')
    call_kwargs = mock_get.call_args[1]
    assert call_kwargs['timeout'] == 30


@patch('test_fixtures.website.requests.get')
def test_website_response_returns_response_object(mock_get: MagicMock) -> None:
    _, website_response_fixture = create_website_fixtures()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    result = website_response_fixture.__wrapped__('https://www.example.com')
    assert result is mock_response


@patch('test_fixtures.website.requests.get')
def test_url_fixture_produces_correct_url(mock_get: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    website_url_fixture, website_response_fixture = create_website_fixtures()
    mock_config = {'website_fqdn': 'www.example.com'}

    url = website_url_fixture.__wrapped__(mock_config)
    website_response_fixture.__wrapped__(url)

    assert url == 'https://www.example.com'


@patch('test_fixtures.website.requests.get')
def test_response_fixture_returns_valid_response(mock_get: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    website_url_fixture, website_response_fixture = create_website_fixtures()
    mock_config = {'website_fqdn': 'www.example.com'}

    url = website_url_fixture.__wrapped__(mock_config)
    response = website_response_fixture.__wrapped__(url)

    assert response.status_code == 200
