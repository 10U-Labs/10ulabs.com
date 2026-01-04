"""Layer 3: Authorization tests for sessions endpoint.

Authorization tests verify permission to INSPECT prerequisite resources.
Not existence, not capability - just permission to check.
"""
import pytest
from botocore.exceptions import ClientError



class TestIamAuthorization:
    """Tests for IAM inspection authorization."""

    def test_can_describe_iam_role(self, iam_client, sessions_config):
        """Verify permission to inspect sessions handler IAM role."""
        has_permission = True
        try:
            iam_client.get_role(RoleName=sessions_config["handler_role_name"])
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pass  # Role doesn't exist but we have permission to check
            elif e.response["Error"]["Code"] == "AccessDenied":
                has_permission = False
            else:
                raise
        assert has_permission, "No permission to inspect IAM role"


class TestDynamoDbAuthorization:
    """Tests for DynamoDB inspection authorization."""

    def test_can_describe_dynamodb_table(self, dynamodb_client, sessions_config):
        """Verify permission to describe DynamoDB table."""
        has_permission = True
        try:
            dynamodb_client.describe_table(TableName=sessions_config["dynamodb_table_name"])
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pass  # Table doesn't exist but we have permission to check
            elif e.response["Error"]["Code"] == "AccessDeniedException":
                has_permission = False
            else:
                raise
        assert has_permission, "No permission to describe DynamoDB table"


class TestS3Authorization:
    """Tests for S3 inspection authorization."""

    def test_can_describe_s3_bucket(self, s3_client, sessions_config):
        """Verify permission to head S3 bucket."""
        has_permission = True
        try:
            s3_client.head_bucket(Bucket=sessions_config["s3_bucket_name"])
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ("403", "AccessDenied"):
                has_permission = False
            elif error_code != "404":
                raise
        assert has_permission, "No permission to inspect S3 bucket"


class TestApiGatewayAuthorization:
    """Tests for API Gateway inspection authorization."""

    def test_can_describe_api_gateway(self, apigateway_client, api_gateway_id):
        """Verify permission to describe API Gateway."""
        if api_gateway_id is None:
            pytest.skip("API Gateway ID not available")
        has_permission = True
        try:
            apigateway_client.get_rest_api(restApiId=api_gateway_id)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NotFoundException":
                pass  # API doesn't exist but we have permission to check
            elif e.response["Error"]["Code"] == "AccessDeniedException":
                has_permission = False
            else:
                raise
        assert has_permission, "No permission to describe API Gateway"
