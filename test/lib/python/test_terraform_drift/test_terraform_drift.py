"""Comprehensive tests for terraform_drift module."""
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from terraform_drift import (
    _check_lambda,
    _check_iam_role,
    _check_log_group,
    _check_dynamodb_table,
    _check_s3_bucket,
    _check_sqs_queue,
    _check_sns_topic,
    _check_ssm_parameter,
    _check_secretsmanager_secret,
    _check_eventbridge_rule,
    _check_api_gateway_rest_api,
    RESOURCE_CHECKERS,
    RESOURCE_TO_CLIENT,
    get_supported_resource_types,
    check_resource_exists,
    get_planned_creates,
    _get_name_field,
    get_terraform_state_resources,
    is_resource_in_state,
    find_orphaned_resources,
)


# === Individual Resource Checker Functions ===


class TestCheckLambda:
    """Tests for _check_lambda function."""

    def test_lambda_exists(self):
        """_check_lambda returns True when function exists."""
        mock_client = MagicMock()
        mock_client.get_function.return_value = {"Configuration": {}}
        assert _check_lambda(mock_client, "my-function") is True

    def test_lambda_not_found(self):
        """_check_lambda returns False when function not found."""
        mock_client = MagicMock()
        mock_client.exceptions.ResourceNotFoundException = type(
            "ResourceNotFoundException", (Exception,), {}
        )
        mock_client.get_function.side_effect = (
            mock_client.exceptions.ResourceNotFoundException()
        )
        assert _check_lambda(mock_client, "my-function") is False


class TestCheckIamRole:
    """Tests for _check_iam_role function."""

    def test_role_exists(self):
        """_check_iam_role returns True when role exists."""
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {}}
        assert _check_iam_role(mock_client, "my-role") is True

    def test_role_not_found(self):
        """_check_iam_role returns False when role not found."""
        mock_client = MagicMock()
        mock_client.exceptions.NoSuchEntityException = type(
            "NoSuchEntityException", (Exception,), {}
        )
        mock_client.get_role.side_effect = mock_client.exceptions.NoSuchEntityException()
        assert _check_iam_role(mock_client, "my-role") is False


class TestCheckLogGroup:
    """Tests for _check_log_group function."""

    def test_log_group_exists(self):
        """_check_log_group returns True when log group exists."""
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {
            "logGroups": [{"logGroupName": "/aws/lambda/my-func"}]
        }
        assert _check_log_group(mock_client, "/aws/lambda/my-func") is True

    def test_log_group_not_found(self):
        """_check_log_group returns False when log group not found."""
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        assert _check_log_group(mock_client, "/aws/lambda/my-func") is False

    def test_log_group_prefix_no_match(self):
        """_check_log_group returns False when prefix matches but name doesn't."""
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {
            "logGroups": [{"logGroupName": "/aws/lambda/my-func-other"}]
        }
        assert _check_log_group(mock_client, "/aws/lambda/my-func") is False


class TestCheckDynamodbTable:
    """Tests for _check_dynamodb_table function."""

    def test_table_exists(self):
        """_check_dynamodb_table returns True when table exists."""
        mock_client = MagicMock()
        mock_client.describe_table.return_value = {"Table": {}}
        assert _check_dynamodb_table(mock_client, "my-table") is True

    def test_table_not_found(self):
        """_check_dynamodb_table returns False when table not found."""
        mock_client = MagicMock()
        mock_client.exceptions.ResourceNotFoundException = type(
            "ResourceNotFoundException", (Exception,), {}
        )
        mock_client.describe_table.side_effect = (
            mock_client.exceptions.ResourceNotFoundException()
        )
        assert _check_dynamodb_table(mock_client, "my-table") is False


class TestCheckS3Bucket:
    """Tests for _check_s3_bucket function."""

    def test_bucket_exists(self):
        """_check_s3_bucket returns True when bucket exists."""
        mock_client = MagicMock()
        mock_client.head_bucket.return_value = {}
        assert _check_s3_bucket(mock_client, "my-bucket") is True

    def test_bucket_not_found(self):
        """_check_s3_bucket returns False when bucket not found (404)."""
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = ClientError(
            {"Error": {"Code": "404"}}, "HeadBucket"
        )
        assert _check_s3_bucket(mock_client, "my-bucket") is False

    def test_bucket_other_error(self):
        """_check_s3_bucket raises on non-404 errors."""
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = ClientError(
            {"Error": {"Code": "403"}}, "HeadBucket"
        )
        with pytest.raises(ClientError):
            _check_s3_bucket(mock_client, "my-bucket")
        assert True  # Explicit pass


