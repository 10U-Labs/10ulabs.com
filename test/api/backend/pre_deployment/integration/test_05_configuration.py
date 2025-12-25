"""Layer 5: Configuration tests for api_backend pre-deployment validation.

Verify prerequisite resources are configured correctly (assumes existence passed).
"""
import pytest
from test_fixtures.integration import Layer5IAMConfigurationTests

pytestmark = pytest.mark.layer(5)


class TestIAMConfiguration(Layer5IAMConfigurationTests):
    """Layer 5: Verify IAM role configuration.

    All tests inherited from base class.
    """
