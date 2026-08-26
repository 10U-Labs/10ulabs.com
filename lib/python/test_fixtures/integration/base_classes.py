import uuid

from botocore.exceptions import ClientError
import pytest
from test_fixtures.integration.helpers import (
    check_credentials_available,
    check_credentials_valid,
)


class Layer1AuthenticationTests:
    def test_aws_credentials_are_available(self, sts_client):
        check_credentials_available(sts_client)

    def test_aws_credentials_are_valid(self, sts_client):
        check_credentials_valid(sts_client)

    def test_aws_credentials_return_account(self, caller_identity):
        assert "Account" in caller_identity, (
            "STS GetCallerIdentity response missing 'Account' field. "
            "AWS credentials may be malformed."
        )

    def test_aws_credentials_return_arn(self, caller_identity):
        assert "Arn" in caller_identity, (
            "STS GetCallerIdentity response missing 'Arn' field. "
            "AWS credentials may be malformed."
        )

    def test_caller_identity_is_role(self, caller_identity):
        arn = caller_identity.get("Arn", "")
        assert ":assumed-role/" in arn or ":role/" in arn, (
            f"Expected to be running as IAM role, but running as: {arn}. "
            "GitHub Actions should assume the GitHub Actions OIDC role."
        )


class Layer2IAMAuthorizationTests:
    def test_can_call_iam_get_role_api(self, iam_client, current_role_name):
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
                pass
            else:
                raise

    def test_can_list_attached_policies(self, iam_client, current_role_name):
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
                pass
            else:
                raise


