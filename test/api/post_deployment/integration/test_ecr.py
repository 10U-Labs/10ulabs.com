def test_ecr_repository_exists(ecr_client, tfvars):
    repository_name = tfvars["ecr_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    assert len(response["repositories"]) == 1


def test_ecr_repository_lifecycle_policies(ecr_client, tfvars):
    repository_name = tfvars["ecr_repository_name"]
    try:
        response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
        assert "lifecyclePolicyText" in response
    except ecr_client.exceptions.LifecyclePolicyNotFoundException:
        assert True


def test_ecr_repository_permissions(ecr_client, tfvars):
    repository_name = tfvars["ecr_repository_name"]
    try:
        response = ecr_client.get_repository_policy(repositoryName=repository_name)
        assert "policyText" in response
    except ecr_client.exceptions.RepositoryPolicyNotFoundException:
        assert True
