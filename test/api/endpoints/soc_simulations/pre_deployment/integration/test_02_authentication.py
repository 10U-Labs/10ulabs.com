"""Layer 2: Authentication tests for soc_simulations endpoint.

Tests that AWS credentials are valid. No authorization or resource checks.
"""
import pytest

from test_fixtures.integration import Layer2EndpointAuthenticationTests


pytest_plugins = ['test_fixtures.aws']


class TestAWSAuthentication(Layer2EndpointAuthenticationTests):
    """Authentication tests - verify AWS credentials are valid."""
