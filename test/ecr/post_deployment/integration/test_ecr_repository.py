def test_ecr_repository_exists(ecr_client, config):
    repository_name = config["ecr_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    assert len(response['repositories']) == 1


def test_ecr_repository_has_scan_on_push_enabled(ecr_client, config):
    repository_name = config["ecr_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo = response['repositories'][0]
    assert repo['imageScanningConfiguration']['scanOnPush'] is True


def test_ecr_repository_has_encryption_enabled(ecr_client, config):
    repository_name = config["ecr_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo = response['repositories'][0]
    assert 'encryptionConfiguration' in repo
