"""Base test classes for 6-layer pre-deployment integration tests.

The 6-layer testing model:
- Layer 1: Authentication - Valid credentials exist
- Layer 2: Authorization - Permission to inspect resources
- Layer 3: State - Terraform state matches AWS reality
- Layer 4: Existence - Required resources exist
- Layer 5: Configuration - Resources configured correctly
- Layer 6: Capability - Can perform required operations
"""
import uuid

from botocore.exceptions import ClientError
import pytest
from test_fixtures.integration.helpers import (
    check_credentials_available,
    check_credentials_valid,
)


class Layer1AuthenticationTests:
    """Layer 1: Verify AWS credentials are valid.

    Inherit from this class to get standard authentication tests.
    All tests use fixtures from test_fixtures.aws.
    """

    def test_aws_credentials_are_available(self, sts_client):
        """Verify AWS credentials are configured."""
        check_credentials_available(sts_client)

    def test_aws_credentials_are_valid(self, sts_client):
        """Verify we can call sts:GetCallerIdentity."""
        check_credentials_valid(sts_client)

    def test_aws_credentials_return_account(self, caller_identity):
        """Verify STS response contains Account."""
        assert "Account" in caller_identity, (
            "STS GetCallerIdentity response missing 'Account' field. "
            "AWS credentials may be malformed."
        )

    def test_aws_credentials_return_arn(self, caller_identity):
        """Verify STS response contains Arn."""
        assert "Arn" in caller_identity, (
            "STS GetCallerIdentity response missing 'Arn' field. "
            "AWS credentials may be malformed."
        )

    def test_caller_identity_is_role(self, caller_identity):
        """Verify we are running as an IAM role (not user)."""
        arn = caller_identity.get("Arn", "")
        assert ":assumed-role/" in arn or ":role/" in arn, (
            f"Expected to be running as IAM role, but running as: {arn}. "
            "GitHub Actions should assume the GitHub Actions OIDC role."
        )


class Layer2IAMAuthorizationTests:
    """Layer 2: Verify permission to inspect IAM roles.

    Inherit from this class to get standard IAM authorization tests.
    """

    def test_can_call_iam_get_role_api(self, iam_client, current_role_name):
        """Verify we have permission to call iam:GetRole."""
        if not current_role_name:
            pytest.skip("Could not determine current role name")
        try:
            iam_client.get_role(RoleName=current_role_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to call iam:GetRole on '{current_role_name}'. "
                    "The role may lack iam:GetRole permission for itself."
                )
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pass  # Role doesn't exist, but we have permission to check
            else:
                raise

    def test_can_list_attached_policies(self, iam_client, current_role_name):
        """Verify we have permission to call iam:ListAttachedRolePolicies."""
        if not current_role_name:
            pytest.skip("Could not determine current role name")
        try:
            iam_client.list_attached_role_policies(RoleName=current_role_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to call iam:ListAttachedRolePolicies "
                    f"on '{current_role_name}'."
                )
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pass  # Role doesn't exist, but we have permission to check
            else:
                raise


