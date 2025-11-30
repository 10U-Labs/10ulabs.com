import json


def test_ecr_image_architecture_matches_task_definition(ecr_client, ecs_client, config, ecr_has_latest_tag):
    repository_name = config["ecr_repository_name"]
    result = True
    if not ecr_has_latest_tag:
        result = True
    else:
        ecr_response = ecr_client.batch_get_image(
            repositoryName=repository_name,
            imageIds=[{'imageTag': 'latest'}],
            acceptedMediaTypes=['application/vnd.oci.image.index.v1+json', 'application/vnd.docker.distribution.manifest.v2+json']
        )
        manifest_text = ecr_response['images'][0]['imageManifest']
        manifest = json.loads(manifest_text)
        ecs_response = ecs_client.list_task_definitions(familyPrefix='github-runner', status='ACTIVE')
        task_def_arn = ecs_response['taskDefinitionArns'][-1]
        task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
        task_arch = task_def['taskDefinition']['runtimePlatform']['cpuArchitecture'].lower()
        image_archs = [m.get('platform', {}).get('architecture', '').lower() for m in manifest.get('manifests', [])]
        result = task_arch in image_archs if image_archs else True
    assert result is True
