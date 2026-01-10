"""Terraform unit tests for dynamodb.tf.

These tests verify DynamoDB tables are correctly configured.
"""

import re

import pytest

# Expected DynamoDB tables
DYNAMODB_TABLES = [
    "idempotency",
    "circuit_breaker_state",
    "incidents",
]


class TestDynamoDBTablesExist:
    """Test that all expected DynamoDB tables are defined."""

    @pytest.mark.parametrize("table_name", DYNAMODB_TABLES)
    def test_dynamodb_table_exists(self, dynamodb_tf_content, table_name):
        """Verify DynamoDB table resource is defined."""
        pattern = rf'resource\s+"aws_dynamodb_table"\s+"{table_name}"'
        assert re.search(pattern, dynamodb_tf_content), (
            f"DynamoDB table '{table_name}' not found in dynamodb.tf"
        )


class TestDynamoDBTableConfiguration:
    """Test DynamoDB table configurations."""

    def test_tables_have_hash_key(self, dynamodb_tf_content):
        """Verify DynamoDB tables have hash_key defined."""
        table_count = len(re.findall(r'resource\s+"aws_dynamodb_table"', dynamodb_tf_content))
        hash_key_count = len(re.findall(r'hash_key\s*=', dynamodb_tf_content))
        assert hash_key_count >= table_count, (
            f"Not all tables have hash_key: "
            f"found {hash_key_count} for {table_count} tables"
        )

    def test_tables_use_pay_per_request(self, dynamodb_tf_content):
        """Verify DynamoDB tables use PAY_PER_REQUEST billing mode."""
        pattern = r'billing_mode\s*=\s*"PAY_PER_REQUEST"'
        pay_per_request_count = len(re.findall(pattern, dynamodb_tf_content))
        table_count = len(re.findall(r'resource\s+"aws_dynamodb_table"', dynamodb_tf_content))
        assert pay_per_request_count >= table_count, (
            f"Not all tables use PAY_PER_REQUEST: "
            f"found {pay_per_request_count} for {table_count} tables"
        )


class TestDynamoDBTTLConfiguration:
    """Test DynamoDB TTL configurations."""

    def test_idempotency_table_has_ttl(self, dynamodb_tf_content):
        """Verify idempotency table has TTL configured."""
        # Look for TTL block in the idempotency table
        pattern = r'ttl\s*\{'
        assert re.search(pattern, dynamodb_tf_content), (
            "TTL configuration not found in dynamodb.tf"
        )

    def test_ttl_attribute_defined(self, dynamodb_tf_content):
        """Verify TTL attribute name is defined."""
        pattern = r'attribute_name\s*='
        assert re.search(pattern, dynamodb_tf_content), (
            "TTL attribute_name not found in dynamodb.tf"
        )


class TestDynamoDBAttributeDefinitions:
    """Test DynamoDB attribute definitions."""

    def test_tables_have_attribute_definitions(self, dynamodb_tf_content):
        """Verify tables have attribute definitions."""
        pattern = r'attribute\s*\{'
        attr_count = len(re.findall(pattern, dynamodb_tf_content))
        table_count = len(re.findall(r'resource\s+"aws_dynamodb_table"', dynamodb_tf_content))
        assert attr_count >= table_count, (
            f"Not all tables have attribute definitions: "
            f"found {attr_count} for {table_count} tables"
        )


class TestDynamoDBNamingConventions:
    """Test DynamoDB naming conventions."""

    @pytest.mark.parametrize("table_name", DYNAMODB_TABLES)
    def test_table_names_use_locals(self, dynamodb_tf_content, table_name):
        """Verify table names use local variables (directly or via interpolation)."""
        # Find the table resource and check its name attribute uses locals
        # Accept both direct local reference and string interpolation with local
        direct_pattern = rf'resource\s+"aws_dynamodb_table"\s+"{table_name}"[^}}]*?name\s*=\s*local\.'
        interpolation_pattern = rf'resource\s+"aws_dynamodb_table"\s+"{table_name}"[^}}]*?name\s*=\s*"\${{local\.'
        assert re.search(direct_pattern, dynamodb_tf_content, re.DOTALL) or \
               re.search(interpolation_pattern, dynamodb_tf_content, re.DOTALL), (
            f"DynamoDB table '{table_name}' should use local variable for name"
        )


class TestDynamoDBPointInTimeRecovery:
    """Test DynamoDB point-in-time recovery configurations."""

    def test_point_in_time_recovery_configured(self, dynamodb_tf_content):
        """Verify point-in-time recovery is configured for tables."""
        pattern = r'point_in_time_recovery\s*\{'
        pitr_count = len(re.findall(pattern, dynamodb_tf_content))
        # At least some tables should have PITR
        assert pitr_count >= 1, (
            "Point-in-time recovery not configured for any table"
        )
