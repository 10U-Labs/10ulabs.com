"""Unit tests that run the later layers' base class methods.

The other half of the base class methods, split from its sibling
because one module of both runs past the length pylint allows.
"""
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

import test_fixtures.integration as integration_module


class TestLayer5S3RegionTestsExecution:
    """Tests that execute Layer5S3RegionTests methods."""

    def test_bucket_in_expected_region_success(self):
        """Test test_bucket_in_expected_region with correct region."""
        instance = integration_module.Layer5S3RegionTests()
        mock_client = MagicMock()
        mock_client.get_bucket_location.return_value = {"LocationConstraint": "us-west-2"}
        assert instance.test_bucket_in_expected_region(
            mock_client, "my-bucket", "us-west-2"
        ) is None

    def test_bucket_in_expected_region_us_east_1_none(self):
        """Test test_bucket_in_expected_region handles us-east-1 as None."""
        instance = integration_module.Layer5S3RegionTests()
        mock_client = MagicMock()
        mock_client.get_bucket_location.return_value = {"LocationConstraint": None}
        assert instance.test_bucket_in_expected_region(
            mock_client, "my-bucket", "us-east-1"
        ) is None

    def test_bucket_in_expected_region_fails_with_wrong_region(self):
        """Test test_bucket_in_expected_region fails with wrong region."""
        instance = integration_module.Layer5S3RegionTests()
        mock_client = MagicMock()
        mock_client.get_bucket_location.return_value = {"LocationConstraint": "eu-west-1"}
        with pytest.raises(AssertionError):
            instance.test_bucket_in_expected_region(mock_client, "my-bucket", "us-west-2")

    def test_expected_region_is_configured_success(self):
        """Test test_expected_region_is_configured with valid region."""
        instance = integration_module.Layer5S3RegionTests()
        assert instance.test_expected_region_is_configured("us-west-2") is None

    def test_expected_region_is_configured_fails_when_empty(self):
        """Test test_expected_region_is_configured fails when empty."""
        instance = integration_module.Layer5S3RegionTests()
        with pytest.raises(AssertionError):
            instance.test_expected_region_is_configured("")


class TestLayer6IAMCapabilityTestsExecution:
    """Tests that execute Layer6IAMCapabilityTests methods."""

    def test_can_list_buckets_success(self):
        """Test test_can_list_buckets with successful call."""
        instance = integration_module.Layer6IAMCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_buckets.return_value = {"Buckets": []}
        assert instance.test_can_list_buckets(mock_client) is None

    def test_can_list_buckets_fails_on_access_denied(self):
        """Test test_can_list_buckets fails on AccessDenied."""
        instance = integration_module.Layer6IAMCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_buckets.side_effect = _create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_list_buckets(mock_client)

    def test_can_list_buckets_reraises_other_errors(self):
        """Test test_can_list_buckets re-raises other errors."""
        instance = integration_module.Layer6IAMCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_buckets.side_effect = _create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_list_buckets(mock_client)

    def test_can_list_roles_success(self):
        """Test test_can_list_roles with successful call."""
        instance = integration_module.Layer6IAMCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_roles.return_value = {"Roles": []}
        assert instance.test_can_list_roles(mock_client) is None

    def test_can_list_roles_fails_on_access_denied(self):
        """Test test_can_list_roles fails on AccessDenied."""
        instance = integration_module.Layer6IAMCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_roles.side_effect = _create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_list_roles(mock_client)

    def test_can_list_roles_reraises_other_errors(self):
        """Test test_can_list_roles re-raises other errors."""
        instance = integration_module.Layer6IAMCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_roles.side_effect = _create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_list_roles(mock_client)


