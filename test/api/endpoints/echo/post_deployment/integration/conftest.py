"""Pytest fixtures for echo integration tests."""
from test.api.conftest import skip_if_endpoint_not_deployed

# Re-export for local imports
__all__ = ['skip_if_endpoint_not_deployed']
