import json
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
    check_resource_exists,
    get_planned_creates,
    _get_name_field,
)


class TestCheckLambda:
    def test_lambda_exists(self) -> None:
        mock_client = MagicMock()
        mock_client.get_function.return_value = {"Configuration": {}}
        assert _check_lambda(mock_client, "my-function") is True

    def test_lambda_not_found(self) -> None:
        mock_client = MagicMock()
        mock_client.exceptions.ResourceNotFoundException = type(
            "ResourceNotFoundException", (Exception,), {}
        )
        mock_client.get_function.side_effect = (
            mock_client.exceptions.ResourceNotFoundException()
        )
        assert _check_lambda(mock_client, "my-function") is False


class TestCheckIamRole:
    def test_role_exists(self) -> None:
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {}}
        assert _check_iam_role(mock_client, "my-role") is True

    def test_role_not_found(self) -> None:
        mock_client = MagicMock()
        mock_client.exceptions.NoSuchEntityException = type(
            "NoSuchEntityException", (Exception,), {}
        )
        mock_client.get_role.side_effect = mock_client.exceptions.NoSuchEntityException()
        assert _check_iam_role(mock_client, "my-role") is False


class TestCheckLogGroup:
    def test_log_group_exists(self) -> None:
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {
            "logGroups": [{"logGroupName": "/aws/lambda/my-func"}]
        }
        assert _check_log_group(mock_client, "/aws/lambda/my-func") is True

    def test_log_group_not_found(self) -> None:
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        assert _check_log_group(mock_client, "/aws/lambda/my-func") is False

    def test_log_group_prefix_no_match(self) -> None:
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {
            "logGroups": [{"logGroupName": "/aws/lambda/my-func-other"}]
        }
        assert _check_log_group(mock_client, "/aws/lambda/my-func") is False


class TestCheckDynamodbTable:
    def test_table_exists(self) -> None:
        mock_client = MagicMock()
        mock_client.describe_table.return_value = {"Table": {}}
        assert _check_dynamodb_table(mock_client, "my-table") is True

    def test_table_not_found(self) -> None:
        mock_client = MagicMock()
        mock_client.exceptions.ResourceNotFoundException = type(
            "ResourceNotFoundException", (Exception,), {}
        )
        mock_client.describe_table.side_effect = (
            mock_client.exceptions.ResourceNotFoundException()
        )
        assert _check_dynamodb_table(mock_client, "my-table") is False


class TestCheckS3Bucket:
    def test_bucket_exists(self) -> None:
        mock_client = MagicMock()
        mock_client.head_bucket.return_value = {}
        assert _check_s3_bucket(mock_client, "my-bucket") is True

    def test_bucket_not_found(self) -> None:
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = ClientError(
            {"Error": {"Code": "404"}}, "HeadBucket"
        )
        assert _check_s3_bucket(mock_client, "my-bucket") is False

    def test_bucket_other_error(self) -> None:
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = ClientError(
            {"Error": {"Code": "403"}}, "HeadBucket"
        )
        with pytest.raises(ClientError):
            _check_s3_bucket(mock_client, "my-bucket")


class TestCheckSqsQueue:
    def test_queue_exists(self) -> None:
        mock_client = MagicMock()
        mock_client.get_queue_url.return_value = {"QueueUrl": "https://..."}
        assert _check_sqs_queue(mock_client, "my-queue") is True

    def test_queue_not_found(self) -> None:
        mock_client = MagicMock()
        mock_client.exceptions.QueueDoesNotExist = type(
            "QueueDoesNotExist", (Exception,), {}
        )
        mock_client.get_queue_url.side_effect = (
            mock_client.exceptions.QueueDoesNotExist()
        )
        assert _check_sqs_queue(mock_client, "my-queue") is False


class TestCheckSnsTopic:
    def test_topic_exists(self) -> None:
        mock_client = MagicMock()
        mock_client.get_topic_attributes.return_value = {"Attributes": {}}
        assert _check_sns_topic(mock_client, "arn:aws:sns:us-east-2:123:my-topic") is True

    def test_topic_not_found(self) -> None:
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
    def test_parameter_exists(self) -> None:
        mock_client = MagicMock()
        mock_client.get_parameter.return_value = {"Parameter": {}}
        assert _check_ssm_parameter(mock_client, "/my/param") is True

    def test_parameter_not_found(self) -> None:
        mock_client = MagicMock()
        mock_client.exceptions.ParameterNotFound = type(
            "ParameterNotFound", (Exception,), {}
        )
        mock_client.get_parameter.side_effect = (
            mock_client.exceptions.ParameterNotFound()
        )
        assert _check_ssm_parameter(mock_client, "/my/param") is False


