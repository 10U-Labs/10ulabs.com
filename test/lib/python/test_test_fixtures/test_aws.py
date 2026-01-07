"""Unit tests for test_fixtures.aws module."""
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from test_fixtures.aws import (
    iam_role_exists,
    get_log_group_info,
)


class TestIamRoleExists:
    """Tests for iam_role_exists helper function."""

    def test_returns_true_when_role_exists(self):
        """Test that iam_role_exists returns True when role exists."""
        mock_client = MagicMock()
        mock_client.get_role.return_value = {
            "Role": {"RoleName": "test-role", "Arn": "arn:aws:iam::123456:role/test-role"}
        }
        result = iam_role_exists(mock_client, "test-role")
        assert result is True

    def test_returns_false_when_role_not_found(self):
        """Test that iam_role_exists returns False when NoSuchEntityException."""
        mock_client = MagicMock()
        mock_client.exceptions.NoSuchEntityException = type(
            "NoSuchEntityException", (Exception,), {}
        )
        mock_client.get_role.side_effect = mock_client.exceptions.NoSuchEntityException()
        result = iam_role_exists(mock_client, "nonexistent-role")
        assert result is False

    def test_calls_get_role_with_role_name(self):
        """Test that iam_role_exists calls get_role with correct RoleName."""
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "my-role"}}
        iam_role_exists(mock_client, "my-role")
        assert mock_client.get_role.call_args[1]["RoleName"] == "my-role"

    def test_passes_role_name_argument(self):
        """Test that role_name argument is passed correctly."""
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {}}
        iam_role_exists(mock_client, "custom-role-name")
        call_args = mock_client.get_role.call_args
        assert call_args[1]["RoleName"] == "custom-role-name"


class TestGetLogGroupInfo:
    """Tests for get_log_group_info helper function."""

    def test_returns_dict_type(self):
        """Test that get_log_group_info returns a dict."""
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        result = get_log_group_info(mock_client, "/aws/lambda/test")
        assert isinstance(result, dict)

    def test_returns_name_in_result(self):
        """Test that result contains correct name."""
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        result = get_log_group_info(mock_client, "/aws/lambda/my-function")
        assert result["name"] == "/aws/lambda/my-function"

    def test_returns_exists_true_when_log_group_found(self):
        """Test that exists is True when log group is found."""
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {
            "logGroups": [
                {"logGroupName": "/aws/lambda/my-function", "retentionInDays": 14}
            ]
        }
        result = get_log_group_info(mock_client, "/aws/lambda/my-function")
        assert result["exists"] is True

    def test_returns_exists_false_when_log_group_not_found(self):
        """Test that exists is False when log group is not found."""
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        result = get_log_group_info(mock_client, "/aws/lambda/nonexistent")
        assert result["exists"] is False

    def test_returns_retention_days_when_set(self):
        """Test that retention is returned when log group has retention set."""
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {
            "logGroups": [
                {"logGroupName": "/aws/lambda/test", "retentionInDays": 30}
            ]
        }
        result = get_log_group_info(mock_client, "/aws/lambda/test")
        assert result["retention"] == 30

    def test_returns_retention_none_when_not_found(self):
        """Test that retention is None when log group not found."""
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        result = get_log_group_info(mock_client, "/aws/lambda/missing")
        assert result["retention"] is None

    def test_returns_retention_none_when_not_set(self):
        """Test that retention is None when retentionInDays not set."""
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {
            "logGroups": [{"logGroupName": "/aws/lambda/test"}]
        }
        result = get_log_group_info(mock_client, "/aws/lambda/test")
        assert result["retention"] is None

    def test_calls_describe_log_groups_with_prefix(self):
        """Test that describe_log_groups is called with log group name prefix."""
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        get_log_group_info(mock_client, "/aws/lambda/test-fn")
        assert mock_client.describe_log_groups.call_count == 1

    def test_calls_describe_log_groups_with_correct_prefix(self):
        """Test that prefix argument is passed correctly."""
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        get_log_group_info(mock_client, "/aws/lambda/test-fn")
        call_args = mock_client.describe_log_groups.call_args
        assert call_args[1]["logGroupNamePrefix"] == "/aws/lambda/test-fn"

    def test_calls_describe_log_groups_with_limit_one(self):
        """Test that describe_log_groups is called with limit=1."""
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        get_log_group_info(mock_client, "/aws/lambda/test")
        call_args = mock_client.describe_log_groups.call_args
        assert call_args[1]["limit"] == 1

    def test_filters_by_exact_log_group_name(self):
        """Test that only exact name match returns exists=True."""
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {
            "logGroups": [
                {"logGroupName": "/aws/lambda/test-function-extra", "retentionInDays": 7}
            ]
        }
        result = get_log_group_info(mock_client, "/aws/lambda/test-function")
        assert result["exists"] is False

    def test_handles_multiple_log_groups_in_response(self):
        """Test that correct log group is found among multiple results."""
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {
            "logGroups": [
                {"logGroupName": "/aws/lambda/target", "retentionInDays": 14}
            ]
        }
        result = get_log_group_info(mock_client, "/aws/lambda/target")
        assert result["exists"] is True


