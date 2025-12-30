"""Comprehensive tests for boto_mocks module."""
from unittest.mock import MagicMock

from botocore.exceptions import ClientError

from boto_mocks import (
    create_client_error,
    create_multi_client_mock,
    create_boto_client_mock,
    create_mock_lambda_list_mappings_error,
    create_mock_lambda_put_concurrency_error,
    create_mock_sns_publish_error,
    create_mock_lambda_with_mappings,
    create_mock_lambda_with_disabled_mappings,
    create_mock_lambda_delete_concurrency_error,
    setup_mock_ec2_vpc_responses,
)


# === create_client_error ===


class TestCreateClientError:
    """Tests for create_client_error function."""

    def test_returns_client_error_instance(self):
        """create_client_error returns a ClientError instance."""
        error = create_client_error("ResourceNotFoundException")
        assert isinstance(error, ClientError)

    def test_sets_error_code(self):
        """create_client_error sets the specified error code."""
        error = create_client_error("ResourceNotFoundException")
        assert error.response["Error"]["Code"] == "ResourceNotFoundException"

    def test_sets_error_message(self):
        """create_client_error sets an error message containing the code."""
        error = create_client_error("ResourceNotFoundException")
        assert "ResourceNotFoundException" in error.response["Error"]["Message"]

    def test_sets_default_operation_name(self):
        """create_client_error sets default operation name."""
        error = create_client_error("ResourceNotFoundException")
        assert error.operation_name == "TestOperation"

    def test_sets_custom_operation_name(self):
        """create_client_error sets custom operation name when provided."""
        error = create_client_error("ResourceNotFoundException", "GetItem")
        assert error.operation_name == "GetItem"

    def test_sets_response_metadata_request_id(self):
        """create_client_error includes RequestId in metadata."""
        error = create_client_error("ResourceNotFoundException")
        assert "RequestId" in error.response["ResponseMetadata"]

    def test_sets_response_metadata_status_code(self):
        """create_client_error sets HTTPStatusCode to 400."""
        error = create_client_error("ResourceNotFoundException")
        assert error.response["ResponseMetadata"]["HTTPStatusCode"] == 400


# === create_multi_client_mock ===


class TestCreateMultiClientMock:
    """Tests for create_multi_client_mock function."""

    def test_returns_ec2_mock_for_ec2(self):
        """create_multi_client_mock returns ec2_mock for 'ec2' service."""
        ec2_mock = MagicMock()
        ssm_mock = MagicMock()
        client_mock = create_multi_client_mock(ec2_mock, ssm_mock)
        assert client_mock("ec2") is ec2_mock

    def test_returns_ssm_mock_for_ssm(self):
        """create_multi_client_mock returns ssm_mock for 'ssm' service."""
        ec2_mock = MagicMock()
        ssm_mock = MagicMock()
        client_mock = create_multi_client_mock(ec2_mock, ssm_mock)
        assert client_mock("ssm") is ssm_mock

    def test_returns_additional_mock_for_extra_service(self):
        """create_multi_client_mock returns additional mock for extra service."""
        ec2_mock = MagicMock()
        ssm_mock = MagicMock()
        sqs_mock = MagicMock()
        client_mock = create_multi_client_mock(ec2_mock, ssm_mock, sqs=sqs_mock)
        assert client_mock("sqs") is sqs_mock

    def test_returns_magicmock_for_unknown_service(self):
        """create_multi_client_mock returns MagicMock for unknown service."""
        ec2_mock = MagicMock()
        ssm_mock = MagicMock()
        client_mock = create_multi_client_mock(ec2_mock, ssm_mock)
        result = client_mock("unknown")
        assert isinstance(result, MagicMock)


# === create_boto_client_mock ===


class TestCreateBotoClientMock:
    """Tests for create_boto_client_mock function."""

    def test_returns_configured_mock_for_service(self):
        """create_boto_client_mock returns configured mock for known service."""
        sqs_mock = MagicMock()
        client_mock = create_boto_client_mock(sqs=sqs_mock)
        assert client_mock("sqs") is sqs_mock

    def test_returns_magicmock_for_unknown_service(self):
        """create_boto_client_mock returns MagicMock for unknown service."""
        client_mock = create_boto_client_mock()
        result = client_mock("unknown")
        assert isinstance(result, MagicMock)

    def test_handles_multiple_services_ec2(self):
        """create_boto_client_mock returns correct mock for ec2."""
        ec2_mock = MagicMock()
        s3_mock = MagicMock()
        client_mock = create_boto_client_mock(ec2=ec2_mock, s3=s3_mock)
        assert client_mock("ec2") is ec2_mock

    def test_handles_multiple_services_s3(self):
        """create_boto_client_mock returns correct mock for s3."""
        ec2_mock = MagicMock()
        s3_mock = MagicMock()
        client_mock = create_boto_client_mock(ec2=ec2_mock, s3=s3_mock)
        assert client_mock("s3") is s3_mock


