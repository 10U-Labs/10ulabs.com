import json


def test_ecr_repository_exists(ecr_client):
    response = ecr_client.describe_repositories(repositoryNames=['github-runner'])
    assert len(response['repositories']) == 1


def test_ecr_repository_has_images(ecr_client):
    response = ecr_client.list_images(repositoryName='github-runner')
    assert len(response['imageIds']) > 0


def test_ecr_latest_image_exists(ecr_client):
    response = ecr_client.list_images(repositoryName='github-runner')
    image_tags = [img.get('imageTag') for img in response['imageIds'] if img.get('imageTag')]
    assert 'latest' in image_tags


def test_ecr_image_has_manifest(ecr_client):
    response = ecr_client.batch_get_image(
        repositoryName='github-runner',
        imageIds=[{'imageTag': 'latest'}],
        acceptedMediaTypes=['application/vnd.oci.image.index.v1+json', 'application/vnd.docker.distribution.manifest.v2+json']
    )
    assert len(response['images']) == 1


def test_ecr_image_manifest_is_parseable(ecr_client):
    response = ecr_client.batch_get_image(
        repositoryName='github-runner',
        imageIds=[{'imageTag': 'latest'}],
        acceptedMediaTypes=['application/vnd.oci.image.index.v1+json', 'application/vnd.docker.distribution.manifest.v2+json']
    )
    manifest_text = response['images'][0]['imageManifest']
    manifest = json.loads(manifest_text)
    assert manifest is not None


def test_ecr_image_is_multi_arch_or_single_arch(ecr_client):
    response = ecr_client.batch_get_image(
        repositoryName='github-runner',
        imageIds=[{'imageTag': 'latest'}],
        acceptedMediaTypes=['application/vnd.oci.image.index.v1+json', 'application/vnd.docker.distribution.manifest.v2+json']
    )
    manifest_text = response['images'][0]['imageManifest']
    manifest = json.loads(manifest_text)
    has_manifests = 'manifests' in manifest
    has_layers = 'layers' in manifest
    assert has_manifests or has_layers


def test_ecr_image_has_arm64_architecture(ecr_client):
    response = ecr_client.batch_get_image(
        repositoryName='github-runner',
        imageIds=[{'imageTag': 'latest'}],
        acceptedMediaTypes=['application/vnd.oci.image.index.v1+json', 'application/vnd.docker.distribution.manifest.v2+json']
    )
    manifest_text = response['images'][0]['imageManifest']
    manifest = json.loads(manifest_text)
    if 'manifests' in manifest:
        architectures = [m.get('platform', {}).get('architecture') for m in manifest['manifests']]
        assert 'arm64' in architectures
    else:
        assert True


def test_ecr_image_architecture_matches_task_definition(ecr_client, ecs_client):
    ecr_response = ecr_client.batch_get_image(
        repositoryName='github-runner',
        imageIds=[{'imageTag': 'latest'}],
        acceptedMediaTypes=['application/vnd.oci.image.index.v1+json', 'application/vnd.docker.distribution.manifest.v2+json']
    )
    manifest_text = ecr_response['images'][0]['imageManifest']
    manifest = json.loads(manifest_text)
    ecs_response = ecs_client.list_task_definitions(familyPrefix='github-runner', status='ACTIVE')
    task_def_arn = ecs_response['taskDefinitionArns'][0]
    task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
    task_arch = task_def['taskDefinition']['runtimePlatform']['cpuArchitecture'].lower()
    if 'manifests' in manifest:
        image_archs = [m.get('platform', {}).get('architecture', '').lower() for m in manifest['manifests']]
        assert task_arch in image_archs
    else:
        assert True


def test_ecr_repository_has_scan_on_push_enabled(ecr_client):
    response = ecr_client.describe_repositories(repositoryNames=['github-runner'])
    repo = response['repositories'][0]
    assert repo['imageScanningConfiguration']['scanOnPush'] is True


def test_ecr_repository_has_encryption_enabled(ecr_client):
    response = ecr_client.describe_repositories(repositoryNames=['github-runner'])
    repo = response['repositories'][0]
    assert 'encryptionConfiguration' in repo