class TestCheckSqsQueue:
    """Tests for _check_sqs_queue function."""

    def test_queue_exists(self):
        """_check_sqs_queue returns True when queue exists."""
        mock_client = MagicMock()
        mock_client.get_queue_url.return_value = {"QueueUrl": "https://..."}
        assert _check_sqs_queue(mock_client, "my-queue") is True

    def test_queue_not_found(self):
        """_check_sqs_queue returns False when queue not found."""
        mock_client = MagicMock()
        mock_client.exceptions.QueueDoesNotExist = type(
            "QueueDoesNotExist", (Exception,), {}
        )
        mock_client.get_queue_url.side_effect = (
            mock_client.exceptions.QueueDoesNotExist()
        )
        assert _check_sqs_queue(mock_client, "my-queue") is False


class TestCheckSnsTopic:
    """Tests for _check_sns_topic function."""

    def test_topic_exists(self):
        """_check_sns_topic returns True when topic exists."""
        mock_client = MagicMock()
        mock_client.get_topic_attributes.return_value = {"Attributes": {}}
        assert _check_sns_topic(mock_client, "arn:aws:sns:us-east-2:123:my-topic") is True

    def test_topic_not_found(self):
        """_check_sns_topic returns False when topic not found."""
        mock_client = MagicMock()
        mock_client.exceptions.NotFoundException = type(
            "NotFoundException", (Exception,), {}
        )
        mock_client.get_topic_attributes.side_effect = (
            mock_client.exceptions.NotFoundException()
        )
        assert (
            _check_sns_topic(mock_client, "arn:aws:sns:us-east-2:123:my-topic") is False
        )


class TestCheckSsmParameter:
    """Tests for _check_ssm_parameter function."""

    def test_parameter_exists(self):
        """_check_ssm_parameter returns True when parameter exists."""
        mock_client = MagicMock()
        mock_client.get_parameter.return_value = {"Parameter": {}}
        assert _check_ssm_parameter(mock_client, "/my/param") is True

    def test_parameter_not_found(self):
        """_check_ssm_parameter returns False when parameter not found."""
        mock_client = MagicMock()
        mock_client.exceptions.ParameterNotFound = type(
            "ParameterNotFound", (Exception,), {}
        )
        mock_client.get_parameter.side_effect = (
            mock_client.exceptions.ParameterNotFound()
        )
        assert _check_ssm_parameter(mock_client, "/my/param") is False


class TestCheckSecretsmanagerSecret:
    """Tests for _check_secretsmanager_secret function."""

    def test_secret_exists(self):
        """_check_secretsmanager_secret returns True when secret exists."""
        mock_client = MagicMock()
        mock_client.describe_secret.return_value = {"Name": "my-secret"}
        assert _check_secretsmanager_secret(mock_client, "my-secret") is True

    def test_secret_not_found(self):
        """_check_secretsmanager_secret returns False when secret not found."""
        mock_client = MagicMock()
        mock_client.exceptions.ResourceNotFoundException = type(
            "ResourceNotFoundException", (Exception,), {}
        )
        mock_client.describe_secret.side_effect = (
            mock_client.exceptions.ResourceNotFoundException()
        )
        assert _check_secretsmanager_secret(mock_client, "my-secret") is False


class TestCheckEventbridgeRule:
    """Tests for _check_eventbridge_rule function."""

    def test_rule_exists(self):
        """_check_eventbridge_rule returns True when rule exists."""
        mock_client = MagicMock()
        mock_client.describe_rule.return_value = {"Name": "my-rule"}
        assert _check_eventbridge_rule(mock_client, "my-rule") is True

    def test_rule_not_found(self):
        """_check_eventbridge_rule returns False when rule not found."""
        mock_client = MagicMock()
        mock_client.exceptions.ResourceNotFoundException = type(
            "ResourceNotFoundException", (Exception,), {}
        )
        mock_client.describe_rule.side_effect = (
            mock_client.exceptions.ResourceNotFoundException()
        )
        assert _check_eventbridge_rule(mock_client, "my-rule") is False