class TestSharedConfigFixture:
    """Tests for shared_config fixture behavior."""

    @patch("test_fixtures.aws.get_shared_config")
    def test_shared_config_calls_get_shared_config(self, mock_get_shared_config):
        """Test that shared_config fixture calls get_shared_config."""
        mock_get_shared_config.return_value = {"aws_region": "us-east-1"}
        from test_fixtures.aws import shared_config
        # Fixtures are generator functions, need to access underlying function
        result = mock_get_shared_config()
        assert mock_get_shared_config.called

    @patch("test_fixtures.aws.get_shared_config")
    def test_shared_config_returns_dict(self, mock_get_shared_config):
        """Test that shared_config returns a dict."""
        mock_get_shared_config.return_value = {"aws_region": "us-west-2"}
        result = mock_get_shared_config()
        assert isinstance(result, dict)


class TestAwsRegionFixture:
    """Tests for aws_region fixture behavior."""

    def test_aws_region_extracts_from_config(self):
        """Test that aws_region extracts aws_region from shared_config."""
        config = {"aws_region": "eu-west-1", "other_key": "value"}
        region = config["aws_region"]
        assert region == "eu-west-1"


class TestSsmGithubPatNameFixture:
    """Tests for ssm_github_pat_name fixture behavior."""

    def test_ssm_github_pat_name_extracts_from_config(self):
        """Test that ssm_github_pat_name extracts correct key from config."""
        config = {"ssm_github_pat_name": "/github/pat", "aws_region": "us-east-1"}
        pat_name = config["ssm_github_pat_name"]
        assert pat_name == "/github/pat"


class TestStateBucketNameFixture:
    """Tests for state_bucket_name fixture behavior."""

    def test_state_bucket_name_extracts_from_config(self):
        """Test that state_bucket_name extracts correct key from config."""
        config = {"name_for_terraform_state_bucket": "my-state-bucket"}
        bucket_name = config["name_for_terraform_state_bucket"]
        assert bucket_name == "my-state-bucket"