# === create_mock_lambda_list_mappings_error ===


class TestCreateMockLambdaListMappingsError:
    """Tests for create_mock_lambda_list_mappings_error function."""

    def test_returns_magicmock(self):
        """create_mock_lambda_list_mappings_error returns a MagicMock."""
        mock = create_mock_lambda_list_mappings_error()
        assert isinstance(mock, MagicMock)

    def test_list_event_source_mappings_raises_client_error(self):
        """list_event_source_mappings raises ClientError."""
        mock = create_mock_lambda_list_mappings_error()
        raised = False
        try:
            mock.list_event_source_mappings()
        except ClientError:
            raised = True
        assert raised is True

    def test_list_event_source_mappings_error_code(self):
        """list_event_source_mappings raises ServiceUnavailable."""
        mock = create_mock_lambda_list_mappings_error()
        try:
            mock.list_event_source_mappings()
        except ClientError as e:
            assert e.response["Error"]["Code"] == "ServiceUnavailable"


# === create_mock_lambda_put_concurrency_error ===


class TestCreateMockLambdaPutConcurrencyError:
    """Tests for create_mock_lambda_put_concurrency_error function."""

    def test_returns_magicmock(self):
        """create_mock_lambda_put_concurrency_error returns a MagicMock."""
        mock = create_mock_lambda_put_concurrency_error()
        assert isinstance(mock, MagicMock)

    def test_put_function_concurrency_raises_client_error(self):
        """put_function_concurrency raises ClientError."""
        mock = create_mock_lambda_put_concurrency_error()
        raised = False
        try:
            mock.put_function_concurrency()
        except ClientError:
            raised = True
        assert raised is True

    def test_put_function_concurrency_error_code(self):
        """put_function_concurrency raises ServiceUnavailable."""
        mock = create_mock_lambda_put_concurrency_error()
        try:
            mock.put_function_concurrency()
        except ClientError as e:
            assert e.response["Error"]["Code"] == "ServiceUnavailable"


# === create_mock_sns_publish_error ===


class TestCreateMockSnsPublishError:
    """Tests for create_mock_sns_publish_error function."""

    def test_returns_magicmock(self):
        """create_mock_sns_publish_error returns a MagicMock."""
        mock = create_mock_sns_publish_error()
        assert isinstance(mock, MagicMock)

    def test_publish_raises_client_error(self):
        """publish raises ClientError."""
        mock = create_mock_sns_publish_error()
        raised = False
        try:
            mock.publish()
        except ClientError:
            raised = True
        assert raised is True

    def test_publish_error_code(self):
        """publish raises ServiceUnavailable."""
        mock = create_mock_sns_publish_error()
        try:
            mock.publish()
        except ClientError as e:
            assert e.response["Error"]["Code"] == "ServiceUnavailable"


# === create_mock_lambda_with_mappings ===


class TestCreateMockLambdaWithMappings:
    """Tests for create_mock_lambda_with_mappings function."""

    def test_returns_magicmock(self):
        """create_mock_lambda_with_mappings returns a MagicMock."""
        mock = create_mock_lambda_with_mappings()
        assert isinstance(mock, MagicMock)

    def test_list_event_source_mappings_returns_one_mapping(self):
        """list_event_source_mappings returns one mapping."""
        mock = create_mock_lambda_with_mappings()
        result = mock.list_event_source_mappings()
        assert len(result["EventSourceMappings"]) == 1

    def test_list_event_source_mappings_returns_enabled_state(self):
        """list_event_source_mappings returns Enabled state."""
        mock = create_mock_lambda_with_mappings()
        result = mock.list_event_source_mappings()
        assert result["EventSourceMappings"][0]["State"] == "Enabled"

    def test_list_event_source_mappings_returns_uuid(self):
        """list_event_source_mappings returns mapping with UUID."""
        mock = create_mock_lambda_with_mappings()
        result = mock.list_event_source_mappings()
        assert result["EventSourceMappings"][0]["UUID"] == "test-uuid"