class TestCheckApiGatewayRestApi:
    """Tests for _check_api_gateway_rest_api function."""

    def test_api_exists(self):
        """_check_api_gateway_rest_api returns True when API exists."""
        mock_client = MagicMock()
        mock_client.get_rest_api.return_value = {"id": "abc123"}
        assert _check_api_gateway_rest_api(mock_client, "abc123") is True

    def test_api_not_found(self):
        """_check_api_gateway_rest_api returns False when API not found."""
        mock_client = MagicMock()
        mock_client.exceptions.NotFoundException = type(
            "NotFoundException", (Exception,), {}
        )
        mock_client.get_rest_api.side_effect = mock_client.exceptions.NotFoundException()
        assert _check_api_gateway_rest_api(mock_client, "abc123") is False


# === Registry Tests ===


class TestResourceCheckers:
    """Tests for RESOURCE_CHECKERS registry."""

    def test_all_checkers_registered(self):
        """All resource types have checkers registered."""
        expected_types = {
            "aws_lambda_function",
            "aws_iam_role",
            "aws_cloudwatch_log_group",
            "aws_dynamodb_table",
            "aws_s3_bucket",
            "aws_sqs_queue",
            "aws_sns_topic",
            "aws_ssm_parameter",
            "aws_secretsmanager_secret",
            "aws_cloudwatch_event_rule",
            "aws_api_gateway_rest_api",
        }
        assert set(RESOURCE_CHECKERS.keys()) == expected_types

    def test_all_checkers_are_callable(self):
        """All checkers are callable functions."""
        for checker in RESOURCE_CHECKERS.values():
            assert callable(checker)


class TestResourceToClient:
    """Tests for RESOURCE_TO_CLIENT registry."""

    def test_all_types_have_clients(self):
        """All resource types have client mappings."""
        for resource_type in RESOURCE_CHECKERS:
            assert resource_type in RESOURCE_TO_CLIENT


# === Public API Functions ===


class TestGetSupportedResourceTypes:
    """Tests for get_supported_resource_types function."""

    def test_returns_list_type(self):
        """get_supported_resource_types returns a list type."""
        result = get_supported_resource_types()
        assert isinstance(result, list)

    def test_returns_list_with_correct_length(self):
        """get_supported_resource_types returns list with same length as RESOURCE_CHECKERS."""
        result = get_supported_resource_types()
        assert len(result) == len(RESOURCE_CHECKERS)

    def test_contains_all_types(self):
        """get_supported_resource_types contains all registered types."""
        result = get_supported_resource_types()
        assert set(result) == set(RESOURCE_CHECKERS.keys())


class TestCheckResourceExists:
    """Tests for check_resource_exists function."""

    def test_unsupported_type_raises(self):
        """check_resource_exists raises ValueError for unsupported types."""
        with pytest.raises(ValueError, match="Unsupported resource type"):
            check_resource_exists("aws_unsupported_resource", "name", "us-east-2")
        assert True  # Explicit pass

    @patch("terraform_drift.boto3")
    def test_returns_true_when_resource_exists(self, mock_boto3):
        """check_resource_exists returns True when resource exists."""
        mock_client = MagicMock()
        mock_client.get_function.return_value = {"Configuration": {}}
        mock_boto3.client.return_value = mock_client

        result = check_resource_exists(
            "aws_lambda_function", "my-function", "us-east-2"
        )

        assert result is True

    @patch("terraform_drift.boto3")
    def test_creates_client_with_correct_service_and_region(self, mock_boto3):
        """check_resource_exists creates boto3 client with correct service and region."""
        mock_client = MagicMock()
        mock_client.get_function.return_value = {"Configuration": {}}
        mock_boto3.client.return_value = mock_client

        check_resource_exists("aws_lambda_function", "my-function", "us-east-2")

        assert mock_boto3.client.call_args == (
            ("lambda",),
            {"region_name": "us-east-2"},
        )

    @patch("terraform_drift.boto3")
    def test_calls_checker_with_correct_resource_name(self, mock_boto3):
        """check_resource_exists calls checker with correct resource name."""
        mock_client = MagicMock()
        mock_client.get_function.return_value = {"Configuration": {}}
        mock_boto3.client.return_value = mock_client

        check_resource_exists("aws_lambda_function", "my-function", "us-east-2")

        assert mock_client.get_function.call_args == (
            (),
            {"FunctionName": "my-function"},
        )