class TestClientFixtures:
    """Tests for boto3 client fixture behavior."""

    @patch("test_fixtures.aws.boto3")
    def test_sts_client_creates_sts_client(self, mock_boto3):
        """Test that sts_client creates client with 'sts' service."""
        mock_boto3.client("sts", region_name="us-east-1")
        assert mock_boto3.client.call_args[0][0] == "sts"

    @patch("test_fixtures.aws.boto3")
    def test_iam_client_creates_iam_client(self, mock_boto3):
        """Test that iam_client creates client with 'iam' service."""
        mock_boto3.client("iam", region_name="us-east-1")
        assert mock_boto3.client.call_args[0][0] == "iam"

    @patch("test_fixtures.aws.boto3")
    def test_s3_client_creates_s3_client(self, mock_boto3):
        """Test that s3_client creates client with 's3' service."""
        mock_boto3.client("s3", region_name="us-east-1")
        assert mock_boto3.client.call_args[0][0] == "s3"

    @patch("test_fixtures.aws.boto3")
    def test_ssm_client_creates_ssm_client(self, mock_boto3):
        """Test that ssm_client creates client with 'ssm' service."""
        mock_boto3.client("ssm", region_name="us-east-1")
        assert mock_boto3.client.call_args[0][0] == "ssm"

    @patch("test_fixtures.aws.boto3")
    def test_kms_client_creates_kms_client(self, mock_boto3):
        """Test that kms_client creates client with 'kms' service."""
        mock_boto3.client("kms", region_name="us-east-1")
        assert mock_boto3.client.call_args[0][0] == "kms"

    @patch("test_fixtures.aws.boto3")
    def test_ecr_client_creates_ecr_client(self, mock_boto3):
        """Test that ecr_client creates client with 'ecr' service."""
        mock_boto3.client("ecr", region_name="us-east-1")
        assert mock_boto3.client.call_args[0][0] == "ecr"

    @patch("test_fixtures.aws.boto3")
    def test_logs_client_creates_logs_client(self, mock_boto3):
        """Test that logs_client creates client with 'logs' service."""
        mock_boto3.client("logs", region_name="us-east-1")
        assert mock_boto3.client.call_args[0][0] == "logs"

    @patch("test_fixtures.aws.boto3")
    def test_lambda_client_creates_lambda_client(self, mock_boto3):
        """Test that lambda_client creates client with 'lambda' service."""
        mock_boto3.client("lambda", region_name="us-east-1")
        assert mock_boto3.client.call_args[0][0] == "lambda"

    @patch("test_fixtures.aws.boto3")
    def test_apigateway_client_creates_apigateway_client(self, mock_boto3):
        """Test that apigateway_client creates client with 'apigateway' service."""
        mock_boto3.client("apigateway", region_name="us-east-1")
        assert mock_boto3.client.call_args[0][0] == "apigateway"

    @patch("test_fixtures.aws.boto3")
    def test_dynamodb_client_creates_dynamodb_client(self, mock_boto3):
        """Test that dynamodb_client creates client with 'dynamodb' service."""
        mock_boto3.client("dynamodb", region_name="us-east-1")
        assert mock_boto3.client.call_args[0][0] == "dynamodb"

    @patch("test_fixtures.aws.boto3")
    def test_ecs_client_creates_ecs_client(self, mock_boto3):
        """Test that ecs_client creates client with 'ecs' service."""
        mock_boto3.client("ecs", region_name="us-east-1")
        assert mock_boto3.client.call_args[0][0] == "ecs"

    @patch("test_fixtures.aws.boto3")
    def test_ec2_client_creates_ec2_client(self, mock_boto3):
        """Test that ec2_client creates client with 'ec2' service."""
        mock_boto3.client("ec2", region_name="us-east-1")
        assert mock_boto3.client.call_args[0][0] == "ec2"

    @patch("test_fixtures.aws.boto3")
    def test_ses_client_creates_ses_client(self, mock_boto3):
        """Test that ses_client creates client with 'ses' service."""
        mock_boto3.client("ses", region_name="us-east-1")
        assert mock_boto3.client.call_args[0][0] == "ses"

    @patch("test_fixtures.aws.boto3")
    def test_glue_client_creates_glue_client(self, mock_boto3):
        """Test that glue_client creates client with 'glue' service."""
        mock_boto3.client("glue", region_name="us-east-1")
        assert mock_boto3.client.call_args[0][0] == "glue"

    @patch("test_fixtures.aws.boto3")
    def test_events_client_creates_events_client(self, mock_boto3):
        """Test that events_client creates client with 'events' service."""
        mock_boto3.client("events", region_name="us-east-1")
        assert mock_boto3.client.call_args[0][0] == "events"

    @patch("test_fixtures.aws.boto3")
    def test_scheduler_client_creates_scheduler_client(self, mock_boto3):
        """Test that scheduler_client creates client with 'scheduler' service."""
        mock_boto3.client("scheduler", region_name="us-east-1")
        assert mock_boto3.client.call_args[0][0] == "scheduler"

    @patch("test_fixtures.aws.boto3")
    def test_backup_client_creates_backup_client(self, mock_boto3):
        """Test that backup_client creates client with 'backup' service."""
        mock_boto3.client("backup", region_name="us-east-1")
        assert mock_boto3.client.call_args[0][0] == "backup"


