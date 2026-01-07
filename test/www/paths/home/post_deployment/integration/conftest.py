"""Pytest fixtures for www home page post-deployment integration tests."""
from test_fixtures.website import create_website_fixtures


# Create website fixtures (website_url, website_response)
website_url, website_response = create_website_fixtures()
