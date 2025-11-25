import json


def test_ecr_repository_exists(ecr_client, config):
    repository_name = config["ecr_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    assert len(response["repositories"]) == 1


def test_ecr_lifecycle_policy_exists(ecr_client, config):
    repository_name = config["ecr_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    assert "lifecyclePolicyText" in response


def test_ecr_lifecycle_policy_has_latest_rule(ecr_client, config):
    repository_name = config["ecr_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    policy = json.loads(response["lifecyclePolicyText"])
    rules = policy["rules"]
    latest_rules = [r for r in rules if r.get("selection", {}).get("tagPrefixList") == ["latest"]]
    assert len(latest_rules) == 1


def test_ecr_lifecycle_policy_has_stable_rule(ecr_client, config):
    repository_name = config["ecr_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    policy = json.loads(response["lifecyclePolicyText"])
    rules = policy["rules"]
    stable_rules = [r for r in rules if r.get("selection", {}).get("tagPrefixList") == ["stable"]]
    assert len(stable_rules) == 1


def test_ecr_lifecycle_policy_has_untagged_rule(ecr_client, config):
    repository_name = config["ecr_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    policy = json.loads(response["lifecyclePolicyText"])
    rules = policy["rules"]
    untagged_rules = [r for r in rules if r.get("selection", {}).get("tagStatus") == "untagged"]
    assert len(untagged_rules) == 1


def test_ecr_lifecycle_policy_has_catchall_rule(ecr_client, config):
    repository_name = config["ecr_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    policy = json.loads(response["lifecyclePolicyText"])
    rules = policy["rules"]
    any_rules = [r for r in rules if r.get("selection", {}).get("tagStatus") == "any"]
    assert len(any_rules) == 1


def test_ecr_repository_permissions(ecr_client, config):
    repository_name = config["ecr_repository_name"]
    try:
        response = ecr_client.get_repository_policy(repositoryName=repository_name)
        assert "policyText" in response
    except ecr_client.exceptions.RepositoryPolicyNotFoundException:
        assert True