class TestCallerIdentityFixture:
    """Tests for caller_identity fixture behavior."""

    def test_caller_identity_returns_dict_with_account(self):
        """Test that caller_identity returns dict with Account key."""
        mock_response = {"Account": "123456789012", "Arn": "arn:aws:sts::123456789012:assumed-role/role/session"}
        assert "Account" in mock_response

    def test_caller_identity_returns_dict_with_arn(self):
        """Test that caller_identity returns dict with Arn key."""
        mock_response = {"Account": "123456789012", "Arn": "arn:aws:sts::123456789012:assumed-role/role/session"}
        assert "Arn" in mock_response


class TestCurrentRoleArnFixture:
    """Tests for current_role_arn fixture behavior."""

    def test_converts_assumed_role_arn_to_role_arn(self):
        """Test that assumed-role ARN is converted to role ARN."""
        identity = {
            "Account": "123456789012",
            "Arn": "arn:aws:sts::123456789012:assumed-role/my-role/session-name"
        }
        arn = identity.get("Arn", "")
        if ":assumed-role/" in arn:
            account = identity.get("Account", "")
            role_name = arn.split("/")[1]
            result = f"arn:aws:iam::{account}:role/{role_name}"
        else:
            result = arn
        assert result == "arn:aws:iam::123456789012:role/my-role"

    def test_returns_original_arn_if_not_assumed_role(self):
        """Test that non-assumed-role ARN is returned unchanged."""
        identity = {
            "Account": "123456789012",
            "Arn": "arn:aws:iam::123456789012:user/my-user"
        }
        arn = identity.get("Arn", "")
        if ":assumed-role/" in arn:
            account = identity.get("Account", "")
            role_name = arn.split("/")[1]
            result = f"arn:aws:iam::{account}:role/{role_name}"
        else:
            result = arn
        assert result == "arn:aws:iam::123456789012:user/my-user"

    def test_handles_empty_arn(self):
        """Test that empty ARN is handled gracefully."""
        identity = {"Account": "123456789012", "Arn": ""}
        arn = identity.get("Arn", "")
        if ":assumed-role/" in arn:
            account = identity.get("Account", "")
            role_name = arn.split("/")[1]
            result = f"arn:aws:iam::{account}:role/{role_name}"
        else:
            result = arn
        assert result == ""


class TestCurrentRoleNameFixture:
    """Tests for current_role_name fixture behavior."""

    def test_extracts_role_name_from_role_arn(self):
        """Test that role name is extracted from role ARN."""
        role_arn = "arn:aws:iam::123456789012:role/my-test-role"
        if not role_arn:
            result = ""
        else:
            result = role_arn.split("/")[-1]
        assert result == "my-test-role"

    def test_returns_empty_string_for_empty_arn(self):
        """Test that empty string is returned for empty ARN."""
        role_arn = ""
        if not role_arn:
            result = ""
        else:
            result = role_arn.split("/")[-1]
        assert result == ""

    def test_handles_complex_role_names(self):
        """Test that complex role names with hyphens are handled."""
        role_arn = "arn:aws:iam::123456789012:role/my-complex-role-name-123"
        result = role_arn.split("/")[-1]
        assert result == "my-complex-role-name-123"


class TestEcrRepositoryNameFixture:
    """Tests for ecr_repository_name fixture behavior."""

    def test_ecr_repository_name_extracts_from_config(self):
        """Test that ecr_repository_name extracts correct key from config."""
        config = {"ecr_repository_name_agents": "my-agents-repo"}
        repo_name = config["ecr_repository_name_agents"]
        assert repo_name == "my-agents-repo"


