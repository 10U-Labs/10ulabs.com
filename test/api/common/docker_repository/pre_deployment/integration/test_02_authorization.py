"""Layer 2: Authorization tests for api/common/docker_repository pre-deployment.

Tests that credentials have permission to INSPECT prerequisite resources.
Not existence, not capability - just permission to check.

Six-layer testing model:
- Layer 2: Authorization - Permission to inspect resources
"""

import pytest
from test_fixtures.integration import (
    Layer2IAMAuthorizationTests,
    Layer2S3AuthorizationTests,
    Layer2ECRAuthorizationTests,
)




class TestIAMRoleInspectionAuthorization(Layer2IAMAuthorizationTests):
    """Layer 2: Verify permission to inspect IAM roles."""


class TestS3AndECRInspectionAuthorization(
    Layer2S3AuthorizationTests, Layer2ECRAuthorizationTests
):
    """Layer 2: Verify permission to inspect S3 buckets and ECR repositories."""
