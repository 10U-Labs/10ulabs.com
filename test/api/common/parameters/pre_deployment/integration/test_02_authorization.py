"""Layer 2: Authorization tests for api/common/parameters pre-deployment.

Tests that we have permission to inspect required resources.

Six-layer testing model:
- Layer 2: Authorization - Permission to inspect resources
"""

import pytest
from test_fixtures.integration import Layer2IAMAuthorizationTests, Layer2S3AuthorizationTests


pytestmark = pytest.mark.layer(2)


class TestIAMAuthorization(Layer2IAMAuthorizationTests):
    """Layer 2: Verify IAM inspection permissions."""


class TestS3Authorization(Layer2S3AuthorizationTests):
    """Layer 2: Verify S3 inspection permissions."""