class TestLayer6S3WriteCapabilityTestsExecution:
    """Tests that execute Layer6S3WriteCapabilityTests methods."""

    def test_can_write_to_bucket_success(self):
        """Test test_can_write_to_bucket with successful call."""
        instance = integration_module.Layer6S3WriteCapabilityTests()
        mock_client = MagicMock()
        mock_client.put_object.return_value = {}
        mock_client.delete_object.return_value = {}
        assert instance.test_can_write_to_bucket(mock_client, "my-bucket") is None
        mock_client.put_object.assert_called_once()
        mock_client.delete_object.assert_called_once()

    def test_can_write_to_bucket_fails_on_access_denied(self):
        """Test test_can_write_to_bucket fails on AccessDenied."""
        instance = integration_module.Layer6S3WriteCapabilityTests()
        mock_client = MagicMock()
        mock_client.put_object.side_effect = _create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_write_to_bucket(mock_client, "my-bucket")

    def test_can_write_to_bucket_reraises_other_errors(self):
        """Test test_can_write_to_bucket re-raises other errors."""
        instance = integration_module.Layer6S3WriteCapabilityTests()
        mock_client = MagicMock()
        mock_client.put_object.side_effect = _create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_write_to_bucket(mock_client, "my-bucket")

    def test_can_write_to_bucket_cleanup_on_delete_failure(self):
        """Test test_can_write_to_bucket handles delete failure gracefully."""
        instance = integration_module.Layer6S3WriteCapabilityTests()
        mock_client = MagicMock()
        mock_client.put_object.return_value = {}
        mock_client.delete_object.side_effect = _create_client_error("InternalError")
        # Should not raise - cleanup failures are suppressed
        assert instance.test_can_write_to_bucket(mock_client, "my-bucket") is None

    def test_can_delete_from_bucket_success(self):
        """Test test_can_delete_from_bucket with successful call."""
        instance = integration_module.Layer6S3WriteCapabilityTests()
        mock_client = MagicMock()
        mock_client.put_object.return_value = {}
        mock_client.delete_object.return_value = {}
        assert instance.test_can_delete_from_bucket(mock_client, "my-bucket") is None

    def test_can_delete_from_bucket_fails_on_access_denied(self):
        """Test test_can_delete_from_bucket fails on AccessDenied."""
        instance = integration_module.Layer6S3WriteCapabilityTests()
        mock_client = MagicMock()
        mock_client.put_object.return_value = {}
        # First delete call (the actual test) fails, second (cleanup) also fails
        mock_client.delete_object.side_effect = _create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_delete_from_bucket(mock_client, "my-bucket")

    def test_can_delete_from_bucket_reraises_other_errors(self):
        """Test test_can_delete_from_bucket re-raises other errors."""
        instance = integration_module.Layer6S3WriteCapabilityTests()
        mock_client = MagicMock()
        mock_client.put_object.return_value = {}
        mock_client.delete_object.side_effect = _create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_delete_from_bucket(mock_client, "my-bucket")


class TestLayer6ECRCapabilityTestsExecution:
    """Tests that execute Layer6ECRCapabilityTests methods."""

    def test_can_create_ecr_repository_success(self):
        """Test test_can_create_ecr_repository with successful call."""
        instance = integration_module.Layer6ECRCapabilityTests()
        mock_client = MagicMock()
        mock_client.create_repository.return_value = {"repository": {}}
        mock_client.delete_repository.return_value = {}
        assert instance.test_can_create_ecr_repository(mock_client) is None
        mock_client.create_repository.assert_called_once()
        mock_client.delete_repository.assert_called_once()

    def test_can_create_ecr_repository_fails_on_access_denied(self):
        """Test test_can_create_ecr_repository fails on AccessDeniedException."""
        instance = integration_module.Layer6ECRCapabilityTests()
        mock_client = MagicMock()
        mock_client.create_repository.side_effect = _create_client_error(
            "AccessDeniedException"
        )
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_create_ecr_repository(mock_client)

    def test_can_create_ecr_repository_reraises_other_errors(self):
        """Test test_can_create_ecr_repository re-raises other errors."""
        instance = integration_module.Layer6ECRCapabilityTests()
        mock_client = MagicMock()
        mock_client.create_repository.side_effect = _create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_create_ecr_repository(mock_client)

    def test_can_create_ecr_repository_cleanup_on_delete_failure(self):
        """Test test_can_create_ecr_repository handles delete failure gracefully."""
        instance = integration_module.Layer6ECRCapabilityTests()
        mock_client = MagicMock()
        mock_client.create_repository.return_value = {"repository": {}}
        mock_client.delete_repository.side_effect = _create_client_error("InternalError")
        # Should not raise - cleanup failures are suppressed
        assert instance.test_can_create_ecr_repository(mock_client) is None

    def test_can_delete_ecr_repository_success(self):
        """Test test_can_delete_ecr_repository with successful call."""
        instance = integration_module.Layer6ECRCapabilityTests()
        mock_client = MagicMock()
        mock_client.create_repository.return_value = {"repository": {}}
        mock_client.delete_repository.return_value = {}
        assert instance.test_can_delete_ecr_repository(mock_client) is None

    def test_can_delete_ecr_repository_fails_on_access_denied(self):
        """Test test_can_delete_ecr_repository fails on AccessDeniedException."""
        instance = integration_module.Layer6ECRCapabilityTests()
        mock_client = MagicMock()
        mock_client.create_repository.return_value = {"repository": {}}
        mock_client.delete_repository.side_effect = _create_client_error(
            "AccessDeniedException"
        )
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_delete_ecr_repository(mock_client)

    def test_can_delete_ecr_repository_reraises_other_errors(self):
        """Test test_can_delete_ecr_repository re-raises other errors."""
        instance = integration_module.Layer6ECRCapabilityTests()
        mock_client = MagicMock()
        mock_client.create_repository.return_value = {"repository": {}}
        mock_client.delete_repository.side_effect = _create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_delete_ecr_repository(mock_client)