class Layer2S3AuthorizationTests:
    """Layer 2: Verify permission to inspect S3 buckets.

    Inherit from this class to get standard S3 authorization tests.
    Requires a `state_bucket_name` fixture.
    """

    def test_can_call_s3_head_bucket_api(self, s3_client, state_bucket_name):
        """Verify we have permission to call s3:HeadBucket."""
        try:
            s3_client.head_bucket(Bucket=state_bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "403":
                pytest.fail(
                    f"No permission to call HeadBucket on '{state_bucket_name}'. "
                    "Check IAM permissions for s3:HeadBucket."
                )
            if e.response["Error"]["Code"] == "404":
                pass  # Bucket doesn't exist, but we have permission to check
            else:
                raise

    def test_state_bucket_name_configured(self, state_bucket_name):
        """Verify state bucket name is configured."""
        assert state_bucket_name, (
            "State bucket name is not configured. "
            "Check shared config for name_for_terraform_state_bucket."
        )


class Layer2ECRAuthorizationTests:
    """Layer 2: Verify permission to inspect ECR repositories.

    Inherit from this class to get standard ECR authorization tests.
    """

    def test_can_call_ecr_describe_repositories_api(self, ecr_client):
        """Verify we have permission to call ecr:DescribeRepositories."""
        try:
            ecr_client.describe_repositories(maxResults=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call ecr:DescribeRepositories. "
                    "Check IAM permissions for ecr:DescribeRepositories."
                )
            raise

    def test_ecr_client_is_valid(self, ecr_client):
        """Verify ECR client is available and valid."""
        assert ecr_client is not None, "ECR client is not available"


class Layer4TerraformStateExistenceTests:
    """Layer 4: Verify Terraform state bucket exists.

    Inherit from this class to get standard state bucket existence tests.
    Requires `s3_client` and `state_bucket_name` fixtures.
    """

    def test_state_bucket_exists(self, s3_client, state_bucket_name):
        """Verify the Terraform state bucket exists."""
        try:
            s3_client.head_bucket(Bucket=state_bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                pytest.fail(
                    f"Terraform state bucket '{state_bucket_name}' does not exist. "
                    "Run bootstrap to create the state bucket."
                )
            raise

    def test_state_bucket_has_name(self, state_bucket_name):
        """Verify state bucket name is configured."""
        assert state_bucket_name, (
            "State bucket name is empty. "
            "Check shared config for name_for_terraform_state_bucket."
        )


class Layer5S3ConfigurationTests:
    """Layer 5: Verify S3 bucket configuration.

    Inherit from this class to get standard S3 configuration tests.
    Requires `s3_client` and `state_bucket_name` fixtures.
    """

    def test_state_bucket_is_encrypted(self, s3_client, state_bucket_name):
        """Verify the state bucket has encryption enabled."""
        try:
            response = s3_client.get_bucket_encryption(Bucket=state_bucket_name)
            rules = response.get("ServerSideEncryptionConfiguration", {}).get(
                "Rules", []
            )
            assert len(rules) > 0, (
                f"State bucket '{state_bucket_name}' has no encryption rules. "
                "Enable server-side encryption for security."
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ServerSideEncryptionConfigurationNotFoundError":
                pytest.fail(
                    f"State bucket '{state_bucket_name}' has no encryption configured. "
                    "Enable server-side encryption for security."
                )
            raise

    def test_state_bucket_versioning_disabled(self, s3_client, state_bucket_name):
        """Verify the state bucket has versioning disabled."""
        response = s3_client.get_bucket_versioning(Bucket=state_bucket_name)
        status = response.get("Status", "")
        assert status != "Enabled", (
            f"State bucket '{state_bucket_name}' versioning is '{status}', "
            "but versioning must be disabled per project policy."
        )


class Layer6S3CapabilityTests:
    """Layer 6: Verify S3 operational capabilities.

    Inherit from this class to get standard S3 capability tests.
    Requires `s3_client` and `state_bucket_name` fixtures.
    """

    def test_can_list_bucket_objects(self, s3_client, state_bucket_name):
        """Verify we can list objects in the state bucket."""
        try:
            s3_client.list_objects_v2(Bucket=state_bucket_name, MaxKeys=1)
        except ClientError as e:
            pytest.fail(
                f"Cannot list objects in '{state_bucket_name}': "
                f"{e.response['Error']['Message']}. "
                "Check IAM permissions for s3:ListBucket."
            )

    def test_can_get_bucket_location(self, s3_client, state_bucket_name):
        """Verify we can get the bucket location."""
        try:
            s3_client.get_bucket_location(Bucket=state_bucket_name)
        except ClientError as e:
            pytest.fail(
                f"Cannot get location of '{state_bucket_name}': "
                f"{e.response['Error']['Message']}. "
                "Check IAM permissions for s3:GetBucketLocation."
            )


class Layer4IAMRoleExistenceTests:
    """Layer 4: Verify IAM role exists.

    Inherit from this class to get standard IAM role existence tests.
    Requires `iam_client` and `current_role_name` fixtures.
    """

    def test_iam_role_exists(self, iam_client, current_role_name):
        """Verify the IAM role exists."""
        if not current_role_name:
            pytest.skip("Could not determine current role name")
        try:
            response = iam_client.get_role(RoleName=current_role_name)
            assert response["Role"]["RoleName"] == current_role_name
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.fail(
                    f"IAM role '{current_role_name}' does not exist. "
                    "Run terraform apply in src/bootstrap/"
                )
            raise

    def test_current_role_name_is_configured(self, current_role_name):
        """Verify current role name is determined."""
        assert current_role_name, "Current role name could not be determined"


class Layer4PrerequisiteExistenceTests(
    Layer4IAMRoleExistenceTests, Layer4TerraformStateExistenceTests
):
    """Layer 4: Verify prerequisite resources exist.

    Combined tests for IAM role and terraform state bucket existence.
    """


class Layer5IAMConfigurationTests:
    """Layer 5: Verify IAM role configuration.

    Inherit from this class to get standard IAM configuration tests.
    Requires `iam_client` and `current_role_name` fixtures.
    """

    def test_role_has_administrator_access_policy(
        self, iam_client, current_role_name
    ):
        """Verify the role has AdministratorAccess policy attached."""
        if not current_role_name:
            pytest.skip("Could not determine current role name")
        try:
            response = iam_client.list_attached_role_policies(
                RoleName=current_role_name
            )
            policy_names = [p["PolicyName"] for p in response["AttachedPolicies"]]
            assert "AdministratorAccess" in policy_names, (
                f"Role '{current_role_name}' missing AdministratorAccess policy. "
                f"Attached policies: {policy_names}"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.skip(
                    "Cannot verify - no permission to list attached policies"
                )
            raise

    def test_role_has_at_least_one_policy(self, iam_client, current_role_name):
        """Verify the role has at least one policy attached."""
        if not current_role_name:
            pytest.skip("Could not determine current role name")
        try:
            response = iam_client.list_attached_role_policies(
                RoleName=current_role_name
            )
            assert len(response["AttachedPolicies"]) > 0, (
                f"Role '{current_role_name}' has no attached policies"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.skip(
                    "Cannot verify - no permission to list attached policies"
                )
            raise


class Layer5S3RegionTests:
    """Layer 5: Verify S3 bucket region configuration.

    Inherit from this class to get standard S3 region tests.
    Requires `s3_client`, `state_bucket_name`, and `state_bucket_region` fixtures.
    """

    def test_bucket_in_expected_region(
        self, s3_client, state_bucket_name, state_bucket_region
    ):
        """Verify bucket is in the expected region."""
        response = s3_client.get_bucket_location(Bucket=state_bucket_name)
        # AWS returns None for us-east-1, otherwise the region name
        location = response.get("LocationConstraint")
        actual_region = location if location else "us-east-1"
        assert actual_region == state_bucket_region, (
            f"Bucket '{state_bucket_name}' is in region '{actual_region}', "
            f"expected '{state_bucket_region}'."
        )

    def test_expected_region_is_configured(self, state_bucket_region):
        """Verify expected bucket region is configured."""
        assert state_bucket_region, "Expected bucket region is not configured"


class Layer5PrerequisiteConfigurationTests(
    Layer5IAMConfigurationTests, Layer5S3ConfigurationTests, Layer5S3RegionTests
):
    """Layer 5: Verify prerequisite resources are configured correctly.

    Combined tests for IAM role and S3 bucket configuration.
    """


class Layer6IAMCapabilityTests:
    """Layer 6: Verify basic IAM/S3 listing capabilities.

    Inherit from this class to get standard IAM capability tests.
    Requires `s3_client` and `iam_client` fixtures.
    """

    def test_can_list_buckets(self, s3_client):
        """Verify we can call s3:ListBuckets (basic S3 permission check)."""
        try:
            s3_client.list_buckets()
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    "No permission to call s3:ListBuckets. "
                    "The role may lack S3 permissions required for terraform state."
                )
            raise

    def test_can_list_roles(self, iam_client):
        """Verify we can call iam:ListRoles (basic IAM permission check)."""
        try:
            iam_client.list_roles(MaxItems=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    "No permission to call iam:ListRoles. "
                    "The role may lack IAM permissions required for deployment."
                )
            raise


class Layer6S3WriteCapabilityTests:
    """Layer 6: Verify S3 write/delete capabilities.

    Inherit from this class to get S3 write capability tests.
    Requires `s3_client` and `state_bucket_name` fixtures.
    """

    def test_can_write_to_bucket(self, s3_client, state_bucket_name):
        """Verify we can write to the state bucket."""
        test_key = f".pre-deployment-test/{uuid.uuid4()}"
        try:
            s3_client.put_object(
                Bucket=state_bucket_name,
                Key=test_key,
                Body=b"pre-deployment-test"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to write to '{state_bucket_name}'. "
                    "Check IAM permissions for s3:PutObject."
                )
            raise
        finally:
            try:
                s3_client.delete_object(Bucket=state_bucket_name, Key=test_key)
            except ClientError:
                pass

    def test_can_delete_from_bucket(self, s3_client, state_bucket_name):
        """Verify we can delete objects from the state bucket."""
        test_key = f".pre-deployment-test/{uuid.uuid4()}"
        try:
            s3_client.put_object(
                Bucket=state_bucket_name,
                Key=test_key,
                Body=b"pre-deployment-test"
            )
            s3_client.delete_object(Bucket=state_bucket_name, Key=test_key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to delete from '{state_bucket_name}'. "
                    "Check IAM permissions for s3:DeleteObject."
                )
            raise
        finally:
            try:
                s3_client.delete_object(Bucket=state_bucket_name, Key=test_key)
            except ClientError:
                pass


class Layer6ECRCapabilityTests:
    """Layer 6: Verify ECR create/delete capabilities.

    Inherit from this class to get ECR capability tests.
    Requires `ecr_client` fixture.
    """

    def test_can_create_ecr_repository(self, ecr_client):
        """Verify we can create ECR repositories."""
        test_repo_name = f"pre-deployment-test-{uuid.uuid4().hex[:8]}"
        try:
            ecr_client.create_repository(repositoryName=test_repo_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call ecr:CreateRepository. "
                    "Check IAM permissions for ecr:CreateRepository."
                )
            raise
        finally:
            try:
                ecr_client.delete_repository(
                    repositoryName=test_repo_name,
                    force=True
                )
            except ClientError:
                pass

    def test_can_delete_ecr_repository(self, ecr_client):
        """Verify we can delete ECR repositories."""
        test_repo_name = f"pre-deployment-test-{uuid.uuid4().hex[:8]}"
        try:
            ecr_client.create_repository(repositoryName=test_repo_name)
            ecr_client.delete_repository(repositoryName=test_repo_name, force=True)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call ecr:DeleteRepository. "
                    "Check IAM permissions for ecr:DeleteRepository."
                )
            raise
        finally:
            try:
                ecr_client.delete_repository(
                    repositoryName=test_repo_name,
                    force=True
                )
            except ClientError:
                pass


# =============================================================================
# Endpoint-style test base classes (for diagnostics, health, contact, etc.)
# =============================================================================


class Layer1EndpointAuthenticationTests:
    """Layer 1: Verify AWS credentials are valid (endpoint-style).

    Simpler authentication tests that directly call STS without using
    caller_identity fixture. Used by diagnostics, health, and similar endpoints.
    """

    def test_aws_credentials_are_valid(self, sts_client):
        """Verify AWS credentials are valid by calling GetCallerIdentity."""
        response = sts_client.get_caller_identity()
        assert response["Account"] is not None, (
            "AWS credentials invalid - GetCallerIdentity returned no Account"
        )

    def test_aws_credentials_return_account_id(self, sts_client):
        """Verify AWS credentials return a valid account ID."""
        response = sts_client.get_caller_identity()
        assert len(response["Account"]) == 12, (
            f"AWS account ID has unexpected length: {len(response['Account'])}"
        )

    def test_aws_credentials_return_arn(self, sts_client):
        """Verify AWS credentials return an ARN."""
        response = sts_client.get_caller_identity()
        assert "Arn" in response, "AWS credentials did not return an ARN"

    def test_aws_credentials_arn_has_valid_format(self, sts_client):
        """Verify AWS credentials ARN has valid format."""
        response = sts_client.get_caller_identity()
        assert response["Arn"].startswith("arn:aws:"), (
            f"ARN has unexpected format: {response['Arn']}"
        )


class Layer2APIGatewayAuthorizationTests:
    """Layer 2: Verify permission to inspect API Gateway resources.

    Requires `apigateway_client` and `api_gateway_info` fixtures.
    """

    def test_can_describe_rest_apis(self, apigateway_client):
        """Verify permission to describe REST APIs."""
        try:
            apigateway_client.get_rest_apis(limit=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail("No permission to describe API Gateway REST APIs")
            raise

    def test_can_access_specific_rest_api(self, api_gateway_info):
        """Verify permission to describe specific REST API."""
        if api_gateway_info["id"] is None:
            pytest.skip("api_gateway_rest_api_id output not available")
        assert api_gateway_info["accessible"], (
            f"No permission to describe API Gateway '{api_gateway_info['id']}'"
        )


class Layer2LambdaAndIAMAuthorizationTests:
    """Layer 2: Verify permission to inspect Lambda and IAM resources.

    Requires `lambda_client` and `iam_client` fixtures.
    """

    def test_can_list_functions(self, lambda_client):
        """Verify permission to list Lambda functions."""
        try:
            lambda_client.list_functions(MaxItems=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail("No permission to list Lambda functions")
            raise

    def test_can_list_roles(self, iam_client):
        """Verify permission to list IAM roles."""
        try:
            iam_client.list_roles(MaxItems=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail("No permission to list IAM roles")
            raise


class Layer4APIBackendPrerequisiteTests:
    """Layer 4: Verify api_backend prerequisites exist.

    Requires `api_backend_outputs` and `apigateway_client` fixtures.
    """

    def test_api_gateway_rest_api_id_output_exists(self, api_backend_outputs):
        """Verify api_gateway_rest_api_id output is available from api_backend."""
        assert api_backend_outputs.get("api_gateway_rest_api_id"), (
            "api_gateway_rest_api_id output not found in api_backend. "
            "Run terraform apply in src/api/backend/"
        )

    def test_api_gateway_exists_in_aws(self, apigateway_client, api_backend_outputs):
        """Verify the API Gateway exists in AWS."""
        api_id = api_backend_outputs.get("api_gateway_rest_api_id")
        if not api_id:
            pytest.skip("api_gateway_rest_api_id output not available")
        try:
            response = apigateway_client.get_rest_api(restApiId=api_id)
            assert response["id"] == api_id, (
                f"API Gateway ID mismatch: expected {api_id}, got {response['id']}"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NotFoundException":
                pytest.fail(
                    f"API Gateway '{api_id}' does not exist. "
                    "Run terraform apply in src/api/backend/"
                )
            raise


class Layer5APIGatewayRegionalTests:
    """Layer 5: Verify API Gateway is REGIONAL endpoint type.

    Requires `api_gateway_info` fixture.
    """

    def test_api_gateway_is_regional(self, api_gateway_info):
        """Verify API Gateway endpoint type is REGIONAL."""
        if api_gateway_info["id"] is None:
            pytest.skip("api_gateway_rest_api_id output not available")
        if not api_gateway_info["exists"]:
            pytest.skip("API Gateway does not exist")
        types = api_gateway_info.get("endpoint_types", [])
        assert "REGIONAL" in types, (
            f"API Gateway '{api_gateway_info['id']}' should be REGIONAL, got: {types}"
        )

    def test_api_gateway_info_has_id(self, api_gateway_info):
        """Verify API Gateway info contains an ID."""
        assert "id" in api_gateway_info, "API Gateway info missing 'id' field"


class Layer6DeploymentCapabilityTests:
    """Layer 6: Verify capabilities to deploy Lambda, CloudWatch, and IAM.

    Requires `lambda_client`, `logs_client`, and `iam_client` fixtures.
    """

    def test_can_get_lambda_function_configuration(self, lambda_client):
        """Verify capability to get Lambda function configuration."""
        try:
            response = lambda_client.list_functions(MaxItems=1)
            functions = response.get("Functions", [])
            if functions:
                lambda_client.get_function_configuration(
                    FunctionName=functions[0]["FunctionName"]
                )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "Cannot get Lambda function configuration - required for deployment"
                )
            raise

    def test_can_create_log_group_dry_run(self, logs_client):
        """Verify capability to interact with CloudWatch Logs."""
        try:
            logs_client.describe_log_groups(limit=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "Cannot access CloudWatch Logs - required for deployment"
                )
            raise

    def test_can_get_iam_role_details(self, iam_client):
        """Verify capability to get IAM role details for deployment."""
        try:
            response = iam_client.list_roles(MaxItems=1)
            roles = response.get("Roles", [])
            if roles:
                iam_client.get_role(RoleName=roles[0]["RoleName"])
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    "Cannot get IAM role details - required for deployment"
                )
            raise