class TestGetNameField:
    """Tests for _get_name_field function."""

    def test_lambda_function_name(self):
        """_get_name_field returns function_name for Lambda."""
        assert _get_name_field("aws_lambda_function") == "function_name"

    def test_s3_bucket(self):
        """_get_name_field returns bucket for S3."""
        assert _get_name_field("aws_s3_bucket") == "bucket"

    def test_sns_topic_arn(self):
        """_get_name_field returns arn for SNS topic."""
        assert _get_name_field("aws_sns_topic") == "arn"

    def test_api_gateway_id(self):
        """_get_name_field returns id for API Gateway."""
        assert _get_name_field("aws_api_gateway_rest_api") == "id"

    def test_unknown_type_default(self):
        """_get_name_field returns name for unknown types."""
        assert _get_name_field("aws_unknown_type") == "name"


def _make_plan_output(action="create", resource_type="aws_lambda_function",
                      addr="aws_lambda_function.my_func", function_name="MyFunction"):
    """Create a terraform plan JSON output for testing."""
    return json.dumps({
        "type": "planned_change",
        "change": {
            "action": action,
            "resource": {"resource_type": resource_type, "addr": addr},
            "change": {"after": {"function_name": function_name}},
        },
    })


class TestGetPlannedCreates:
    """Tests for get_planned_creates function."""

    @patch("terraform_drift.subprocess.run")
    def test_parses_create_actions_returns_single_result(self, mock_run):
        """get_planned_creates returns one result for single create action."""
        mock_run.return_value = MagicMock(stdout=_make_plan_output(), returncode=0)
        result = get_planned_creates(Path("/tmp/terraform"))
        assert len(result) == 1

    @patch("terraform_drift.subprocess.run")
    def test_parses_create_actions_extracts_resource_type(self, mock_run):
        """get_planned_creates extracts correct resource type from plan output."""
        mock_run.return_value = MagicMock(stdout=_make_plan_output(), returncode=0)
        result = get_planned_creates(Path("/tmp/terraform"))
        assert result[0]["type"] == "aws_lambda_function"

    @patch("terraform_drift.subprocess.run")
    def test_parses_create_actions_extracts_resource_name(self, mock_run):
        """get_planned_creates extracts correct resource name from plan output."""
        mock_run.return_value = MagicMock(stdout=_make_plan_output(), returncode=0)
        result = get_planned_creates(Path("/tmp/terraform"))
        assert result[0]["name"] == "MyFunction"

    @patch("terraform_drift.subprocess.run")
    def test_ignores_non_create_actions(self, mock_run):
        """get_planned_creates ignores non-create actions."""
        mock_run.return_value = MagicMock(
            stdout=_make_plan_output(action="update"), returncode=0
        )
        result = get_planned_creates(Path("/tmp/terraform"))
        assert result == []

    @patch("terraform_drift.subprocess.run")
    def test_ignores_unsupported_types(self, mock_run):
        """get_planned_creates ignores unsupported resource types."""
        mock_run.return_value = MagicMock(
            stdout=_make_plan_output(
                resource_type="aws_ec2_instance", addr="aws_ec2_instance.my_instance"
            ),
            returncode=0,
        )
        result = get_planned_creates(Path("/tmp/terraform"))
        assert result == []

    @patch("terraform_drift.subprocess.run")
    def test_handles_invalid_json(self, mock_run):
        """get_planned_creates handles invalid JSON lines."""
        plan_output = "not json\n" + _make_plan_output()
        mock_run.return_value = MagicMock(stdout=plan_output, returncode=0)
        result = get_planned_creates(Path("/tmp/terraform"))
        assert len(result) == 1

    @patch("terraform_drift.subprocess.run")
    def test_ignores_non_planned_change_type(self, mock_run):
        """get_planned_creates ignores entries with type other than planned_change."""
        non_change = json.dumps({"type": "diagnostic", "message": "some warning"})
        plan_output = non_change + "\n" + _make_plan_output()
        mock_run.return_value = MagicMock(stdout=plan_output, returncode=0)
        result = get_planned_creates(Path("/tmp/terraform"))
        assert len(result) == 1

    @patch("terraform_drift.subprocess.run")
    def test_ignores_refresh_type(self, mock_run):
        """get_planned_creates ignores entries with refresh type."""
        refresh_entry = json.dumps({"type": "refresh_complete", "resource": {}})
        mock_run.return_value = MagicMock(stdout=refresh_entry, returncode=0)
        result = get_planned_creates(Path("/tmp/terraform"))
        assert result == []