class TestLayer1EndpointAuthenticationTestsExecution:
    """Tests that execute Layer1EndpointAuthenticationTests methods."""

    def test_aws_credentials_are_valid_success(self):
        """Test test_aws_credentials_are_valid with valid credentials."""
        instance = integration_module.Layer1EndpointAuthenticationTests()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": "123456789012"}
        assert instance.test_aws_credentials_are_valid(mock_client) is None

    def test_aws_credentials_are_valid_fails_with_none_account(self):
        """Test test_aws_credentials_are_valid fails with None account."""
        instance = integration_module.Layer1EndpointAuthenticationTests()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": None}
        with pytest.raises(AssertionError):
            instance.test_aws_credentials_are_valid(mock_client)

    def test_aws_credentials_return_account_id_success(self):
        """Test test_aws_credentials_return_account_id with 12-digit account."""
        instance = integration_module.Layer1EndpointAuthenticationTests()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": "123456789012"}
        assert instance.test_aws_credentials_return_account_id(mock_client) is None

    def test_aws_credentials_return_account_id_fails_with_wrong_length(self):
        """Test test_aws_credentials_return_account_id fails with wrong length."""
        instance = integration_module.Layer1EndpointAuthenticationTests()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": "12345"}
        with pytest.raises(AssertionError):
            instance.test_aws_credentials_return_account_id(mock_client)

    def test_aws_credentials_return_arn_success(self):
        """Test test_aws_credentials_return_arn with ARN present."""
        instance = integration_module.Layer1EndpointAuthenticationTests()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {
            "Account": "123",
            "Arn": "arn:aws:iam::123:role/MyRole"
        }
        assert instance.test_aws_credentials_return_arn(mock_client) is None

    def test_aws_credentials_return_arn_fails_without_arn(self):
        """Test test_aws_credentials_return_arn fails without ARN."""
        instance = integration_module.Layer1EndpointAuthenticationTests()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": "123"}
        with pytest.raises(AssertionError):
            instance.test_aws_credentials_return_arn(mock_client)

    def test_aws_credentials_arn_has_valid_format_success(self):
        """Test test_aws_credentials_arn_has_valid_format with valid ARN."""
        instance = integration_module.Layer1EndpointAuthenticationTests()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {
            "Arn": "arn:aws:iam::123:role/MyRole"
        }
        assert instance.test_aws_credentials_arn_has_valid_format(mock_client) is None

    def test_aws_credentials_arn_has_valid_format_fails_with_invalid_arn(self):
        """Test test_aws_credentials_arn_has_valid_format fails with invalid ARN."""
        instance = integration_module.Layer1EndpointAuthenticationTests()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Arn": "invalid-arn"}
        with pytest.raises(AssertionError):
            instance.test_aws_credentials_arn_has_valid_format(mock_client)


