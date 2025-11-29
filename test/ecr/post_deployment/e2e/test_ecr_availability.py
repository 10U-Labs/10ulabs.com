def test_ecr_repository_accessible(ecr_client, config):
    repository_name = config["ecr_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    assert response['repositories'][0]['repositoryName'] == repository_name