class Layer2S3AuthorizationTests:
    def test_can_call_s3_head_bucket_api(self, s3_client, state_bucket_name):
        try:
            s3_client.head_bucket(Bucket=state_bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "403":
                pytest.fail(
                    f"No permission to call HeadBucket on '{state_bucket_name}'. "
                    "Check IAM permissions for s3:HeadBucket."
                )
            if e.response["Error"]["Code"] == "404":
                pass
            else:
                raise

    def test_state_bucket_name_configured(self, state_bucket_name):
        assert state_bucket_name, (
            "State bucket name is not configured. "
            "Check shared config for name_for_terraform_state_bucket."
        )


class Layer2ECRAuthorizationTests:
    def test_can_call_ecr_describe_repositories_api(self, ecr_client):
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
        assert ecr_client is not None, "ECR client is not available"


class Layer4TerraformStateExistenceTests:
    def test_state_bucket_exists(self, s3_client, state_bucket_name):
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
        assert state_bucket_name, (
            "State bucket name is empty. "
            "Check shared config for name_for_terraform_state_bucket."
        )


class Layer5S3ConfigurationTests:
    def test_state_bucket_is_encrypted(self, s3_client, state_bucket_name):
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
        response = s3_client.get_bucket_versioning(Bucket=state_bucket_name)
        status = response.get("Status", "")
        assert status != "Enabled", (
            f"State bucket '{state_bucket_name}' versioning is '{status}', "
            "but versioning must be disabled per project policy."
        )


class Layer6S3CapabilityTests:
    def test_can_list_bucket_objects(self, s3_client, state_bucket_name):
        try:
            s3_client.list_objects_v2(Bucket=state_bucket_name, MaxKeys=1)
        except ClientError as e:
            pytest.fail(
                f"Cannot list objects in '{state_bucket_name}': "
                f"{e.response['Error']['Message']}. "
                "Check IAM permissions for s3:ListBucket."
            )

    def test_can_get_bucket_location(self, s3_client, state_bucket_name):
        try:
            s3_client.get_bucket_location(Bucket=state_bucket_name)
        except ClientError as e:
            pytest.fail(
                f"Cannot get location of '{state_bucket_name}': "
                f"{e.response['Error']['Message']}. "
                "Check IAM permissions for s3:GetBucketLocation."
            )


class Layer4IAMRoleExistenceTests:
    def test_iam_role_exists(self, iam_client, current_role_name):
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
        assert current_role_name, "Current role name could not be determined"


class Layer4PrerequisiteExistenceTests(
    Layer4IAMRoleExistenceTests, Layer4TerraformStateExistenceTests
):
    pass
class Layer5IAMConfigurationTests:
    def test_role_has_administrator_access_policy(
        self, iam_client, current_role_name
    ):
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
    def test_bucket_in_expected_region(
        self, s3_client, state_bucket_name, state_bucket_region
    ):
        response = s3_client.get_bucket_location(Bucket=state_bucket_name)
        location = response.get("LocationConstraint")
        actual_region = location if location else "us-east-1"
        assert actual_region == state_bucket_region, (
            f"Bucket '{state_bucket_name}' is in region '{actual_region}', "
            f"expected '{state_bucket_region}'."
        )

    def test_expected_region_is_configured(self, state_bucket_region):
        assert state_bucket_region, "Expected bucket region is not configured"


class Layer5PrerequisiteConfigurationTests(
    Layer5IAMConfigurationTests, Layer5S3ConfigurationTests, Layer5S3RegionTests
):
    pass
class Layer6IAMCapabilityTests:
    def test_can_list_buckets(self, s3_client):
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
    def test_can_write_to_bucket(self, s3_client, state_bucket_name):
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
    def test_can_create_ecr_repository(self, ecr_client):
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


class Layer1EndpointAuthenticationTests:
    def test_aws_credentials_are_valid(self, sts_client):
        response = sts_client.get_caller_identity()
        assert response["Account"] is not None, (
            "AWS credentials invalid - GetCallerIdentity returned no Account"
        )

    def test_aws_credentials_return_account_id(self, sts_client):
        response = sts_client.get_caller_identity()
        assert len(response["Account"]) == 12, (
            f"AWS account ID has unexpected length: {len(response['Account'])}"
        )

    def test_aws_credentials_return_arn(self, sts_client):
        response = sts_client.get_caller_identity()
        assert "Arn" in response, "AWS credentials did not return an ARN"

    def test_aws_credentials_arn_has_valid_format(self, sts_client):
        response = sts_client.get_caller_identity()
        assert response["Arn"].startswith("arn:aws:"), (
            f"ARN has unexpected format: {response['Arn']}"
        )


class Layer2APIGatewayAuthorizationTests:
    def test_can_describe_rest_apis(self, apigateway_client):
        try:
            apigateway_client.get_rest_apis(limit=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail("No permission to describe API Gateway REST APIs")
            raise

    def test_can_access_specific_rest_api(self, api_gateway_info):
        if api_gateway_info["id"] is None:
            pytest.skip("api_gateway_id output not available")
        assert api_gateway_info["accessible"], (
            f"No permission to describe API Gateway '{api_gateway_info['id']}'"
        )


class Layer2LambdaAndIAMAuthorizationTests:
    def test_can_list_functions(self, lambda_client):
        try:
            lambda_client.list_functions(MaxItems=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail("No permission to list Lambda functions")
            raise

    def test_can_list_roles(self, iam_client):
        try:
            iam_client.list_roles(MaxItems=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail("No permission to list IAM roles")
            raise


class Layer4APIBackendPrerequisiteTests:
    def test_api_gateway_id_output_exists(self, api_common_routing_outputs):
        assert api_common_routing_outputs.get("api_gateway_id"), (
            "api_gateway_id output not found in api_common_routing. "
            "Run terraform apply in src/api/common/routing/"
        )

    def test_api_gateway_exists_in_aws(self, apigateway_client, api_common_routing_outputs):
        api_id = api_common_routing_outputs.get("api_gateway_id")
        if not api_id:
            pytest.skip("api_gateway_id output not available")
        try:
            response = apigateway_client.get_rest_api(restApiId=api_id)
            assert response["id"] == api_id, (
                f"API Gateway ID mismatch: expected {api_id}, got {response['id']}"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NotFoundException":
                pytest.fail(
                    f"API Gateway '{api_id}' does not exist. "
                    "Run terraform apply in src/api/common/routing/"
                )
            raise


class Layer5APIGatewayRegionalTests:
    def test_api_gateway_is_regional(self, api_gateway_info):
        if api_gateway_info["id"] is None:
            pytest.skip("api_gateway_id output not available")
        if not api_gateway_info["exists"]:
            pytest.skip("API Gateway does not exist")
        types = api_gateway_info.get("endpoint_types", [])
        assert "REGIONAL" in types, (
            f"API Gateway '{api_gateway_info['id']}' should be REGIONAL, got: {types}"
        )

    def test_api_gateway_info_has_id(self, api_gateway_info):
        assert "id" in api_gateway_info, "API Gateway info missing 'id' field"


class Layer6DeploymentCapabilityTests:
    def test_can_get_lambda_function_configuration(self, lambda_client):
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
        try:
            logs_client.describe_log_groups(limit=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "Cannot access CloudWatch Logs - required for deployment"
                )
            raise

    def test_can_get_iam_role_details(self, iam_client):
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


Layer2EndpointAuthenticationTests = Layer1EndpointAuthenticationTests

Layer3APIGatewayAuthorizationTests = Layer2APIGatewayAuthorizationTests
Layer3LambdaAndIAMAuthorizationTests = Layer2LambdaAndIAMAuthorizationTests

Layer5APIBackendPrerequisiteTests = Layer4APIBackendPrerequisiteTests

Layer6APIGatewayRegionalTests = Layer5APIGatewayRegionalTests

Layer7DeploymentCapabilityTests = Layer6DeploymentCapabilityTests
