"""Unit tests for test_fixtures.website module."""
from unittest.mock import MagicMock, patch

from test_fixtures.website import create_website_fixtures


class TestCreateWebsiteFixtures:
    """Tests for create_website_fixtures function."""

    def test_returns_tuple(self):
        """Test that create_website_fixtures returns a tuple."""
        result = create_website_fixtures()
        assert isinstance(result, tuple)

    def test_returns_two_fixtures(self):
        """Test that create_website_fixtures returns two fixtures."""
        result = create_website_fixtures()
        assert len(result) == 2

    def test_fixtures_are_callable(self):
        """Test that both returned fixtures are callable."""
        website_url, website_response = create_website_fixtures()
        assert callable(website_url)
        assert callable(website_response)


class TestWebsiteUrlFixture:
    """Tests for the website_url fixture returned by create_website_fixtures."""

    def test_website_url_constructs_https_url(self):
        """Test that website_url fixture constructs https URL."""
        website_url_fixture, _ = create_website_fixtures()
        mock_config = {'website_fqdn': 'www.example.com'}
        result = website_url_fixture.__wrapped__(mock_config)
        assert result == 'https://www.example.com'

    def test_website_url_uses_config_fqdn(self):
        """Test that website_url fixture uses website_fqdn from config."""
        website_url_fixture, _ = create_website_fixtures()
        mock_config = {'website_fqdn': 'www.test-site.org'}
        result = website_url_fixture.__wrapped__(mock_config)
        assert 'www.test-site.org' in result

    def test_website_url_has_https_prefix(self):
        """Test that website_url fixture always uses https prefix."""
        website_url_fixture, _ = create_website_fixtures()
        mock_config = {'website_fqdn': 'any-domain.com'}
        result = website_url_fixture.__wrapped__(mock_config)
        assert result.startswith('https://')


class TestWebsiteResponseFixture:
    """Tests for the website_response fixture returned by create_website_fixtures."""

    @patch('test_fixtures.website.requests.get')
    def test_website_response_calls_requests_get(self, mock_get):
        """Test that website_response fixture calls requests.get."""
        _, website_response_fixture = create_website_fixtures()
        mock_response = MagicMock()
        mock_get.return_value = mock_response
        website_response_fixture.__wrapped__('https://www.example.com')
        mock_get.assert_called_once()

    @patch('test_fixtures.website.requests.get')
    def test_website_response_passes_url(self, mock_get):
        """Test that website_response fixture passes URL to requests.get."""
        _, website_response_fixture = create_website_fixtures()
        mock_response = MagicMock()
        mock_get.return_value = mock_response
        website_response_fixture.__wrapped__('https://www.test.com')
        mock_get.assert_called_with('https://www.test.com', timeout=30)

    @patch('test_fixtures.website.requests.get')
    def test_website_response_uses_30_second_timeout(self, mock_get):
        """Test that website_response fixture uses 30 second timeout."""
        _, website_response_fixture = create_website_fixtures()
        mock_response = MagicMock()
        mock_get.return_value = mock_response
        website_response_fixture.__wrapped__('https://www.example.com')
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs['timeout'] == 30

    @patch('test_fixtures.website.requests.get')
    def test_website_response_returns_response_object(self, mock_get):
        """Test that website_response fixture returns the response object."""
        _, website_response_fixture = create_website_fixtures()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        result = website_response_fixture.__wrapped__('https://www.example.com')
        assert result is mock_response


class TestFixtureIntegration:
    """Integration tests for the website fixtures working together."""

    @patch('test_fixtures.website.requests.get')
    def test_fixtures_can_be_used_together(self, mock_get):
        """Test that both fixtures can be used together."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        website_url_fixture, website_response_fixture = create_website_fixtures()
        mock_config = {'website_fqdn': 'www.example.com'}

        url = website_url_fixture.__wrapped__(mock_config)
        response = website_response_fixture.__wrapped__(url)

        assert url == 'https://www.example.com'
        assert response.status_code == 200