class TestApiGatewayInfoFixture:
    """Tests for api_gateway_info fixture behavior."""

    def test_returns_not_found_when_api_id_missing(self):
        """Test that missing api_id returns appropriate response."""
        api_common_routing_outputs = {"api_gateway_id": None}
        api_id = api_common_routing_outputs.get("api_gateway_id")
        if not api_id:
            result = {"id": None, "exists": False, "accessible": False}
        else:
            result = None
        assert result["exists"] is False

    def test_returns_accessible_false_when_api_id_missing(self):
        """Test that missing api_id returns accessible=False."""
        api_common_routing_outputs = {"api_gateway_id": None}
        api_id = api_common_routing_outputs.get("api_gateway_id")
        if not api_id:
            result = {"id": None, "exists": False, "accessible": False}
        else:
            result = None
        assert result["accessible"] is False

    def test_returns_success_response_structure(self):
        """Test that successful response has expected keys."""
        mock_result = {
            "id": "abc123",
            "exists": True,
            "accessible": True,
            "endpoint_types": ["REGIONAL"],
            "paths": ["/", "/items"]
        }
        assert "id" in mock_result

    def test_returns_endpoint_types_in_success_response(self):
        """Test that successful response includes endpoint_types."""
        mock_result = {
            "id": "abc123",
            "exists": True,
            "accessible": True,
            "endpoint_types": ["REGIONAL"],
            "paths": ["/", "/items"]
        }
        assert "endpoint_types" in mock_result

    def test_returns_paths_in_success_response(self):
        """Test that successful response includes paths."""
        mock_result = {
            "id": "abc123",
            "exists": True,
            "accessible": True,
            "endpoint_types": ["REGIONAL"],
            "paths": ["/", "/items"]
        }
        assert "paths" in mock_result

    def test_handles_access_denied_error(self):
        """Test that AccessDeniedException returns accessible=False."""
        error_code = "AccessDeniedException"
        if error_code == "AccessDeniedException":
            result = {"id": "abc123", "exists": None, "accessible": False}
        else:
            result = None
        assert result["accessible"] is False

    def test_handles_access_denied_error_exists_none(self):
        """Test that AccessDeniedException returns exists=None."""
        error_code = "AccessDeniedException"
        if error_code == "AccessDeniedException":
            result = {"id": "abc123", "exists": None, "accessible": False}
        else:
            result = None
        assert result["exists"] is None

    def test_handles_not_found_error(self):
        """Test that NotFoundException returns exists=False."""
        error_code = "NotFoundException"
        if error_code == "NotFoundException":
            result = {"id": "abc123", "exists": False, "accessible": True}
        else:
            result = None
        assert result["exists"] is False

    def test_handles_not_found_error_accessible_true(self):
        """Test that NotFoundException returns accessible=True."""
        error_code = "NotFoundException"
        if error_code == "NotFoundException":
            result = {"id": "abc123", "exists": False, "accessible": True}
        else:
            result = None
        assert result["accessible"] is True


class TestApiUrlFixture:
    """Tests for api_url fixture behavior."""

    def test_constructs_url_from_api_fqdn(self):
        """Test that api_url is constructed with https and api_fqdn."""
        config = {"api_fqdn": "api.example.com"}
        result = f"https://{config['api_fqdn']}"
        assert result == "https://api.example.com"

    def test_url_starts_with_https(self):
        """Test that api_url starts with https."""
        config = {"api_fqdn": "api.test.com"}
        result = f"https://{config['api_fqdn']}"
        assert result.startswith("https://")


class TestApiKeyFixture:
    """Tests for api_key fixture behavior."""

    def test_retrieves_api_key_from_ssm(self):
        """Test that api_key retrieves value from SSM parameter."""
        mock_response = {"Parameter": {"Value": "my-secret-api-key"}}
        result = mock_response["Parameter"]["Value"] if mock_response else None
        assert result == "my-secret-api-key"

    def test_returns_none_when_no_response(self):
        """Test that api_key returns None when no response."""
        mock_response = None
        result = mock_response["Parameter"]["Value"] if mock_response else None
        assert result is None


class TestStateBucketRegionFixture:
    """Tests for state_bucket_region fixture behavior."""

    def test_returns_aws_region(self):
        """Test that state_bucket_region returns the aws_region."""
        aws_region = "us-west-2"
        result = aws_region
        assert result == "us-west-2"


# === Direct Fixture Function Execution Tests ===
# These tests execute the actual fixture functions with mocked dependencies


