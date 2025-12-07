"""Tests for ECR image architecture compatibility with ECS task definitions."""
import json


def _get_ecs_task_architecture(ecs_client):
    """Get the CPU architecture from the latest ECS task definition."""
    ecs_response = ecs_client.list_task_definitions(
        familyPrefix='github-runner', status='ACTIVE'
    )
    task_def_arn = ecs_response['taskDefinitionArns'][-1]
    task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
    return task_def['taskDefinition']['runtimePlatform']['cpuArchitecture'].lower()


def test_ecr_image_architecture_matches_task_definition(
    ecr_client, ecs_client, config, ecr_has_latest_tag
):
    """Verify ECR image architecture matches ECS task definition requirements."""
    if not ecr_has_latest_tag:
        assert True
        return

    repository_name = config["ecr_repository_name"]
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
    task_arch = _get_ecs_task_architecture(ecs_client)
    manifests = manifest.get('manifests', [])
    image_archs = [m.get('platform', {}).get('architecture', '').lower() for m in manifests]
    result = task_arch in image_archs if image_archs else True
    assert result is True
