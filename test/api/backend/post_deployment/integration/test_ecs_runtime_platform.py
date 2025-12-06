"""Tests for ECS task definition runtime platform configuration."""
import pytest


def get_task_definition_or_skip(ecs_client):
    """Get the latest github-runner task definition or skip if none exist."""
    response = ecs_client.list_task_definitions(familyPrefix='github-runner', status='ACTIVE')
    if not response['taskDefinitionArns']:
        pytest.skip("ECS task definitions not deployed (managed by ecs_runner.yml workflow)")
    task_def_arn = response['taskDefinitionArns'][-1]
    return ecs_client.describe_task_definition(taskDefinition=task_def_arn)['taskDefinition']


def test_ecs_task_definition_has_runtime_platform(ecs_client):
    """Verify ECS task definition includes runtime platform."""
    task_def = get_task_definition_or_skip(ecs_client)
    assert 'runtimePlatform' in task_def


def test_ecs_task_definition_runtime_platform_not_none(ecs_client):
    """Verify runtime platform is not None."""
    task_def = get_task_definition_or_skip(ecs_client)
    assert task_def['runtimePlatform'] is not None


def test_ecs_task_definition_runtime_platform_has_cpu_architecture(ecs_client):
    """Verify runtime platform specifies CPU architecture."""
    task_def = get_task_definition_or_skip(ecs_client)
    assert 'cpuArchitecture' in task_def['runtimePlatform']


def test_ecs_task_definition_runtime_platform_has_operating_system_family(ecs_client):
    """Verify runtime platform specifies operating system family."""
    task_def = get_task_definition_or_skip(ecs_client)
    assert 'operatingSystemFamily' in task_def['runtimePlatform']


def test_ecs_task_definition_cpu_architecture_is_arm64(ecs_client):
    """Verify CPU architecture is ARM64."""
    task_def = get_task_definition_or_skip(ecs_client)
    assert task_def['runtimePlatform']['cpuArchitecture'] == 'ARM64'


def test_ecs_task_definition_operating_system_family_is_linux(ecs_client):
    """Verify operating system family is LINUX."""
    task_def = get_task_definition_or_skip(ecs_client)
    assert task_def['runtimePlatform']['operatingSystemFamily'] == 'LINUX'


def test_ecs_task_definition_has_cpu_value(ecs_client):
    """Verify task definition specifies CPU value."""
    task_def = get_task_definition_or_skip(ecs_client)
    assert 'cpu' in task_def


def test_ecs_task_definition_cpu_is_valid_fargate_value(ecs_client):
    """Verify CPU value is valid for Fargate."""
    task_def = get_task_definition_or_skip(ecs_client)
    assert task_def['cpu'] in ['256', '512', '1024', '2048', '4096']


def test_ecs_task_definition_has_memory_value(ecs_client):
    """Verify task definition specifies memory value."""
    task_def = get_task_definition_or_skip(ecs_client)
    assert 'memory' in task_def


def test_ecs_task_definition_memory_is_valid_for_cpu(ecs_client):
    """Verify memory value is valid for the configured CPU."""
    task_def = get_task_definition_or_skip(ecs_client)
    cpu = int(task_def['cpu'])
    memory = int(task_def['memory'])
    assert memory >= cpu * 2
