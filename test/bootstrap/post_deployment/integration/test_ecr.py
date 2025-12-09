"""Integration tests for ECR repository configuration."""
import json


def test_ecr_runners_repository_exists(ecr_client, config):
    """Test that the runners ECR repository exists."""
    repository_name = config["ecr_runners_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    assert len(response['repositories']) == 1


def test_ecr_agents_repository_exists(ecr_client, config):
    """Test that the agents ECR repository exists."""
    repository_name = config["ecr_agents_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    assert len(response['repositories']) == 1


def test_ecr_runners_repository_has_scan_on_push_enabled(ecr_client, config):
    """Test that scan on push is enabled for the runners repository."""
    repository_name = config["ecr_runners_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo = response['repositories'][0]
    assert repo['imageScanningConfiguration']['scanOnPush'] is True


def test_ecr_agents_repository_has_scan_on_push_enabled(ecr_client, config):
    """Test that scan on push is enabled for the agents repository."""
    repository_name = config["ecr_agents_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo = response['repositories'][0]
    assert repo['imageScanningConfiguration']['scanOnPush'] is True


def test_ecr_runners_repository_has_encryption_enabled(ecr_client, config):
    """Test that encryption is enabled for the runners repository."""
    repository_name = config["ecr_runners_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo = response['repositories'][0]
    assert 'encryptionConfiguration' in repo


def test_ecr_agents_repository_has_encryption_enabled(ecr_client, config):
    """Test that encryption is enabled for the agents repository."""
    repository_name = config["ecr_agents_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo = response['repositories'][0]
    assert 'encryptionConfiguration' in repo


def test_ecr_runners_repository_encryption_type_is_aes256(ecr_client, config):
    """Test that the runners repository uses AES256 encryption."""
    repository_name = config["ecr_runners_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo = response['repositories'][0]
    assert repo['encryptionConfiguration']['encryptionType'] == 'AES256'


def test_ecr_agents_repository_encryption_type_is_aes256(ecr_client, config):
    """Test that the agents repository uses AES256 encryption."""
    repository_name = config["ecr_agents_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo = response['repositories'][0]
    assert repo['encryptionConfiguration']['encryptionType'] == 'AES256'


def test_ecr_runners_repository_image_tag_mutability_is_mutable(ecr_client, config):
    """Test that image tag mutability is set to MUTABLE for runners."""
    repository_name = config["ecr_runners_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo = response['repositories'][0]
    assert repo['imageTagMutability'] == 'MUTABLE'


def test_ecr_agents_repository_image_tag_mutability_is_mutable(ecr_client, config):
    """Test that image tag mutability is set to MUTABLE for agents."""
    repository_name = config["ecr_agents_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo = response['repositories'][0]
    assert repo['imageTagMutability'] == 'MUTABLE'


def test_ecr_runners_repository_has_managed_by_tag(ecr_client, config):
    """Test that the runners repository has the ManagedBy tag."""
    repository_name = config["ecr_runners_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo_arn = response['repositories'][0]['repositoryArn']
    tags_response = ecr_client.list_tags_for_resource(resourceArn=repo_arn)
    tags = {tag['Key']: tag['Value'] for tag in tags_response['tags']}
    assert tags.get('ManagedBy') == 'terraform'


def test_ecr_agents_repository_has_managed_by_tag(ecr_client, config):
    """Test that the agents repository has the ManagedBy tag."""
    repository_name = config["ecr_agents_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo_arn = response['repositories'][0]['repositoryArn']
    tags_response = ecr_client.list_tags_for_resource(resourceArn=repo_arn)
    tags = {tag['Key']: tag['Value'] for tag in tags_response['tags']}
    assert tags.get('ManagedBy') == 'terraform'


def test_ecr_runners_lifecycle_policy_exists(ecr_client, config):
    """Test that a lifecycle policy exists for the runners repository."""
    repository_name = config["ecr_runners_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    assert 'lifecyclePolicyText' in response


def test_ecr_agents_lifecycle_policy_exists(ecr_client, config):
    """Test that a lifecycle policy exists for the agents repository."""
    repository_name = config["ecr_agents_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    assert 'lifecyclePolicyText' in response


def test_ecr_runners_lifecycle_policy_has_latest_rule(ecr_client, config):
    """Test that the runners lifecycle policy has a rule for latest tag."""
    repository_name = config["ecr_runners_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    policy = json.loads(response['lifecyclePolicyText'])
    rule_priorities = [rule['rulePriority'] for rule in policy['rules']]
    assert 1 in rule_priorities


def test_ecr_runners_lifecycle_policy_has_stable_rule(ecr_client, config):
    """Test that the runners lifecycle policy has a rule for stable tag."""
    repository_name = config["ecr_runners_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    policy = json.loads(response['lifecyclePolicyText'])
    rule_priorities = [rule['rulePriority'] for rule in policy['rules']]
    assert 2 in rule_priorities


def test_ecr_agents_lifecycle_policy_has_agent_creator_rule(ecr_client, config):
    """Test that the agents lifecycle policy has a rule for agent-creator."""
    repository_name = config["ecr_agents_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    policy = json.loads(response['lifecyclePolicyText'])
    has_agent_creator_rule = any(
        'agent-creator-' in str(rule.get('selection', {}).get('tagPrefixList', []))
        for rule in policy['rules']
    )
    assert has_agent_creator_rule


def test_ecr_agents_lifecycle_policy_has_workflow_fixer_rule(ecr_client, config):
    """Test that the agents lifecycle policy has a rule for workflow-fixer."""
    repository_name = config["ecr_agents_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    policy = json.loads(response['lifecyclePolicyText'])
    has_workflow_fixer_rule = any(
        'workflow-fixer-' in str(rule.get('selection', {}).get('tagPrefixList', []))
        for rule in policy['rules']
    )
    assert has_workflow_fixer_rule


def test_ecr_agents_lifecycle_policy_has_test_auditor_rule(ecr_client, config):
    """Test that the agents lifecycle policy has a rule for test-auditor."""
    repository_name = config["ecr_agents_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    policy = json.loads(response['lifecyclePolicyText'])
    has_test_auditor_rule = any(
        'test-auditor-' in str(rule.get('selection', {}).get('tagPrefixList', []))
        for rule in policy['rules']
    )
    assert has_test_auditor_rule


def test_ecr_get_authorization_token_succeeds(ecr_client):
    """Verify current credentials can get ECR authorization token."""
    response = ecr_client.get_authorization_token()
    assert "authorizationData" in response
    assert len(response["authorizationData"]) > 0
    auth_data = response["authorizationData"][0]
    assert "authorizationToken" in auth_data
    assert auth_data["authorizationToken"]
