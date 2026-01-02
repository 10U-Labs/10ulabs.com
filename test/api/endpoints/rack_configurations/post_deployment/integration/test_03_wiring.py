"""Layer 3: Wiring tests for rack designer endpoint.

Tests that components are connected. Assumes existence and configuration passed.
These tests verify that resources are properly wired together.

Three-layer testing model:
- Layer 3: Wiring - Components connected properly
"""
import pytest
from botocore.exceptions import ClientError


pytestmark = pytest.mark.layer(3)


class TestLambdaWiring:
    """Layer 3: Verify Lambda is wired to API Gateway and has correct role."""

    def test_handler_has_api_gateway_permission(
        self, lambda_client, handler_function_name
    ):
        """Verify handler Lambda has permission to be invoked by API Gateway."""
        try:
            response = lambda_client.get_policy(FunctionName=handler_function_name)
            policy = response.get("Policy", "")
            assert "apigateway.amazonaws.com" in policy, (
                f"Lambda '{handler_function_name}' missing API Gateway invoke permission"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"Lambda '{handler_function_name}' has no resource policy - "
                    "API Gateway cannot invoke it"
                )
            raise

    def test_handler_has_role_attached(self, lambda_client, handler_function_name):
        """Verify handler Lambda function has IAM role attached."""
        response = lambda_client.get_function(FunctionName=handler_function_name)
        role_arn = response["Configuration"].get("Role", "")
        assert role_arn, f"Lambda '{handler_function_name}' has no IAM role attached"

    def test_handler_role_follows_naming_pattern(
        self, lambda_client, handler_function_name, handler_role_name
    ):
        """Verify handler Lambda role ARN follows expected naming pattern."""
        response = lambda_client.get_function(FunctionName=handler_function_name)
        role_arn = response["Configuration"].get("Role", "")
        assert handler_role_name in role_arn, (
            f"Lambda role ARN '{role_arn}' doesn't match expected pattern "
            f"containing '{handler_role_name}'"
        )


class TestHandlerIAMWiring:
    """Layer 3: Verify handler IAM role has required policies attached."""

    def test_handler_role_has_basic_execution_policy(
        self, iam_client, handler_role_name
    ):
        """Verify handler IAM role has Lambda basic execution policy attached."""
        response = iam_client.list_attached_role_policies(RoleName=handler_role_name)
        policy_arns = [p["PolicyArn"] for p in response["AttachedPolicies"]]
        basic_execution = (
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )
        assert basic_execution in policy_arns, (
            f"IAM role '{handler_role_name}' missing AWSLambdaBasicExecutionRole policy. "
            f"Attached policies: {policy_arns}"
        )

    def test_handler_role_has_dynamodb_policy(self, iam_client, handler_role_name):
        """Verify handler IAM role has DynamoDB access inline policy."""
        response = iam_client.list_role_policies(RoleName=handler_role_name)
        inline_policies = response.get("PolicyNames", [])
        has_dynamodb = any("DynamoDB" in p or "dynamodb" in p for p in inline_policies)
        assert has_dynamodb, (
            f"IAM role '{handler_role_name}' missing DynamoDB inline policy. "
            f"Available policies: {inline_policies}"
        )


class TestExportLambdaWiring:
    """Layer 3: Verify export Lambda IAM role has required policies."""

    def test_export_role_has_basic_execution_policy(self, iam_client, export_role_name):
        """Verify export IAM role has Lambda basic execution policy attached."""
        response = iam_client.list_attached_role_policies(RoleName=export_role_name)
        policy_arns = [p["PolicyArn"] for p in response["AttachedPolicies"]]
        basic_execution = (
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )
        assert basic_execution in policy_arns, (
            f"IAM role '{export_role_name}' missing AWSLambdaBasicExecutionRole policy. "
            f"Attached policies: {policy_arns}"
        )

    def test_export_role_has_export_permissions_policy(
        self, iam_client, export_role_name
    ):
        """Verify export IAM role has ExportPermissions inline policy."""
        response = iam_client.list_role_policies(RoleName=export_role_name)
        inline_policies = response.get("PolicyNames", [])
        has_export = "ExportPermissions" in inline_policies
        assert has_export, (
            f"IAM role '{export_role_name}' missing ExportPermissions policy. "
            f"Available policies: {inline_policies}"
        )

    def test_export_permissions_policy_has_dynamodb_actions(
        self, iam_client, export_role_name
    ):
        """Verify ExportPermissions policy includes DynamoDB export actions."""
        response = iam_client.get_role_policy(
            RoleName=export_role_name, PolicyName="ExportPermissions"
        )
        policy_doc = response.get("PolicyDocument", {})
        statements = policy_doc.get("Statement", [])
        actions = []
        for stmt in statements:
            stmt_actions = stmt.get("Action", [])
            if isinstance(stmt_actions, str):
                stmt_actions = [stmt_actions]
            actions.extend(stmt_actions)
        has_dynamodb = any("dynamodb:" in a for a in actions)
        assert has_dynamodb, (
            f"ExportPermissions policy missing DynamoDB actions. Actions: {actions}"
        )


class TestCrawlerTriggerWiring:
    """Layer 3: Verify crawler trigger Lambda IAM role has required policies."""

    def test_crawler_trigger_role_has_basic_execution_policy(
        self, iam_client, crawler_trigger_role_name
    ):
        """Verify crawler trigger IAM role has Lambda basic execution policy."""
        response = iam_client.list_attached_role_policies(
            RoleName=crawler_trigger_role_name
        )
        policy_arns = [p["PolicyArn"] for p in response["AttachedPolicies"]]
        basic_execution = (
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )
        assert basic_execution in policy_arns, (
            f"IAM role '{crawler_trigger_role_name}' missing "
            f"AWSLambdaBasicExecutionRole policy. Attached policies: {policy_arns}"
        )

    def test_crawler_trigger_role_has_glue_policy(
        self, iam_client, crawler_trigger_role_name
    ):
        """Verify crawler trigger IAM role has Glue start crawler policy."""
        response = iam_client.list_role_policies(RoleName=crawler_trigger_role_name)
        inline_policies = response.get("PolicyNames", [])
        has_glue = any("Glue" in p or "glue" in p for p in inline_policies)
        assert has_glue, (
            f"IAM role '{crawler_trigger_role_name}' missing Glue policy. "
            f"Available policies: {inline_policies}"
        )


class TestGlueCrawlerWiring:
    """Layer 3: Verify Glue crawler IAM role has required policies."""

    def test_glue_crawler_role_has_service_policy(
        self, iam_client, glue_crawler_role_name
    ):
        """Verify Glue crawler IAM role has AWS managed Glue service policy."""
        response = iam_client.list_attached_role_policies(
            RoleName=glue_crawler_role_name
        )
        policy_arns = [p["PolicyArn"] for p in response["AttachedPolicies"]]
        glue_service = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
        assert glue_service in policy_arns, (
            f"IAM role '{glue_crawler_role_name}' missing AWSGlueServiceRole policy. "
            f"Attached policies: {policy_arns}"
        )

    def test_glue_crawler_role_has_s3_access(self, iam_client, glue_crawler_role_name):
        """Verify Glue crawler IAM role has S3 access inline policy."""
        response = iam_client.list_role_policies(RoleName=glue_crawler_role_name)
        inline_policies = response.get("PolicyNames", [])
        has_s3 = any("S3" in p or "s3" in p for p in inline_policies)
        assert has_s3, (
            f"IAM role '{glue_crawler_role_name}' missing S3 policy. "
            f"Available policies: {inline_policies}"
        )