# === create_mock_lambda_with_disabled_mappings ===


class TestCreateMockLambdaWithDisabledMappings:
    """Tests for create_mock_lambda_with_disabled_mappings function."""

    def test_returns_magicmock(self):
        """create_mock_lambda_with_disabled_mappings returns a MagicMock."""
        mock = create_mock_lambda_with_disabled_mappings()
        assert isinstance(mock, MagicMock)

    def test_list_event_source_mappings_returns_one_disabled_mapping(self):
        """list_event_source_mappings returns one mapping."""
        mock = create_mock_lambda_with_disabled_mappings()
        result = mock.list_event_source_mappings()
        assert len(result["EventSourceMappings"]) == 1

    def test_list_event_source_mappings_returns_disabled_state(self):
        """list_event_source_mappings returns Disabled state."""
        mock = create_mock_lambda_with_disabled_mappings()
        result = mock.list_event_source_mappings()
        assert result["EventSourceMappings"][0]["State"] == "Disabled"


# === create_mock_lambda_delete_concurrency_error ===


class TestCreateMockLambdaDeleteConcurrencyError:
    """Tests for create_mock_lambda_delete_concurrency_error function."""

    def test_returns_magicmock(self):
        """create_mock_lambda_delete_concurrency_error returns a MagicMock."""
        mock = create_mock_lambda_delete_concurrency_error()
        assert isinstance(mock, MagicMock)

    def test_delete_function_concurrency_raises_client_error(self):
        """delete_function_concurrency raises ClientError."""
        mock = create_mock_lambda_delete_concurrency_error()
        raised = False
        try:
            mock.delete_function_concurrency()
        except ClientError:
            raised = True
        assert raised is True

    def test_delete_function_concurrency_error_code(self):
        """delete_function_concurrency raises ServiceUnavailable."""
        mock = create_mock_lambda_delete_concurrency_error()
        try:
            mock.delete_function_concurrency()
        except ClientError as e:
            assert e.response["Error"]["Code"] == "ServiceUnavailable"


# === setup_mock_ec2_vpc_responses ===


class TestSetupMockEc2VpcResponses:
    """Tests for setup_mock_ec2_vpc_responses function."""

    def test_configures_describe_security_groups_key(self):
        """setup_mock_ec2_vpc_responses returns SecurityGroups key."""
        mock_ec2 = MagicMock()
        setup_mock_ec2_vpc_responses(mock_ec2)
        result = mock_ec2.describe_security_groups()
        assert "SecurityGroups" in result

    def test_configures_describe_security_groups_value(self):
        """setup_mock_ec2_vpc_responses returns correct group ID."""
        mock_ec2 = MagicMock()
        setup_mock_ec2_vpc_responses(mock_ec2)
        result = mock_ec2.describe_security_groups()
        assert result["SecurityGroups"][0]["GroupId"] == "sg-test"

    def test_configures_describe_subnets_key(self):
        """setup_mock_ec2_vpc_responses returns Subnets key."""
        mock_ec2 = MagicMock()
        setup_mock_ec2_vpc_responses(mock_ec2)
        result = mock_ec2.describe_subnets()
        assert "Subnets" in result

    def test_configures_describe_subnets_count(self):
        """setup_mock_ec2_vpc_responses returns two subnets."""
        mock_ec2 = MagicMock()
        setup_mock_ec2_vpc_responses(mock_ec2)
        result = mock_ec2.describe_subnets()
        assert len(result["Subnets"]) == 2

    def test_configures_describe_vpcs_key(self):
        """setup_mock_ec2_vpc_responses returns Vpcs key."""
        mock_ec2 = MagicMock()
        setup_mock_ec2_vpc_responses(mock_ec2)
        result = mock_ec2.describe_vpcs()
        assert "Vpcs" in result

    def test_configures_describe_vpcs_value(self):
        """setup_mock_ec2_vpc_responses returns correct VPC ID."""
        mock_ec2 = MagicMock()
        setup_mock_ec2_vpc_responses(mock_ec2)
        result = mock_ec2.describe_vpcs()
        assert result["Vpcs"][0]["VpcId"] == "vpc-test"