class TestLayer2APIGatewayAuthorizationTestsExecution:
    """Tests that execute Layer2APIGatewayAuthorizationTests methods."""

    def test_can_describe_rest_apis_success(self):
        """Test test_can_describe_rest_apis with successful call."""
        instance = integration_module.Layer2APIGatewayAuthorizationTests()
        mock_client = MagicMock()
        mock_client.get_rest_apis.return_value = {"items": []}
        assert instance.test_can_describe_rest_apis(mock_client) is None

    def test_can_describe_rest_apis_fails_on_access_denied(self):
        """Test test_can_describe_rest_apis fails on AccessDeniedException."""
        instance = integration_module.Layer2APIGatewayAuthorizationTests()
        mock_client = MagicMock()
        mock_client.get_rest_apis.side_effect = _create_client_error(
            "AccessDeniedException"
        )
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_describe_rest_apis(mock_client)

    def test_can_describe_rest_apis_reraises_other_errors(self):
        """Test test_can_describe_rest_apis re-raises other errors."""
        instance = integration_module.Layer2APIGatewayAuthorizationTests()
        mock_client = MagicMock()
        mock_client.get_rest_apis.side_effect = _create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_describe_rest_apis(mock_client)

    def test_can_access_specific_rest_api_success(self):
        """Test test_can_access_specific_rest_api with accessible API."""
        instance = integration_module.Layer2APIGatewayAuthorizationTests()
        api_gateway_info = {"id": "abc123", "accessible": True}
        assert instance.test_can_access_specific_rest_api(api_gateway_info) is None

    def test_can_access_specific_rest_api_skips_when_id_is_none(self):
        """Test test_can_access_specific_rest_api skips when ID is None."""
        instance = integration_module.Layer2APIGatewayAuthorizationTests()
        api_gateway_info = {"id": None, "accessible": False}
        with pytest.raises(pytest.skip.Exception):
            instance.test_can_access_specific_rest_api(api_gateway_info)

    def test_can_access_specific_rest_api_fails_when_not_accessible(self):
        """Test test_can_access_specific_rest_api fails when not accessible."""
        instance = integration_module.Layer2APIGatewayAuthorizationTests()
        api_gateway_info = {"id": "abc123", "accessible": False}
        with pytest.raises(AssertionError):
            instance.test_can_access_specific_rest_api(api_gateway_info)


class TestLayer2LambdaAndIAMAuthorizationTestsExecution:
    """Tests that execute Layer2LambdaAndIAMAuthorizationTests methods."""

    def test_can_list_functions_success(self):
        """Test test_can_list_functions with successful call."""
        instance = integration_module.Layer2LambdaAndIAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.list_functions.return_value = {"Functions": []}
        assert instance.test_can_list_functions(mock_client) is None

    def test_can_list_functions_fails_on_access_denied(self):
        """Test test_can_list_functions fails on AccessDeniedException."""
        instance = integration_module.Layer2LambdaAndIAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.list_functions.side_effect = _create_client_error(
            "AccessDeniedException"
        )
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_list_functions(mock_client)

    def test_can_list_functions_reraises_other_errors(self):
        """Test test_can_list_functions re-raises other errors."""
        instance = integration_module.Layer2LambdaAndIAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.list_functions.side_effect = _create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_list_functions(mock_client)

    def test_can_list_roles_iam_success(self):
        """Test test_can_list_roles with successful call."""
        instance = integration_module.Layer2LambdaAndIAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.list_roles.return_value = {"Roles": []}
        assert instance.test_can_list_roles(mock_client) is None

    def test_can_list_roles_iam_fails_on_access_denied(self):
        """Test test_can_list_roles fails on AccessDenied."""
        instance = integration_module.Layer2LambdaAndIAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.list_roles.side_effect = _create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_list_roles(mock_client)

    def test_can_list_roles_iam_reraises_other_errors(self):
        """Test test_can_list_roles re-raises other errors."""
        instance = integration_module.Layer2LambdaAndIAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.list_roles.side_effect = _create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_list_roles(mock_client)