class TestCheckSecretsmanagerSecret:
    def test_secret_exists(self) -> None:
        mock_client = MagicMock()
        mock_client.describe_secret.return_value = {"Name": "my-secret"}
        assert _check_secretsmanager_secret(mock_client, "my-secret") is True

    def test_secret_not_found(self) -> None:
        mock_client = MagicMock()
        mock_client.exceptions.ResourceNotFoundException = type(
            "ResourceNotFoundException", (Exception,), {}
        )
        mock_client.describe_secret.side_effect = (
            mock_client.exceptions.ResourceNotFoundException()
        )
        assert _check_secretsmanager_secret(mock_client, "my-secret") is False


class TestCheckEventbridgeRule:
    def test_rule_exists(self) -> None:
        mock_client = MagicMock()
        mock_client.describe_rule.return_value = {"Name": "my-rule"}
        assert _check_eventbridge_rule(mock_client, "my-rule") is True

    def test_rule_not_found(self) -> None:
        mock_client = MagicMock()
        mock_client.exceptions.ResourceNotFoundException = type(
            "ResourceNotFoundException", (Exception,), {}
        )
        mock_client.describe_rule.side_effect = (
            mock_client.exceptions.ResourceNotFoundException()
        )
        assert _check_eventbridge_rule(mock_client, "my-rule") is False


class TestCheckApiGatewayRestApi:
    def test_api_exists(self) -> None:
        mock_client = MagicMock()
        mock_client.get_rest_api.return_value = {"id": "abc123"}
        assert _check_api_gateway_rest_api(mock_client, "abc123") is True

    def test_api_not_found(self) -> None:
        mock_client = MagicMock()
        mock_client.exceptions.NotFoundException = type(
            "NotFoundException", (Exception,), {}
        )
        mock_client.get_rest_api.side_effect = mock_client.exceptions.NotFoundException()
        assert _check_api_gateway_rest_api(mock_client, "abc123") is False


class TestResourceCheckers:
    def test_all_checkers_registered(self) -> None:
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

    def test_all_checkers_are_callable(self) -> None:
        for checker in RESOURCE_CHECKERS.values():
            assert callable(checker)


def test_resource_to_client() -> None:
    for resource_type in RESOURCE_CHECKERS:
        assert resource_type in RESOURCE_TO_CLIENT


