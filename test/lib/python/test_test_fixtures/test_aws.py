from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from test_fixtures.aws import (
    api_gateway_info,
    aws_region,
    backup_client,
    caller_identity,
    _current_role_arn,
    current_role_name,
    dynamodb_client,
    find_lifecycle_rule,
    get_log_group_info,
    iam_client,
    iam_role_exists,
    logs_client,
    s3_client,
    scheduler_client,
    shared_config,
    ssm_client,
    stale_delete_markers,
    state_bucket_name,
    sts_client,
)


class TestIamRoleExists:
    def test_returns_true_when_role_exists(self):
        mock_client = MagicMock()
        mock_client.get_role.return_value = {
            "Role": {"RoleName": "test-role", "Arn": "arn:aws:iam::123456:role/test-role"}
        }
        result = iam_role_exists(mock_client, "test-role")
        assert result is True

    def test_returns_false_when_role_not_found(self):
        mock_client = MagicMock()
        mock_client.exceptions.NoSuchEntityException = type(
            "NoSuchEntityException", (Exception,), {}
        )
        mock_client.get_role.side_effect = mock_client.exceptions.NoSuchEntityException()
        result = iam_role_exists(mock_client, "nonexistent-role")
        assert result is False

    def test_calls_get_role_with_role_name(self):
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "my-role"}}
        iam_role_exists(mock_client, "my-role")
        assert mock_client.get_role.call_args[1]["RoleName"] == "my-role"

    def test_passes_role_name_argument(self):
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {}}
        iam_role_exists(mock_client, "custom-role-name")
        call_args = mock_client.get_role.call_args
        assert call_args[1]["RoleName"] == "custom-role-name"


class TestGetLogGroupInfo:
    def test_returns_dict_type(self):
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        result = get_log_group_info(mock_client, "/aws/lambda/test")
        assert isinstance(result, dict)

    def test_returns_name_in_result(self):
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        result = get_log_group_info(mock_client, "/aws/lambda/my-function")
        assert result["name"] == "/aws/lambda/my-function"

    def test_returns_exists_true_when_log_group_found(self):
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {
            "logGroups": [
                {"logGroupName": "/aws/lambda/my-function", "retentionInDays": 14}
            ]
        }
        result = get_log_group_info(mock_client, "/aws/lambda/my-function")
        assert result["exists"] is True

    def test_returns_exists_false_when_log_group_not_found(self):
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        result = get_log_group_info(mock_client, "/aws/lambda/nonexistent")
        assert result["exists"] is False

    def test_returns_retention_days_when_set(self):
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {
            "logGroups": [
                {"logGroupName": "/aws/lambda/test", "retentionInDays": 30}
            ]
        }
        result = get_log_group_info(mock_client, "/aws/lambda/test")
        assert result["retention"] == 30

    def test_returns_retention_none_when_not_found(self):
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        result = get_log_group_info(mock_client, "/aws/lambda/missing")
        assert result["retention"] is None

    def test_returns_retention_none_when_not_set(self):
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {
            "logGroups": [{"logGroupName": "/aws/lambda/test"}]
        }
        result = get_log_group_info(mock_client, "/aws/lambda/test")
        assert result["retention"] is None

    def test_calls_describe_log_groups_with_prefix(self):
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        get_log_group_info(mock_client, "/aws/lambda/test-fn")
        assert mock_client.describe_log_groups.call_count == 1

    def test_calls_describe_log_groups_with_correct_prefix(self):
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        get_log_group_info(mock_client, "/aws/lambda/test-fn")
        call_args = mock_client.describe_log_groups.call_args
        assert call_args[1]["logGroupNamePrefix"] == "/aws/lambda/test-fn"

    def test_calls_describe_log_groups_with_limit_one(self):
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        get_log_group_info(mock_client, "/aws/lambda/test")
        call_args = mock_client.describe_log_groups.call_args
        assert call_args[1]["limit"] == 1

    def test_filters_by_exact_log_group_name(self):
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {
            "logGroups": [
                {"logGroupName": "/aws/lambda/test-function-extra", "retentionInDays": 7}
            ]
        }
        result = get_log_group_info(mock_client, "/aws/lambda/test-function")
        assert result["exists"] is False

    def test_handles_multiple_log_groups_in_response(self):
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {
            "logGroups": [
                {"logGroupName": "/aws/lambda/target", "retentionInDays": 14}
            ]
        }
        result = get_log_group_info(mock_client, "/aws/lambda/target")
        assert result["exists"] is True


@patch("test_fixtures.aws.get_shared_config")
def test_shared_config_fixture_execution(mock_get_config):
    mock_get_config.return_value = {"aws_region": "us-east-1", "key": "value"}
    result = shared_config.__wrapped__()
    assert result == {"aws_region": "us-east-1", "key": "value"}
    mock_get_config.assert_called_once()


