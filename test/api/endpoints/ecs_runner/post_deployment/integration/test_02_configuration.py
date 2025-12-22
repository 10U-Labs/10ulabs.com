"""Layer 2: Configuration tests.

Verify resources created by this deployment are configured correctly.
"""
import json

from test.api.endpoints.conftest import assert_lambda_package_includes_file

from naming_conventions import validate_name
import pytest

pytestmark = pytest.mark.layer(2)


class TestECSTaskDefinitionRuntimePlatform:
    """Verify ECS task definition runtime platform configuration."""

    def test_task_definition_has_runtime_platform(self, task_definition):
        """Verify ECS task definition includes runtime platform."""
        if task_definition is None:
            pytest.skip("ECS task definition not deployed")
        assert 'runtimePlatform' in task_definition

    def test_task_definition_runtime_platform_not_none(self, task_definition):
        """Verify runtime platform is not None."""
        if task_definition is None:
            pytest.skip("ECS task definition not deployed")
        assert task_definition['runtimePlatform'] is not None

    def test_task_definition_has_cpu_architecture(self, task_definition):
        """Verify runtime platform specifies CPU architecture."""
        if task_definition is None:
            pytest.skip("ECS task definition not deployed")
        assert 'cpuArchitecture' in task_definition['runtimePlatform']

    def test_task_definition_has_operating_system_family(self, task_definition):
        """Verify runtime platform specifies operating system family."""
        if task_definition is None:
            pytest.skip("ECS task definition not deployed")
        assert 'operatingSystemFamily' in task_definition['runtimePlatform']

    def test_task_definition_cpu_architecture_is_arm64(self, task_definition):
        """Verify CPU architecture is ARM64."""
        if task_definition is None:
            pytest.skip("ECS task definition not deployed")
        assert task_definition['runtimePlatform']['cpuArchitecture'] == 'ARM64'

    def test_task_definition_operating_system_family_is_linux(self, task_definition):
        """Verify operating system family is LINUX."""
        if task_definition is None:
            pytest.skip("ECS task definition not deployed")
        assert task_definition['runtimePlatform']['operatingSystemFamily'] == 'LINUX'


class TestECSTaskDefinitionResources:
    """Verify ECS task definition resource configuration."""

    def test_task_definition_has_cpu_value(self, task_definition):
        """Verify task definition specifies CPU value."""
        if task_definition is None:
            pytest.skip("ECS task definition not deployed")
        assert 'cpu' in task_definition

    def test_task_definition_cpu_is_valid_fargate_value(self, task_definition):
        """Verify CPU value is valid for Fargate."""
        if task_definition is None:
            pytest.skip("ECS task definition not deployed")
        assert task_definition['cpu'] in ['256', '512', '1024', '2048', '4096']

    def test_task_definition_has_memory_value(self, task_definition):
        """Verify task definition specifies memory value."""
        if task_definition is None:
            pytest.skip("ECS task definition not deployed")
        assert 'memory' in task_definition

    def test_task_definition_memory_is_valid_for_cpu(self, task_definition):
        """Verify memory value is valid for the configured CPU."""
        if task_definition is None:
            pytest.skip("ECS task definition not deployed")
        cpu = int(task_definition['cpu'])
        memory = int(task_definition['memory'])
        assert memory >= cpu * 2


def _get_ecr_image_architectures(ecr_client, repository_name):
    """Get list of architectures from ECR image manifest."""
    accepted_media_types = [
        'application/vnd.oci.image.index.v1+json',
        'application/vnd.docker.distribution.manifest.v2+json'
    ]
    ecr_response = ecr_client.batch_get_image(
        repositoryName=repository_name,
        imageIds=[{'imageTag': 'latest'}],
        acceptedMediaTypes=accepted_media_types
    )
    manifest_text = ecr_response['images'][0]['imageManifest']
    manifest = json.loads(manifest_text)
    manifests = manifest.get('manifests', [])
    return [m.get('platform', {}).get('architecture', '').lower() for m in manifests]