class TestCheckResourceExists:
    def test_unsupported_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported resource type"):
            check_resource_exists("aws_unsupported_resource", "name", "us-east-2")

    @patch("terraform_drift.boto3")
    def test_returns_true_when_resource_exists(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.get_function.return_value = {"Configuration": {}}
        mock_boto3.client.return_value = mock_client

        result = check_resource_exists(
            "aws_lambda_function", "my-function", "us-east-2"
        )

        assert result is True

    @patch("terraform_drift.boto3")
    def test_creates_client_with_correct_service_and_region(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.get_function.return_value = {"Configuration": {}}
        mock_boto3.client.return_value = mock_client

        check_resource_exists("aws_lambda_function", "my-function", "us-east-2")

        assert mock_boto3.client.call_args == (
            ("lambda",),
            {"region_name": "us-east-2"},
        )

    @patch("terraform_drift.boto3")
    def test_calls_checker_with_correct_resource_name(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.get_function.return_value = {"Configuration": {}}
        mock_boto3.client.return_value = mock_client

        check_resource_exists("aws_lambda_function", "my-function", "us-east-2")

        assert mock_client.get_function.call_args == (
            (),
            {"FunctionName": "my-function"},
        )


class TestGetNameField:
    def test_lambda_function_name(self) -> None:
        assert _get_name_field("aws_lambda_function") == "function_name"

    def test_s3_bucket(self) -> None:
        assert _get_name_field("aws_s3_bucket") == "bucket"

    def test_sns_topic_arn(self) -> None:
        assert _get_name_field("aws_sns_topic") == "arn"

    def test_api_gateway_id(self) -> None:
        assert _get_name_field("aws_api_gateway_rest_api") == "id"

    def test_unknown_type_default(self) -> None:
        assert _get_name_field("aws_unknown_type") == "name"


def _make_plan_output(
    action: str = "create",
    resource_type: str = "aws_lambda_function",
    addr: str = "aws_lambda_function.my_func",
    function_name: str = "MyFunction"
) -> str:
    return json.dumps({
        "type": "planned_change",
        "change": {
            "action": action,
            "resource": {"resource_type": resource_type, "addr": addr},
            "change": {"after": {"function_name": function_name}},
        },
    })


class TestGetPlannedCreates:
    @patch("terraform_drift.subprocess.run")
    def test_parses_create_actions_returns_single_result(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(stdout=_make_plan_output(), returncode=0)
        result = get_planned_creates(Path("/tmp/terraform"))
        assert len(result) == 1

    @patch("terraform_drift.subprocess.run")
    def test_parses_create_actions_extracts_resource_type(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(stdout=_make_plan_output(), returncode=0)
        result = get_planned_creates(Path("/tmp/terraform"))
        assert result[0]["type"] == "aws_lambda_function"

    @patch("terraform_drift.subprocess.run")
    def test_parses_create_actions_extracts_resource_name(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(stdout=_make_plan_output(), returncode=0)
        result = get_planned_creates(Path("/tmp/terraform"))
        assert result[0]["name"] == "MyFunction"

    @patch("terraform_drift.subprocess.run")
    def test_ignores_non_create_actions(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(
            stdout=_make_plan_output(action="update"), returncode=0
        )
        result = get_planned_creates(Path("/tmp/terraform"))
        assert not result

    @patch("terraform_drift.subprocess.run")
    def test_ignores_unsupported_types(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(
            stdout=_make_plan_output(
                resource_type="aws_ec2_instance", addr="aws_ec2_instance.my_instance"
            ),
            returncode=0,
        )
        result = get_planned_creates(Path("/tmp/terraform"))
        assert not result

    @patch("terraform_drift.subprocess.run")
    def test_handles_invalid_json(self, mock_run: MagicMock) -> None:
        plan_output = "not json\n" + _make_plan_output()
        mock_run.return_value = MagicMock(stdout=plan_output, returncode=0)
        result = get_planned_creates(Path("/tmp/terraform"))
        assert len(result) == 1

    @patch("terraform_drift.subprocess.run")
    def test_ignores_non_planned_change_type(self, mock_run: MagicMock) -> None:
        non_change = json.dumps({"type": "diagnostic", "message": "some warning"})
        plan_output = non_change + "\n" + _make_plan_output()
        mock_run.return_value = MagicMock(stdout=plan_output, returncode=0)
        result = get_planned_creates(Path("/tmp/terraform"))
        assert len(result) == 1

    @patch("terraform_drift.subprocess.run")
    def test_ignores_refresh_type(self, mock_run: MagicMock) -> None:
        refresh_entry = json.dumps({"type": "refresh_complete", "resource": {}})
        mock_run.return_value = MagicMock(stdout=refresh_entry, returncode=0)
        result = get_planned_creates(Path("/tmp/terraform"))
        assert not result

    @patch("terraform_drift.subprocess.run")
    def test_ignores_create_with_empty_resource_name(self, mock_run: MagicMock) -> None:
        plan_with_empty_name = json.dumps({
            "type": "planned_change",
            "change": {
                "action": "create",
                "resource": {
                    "resource_type": "aws_lambda_function",
                    "addr": "aws_lambda_function.my_func"
                },
                "change": {"after": {"function_name": ""}},
            },
        })
        mock_run.return_value = MagicMock(stdout=plan_with_empty_name, returncode=0)
        result = get_planned_creates(Path("/tmp/terraform"))
        assert not result

    @patch("terraform_drift.subprocess.run")
    def test_ignores_create_with_missing_name_field(self, mock_run: MagicMock) -> None:
        plan_with_missing_name = json.dumps({
            "type": "planned_change",
            "change": {
                "action": "create",
                "resource": {
                    "resource_type": "aws_lambda_function",
                    "addr": "aws_lambda_function.my_func"
                },
                "change": {"after": {"runtime": "python3.11"}},
            },
        })
        mock_run.return_value = MagicMock(stdout=plan_with_missing_name, returncode=0)
        result = get_planned_creates(Path("/tmp/terraform"))
        assert not result
