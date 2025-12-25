"""Shared base classes for 6-layer pre-deployment integration tests.

The 6-layer testing model:
- Layer 1: Authentication - Valid credentials exist
- Layer 2: Authorization - Permission to inspect resources
- Layer 3: State - Terraform state matches AWS reality
- Layer 4: Existence - Required resources exist
- Layer 5: Configuration - Resources configured correctly
- Layer 6: Capability - Can perform required operations

Usage:
    # In your test file:
    from test_fixtures.integration import Layer1AuthenticationTests

    class TestAWSAuthentication(Layer1AuthenticationTests):
        pass  # Inherits all base tests
"""

from botocore.exceptions import ClientError, NoCredentialsError
import pytest


class Layer1AuthenticationTests:
    """Layer 1: Verify AWS credentials are valid.

    Inherit from this class to get standard authentication tests.
    All tests use fixtures from test_fixtures.aws.
    """

    def test_aws_credentials_are_available(self, sts_client):
        """Verify AWS credentials are configured."""
        try:
            sts_client.get_caller_identity()
        except NoCredentialsError:
            pytest.fail(
                "No AWS credentials found. "
                "Configure credentials via environment variables, "
                "~/.aws/credentials, or IAM role."
            )

    def test_aws_credentials_are_valid(self, sts_client):
        """Verify we can call sts:GetCallerIdentity."""
        try:
            sts_client.get_caller_identity()
        except ClientError as e:
            pytest.fail(
                f"Failed to call sts:GetCallerIdentity: "
                f"{e.response['Error']['Message']}. "
                "Check AWS credentials are valid and not expired."
            )

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

    def test_state_bucket_versioning_enabled(self, s3_client, state_bucket_name):
        """Verify the state bucket has versioning enabled."""
        response = s3_client.get_bucket_versioning(Bucket=state_bucket_name)
        status = response.get("Status", "")
        assert status == "Enabled", (
            f"State bucket '{state_bucket_name}' versioning is '{status}', "
            "expected 'Enabled'. Enable versioning for state recovery."
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


class Layer4PrerequisiteExistenceTests(
    Layer4IAMRoleExistenceTests, Layer4TerraformStateExistenceTests
):
    """Layer 4: Verify prerequisite resources exist.

    Combined tests for IAM role and terraform state bucket existence.
    """

    pass


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


class Layer5PrerequisiteConfigurationTests(
    Layer5IAMConfigurationTests, Layer5S3ConfigurationTests, Layer5S3RegionTests
):
    """Layer 5: Verify prerequisite resources are configured correctly.

    Combined tests for IAM role and S3 bucket configuration.
    """

    pass


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
        import uuid
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
        import uuid
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
        import uuid
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
        import uuid
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


# =============================================================================
# Factory functions for creating test classes
# =============================================================================


def create_layer1_authentication_tests():
    """Create Layer 1 authentication test class.

    Returns a test class with standard AWS credential verification tests.
    Used by ecs_runner, image_for_ecs_runners, and similar endpoints.

    Returns:
        Test class with Layer 1 authentication tests
    """

    class TestAWSAuthentication:
        """Layer 1: Authentication tests - Verify AWS credentials."""

        def test_credentials_available(self, sts_client):
            """Verify AWS credentials are configured."""
            assert sts_client is not None, (
                "No AWS credentials found. Configure via environment variables, "
                "~/.aws/credentials, or IAM role."
            )

        def test_can_call_sts_api(self, sts_client):
            """Verify credentials are valid by calling STS."""
            try:
                response = sts_client.get_caller_identity()
                assert response.get("Account"), "STS returned no account ID"
            except NoCredentialsError:
                pytest.fail(
                    "No AWS credentials found. "
                    "Configure credentials via environment variables, "
                    "~/.aws/credentials, or IAM role."
                )
            except ClientError as e:
                pytest.fail(
                    f"Credentials invalid or expired: {e.response['Error']['Message']}"
                )

        def test_identity_has_arn(self, sts_client):
            """Verify identity response has Arn."""
            response = sts_client.get_caller_identity()
            assert "Arn" in response, "STS response missing Arn field"

    return TestAWSAuthentication


def create_layer6_capability_tests(
    include_lambda: bool = True,
    include_iam: bool = True,
    include_ssm: bool = False,
    include_dynamodb: bool = False,
    include_logs: bool = False,
    include_s3: bool = False,
):
    """Create Layer 6 deployment capability test class.

    Args:
        include_lambda: Include Lambda list functions test
        include_iam: Include IAM list roles test
        include_ssm: Include SSM describe parameters test
        include_dynamodb: Include DynamoDB list tables test
        include_logs: Include CloudWatch logs describe test
        include_s3: Include S3 list buckets test

    Returns:
        Test class with Layer 6 capability tests
    """

    class TestDeploymentCapabilities:
        """Layer 6: Verify deployment capabilities."""

        pass

    if include_lambda:

        def test_can_list_lambda_functions(self, lambda_client):
            """Verify we can list Lambda functions (required for deployment)."""
            try:
                lambda_client.list_functions(MaxItems=1)
            except ClientError as e:
                pytest.fail(
                    f"Cannot list Lambda functions, deployment will fail: {e}"
                )

        TestDeploymentCapabilities.test_can_list_lambda_functions = (
            test_can_list_lambda_functions
        )

    if include_iam:

        def test_can_list_iam_roles(self, iam_client):
            """Verify we can list IAM roles (required for deployment)."""
            try:
                iam_client.list_roles(MaxItems=1)
            except ClientError as e:
                pytest.fail(
                    f"Cannot list IAM roles, deployment will fail: {e}"
                )

        TestDeploymentCapabilities.test_can_list_iam_roles = test_can_list_iam_roles

    if include_ssm:

        def test_can_describe_ssm_parameters(self, ssm_client):
            """Verify we can describe SSM parameters (required for deployment)."""
            try:
                ssm_client.describe_parameters(MaxResults=1)
            except ClientError as e:
                pytest.fail(
                    f"Cannot describe SSM parameters, deployment will fail: {e}"
                )

        TestDeploymentCapabilities.test_can_describe_ssm_parameters = (
            test_can_describe_ssm_parameters
        )

    if include_dynamodb:

        def test_can_list_dynamodb_tables(self, dynamodb_client):
            """Verify we can list DynamoDB tables (required for deployment)."""
            try:
                dynamodb_client.list_tables(Limit=1)
            except ClientError as e:
                pytest.fail(
                    f"Cannot list DynamoDB tables, deployment will fail: {e}"
                )

        TestDeploymentCapabilities.test_can_list_dynamodb_tables = (
            test_can_list_dynamodb_tables
        )

    if include_logs:

        def test_can_list_log_groups(self, logs_client):
            """Verify we can list CloudWatch log groups (required for deployment)."""
            try:
                logs_client.describe_log_groups(limit=1)
            except ClientError as e:
                pytest.fail(
                    f"Cannot list CloudWatch log groups, deployment will fail: {e}"
                )

        TestDeploymentCapabilities.test_can_list_log_groups = test_can_list_log_groups

    if include_s3:

        def test_can_list_s3_buckets(self, s3_client):
            """Verify we can list S3 buckets (required for deployment)."""
            try:
                s3_client.list_buckets()
            except ClientError as e:
                pytest.fail(
                    f"Cannot list S3 buckets, deployment will fail: {e}"
                )

        TestDeploymentCapabilities.test_can_list_s3_buckets = test_can_list_s3_buckets

    return TestDeploymentCapabilities


def create_layer2_s3_authorization_tests():
    """Create Layer 2 S3 authorization tests.

    Tests permission to call s3:HeadBucket on the state bucket.
    Requires `s3_client` and `state_bucket_name` fixtures.

    Returns:
        Test class with S3 authorization tests
    """

    class TestS3Authorization:
        """Layer 2: Verify S3 authorization."""

        def test_can_call_s3_head_bucket(self, s3_client, state_bucket_name):
            """Verify permission to call s3:HeadBucket on state bucket."""
            try:
                s3_client.head_bucket(Bucket=state_bucket_name)
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code in ("403", "AccessDenied"):
                    pytest.fail(
                        f"No permission to call s3:HeadBucket on '{state_bucket_name}'"
                    )
                # 404 means bucket doesn't exist but we have permission to check - OK
                if error_code != "404":
                    raise

    return TestS3Authorization


def create_ecs_runner_outputs_tests():
    """Create tests for ECS runner terraform outputs existence.

    Tests that ecs_runner terraform outputs are accessible.
    Requires `ecs_runner_outputs` fixture.

    Returns:
        Test class with ECS runner output tests
    """

    class TestECSRunnerOutputs:
        """Verify ecs_runner terraform outputs are accessible."""

        def test_cluster_arn_output_exists(self, ecs_runner_outputs):
            """Verify cluster_arn output is available."""
            assert ecs_runner_outputs.get("cluster_arn"), (
                "cluster_arn output not found in ecs_runner. "
                "Run terraform apply in src/api/endpoints/ecs_runner/"
            )

        def test_cluster_name_output_exists(self, ecs_runner_outputs):
            """Verify cluster_name output is available."""
            assert ecs_runner_outputs.get("cluster_name"), (
                "cluster_name output not found in ecs_runner. "
                "Run terraform apply in src/api/endpoints/ecs_runner/"
            )

        def test_lambda_function_name_output_exists(self, ecs_runner_outputs):
            """Verify lambda_function_name output is available."""
            assert ecs_runner_outputs.get("lambda_function_name"), (
                "lambda_function_name output not found in ecs_runner. "
                "Run terraform apply in src/api/endpoints/ecs_runner/"
            )

    return TestECSRunnerOutputs


def create_ecs_runner_lambda_existence_tests():
    """Create tests for ECS runner Lambda function existence.

    Used by endpoints that depend on the ECS runner Lambda function.
    Requires `lambda_client` and `ecs_runner_outputs` fixtures.

    Returns:
        Test class with ECS runner Lambda existence tests
    """

    class TestECSRunnerLambdaExistence:
        """Verify the ECS runner Lambda function exists in AWS."""

        def test_lambda_function_exists(self, lambda_client, ecs_runner_outputs):
            """Verify the ECS runner Lambda function exists."""
            function_name = ecs_runner_outputs.get("lambda_function_name")
            if not function_name:
                pytest.skip("lambda_function_name output not available")
            try:
                lambda_client.get_function(FunctionName=function_name)
            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    pytest.fail(
                        f"Lambda function '{function_name}' does not exist. "
                        "Run terraform apply in src/api/endpoints/ecs_runner/"
                    )
                raise

        def test_lambda_function_is_active(self, lambda_client, ecs_runner_outputs):
            """Verify the ECS runner Lambda function is active."""
            function_name = ecs_runner_outputs.get("lambda_function_name")
            if not function_name:
                pytest.skip("lambda_function_name output not available")
            try:
                response = lambda_client.get_function(FunctionName=function_name)
                state = response["Configuration"]["State"]
                assert state == "Active", (
                    f"Lambda function '{function_name}' is not active (state: {state}). "
                    "Check Lambda function configuration."
                )
            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    pytest.skip("Lambda function does not exist")
                raise

    return TestECSRunnerLambdaExistence


def create_lambda_api_gateway_wiring_tests(
    function_name_config_key: str,
    default_function_name: str,
):
    """Create Lambda API Gateway wiring tests for an endpoint.

    Creates a test class that verifies:
    - Lambda has API Gateway invoke permission
    - Lambda has IAM role attached
    - Lambda role follows naming pattern

    Args:
        function_name_config_key: Config key for function name (e.g., 'health_handler_function_name')
        default_function_name: Default function name if not in config

    Returns:
        Test class with Lambda wiring tests
    """

    class TestLambdaWiring:
        """Layer 3: Verify Lambda is wired to API Gateway and has correct role."""

        def test_handler_has_api_gateway_permission(self, lambda_client, config):
            """Verify Lambda has permission to be invoked by API Gateway."""
            function_name = config.get(function_name_config_key, default_function_name)
            try:
                response = lambda_client.get_policy(FunctionName=function_name)
                policy = response.get("Policy", "")
                # Check that API Gateway has permission to invoke
                assert "apigateway.amazonaws.com" in policy, (
                    f"Lambda '{function_name}' missing API Gateway invoke permission"
                )
            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    pytest.fail(
                        f"Lambda '{function_name}' has no resource policy - "
                        "API Gateway cannot invoke it"
                    )
                raise

        def test_handler_has_role_attached(self, lambda_client, config):
            """Verify Lambda function has IAM role attached."""
            function_name = config.get(function_name_config_key, default_function_name)
            response = lambda_client.get_function(FunctionName=function_name)
            role_arn = response["Configuration"].get("Role", "")
            assert role_arn, f"Lambda '{function_name}' has no IAM role attached"

        def test_handler_role_follows_naming_pattern(self, lambda_client, config):
            """Verify Lambda role ARN follows expected naming pattern."""
            function_name = config.get(function_name_config_key, default_function_name)
            response = lambda_client.get_function(FunctionName=function_name)
            role_arn = response["Configuration"].get("Role", "")
            expected_role_suffix = f"{function_name}ServiceRole"
            assert expected_role_suffix in role_arn, (
                f"Lambda role ARN '{role_arn}' doesn't match expected pattern "
                f"containing '{expected_role_suffix}'"
            )

    return TestLambdaWiring


def create_lambda_iam_wiring_tests(
    function_name_config_key: str,
    default_function_name: str,
    check_basic_execution: bool = True,
    check_lambda_trust: bool = True,
):
    """Create Lambda IAM policy wiring tests for an endpoint.

    Creates a test class that verifies IAM role policies are properly configured.

    Args:
        function_name_config_key: Config key for function name
        default_function_name: Default function name if not in config
        check_basic_execution: Whether to check for basic execution policy
        check_lambda_trust: Whether to check Lambda can assume the role

    Returns:
        Test class with IAM policy wiring tests
    """

    class TestIAMPolicyWiring:
        """Layer 3: Verify IAM role has required policies attached."""

        pass

    if check_basic_execution:
        def test_handler_role_has_basic_execution_policy(self, iam_client, config):
            """Verify IAM role has Lambda basic execution policy attached."""
            function_name = config.get(function_name_config_key, default_function_name)
            role_name = f"{function_name}ServiceRole"
            response = iam_client.list_attached_role_policies(RoleName=role_name)
            policy_arns = [p["PolicyArn"] for p in response["AttachedPolicies"]]
            basic_execution = (
                "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
            )
            assert basic_execution in policy_arns, (
                f"IAM role '{role_name}' missing AWSLambdaBasicExecutionRole policy. "
                f"Attached policies: {policy_arns}"
            )

        TestIAMPolicyWiring.test_handler_role_has_basic_execution_policy = (
            test_handler_role_has_basic_execution_policy
        )

    if check_lambda_trust:
        def test_handler_role_can_assume_lambda_service(self, iam_client, config):
            """Verify IAM role trust policy allows Lambda service to assume it."""
            function_name = config.get(function_name_config_key, default_function_name)
            role_name = f"{function_name}ServiceRole"
            response = iam_client.get_role(RoleName=role_name)
            assume_policy = response["Role"]["AssumeRolePolicyDocument"]
            statements = assume_policy.get("Statement", [])
            lambda_principals = [
                s for s in statements
                if s.get("Principal", {}).get("Service") == "lambda.amazonaws.com"
            ]
            assert lambda_principals, (
                f"IAM role '{role_name}' missing Lambda service in trust policy"
            )

        TestIAMPolicyWiring.test_handler_role_can_assume_lambda_service = (
            test_handler_role_can_assume_lambda_service
        )

    return TestIAMPolicyWiring


def create_www_shared_fixtures(
    include_cloudfront: bool = False,
    include_website_domain: bool = False,
):
    """Create www_shared terraform fixtures.

    Creates fixtures for accessing www_shared terraform outputs including
    bucket information and optionally CloudFront/website domain info.

    Args:
        include_cloudfront: Include CloudFront distribution ID in outputs
        include_website_domain: Include website domain name in outputs

    Returns:
        Tuple of (www_shared_terraform_initialized, www_shared_outputs) fixtures
    """
    from repo_utils import REPO_ROOT
    from test_fixtures.terraform import terraform_init, terraform_output

    WWW_SHARED_DIR = REPO_ROOT / "src" / "www" / "shared"

    @pytest.fixture(scope="session")
    def www_shared_terraform_initialized():
        """Initialize terraform for www_shared state access."""
        return terraform_init(WWW_SHARED_DIR)

    @pytest.fixture(scope="session")
    def www_shared_outputs(request):
        """Get www_shared terraform outputs."""
        if not request.getfixturevalue("www_shared_terraform_initialized"):
            pytest.skip("Terraform init failed for www_shared")
        outputs = {
            "bucket_name": terraform_output(WWW_SHARED_DIR, "bucket_name"),
            "bucket_arn": terraform_output(WWW_SHARED_DIR, "bucket_arn"),
        }
        if include_website_domain:
            outputs["website_domain_name"] = terraform_output(
                WWW_SHARED_DIR, "website_domain_name"
            )
        if include_cloudfront:
            outputs["cloudfront_distribution_id"] = terraform_output(
                WWW_SHARED_DIR, "cloudfront_distribution_id"
            )
        return outputs

    return www_shared_terraform_initialized, www_shared_outputs


def create_www_shared_s3_existence_tests():
    """Create S3 bucket existence tests for www_shared.

    Creates a test class that verifies the www_shared S3 bucket exists.
    Requires `s3_client` and `www_shared_outputs` fixtures.

    Returns:
        Test class with S3 bucket existence tests
    """

    class TestWWWSharedS3Existence:
        """Verify www_shared S3 bucket exists."""

        def test_bucket_name_output_exists(self, www_shared_outputs):
            """Verify bucket_name output is available."""
            assert www_shared_outputs.get("bucket_name"), (
                "bucket_name output not found in www_shared. "
                "Run terraform apply in src/www/shared/"
            )

        def test_s3_bucket_exists(self, s3_client, www_shared_outputs):
            """Verify the S3 bucket exists in AWS."""
            bucket_name = www_shared_outputs.get("bucket_name")
            if not bucket_name:
                pytest.skip("bucket_name output not available")
            try:
                s3_client.head_bucket(Bucket=bucket_name)
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    pytest.fail(
                        f"S3 bucket '{bucket_name}' does not exist. "
                        "Run terraform apply in src/www/shared/"
                    )
                raise

    return TestWWWSharedS3Existence


def _check_service_can_assume_role(trust_policy, service_name):
    """Check if a service can assume a role based on trust policy."""
    statements = trust_policy.get("Statement", [])
    for statement in statements:
        if statement.get("Effect") != "Allow":
            continue
        principals = statement.get("Principal", {})
        service = principals.get("Service", [])
        if isinstance(service, str):
            service = [service]
        if service_name in service:
            return True
    return False


def create_lambda_execution_role_wiring_tests(fixture_name: str = "lambda_function"):
    """Create Lambda execution role wiring tests.

    Creates a test class that verifies Lambda function has proper
    IAM execution role configuration and wiring.

    Args:
        fixture_name: Name of the fixture providing Lambda config
                     (e.g., 'lambda_function' or 'lambda_config')

    Returns:
        Test class with Lambda execution role wiring tests
    """

    class TestLambdaExecutionRole:
        """Verify Lambda execution role wiring."""

        def test_lambda_has_execution_role_key(self, request):
            """Verify Lambda function has Role key in configuration."""
            lambda_config = request.getfixturevalue(fixture_name)
            assert "Role" in lambda_config

        def test_lambda_has_execution_role_value(self, request):
            """Verify Lambda function execution role is not empty."""
            lambda_config = request.getfixturevalue(fixture_name)
            assert lambda_config.get("Role")

        def test_lambda_role_starts_with_iam_arn(self, request):
            """Verify Lambda execution role starts with IAM ARN prefix."""
            lambda_config = request.getfixturevalue(fixture_name)
            role_arn = lambda_config.get("Role", "")
            assert role_arn.startswith("arn:aws:iam::"), (
                f"Lambda role '{role_arn}' is not a valid IAM ARN"
            )

        def test_lambda_role_contains_role_path(self, request):
            """Verify Lambda execution role ARN contains :role/ path."""
            lambda_config = request.getfixturevalue(fixture_name)
            role_arn = lambda_config.get("Role", "")
            assert ":role/" in role_arn, (
                f"Lambda role '{role_arn}' does not appear to be a role ARN"
            )

        def test_lambda_role_exists(self, iam_client, request):
            """Verify the Lambda execution role exists in IAM."""
            lambda_config = request.getfixturevalue(fixture_name)
            role_arn = lambda_config.get("Role", "")
            role_name = role_arn.split("/")[-1] if "/" in role_arn else ""

            if not role_name:
                pytest.fail("Could not extract role name from Lambda configuration")

            try:
                response = iam_client.get_role(RoleName=role_name)
                assert response.get("Role") is not None
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchEntity":
                    pytest.fail(
                        f"Lambda execution role '{role_name}' does not exist in IAM. "
                        "The Lambda is configured with a non-existent role."
                    )
                raise

        def test_lambda_role_can_be_assumed_by_lambda(self, iam_client, request):
            """Verify the Lambda execution role has a trust policy for Lambda service."""
            lambda_config = request.getfixturevalue(fixture_name)
            role_arn = lambda_config.get("Role", "")
            role_name = role_arn.split("/")[-1] if "/" in role_arn else ""

            if not role_name:
                pytest.skip("Could not extract role name from Lambda configuration")

            try:
                response = iam_client.get_role(RoleName=role_name)
                trust_policy = response["Role"].get("AssumeRolePolicyDocument", {})
                can_assume = _check_service_can_assume_role(
                    trust_policy, "lambda.amazonaws.com"
                )

                assert can_assume, (
                    f"Role '{role_name}' trust policy does not allow Lambda to assume it"
                )
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchEntity":
                    pytest.skip(f"Role '{role_name}' does not exist")
                raise

    return TestLambdaExecutionRole


def create_sqs_fifo_queue_tests(
    queue_name_fixture: str,
    queue_description: str = "queue",
    fail_on_missing: bool = False,
):
    """Create SQS FIFO queue configuration tests.

    Creates a test class that verifies an SQS queue is properly
    configured as a FIFO queue with content-based deduplication.

    Args:
        queue_name_fixture: Name of the fixture providing the queue name
        queue_description: Human-readable description (e.g., "webhook queue", "DLQ")
        fail_on_missing: If True, fail when queue doesn't exist; if False, skip

    Returns:
        Test class with SQS FIFO queue tests
    """

    class TestSQSFIFOQueue:
        """Verify SQS queue is configured as FIFO with deduplication."""

        def test_queue_exists(self, sqs_client, request):
            """Verify the FIFO queue exists."""
            queue_name = request.getfixturevalue(queue_name_fixture)
            try:
                response = sqs_client.get_queue_url(QueueName=queue_name)
                assert response.get("QueueUrl"), (
                    f"{queue_description} {queue_name} URL not returned"
                )
            except ClientError as err:
                if err.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                    if fail_on_missing:
                        pytest.fail(
                            f"{queue_description} {queue_name} does not exist. "
                            "Deploy the endpoint first."
                        )
                    else:
                        pytest.skip(
                            f"{queue_description} {queue_name} not deployed yet. "
                            "Run terraform apply first."
                        )
                raise

        def test_queue_is_fifo(self, sqs_client, request):
            """Verify the queue is configured as FIFO."""
            queue_name = request.getfixturevalue(queue_name_fixture)
            try:
                queue_url = sqs_client.get_queue_url(QueueName=queue_name)["QueueUrl"]
                attrs = sqs_client.get_queue_attributes(
                    QueueUrl=queue_url,
                    AttributeNames=["FifoQueue"]
                )

                fifo_attr = attrs.get("Attributes", {}).get("FifoQueue")
                assert fifo_attr == "true", (
                    f"{queue_description} {queue_name} FifoQueue attribute is "
                    f"'{fifo_attr}', expected 'true'"
                )
            except ClientError as err:
                if err.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                    pytest.skip(f"{queue_description} {queue_name} not deployed yet")
                raise

        def test_queue_has_deduplication(self, sqs_client, request):
            """Verify the queue has content-based deduplication enabled."""
            queue_name = request.getfixturevalue(queue_name_fixture)
            try:
                queue_url = sqs_client.get_queue_url(QueueName=queue_name)["QueueUrl"]
                attrs = sqs_client.get_queue_attributes(
                    QueueUrl=queue_url,
                    AttributeNames=["ContentBasedDeduplication"]
                )

                dedup_attr = attrs.get("Attributes", {}).get("ContentBasedDeduplication")
                assert dedup_attr == "true", (
                    f"{queue_description} {queue_name} ContentBasedDeduplication is "
                    f"'{dedup_attr}', expected 'true'"
                )
            except ClientError as err:
                if err.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                    pytest.skip(f"{queue_description} {queue_name} not deployed yet")
                raise

    return TestSQSFIFOQueue


def create_simple_layer1_authentication_tests():
    """Create simple Layer 1 authentication tests.

    Simpler version with just two basic credential checks.
    Used by bootstrap, www_shared, and similar modules.

    Returns:
        Test class with simple authentication tests
    """

    class TestAWSAuthentication:
        """Layer 1: Authentication tests - Verify AWS credentials."""

        def test_aws_credentials_valid(self, sts_client):
            """Verify AWS credentials are valid."""
            response = sts_client.get_caller_identity()
            assert response["Account"] is not None

        def test_aws_credentials_not_expired(self, sts_client):
            """Verify AWS credentials are not expired."""
            response = sts_client.get_caller_identity()
            assert "Arn" in response

    return TestAWSAuthentication


def handle_ecr_error(error: ClientError, operation: str, repository_name: str) -> None:
    """Handle common ECR ClientError patterns.

    Args:
        error: The ClientError that was raised
        operation: ECR operation name (e.g., "ecr:ListImages")
        repository_name: Name of the ECR repository

    Raises:
        pytest.skip: If repository doesn't exist
        pytest.fail: If access is denied
        ClientError: Re-raises for other error codes
    """
    error_code = error.response["Error"]["Code"]
    if error_code == "RepositoryNotFoundException":
        pytest.skip("Repository does not exist")
    if error_code == "AccessDeniedException":
        pytest.fail(
            f"No permission to call {operation} on '{repository_name}'. "
            "This is required to manage Docker images."
        )
    raise error


def create_security_group_existence_test(
    outputs_fixture: str,
    sg_id_key: str = "runner_security_group_id",
    terraform_path: str = "src/api/shared/runners",
):
    """Create a security group existence test method.

    Args:
        outputs_fixture: Name of the fixture providing terraform outputs
        sg_id_key: Key in outputs containing the security group ID
        terraform_path: Path to show in error message for terraform apply

    Returns:
        Test method that checks security group exists
    """
    def test_security_group_exists(self, ec2_client, request):
        """Verify the security group exists."""
        outputs = request.getfixturevalue(outputs_fixture)
        sg_id = outputs.get(sg_id_key)
        if not sg_id:
            pytest.skip(f"{sg_id_key} output not available")
        try:
            response = ec2_client.describe_security_groups(GroupIds=[sg_id])
            assert len(response["SecurityGroups"]) == 1, (
                f"Security group {sg_id} not found."
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidGroup.NotFound":
                pytest.fail(
                    f"Security group {sg_id} does not exist. "
                    f"Run: cd {terraform_path} && terraform apply"
                )
            raise
    return test_security_group_exists