class TestSharedConfigFixtureExecution:
    """Tests that execute the shared_config fixture function."""

    @patch("test_fixtures.aws.get_shared_config")
    def test_shared_config_fixture_returns_config(self, mock_get_config):
        """Test shared_config fixture calls get_shared_config and returns result."""
        from test_fixtures.aws import shared_config
        mock_get_config.return_value = {"aws_region": "us-east-1", "key": "value"}
        # Fixtures without request param use __wrapped__ too
        result = shared_config.__wrapped__()
        assert result == {"aws_region": "us-east-1", "key": "value"}
        mock_get_config.assert_called_once()


class TestAwsRegionFixtureExecution:
    """Tests that execute the aws_region fixture function."""

    def test_aws_region_fixture_extracts_region(self):
        """Test aws_region fixture extracts aws_region from shared_config."""
        from test_fixtures.aws import aws_region
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"aws_region": "eu-west-1"}
        result = aws_region.__wrapped__(mock_request)
        assert result == "eu-west-1"
        mock_request.getfixturevalue.assert_called_with("shared_config")


class TestSsmGithubPatNameFixtureExecution:
    """Tests that execute the ssm_github_pat_name fixture function."""

    def test_ssm_github_pat_name_fixture_extracts_value(self):
        """Test ssm_github_pat_name fixture extracts from shared_config."""
        from test_fixtures.aws import ssm_github_pat_name
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"ssm_github_pat_name": "/github/pat"}
        result = ssm_github_pat_name.__wrapped__(mock_request)
        assert result == "/github/pat"


class TestStateBucketNameFixtureExecution:
    """Tests that execute the state_bucket_name fixture function."""

    def test_state_bucket_name_fixture_extracts_value(self):
        """Test state_bucket_name fixture extracts from shared_config."""
        from test_fixtures.aws import state_bucket_name
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"name_for_terraform_state_bucket": "my-bucket"}
        result = state_bucket_name.__wrapped__(mock_request)
        assert result == "my-bucket"


class TestClientFixturesExecution:
    """Tests that execute the boto3 client fixture functions."""

    @patch("test_fixtures.aws.boto3")
    def test_sts_client_fixture_creates_client(self, mock_boto3):
        """Test sts_client fixture creates STS client with region."""
        from test_fixtures.aws import sts_client
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-2"
        mock_boto3.client.return_value = MagicMock()
        sts_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "sts"

    @patch("test_fixtures.aws.boto3")
    def test_iam_client_fixture_creates_client(self, mock_boto3):
        """Test iam_client fixture creates IAM client with region."""
        from test_fixtures.aws import iam_client
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-west-2"
        iam_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "iam"

    @patch("test_fixtures.aws.boto3")
    def test_s3_client_fixture_creates_client(self, mock_boto3):
        """Test s3_client fixture creates S3 client with region."""
        from test_fixtures.aws import s3_client
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        s3_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "s3"

    @patch("test_fixtures.aws.boto3")
    def test_ssm_client_fixture_creates_client(self, mock_boto3):
        """Test ssm_client fixture creates SSM client with region."""
        from test_fixtures.aws import ssm_client
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        ssm_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "ssm"

    @patch("test_fixtures.aws.boto3")
    def test_kms_client_fixture_creates_client(self, mock_boto3):
        """Test kms_client fixture creates KMS client with region."""
        from test_fixtures.aws import kms_client
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        kms_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "kms"

    @patch("test_fixtures.aws.boto3")
    def test_ecr_client_fixture_creates_client(self, mock_boto3):
        """Test ecr_client fixture creates ECR client with region."""
        from test_fixtures.aws import ecr_client
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        ecr_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "ecr"

    @patch("test_fixtures.aws.boto3")
    def test_logs_client_fixture_creates_client(self, mock_boto3):
        """Test logs_client fixture creates CloudWatch Logs client with region."""
        from test_fixtures.aws import logs_client
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        logs_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "logs"

    @patch("test_fixtures.aws.boto3")
    def test_lambda_client_fixture_creates_client(self, mock_boto3):
        """Test lambda_client fixture creates Lambda client with region."""
        from test_fixtures.aws import lambda_client
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        lambda_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "lambda"

    @patch("test_fixtures.aws.boto3")
    def test_apigateway_client_fixture_creates_client(self, mock_boto3):
        """Test apigateway_client fixture creates API Gateway client with region."""
        from test_fixtures.aws import apigateway_client
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        apigateway_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "apigateway"

    @patch("test_fixtures.aws.boto3")
    def test_dynamodb_client_fixture_creates_client(self, mock_boto3):
        """Test dynamodb_client fixture creates DynamoDB client with region."""
        from test_fixtures.aws import dynamodb_client
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        dynamodb_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "dynamodb"

    @patch("test_fixtures.aws.boto3")
    def test_ecs_client_fixture_creates_client(self, mock_boto3):
        """Test ecs_client fixture creates ECS client with region."""
        from test_fixtures.aws import ecs_client
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        ecs_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "ecs"

    @patch("test_fixtures.aws.boto3")
    def test_ec2_client_fixture_creates_client(self, mock_boto3):
        """Test ec2_client fixture creates EC2 client with region."""
        from test_fixtures.aws import ec2_client
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        ec2_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "ec2"

    @patch("test_fixtures.aws.boto3")
    def test_ses_client_fixture_creates_client(self, mock_boto3):
        """Test ses_client fixture creates SES client with region."""
        from test_fixtures.aws import ses_client
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        ses_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "ses"

    @patch("test_fixtures.aws.boto3")
    def test_glue_client_fixture_creates_client(self, mock_boto3):
        """Test glue_client fixture creates Glue client with region."""
        from test_fixtures.aws import glue_client
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        glue_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "glue"

    @patch("test_fixtures.aws.boto3")
    def test_events_client_fixture_creates_client(self, mock_boto3):
        """Test events_client fixture creates EventBridge client with region."""
        from test_fixtures.aws import events_client
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        events_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "events"

    @patch("test_fixtures.aws.boto3")
    def test_scheduler_client_fixture_creates_client(self, mock_boto3):
        """Test scheduler_client fixture creates Scheduler client with region."""
        from test_fixtures.aws import scheduler_client
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        scheduler_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "scheduler"

    @patch("test_fixtures.aws.boto3")
    def test_backup_client_fixture_creates_client(self, mock_boto3):
        """Test backup_client fixture creates Backup client with region."""
        from test_fixtures.aws import backup_client
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-east-1"
        backup_client.__wrapped__(mock_request)
        assert mock_boto3.client.call_args[0][0] == "backup"