class TestLayer4APIBackendPrerequisiteTestsExecution:
    """Tests that execute Layer4APIBackendPrerequisiteTests methods."""

    def test_api_gateway_id_output_exists_success(self):
        """Test test_api_gateway_id_output_exists with ID present."""
        instance = integration_module.Layer4APIBackendPrerequisiteTests()
        outputs = {"api_gateway_id": "abc123xyz"}
        assert instance.test_api_gateway_id_output_exists(outputs) is None

    def test_api_gateway_id_output_exists_fails_when_missing(self):
        """Test test_api_gateway_id_output_exists fails when missing."""
        instance = integration_module.Layer4APIBackendPrerequisiteTests()
        outputs = {}
        with pytest.raises(AssertionError):
            instance.test_api_gateway_id_output_exists(outputs)

    def test_api_gateway_id_output_exists_fails_when_empty(self):
        """Test test_api_gateway_id_output_exists fails when empty."""
        instance = integration_module.Layer4APIBackendPrerequisiteTests()
        outputs = {"api_gateway_id": ""}
        with pytest.raises(AssertionError):
            instance.test_api_gateway_id_output_exists(outputs)

    def test_api_gateway_exists_in_aws_success(self):
        """Test test_api_gateway_exists_in_aws with existing API."""
        instance = integration_module.Layer4APIBackendPrerequisiteTests()
        mock_client = MagicMock()
        mock_client.get_rest_api.return_value = {"id": "abc123"}
        outputs = {"api_gateway_id": "abc123"}
        assert instance.test_api_gateway_exists_in_aws(mock_client, outputs) is None

    def test_api_gateway_exists_in_aws_skips_when_no_id(self):
        """Test test_api_gateway_exists_in_aws skips when no ID."""
        instance = integration_module.Layer4APIBackendPrerequisiteTests()
        mock_client = MagicMock()
        outputs = {}
        with pytest.raises(pytest.skip.Exception):
            instance.test_api_gateway_exists_in_aws(mock_client, outputs)

    def test_api_gateway_exists_in_aws_fails_on_not_found(self):
        """Test test_api_gateway_exists_in_aws fails when API doesn't exist."""
        instance = integration_module.Layer4APIBackendPrerequisiteTests()
        mock_client = MagicMock()
        mock_client.get_rest_api.side_effect = _create_client_error("NotFoundException")
        outputs = {"api_gateway_id": "abc123"}
        with pytest.raises(pytest.fail.Exception):
            instance.test_api_gateway_exists_in_aws(mock_client, outputs)

    def test_api_gateway_exists_in_aws_reraises_other_errors(self):
        """Test test_api_gateway_exists_in_aws re-raises other errors."""
        instance = integration_module.Layer4APIBackendPrerequisiteTests()
        mock_client = MagicMock()
        mock_client.get_rest_api.side_effect = _create_client_error("InternalError")
        outputs = {"api_gateway_id": "abc123"}
        with pytest.raises(ClientError):
            instance.test_api_gateway_exists_in_aws(mock_client, outputs)


class TestLayer5APIGatewayRegionalTestsExecution:
    """Tests that execute Layer5APIGatewayRegionalTests methods."""

    def test_api_gateway_is_regional_success(self):
        """Test test_api_gateway_is_regional with REGIONAL type."""
        instance = integration_module.Layer5APIGatewayRegionalTests()
        api_gateway_info = {
            "id": "abc123",
            "exists": True,
            "endpoint_types": ["REGIONAL"]
        }
        assert instance.test_api_gateway_is_regional(api_gateway_info) is None

    def test_api_gateway_is_regional_skips_when_id_none(self):
        """Test test_api_gateway_is_regional skips when ID is None."""
        instance = integration_module.Layer5APIGatewayRegionalTests()
        api_gateway_info = {"id": None, "exists": False, "endpoint_types": []}
        with pytest.raises(pytest.skip.Exception):
            instance.test_api_gateway_is_regional(api_gateway_info)

    def test_api_gateway_is_regional_skips_when_not_exists(self):
        """Test test_api_gateway_is_regional skips when API doesn't exist."""
        instance = integration_module.Layer5APIGatewayRegionalTests()
        api_gateway_info = {"id": "abc123", "exists": False, "endpoint_types": []}
        with pytest.raises(pytest.skip.Exception):
            instance.test_api_gateway_is_regional(api_gateway_info)

    def test_api_gateway_is_regional_fails_when_not_regional(self):
        """Test test_api_gateway_is_regional fails when not REGIONAL."""
        instance = integration_module.Layer5APIGatewayRegionalTests()
        api_gateway_info = {
            "id": "abc123",
            "exists": True,
            "endpoint_types": ["EDGE"]
        }
        with pytest.raises(AssertionError):
            instance.test_api_gateway_is_regional(api_gateway_info)

    def test_api_gateway_info_has_id_success(self):
        """Test test_api_gateway_info_has_id with ID present."""
        instance = integration_module.Layer5APIGatewayRegionalTests()
        api_gateway_info = {"id": "abc123"}
        assert instance.test_api_gateway_info_has_id(api_gateway_info) is None

    def test_api_gateway_info_has_id_fails_when_missing(self):
        """Test test_api_gateway_info_has_id fails when missing."""
        instance = integration_module.Layer5APIGatewayRegionalTests()
        api_gateway_info = {}
        with pytest.raises(AssertionError):
            instance.test_api_gateway_info_has_id(api_gateway_info)


