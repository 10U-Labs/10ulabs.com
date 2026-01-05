"""Layer 6: Configuration tests for soc_simulations endpoint.

Tests that prerequisite resources are configured correctly.
Assumes existence passed.
"""

from test_fixtures.integration import (
    Layer5S3ConfigurationTests,
    Layer6APIGatewayRegionalTests,
)


pytest_plugins = ['test_fixtures.aws']


class TestS3Configuration(Layer5S3ConfigurationTests):
    """Tests that S3 state bucket is configured correctly."""


class TestAPIGatewayConfiguration(Layer6APIGatewayRegionalTests):
    """Tests that API Gateway is configured correctly."""


def test_state_bucket_has_versioning_enabled(s3_client, state_bucket_name):
    """Verify state bucket has versioning enabled."""
    response = s3_client.get_bucket_versioning(Bucket=state_bucket_name)
    versioning_status = response.get("Status")
    has_versioning = versioning_status == "Enabled"
    assert has_versioning, (
        f"State bucket {state_bucket_name} does not have versioning enabled. "
        f"Status: {versioning_status}"
    )


def test_state_bucket_has_encryption_enabled(s3_client, state_bucket_name):
    """Verify state bucket has server-side encryption enabled."""
    response = s3_client.get_bucket_encryption(Bucket=state_bucket_name)
    rules = response.get("ServerSideEncryptionConfiguration", {}).get("Rules", [])
    has_encryption = len(rules) > 0
    assert has_encryption, f"State bucket {state_bucket_name} does not have encryption"