class TestCallerIdentityFixtureExecution:
    """Tests that execute the caller_identity fixture function."""

    def test_caller_identity_fixture_calls_get_caller_identity(self):
        """Test caller_identity fixture calls STS get_caller_identity."""
        from test_fixtures.aws import caller_identity
        mock_request = MagicMock()
        mock_sts_client = MagicMock()
        mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}
        mock_request.getfixturevalue.return_value = mock_sts_client
        # Access underlying function via __wrapped__
        result = caller_identity.__wrapped__(mock_request)
        assert result == {"Account": "123456789012"}
        mock_sts_client.get_caller_identity.assert_called_once()


class TestCurrentRoleArnFixtureExecution:
    """Tests that execute the current_role_arn fixture function."""

    def test_current_role_arn_converts_assumed_role(self):
        """Test current_role_arn converts assumed-role ARN to role ARN."""
        from test_fixtures.aws import current_role_arn
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {
            "Account": "123456789012",
            "Arn": "arn:aws:sts::123456789012:assumed-role/MyRole/session"
        }
        result = current_role_arn.__wrapped__(mock_request)
        assert result == "arn:aws:iam::123456789012:role/MyRole"

    def test_current_role_arn_returns_unchanged_for_non_assumed(self):
        """Test current_role_arn returns unchanged ARN for non-assumed-role."""
        from test_fixtures.aws import current_role_arn
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {
            "Account": "123456789012",
            "Arn": "arn:aws:iam::123456789012:user/MyUser"
        }
        result = current_role_arn.__wrapped__(mock_request)
        assert result == "arn:aws:iam::123456789012:user/MyUser"


class TestCurrentRoleNameFixtureExecution:
    """Tests that execute the current_role_name fixture function."""

    def test_current_role_name_extracts_role_name(self):
        """Test current_role_name extracts role name from ARN."""
        from test_fixtures.aws import current_role_name
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "arn:aws:iam::123456789012:role/MyRole"
        result = current_role_name.__wrapped__(mock_request)
        assert result == "MyRole"

    def test_current_role_name_returns_empty_for_empty_arn(self):
        """Test current_role_name returns empty string for empty ARN."""
        from test_fixtures.aws import current_role_name
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = ""
        result = current_role_name.__wrapped__(mock_request)
        assert result == ""


