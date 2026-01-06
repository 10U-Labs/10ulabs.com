"""Pytest fixtures for www_common post-deployment e2e tests."""
from test_fixtures.website import create_website_fixtures

website_url, website_response = create_website_fixtures()