def test_aws_region_fixture_execution():
    mock_request = MagicMock()
    mock_request.getfixturevalue.return_value = {"aws_region": "eu-west-1"}
    result = aws_region.__wrapped__(mock_request)
    assert result == "eu-west-1"
    mock_request.getfixturevalue.assert_called_with("shared_config")


def test_state_bucket_name_fixture_execution():
    mock_request = MagicMock()
    mock_request.getfixturevalue.return_value = {"name_for_terraform_state_bucket": "my-bucket"}
    result = state_bucket_name.__wrapped__(mock_request)
    assert result == "my-bucket"


class TestClientFixturesExecution:
    @patch("test_fixtures.aws.boto3")
    def test_sts_client_fixture_creates_client(self, mock_boto3):
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-2"
        mock_boto3.client.return_value = MagicMock()
        sts_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "sts"

    @patch("test_fixtures.aws.boto3")
    def test_iam_client_fixture_creates_client(self, mock_boto3):
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-west-2"
        iam_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "iam"

    @patch("test_fixtures.aws.boto3")
    def test_s3_client_fixture_creates_client(self, mock_boto3):
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        s3_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "s3"

    @patch("test_fixtures.aws.boto3")
    def test_ssm_client_fixture_creates_client(self, mock_boto3):
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        ssm_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "ssm"

    @patch("test_fixtures.aws.boto3")
    def test_logs_client_fixture_creates_client(self, mock_boto3):
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        logs_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "logs"

    @patch("test_fixtures.aws.boto3")
    def test_dynamodb_client_fixture_creates_client(self, mock_boto3):
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        dynamodb_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "dynamodb"

    @patch("test_fixtures.aws.boto3")
    def test_scheduler_client_fixture_creates_client(self, mock_boto3):
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        scheduler_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "scheduler"

    @patch("test_fixtures.aws.boto3")
    def test_backup_client_fixture_creates_client(self, mock_boto3):
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        backup_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "backup"


def test_caller_identity_fixture_execution():
    mock_request = MagicMock()
    mock_sts_client = MagicMock()
    mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}
    mock_request.getfixturevalue.return_value = mock_sts_client
    result = caller_identity.__wrapped__(mock_request)
    assert result == {"Account": "123456789012"}
    mock_sts_client.get_caller_identity.assert_called_once()


class TestCurrentRoleArnFixtureExecution:
    def test_current_role_arn_converts_assumed_role(self):
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {
            "Account": "123456789012",
            "Arn": "arn:aws:sts::123456789012:assumed-role/MyRole/session"
        }
        result = _current_role_arn.__wrapped__(mock_request)
        assert result == "arn:aws:iam::123456789012:role/MyRole"

    def test_current_role_arn_returns_unchanged_for_non_assumed(self):
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {
            "Account": "123456789012",
            "Arn": "arn:aws:iam::123456789012:user/MyUser"
        }
        result = _current_role_arn.__wrapped__(mock_request)
        assert result == "arn:aws:iam::123456789012:user/MyUser"


class TestCurrentRoleNameFixtureExecution:
    def test_current_role_name_extracts_role_name(self):
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "arn:aws:iam::123456789012:role/MyRole"
        result = current_role_name.__wrapped__(mock_request)
        assert result == "MyRole"

    def test_current_role_name_returns_empty_for_empty_arn(self):
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = ""
        result = current_role_name.__wrapped__(mock_request)
        assert result == ""


