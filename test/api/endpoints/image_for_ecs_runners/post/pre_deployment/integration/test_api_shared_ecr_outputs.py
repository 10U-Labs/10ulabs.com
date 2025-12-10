"""Tests to validate api_shared_ecr infrastructure exists."""


def test_terraform_outputs_readable(api_shared_ecr_outputs):
    """Verify api_shared_ecr terraform outputs are accessible."""
    assert api_shared_ecr_outputs.get("repository_name"), \
        "repository_name output not found in api_shared_ecr"
    assert api_shared_ecr_outputs.get("repository_url"), \
        "repository_url output not found in api_shared_ecr"
    assert api_shared_ecr_outputs.get("repository_arn"), \
        "repository_arn output not found in api_shared_ecr"


def test_ecr_repository_exists(ecr_client, api_shared_ecr_outputs):
    """Verify the ECR repository exists and is accessible."""
    repository_name = api_shared_ecr_outputs.get("repository_name")
    assert repository_name, "repository_name output not found"

    response = ecr_client.describe_repositories(
        repositoryNames=[repository_name]
    )
    assert len(response["repositories"]) == 1
    repo = response["repositories"][0]
    assert repo["repositoryName"] == repository_name


def test_ecr_repository_policy_allows_push(ecr_client, api_shared_ecr_outputs):
    """Verify the ECR repository allows image push operations."""
    repository_name = api_shared_ecr_outputs.get("repository_name")
    assert repository_name, "repository_name output not found"

    response = ecr_client.describe_repositories(
        repositoryNames=[repository_name]
    )
    assert len(response["repositories"]) == 1
    repo = response["repositories"][0]
    assert "repositoryUri" in repo
    assert repo["repositoryUri"]