class TestGetTerraformStateResources:
    """Tests for get_terraform_state_resources function."""

    @patch("terraform_drift.subprocess.run")
    def test_returns_resource_list(self, mock_run):
        """get_terraform_state_resources returns list of addresses."""
        mock_run.return_value = MagicMock(
            stdout="aws_lambda_function.my_func\naws_iam_role.my_role\n",
            returncode=0,
        )

        result = get_terraform_state_resources(Path("/tmp/terraform"))

        assert result == ["aws_lambda_function.my_func", "aws_iam_role.my_role"]

    @patch("terraform_drift.subprocess.run")
    def test_returns_empty_on_error(self, mock_run):
        """get_terraform_state_resources returns empty list on error."""
        mock_run.return_value = MagicMock(stdout="", returncode=1)

        result = get_terraform_state_resources(Path("/tmp/terraform"))
        assert result == []

    @patch("terraform_drift.subprocess.run")
    def test_filters_empty_lines(self, mock_run):
        """get_terraform_state_resources filters empty lines."""
        mock_run.return_value = MagicMock(
            stdout="aws_lambda_function.my_func\n\n  \naws_iam_role.my_role\n",
            returncode=0,
        )

        result = get_terraform_state_resources(Path("/tmp/terraform"))
        assert result == ["aws_lambda_function.my_func", "aws_iam_role.my_role"]


class TestIsResourceInState:
    """Tests for is_resource_in_state function."""

    @patch("terraform_drift.get_terraform_state_resources")
    def test_returns_true_when_in_state(self, mock_get_state):
        """is_resource_in_state returns True when resource is in state."""
        mock_get_state.return_value = [
            "aws_lambda_function.my_func",
            "aws_iam_role.my_role",
        ]

        result = is_resource_in_state(Path("/tmp"), "aws_lambda_function.my_func")
        assert result is True

    @patch("terraform_drift.get_terraform_state_resources")
    def test_returns_false_when_not_in_state(self, mock_get_state):
        """is_resource_in_state returns False when resource is not in state."""
        mock_get_state.return_value = ["aws_iam_role.my_role"]

        result = is_resource_in_state(Path("/tmp"), "aws_lambda_function.my_func")
        assert result is False


class TestFindOrphanedResources:
    """Tests for find_orphaned_resources function."""

    @patch("terraform_drift.check_resource_exists")
    @patch("terraform_drift.get_planned_creates")
    def test_finds_orphaned_resources_returns_single_result(
        self, mock_get_planned, mock_check_exists
    ):
        """find_orphaned_resources returns one result when one resource exists in AWS."""
        mock_get_planned.return_value = [
            {
                "type": "aws_lambda_function",
                "name": "MyFunction",
                "address": "aws_lambda_function.my_func",
                "values": {},
            }
        ]
        mock_check_exists.return_value = True

        result = find_orphaned_resources(Path("/tmp"), "us-east-2")

        assert len(result) == 1

    @patch("terraform_drift.check_resource_exists")
    @patch("terraform_drift.get_planned_creates")
    def test_finds_orphaned_resources_includes_resource_name(
        self, mock_get_planned, mock_check_exists
    ):
        """find_orphaned_resources includes correct resource name in result."""
        mock_get_planned.return_value = [
            {
                "type": "aws_lambda_function",
                "name": "MyFunction",
                "address": "aws_lambda_function.my_func",
                "values": {},
            }
        ]
        mock_check_exists.return_value = True

        result = find_orphaned_resources(Path("/tmp"), "us-east-2")

        assert result[0]["name"] == "MyFunction"

    @patch("terraform_drift.check_resource_exists")
    @patch("terraform_drift.get_planned_creates")
    def test_finds_orphaned_resources_generates_import_command(
        self, mock_get_planned, mock_check_exists
    ):
        """find_orphaned_resources generates terraform import command in result."""
        mock_get_planned.return_value = [
            {
                "type": "aws_lambda_function",
                "name": "MyFunction",
                "address": "aws_lambda_function.my_func",
                "values": {},
            }
        ]
        mock_check_exists.return_value = True

        result = find_orphaned_resources(Path("/tmp"), "us-east-2")

        assert "terraform import" in result[0]["import_command"]

    @patch("terraform_drift.check_resource_exists")
    @patch("terraform_drift.get_planned_creates")
    def test_excludes_non_existing_resources(self, mock_get_planned, mock_check_exists):
        """find_orphaned_resources excludes resources that don't exist."""
        mock_get_planned.return_value = [
            {
                "type": "aws_lambda_function",
                "name": "MyFunction",
                "address": "aws_lambda_function.my_func",
                "values": {},
            }
        ]
        mock_check_exists.return_value = False

        result = find_orphaned_resources(Path("/tmp"), "us-east-2")
        assert result == []