class TestApiGatewayInfoFixtureExecution:
    def test_api_gateway_info_returns_not_found_when_no_id(self):
        mock_request = MagicMock()
        mock_request.getfixturevalue.side_effect = lambda name: {
            "apigateway_client": MagicMock(),
            "api_common_routing_outputs": {"api_gateway_id": None}
        }[name]
        result = api_gateway_info.__wrapped__(mock_request)
        assert result == {"id": None, "exists": False, "accessible": False}

    def _create_success_mock_request(self):
        mock_request = MagicMock()
        mock_client = MagicMock()
        mock_client.get_rest_api.return_value = {
            "endpointConfiguration": {"types": ["REGIONAL"]}
        }
        mock_client.get_paginator.return_value.paginate.return_value = [
            {"items": [{"path": "/"}, {"path": "/items"}]}
        ]
        mock_request.getfixturevalue.side_effect = lambda name: {
            "apigateway_client": mock_client,
            "api_common_routing_outputs": {"api_gateway_id": "abc123"}
        }[name]
        return api_gateway_info.__wrapped__(mock_request)

    def test_api_gateway_info_returns_correct_id_when_api_exists(self):
        result = self._create_success_mock_request()
        assert result["id"] == "abc123"

    def test_api_gateway_info_returns_exists_true_when_api_exists(self):
        result = self._create_success_mock_request()
        assert result["exists"] is True

    def test_api_gateway_info_returns_accessible_true_when_api_exists(self):
        result = self._create_success_mock_request()
        assert result["accessible"] is True

    def test_api_gateway_info_returns_endpoint_types_when_api_exists(self):
        result = self._create_success_mock_request()
        assert result["endpoint_types"] == ["REGIONAL"]

    def test_api_gateway_info_returns_paths_when_api_exists(self):
        result = self._create_success_mock_request()
        assert result["paths"] == ["/", "/items"]

    def test_api_gateway_info_handles_access_denied(self):
        mock_request = MagicMock()
        mock_client = MagicMock()
        mock_client.get_rest_api.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException"}}, "GetRestApi"
        )
        mock_request.getfixturevalue.side_effect = lambda name: {
            "apigateway_client": mock_client,
            "api_common_routing_outputs": {"api_gateway_id": "abc123"}
        }[name]
        result = api_gateway_info.__wrapped__(mock_request)
        assert result == {"id": "abc123", "exists": None, "accessible": False}

    def test_api_gateway_info_handles_not_found(self):
        mock_request = MagicMock()
        mock_client = MagicMock()
        mock_client.get_rest_api.side_effect = ClientError(
            {"Error": {"Code": "NotFoundException"}}, "GetRestApi"
        )
        mock_request.getfixturevalue.side_effect = lambda name: {
            "apigateway_client": mock_client,
            "api_common_routing_outputs": {"api_gateway_id": "abc123"}
        }[name]
        result = api_gateway_info.__wrapped__(mock_request)
        assert result == {"id": "abc123", "exists": False, "accessible": True}

    def test_api_gateway_info_reraises_other_errors(self):
        mock_request = MagicMock()
        mock_client = MagicMock()
        mock_client.get_rest_api.side_effect = ClientError(
            {"Error": {"Code": "InternalError", "Message": "Test"}}, "GetRestApi"
        )
        mock_request.getfixturevalue.side_effect = lambda name: {
            "apigateway_client": mock_client,
            "api_common_routing_outputs": {"api_gateway_id": "abc123"}
        }[name]
        with pytest.raises(ClientError, match="InternalError"):
            api_gateway_info.__wrapped__(mock_request)


class TestFindLifecycleRule:
    @staticmethod
    def _client(*rules):
        client = MagicMock()
        client.get_bucket_lifecycle_configuration.return_value = {"Rules": list(rules)}
        return client

    def test_returns_the_rule_whose_id_matches(self):
        wanted = {"ID": "expire-delete-markers", "Status": "Enabled"}
        found = find_lifecycle_rule(self._client(wanted), "a-bucket", "expire-delete-markers")
        assert found == wanted

    def test_returns_none_when_no_rule_carries_that_id(self):
        other = {"ID": "abort-multipart-uploads", "Status": "Enabled"}
        found = find_lifecycle_rule(self._client(other), "a-bucket", "expire-delete-markers")
        assert found is None

    def test_reaches_a_rule_that_is_not_the_first(self):
        wanted = {"ID": "expire-delete-markers", "Status": "Enabled"}
        first = {"ID": "abort-multipart-uploads", "Status": "Disabled"}
        found = find_lifecycle_rule(
            self._client(first, wanted), "a-bucket", "expire-delete-markers"
        )
        assert found == wanted


class TestStaleDeleteMarkers:
    @staticmethod
    def _client(*pages):
        client = MagicMock()
        client.get_paginator.return_value.paginate.return_value = list(pages)
        return client

    @staticmethod
    def _marker(key, **age):
        return {"Key": key, "LastModified": datetime.now(timezone.utc) - timedelta(**age)}

    def test_returns_the_key_of_a_marker_older_than_the_cutoff(self):
        pages = self._client({"DeleteMarkers": [self._marker("left-behind", days=30)]})
        assert stale_delete_markers(pages, "a-bucket") == ["left-behind"]

    def test_omits_a_marker_newer_than_the_cutoff(self):
        pages = self._client({"DeleteMarkers": [self._marker("just-deleted", minutes=5)]})
        assert not stale_delete_markers(pages, "a-bucket")

    def test_reads_every_page_the_paginator_yields(self):
        pages = self._client(
            {"DeleteMarkers": [self._marker("first-page", days=30)]},
            {"DeleteMarkers": [self._marker("second-page", days=30)]},
        )
        assert stale_delete_markers(pages, "a-bucket") == ["first-page", "second-page"]