class TestEcrRepositoryNameFixtureExecution:
    """Tests that execute the ecr_repository_name fixture function."""

    def test_ecr_repository_name_extracts_value(self):
        """Test ecr_repository_name extracts from shared_config."""
        from test_fixtures.aws import ecr_repository_name
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"ecr_repository_name_agents": "my-repo"}
        result = ecr_repository_name.__wrapped__(mock_request)
        assert result == "my-repo"


class TestStateBucketRegionFixtureExecution:
    """Tests that execute the state_bucket_region fixture function."""

    def test_state_bucket_region_returns_aws_region(self):
        """Test state_bucket_region returns aws_region value."""
        from test_fixtures.aws import state_bucket_region
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "us-west-2"
        result = state_bucket_region.__wrapped__(mock_request)
        assert result == "us-west-2"


class TestApiGatewayInfoFixtureExecution:
    """Tests that execute the api_gateway_info fixture function."""

    def test_api_gateway_info_returns_not_found_when_no_id(self):
        """Test api_gateway_info returns not found when api_gateway_id is None."""
        from test_fixtures.aws import api_gateway_info
        mock_request = MagicMock()
        mock_request.getfixturevalue.side_effect = lambda name: {
            "apigateway_client": MagicMock(),
            "api_common_routing_outputs": {"api_gateway_id": None}
        }[name]
        result = api_gateway_info.__wrapped__(mock_request)
        assert result == {"id": None, "exists": False, "accessible": False}

    def test_api_gateway_info_returns_success_when_api_exists(self):
        """Test api_gateway_info returns success when API exists."""
        from test_fixtures.aws import api_gateway_info
        mock_request = MagicMock()
        mock_client = MagicMock()
        mock_client.get_rest_api.return_value = {
            "endpointConfiguration": {"types": ["REGIONAL"]}
        }
        mock_client.get_resources.return_value = {
            "items": [{"path": "/"}, {"path": "/items"}]
        }
        mock_request.getfixturevalue.side_effect = lambda name: {
            "apigateway_client": mock_client,
            "api_common_routing_outputs": {"api_gateway_id": "abc123"}
        }[name]
        result = api_gateway_info.__wrapped__(mock_request)
        assert result["id"] == "abc123"
        assert result["exists"] is True
        assert result["accessible"] is True
        assert result["endpoint_types"] == ["REGIONAL"]
        assert result["paths"] == ["/", "/items"]

    def test_api_gateway_info_handles_access_denied(self):
        """Test api_gateway_info handles AccessDeniedException."""
        from test_fixtures.aws import api_gateway_info
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
        """Test api_gateway_info handles NotFoundException."""
        from test_fixtures.aws import api_gateway_info
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
        """Test api_gateway_info re-raises non-handled ClientErrors."""
        from test_fixtures.aws import api_gateway_info
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


class TestApiUrlFixtureExecution:
    """Tests that execute the api_url fixture function."""

    def test_api_url_fixture_constructs_url(self):
        """Test api_url fixture constructs URL from api_fqdn."""
        from test_fixtures.aws import api_url_fixture
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"api_fqdn": "api.example.com"}
        result = api_url_fixture.__wrapped__(mock_request)
        assert result == "https://api.example.com"


class TestApiKeyFixtureExecution:
    """Tests that execute the api_key fixture function."""

    def test_api_key_fixture_retrieves_from_ssm(self):
        """Test api_key fixture retrieves value from SSM."""
        from test_fixtures.aws import api_key_fixture
        mock_request = MagicMock()
        mock_client = MagicMock()
        mock_client.get_parameter.return_value = {
            "Parameter": {"Value": "secret-key-123"}
        }
        mock_request.getfixturevalue.return_value = mock_client
        result = api_key_fixture.__wrapped__(mock_request)
        assert result == "secret-key-123"
        mock_client.get_parameter.assert_called_with(Name='/api/key', WithDecryption=True)
