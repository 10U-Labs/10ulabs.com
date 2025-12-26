"""Pytest configuration for E2E tests."""
from ..conftest import skip_if_endpoint_not_deployed

# Re-export for use in test files
__all__ = ['skip_if_endpoint_not_deployed']
