"""Tests to validate DynamoDB tables before runners deployment.

These tests run after test_01_iam_credentials.py to ensure we have valid
credentials before testing DynamoDB resources.

Five-layer testing model:
- Layer 2: Authorization - Can we call DynamoDB APIs?
- Layer 3: Existence - Do the required tables exist?
- Layer 4: Configuration - Are tables configured correctly?
- Layer 5: Capability - Can we perform required operations?
"""

import uuid

from botocore.exceptions import ClientError
import pytest


# =============================================================================
# Layer 2: Authorization
# =============================================================================

def test_01_can_call_describe_table_api(dynamodb_client, config):
    """Layer 2: Verify we have permission to call dynamodb:DescribeTable."""
    table_name = config['idempotency_table_name']
    try:
        dynamodb_client.describe_table(TableName=table_name)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDeniedException":
            pytest.fail(
                f"No permission to call DescribeTable on '{table_name}'. "
                "Check IAM permissions for dynamodb:DescribeTable."
            )
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            pass  # Table doesn't exist, but we have permission - that's OK here
        else:
            raise


# =============================================================================
# Layer 3: Existence - All Tables
# =============================================================================

class TestDynamoDBTablesExistence:
    """Layer 3: Verify all required DynamoDB tables exist."""

    def test_01_idempotency_table_exists(self, dynamodb_client, config):
        """Verify the idempotency table exists."""
        table_name = config['idempotency_table_name']
        try:
            response = dynamodb_client.describe_table(TableName=table_name)
            assert response["Table"]["TableName"] == table_name
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"DynamoDB table '{table_name}' does not exist. "
                    "Run terraform apply in src/api/endpoints/runners/"
                )
            raise

    def test_02_circuit_breaker_state_table_exists(self, dynamodb_client, config):
        """Verify the circuit breaker state table exists."""
        table_name = config['circuit_breaker_state_table_name']
        try:
            response = dynamodb_client.describe_table(TableName=table_name)
            assert response["Table"]["TableName"] == table_name
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"DynamoDB table '{table_name}' does not exist. "
                    "Run terraform apply in src/api/endpoints/runners/"
                )
            raise

    def test_03_workflow_runners_table_exists(self, dynamodb_client, config):
        """Verify the workflow runners table exists."""
        table_name = config['workflow_runners_table_name']
        try:
            response = dynamodb_client.describe_table(TableName=table_name)
            assert response["Table"]["TableName"] == table_name
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"DynamoDB table '{table_name}' does not exist. "
                    "Run terraform apply in src/api/endpoints/runners/"
                )
            raise

    def test_04_incidents_table_exists(self, dynamodb_client, config):
        """Verify the incidents table exists."""
        table_name = config['incidents_table_name']
        try:
            response = dynamodb_client.describe_table(TableName=table_name)
            assert response["Table"]["TableName"] == table_name
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"DynamoDB table '{table_name}' does not exist. "
                    "Run terraform apply in src/api/endpoints/runners/"
                )
            raise


# =============================================================================
# Layer 4: Configuration - Idempotency Table
# =============================================================================

class TestIdempotencyTableConfiguration:
    """Layer 4: Verify the idempotency table is configured correctly."""

    def test_01_idempotency_table_has_request_id_key(self, dynamodb_client, config):
        """Verify the idempotency table has request_id as partition key."""
        table_name = config['idempotency_table_name']
        try:
            response = dynamodb_client.describe_table(TableName=table_name)
            key_schema = response["Table"]["KeySchema"]
            partition_keys = [
                k["AttributeName"] for k in key_schema if k["KeyType"] == "HASH"
            ]
            assert "request_id" in partition_keys, (
                f"Table '{table_name}' missing 'request_id' partition key. "
                f"Found keys: {partition_keys}"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.skip(f"Table '{table_name}' does not exist")
            raise

    def test_02_idempotency_table_has_ttl_enabled(self, dynamodb_client, config):
        """Verify the idempotency table has TTL enabled."""
        table_name = config['idempotency_table_name']
        try:
            response = dynamodb_client.describe_time_to_live(TableName=table_name)
            ttl_status = response["TimeToLiveDescription"]["TimeToLiveStatus"]
            assert ttl_status == "ENABLED", (
                f"Table '{table_name}' TTL is not enabled (status: {ttl_status}). "
                "TTL should be enabled on 'ttl' attribute for automatic cleanup."
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.skip(f"Table '{table_name}' does not exist")
            raise


# =============================================================================
# Layer 5: Capability - Idempotency Table
# =============================================================================

class TestIdempotencyTableCapability:
    """Layer 5: Verify we can perform operations on the idempotency table."""

    def test_01_can_put_item(self, dynamodb_client, config):
        """Verify we can write to the idempotency table."""
        table_name = config['idempotency_table_name']
        test_id = f"pre-deployment-test-{uuid.uuid4()}"
        try:
            dynamodb_client.put_item(
                TableName=table_name,
                Item={
                    "request_id": {"S": test_id},
                    "ttl": {"N": "0"},
                }
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    f"No permission to write to '{table_name}'. "
                    "Check IAM permissions for dynamodb:PutItem."
                )
            raise
        finally:
            try:
                dynamodb_client.delete_item(
                    TableName=table_name,
                    Key={"request_id": {"S": test_id}}
                )
            except ClientError:
                pass

    def test_02_can_get_item(self, dynamodb_client, config):
        """Verify we can read from the idempotency table."""
        table_name = config['idempotency_table_name']
        test_id = f"pre-deployment-test-{uuid.uuid4()}"
        try:
            dynamodb_client.put_item(
                TableName=table_name,
                Item={
                    "request_id": {"S": test_id},
                    "ttl": {"N": "0"},
                }
            )
            dynamodb_client.get_item(
                TableName=table_name,
                Key={"request_id": {"S": test_id}}
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    f"No permission to read from '{table_name}'. "
                    "Check IAM permissions for dynamodb:GetItem."
                )
            raise
        finally:
            try:
                dynamodb_client.delete_item(
                    TableName=table_name,
                    Key={"request_id": {"S": test_id}}
                )
            except ClientError:
                pass