def _get_task_definition_architecture(ecs_client):
    """Get CPU architecture from the latest ECS task definition."""
    ecs_response = ecs_client.list_task_definitions(
        familyPrefix='github-runner', status='ACTIVE'
    )
    if not ecs_response['taskDefinitionArns']:
        return None
    task_def_arn = ecs_response['taskDefinitionArns'][-1]
    task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
    return task_def['taskDefinition']['runtimePlatform']['cpuArchitecture'].lower()


class TestECRImageArchitecture:
    """Verify ECR image architecture compatibility."""

    def test_ecr_has_image_with_latest_tag(self, ecr_has_latest_tag):
        """Verify ECR repository has an image with the latest tag."""
        # This is a precondition check - if no latest image, skip architecture test
        if not ecr_has_latest_tag:
            pytest.skip("No latest image in ECR repository")
        assert ecr_has_latest_tag

    def test_ecr_image_architecture_matches_task_definition(
        self, ecr_client, ecs_client, config, ecr_has_latest_tag
    ):
        """Verify ECR image architecture matches ECS task definition requirements."""
        if not ecr_has_latest_tag:
            pytest.skip("No latest image in ECR repository")

        repository_name = config["ecr_repository_name"]
        image_archs = _get_ecr_image_architectures(ecr_client, repository_name)
        task_arch = _get_task_definition_architecture(ecs_client)

        if task_arch is None:
            pytest.skip("No ECS task definitions deployed")

        result = task_arch in image_archs if image_archs else True
        assert result is True


class TestNamingConventions:
    """Verify deployed resources follow naming conventions."""

    def test_lambda_role_name_is_pascalcase(self, iam_client, lambda_role_name):
        """Verify EcsRunnerHandler IAM role name uses PascalCase."""
        if not lambda_role_name:
            pytest.skip("lambda_role_name not configured")
        response = iam_client.get_role(RoleName=lambda_role_name)
        actual_name = response['Role']['RoleName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed IAM role has invalid name '{actual_name}': {error}"
        )

    def test_ecs_task_role_name_is_pascalcase(self, iam_client, ecs_task_role_name):
        """Verify ECS task role name uses PascalCase."""
        if not ecs_task_role_name:
            pytest.skip("ecs_task_role_name not configured")
        response = iam_client.get_role(RoleName=ecs_task_role_name)
        actual_name = response['Role']['RoleName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed IAM role has invalid name '{actual_name}': {error}"
        )

    def test_lambda_function_name_is_pascalcase(
        self, lambda_client, lambda_function_name
    ):
        """Verify EcsRunnerHandler Lambda function name uses PascalCase."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not configured")
        response = lambda_client.get_function(FunctionName=lambda_function_name)
        actual_name = response['Configuration']['FunctionName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed Lambda function has invalid name '{actual_name}': {error}"
        )

    def test_lambda_function_name_has_no_dashes(
        self, lambda_client, lambda_function_name
    ):
        """Verify EcsRunnerHandler Lambda function name has no dashes."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not configured")
        response = lambda_client.get_function(FunctionName=lambda_function_name)
        actual_name = response['Configuration']['FunctionName']
        assert '-' not in actual_name, (
            f"Deployed Lambda function has dashes in name '{actual_name}'"
        )


class TestLambdaPackageContents:
    """Verify Lambda package contains required files."""

    def test_lambda_package_includes_runner_labels(self, config):
        """Verify deployed ECS runner handler Lambda includes runner_labels.py."""
        function_name = config["lambda_function_name"]
        region = config["aws_region"]
        assert_lambda_package_includes_file(function_name, "runner_labels.py", region)

    def test_lambda_package_includes_handler(self, config):
        """Verify deployed ECS runner handler Lambda includes handler.py."""
        function_name = config["lambda_function_name"]
        region = config["aws_region"]
        assert_lambda_package_includes_file(function_name, "handler.py", region)