class TestLayer6DeploymentCapabilityTestsExecution:
    """Tests that execute Layer6DeploymentCapabilityTests methods."""

    def test_can_get_lambda_function_configuration_success_with_functions(self):
        """Test test_can_get_lambda_function_configuration with functions."""
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_functions.return_value = {
            "Functions": [{"FunctionName": "my-function"}]
        }
        mock_client.get_function_configuration.return_value = {"FunctionName": "my-function"}
        assert instance.test_can_get_lambda_function_configuration(mock_client) is None
        mock_client.get_function_configuration.assert_called_once()

    def test_can_get_lambda_function_configuration_success_no_functions(self):
        """Test test_can_get_lambda_function_configuration with no functions."""
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_functions.return_value = {"Functions": []}
        assert instance.test_can_get_lambda_function_configuration(mock_client) is None
        mock_client.get_function_configuration.assert_not_called()

    def test_can_get_lambda_function_configuration_fails_on_access_denied(self):
        """Test test_can_get_lambda_function_configuration fails on AccessDeniedException."""
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_functions.return_value = {
            "Functions": [{"FunctionName": "my-function"}]
        }
        mock_client.get_function_configuration.side_effect = _create_client_error(
            "AccessDeniedException"
        )
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_get_lambda_function_configuration(mock_client)

    def test_can_get_lambda_function_configuration_reraises_other_errors(self):
        """Test test_can_get_lambda_function_configuration re-raises other errors."""
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_functions.return_value = {
            "Functions": [{"FunctionName": "my-function"}]
        }
        mock_client.get_function_configuration.side_effect = _create_client_error(
            "InternalError"
        )
        with pytest.raises(ClientError):
            instance.test_can_get_lambda_function_configuration(mock_client)

    def test_can_create_log_group_dry_run_success(self):
        """Test test_can_create_log_group_dry_run with successful call."""
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        assert instance.test_can_create_log_group_dry_run(mock_client) is None

    def test_can_create_log_group_dry_run_fails_on_access_denied(self):
        """Test test_can_create_log_group_dry_run fails on AccessDeniedException."""
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.describe_log_groups.side_effect = _create_client_error(
            "AccessDeniedException"
        )
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_create_log_group_dry_run(mock_client)

    def test_can_create_log_group_dry_run_reraises_other_errors(self):
        """Test test_can_create_log_group_dry_run re-raises other errors."""
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.describe_log_groups.side_effect = _create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_create_log_group_dry_run(mock_client)

    def test_can_get_iam_role_details_success_with_roles(self):
        """Test test_can_get_iam_role_details with roles."""
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_roles.return_value = {"Roles": [{"RoleName": "my-role"}]}
        mock_client.get_role.return_value = {"Role": {"RoleName": "my-role"}}
        assert instance.test_can_get_iam_role_details(mock_client) is None
        mock_client.get_role.assert_called_once()

    def test_can_get_iam_role_details_success_no_roles(self):
        """Test test_can_get_iam_role_details with no roles."""
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_roles.return_value = {"Roles": []}
        assert instance.test_can_get_iam_role_details(mock_client) is None
        mock_client.get_role.assert_not_called()

    def test_can_get_iam_role_details_fails_on_access_denied(self):
        """Test test_can_get_iam_role_details fails on AccessDenied."""
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_roles.return_value = {"Roles": [{"RoleName": "my-role"}]}
        mock_client.get_role.side_effect = _create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_get_iam_role_details(mock_client)

    def test_can_get_iam_role_details_reraises_other_errors(self):
        """Test test_can_get_iam_role_details re-raises other errors."""
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_roles.return_value = {"Roles": [{"RoleName": "my-role"}]}
        mock_client.get_role.side_effect = _create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_get_iam_role_details(mock_client)
