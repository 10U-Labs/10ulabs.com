"""Integration tests for ECR repository configuration."""
import json


def test_ecr_repository_exists(ecr_client, config):
    """Test that the ECR repository exists."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    assert len(response['repositories']) == 1


def test_ecr_repository_has_scan_on_push_enabled(ecr_client, config):
    """Test that scan on push is enabled for the repository."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo = response['repositories'][0]
    assert repo['imageScanningConfiguration']['scanOnPush'] is True


def test_ecr_repository_has_encryption_enabled(ecr_client, config):
    """Test that encryption is enabled for the repository."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo = response['repositories'][0]
    assert 'encryptionConfiguration' in repo


def test_ecr_repository_encryption_type_is_aes256(ecr_client, config):
    """Test that the repository uses AES256 encryption."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo = response['repositories'][0]
    assert repo['encryptionConfiguration']['encryptionType'] == 'AES256'


def test_ecr_repository_image_tag_mutability_is_mutable(ecr_client, config):
    """Test that image tag mutability is set to MUTABLE."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo = response['repositories'][0]
    assert repo['imageTagMutability'] == 'MUTABLE'


def test_ecr_repository_has_managed_by_tag(ecr_client, config):
    """Test that the repository has the ManagedBy tag set to terraform."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo_arn = response['repositories'][0]['repositoryArn']
    tags_response = ecr_client.list_tags_for_resource(resourceArn=repo_arn)
    tags = {tag['Key']: tag['Value'] for tag in tags_response['tags']}
    assert tags.get('ManagedBy') == 'terraform'


def test_ecr_repository_has_purpose_tag(ecr_client, config):
    """Test that the repository has the Purpose tag set to ecr."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo_arn = response['repositories'][0]['repositoryArn']
    tags_response = ecr_client.list_tags_for_resource(resourceArn=repo_arn)
    tags = {tag['Key']: tag['Value'] for tag in tags_response['tags']}
    assert tags.get('Purpose') == 'ecr'


def test_ecr_repository_has_name_tag(ecr_client, config):
    """Test that the repository has the Name tag matching repository name."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo_arn = response['repositories'][0]['repositoryArn']
    tags_response = ecr_client.list_tags_for_resource(resourceArn=repo_arn)
    tags = {tag['Key']: tag['Value'] for tag in tags_response['tags']}
    assert tags.get('Name') == repository_name


def test_ecr_lifecycle_policy_exists(ecr_client, config):
    """Test that a lifecycle policy exists for the repository."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    assert 'lifecyclePolicyText' in response


def test_ecr_lifecycle_policy_has_rule_priority_1(ecr_client, config):
    """Test that the lifecycle policy has a rule with priority 1."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    policy = json.loads(response['lifecyclePolicyText'])
    priorities = [rule['rulePriority'] for rule in policy['rules']]
    assert 1 in priorities


def test_ecr_lifecycle_policy_has_rule_priority_2(ecr_client, config):
    """Test that the lifecycle policy has a rule with priority 2."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    policy = json.loads(response['lifecyclePolicyText'])
    priorities = [rule['rulePriority'] for rule in policy['rules']]
    assert 2 in priorities


def test_ecr_lifecycle_policy_has_rule_priority_10(ecr_client, config):
    """Test that the lifecycle policy has a rule with priority 10."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    policy = json.loads(response['lifecyclePolicyText'])
    priorities = [rule['rulePriority'] for rule in policy['rules']]
    assert 10 in priorities


def test_ecr_lifecycle_policy_has_rule_priority_20(ecr_client, config):
    """Test that the lifecycle policy has a rule with priority 20."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    policy = json.loads(response['lifecyclePolicyText'])
    priorities = [rule['rulePriority'] for rule in policy['rules']]
    assert 20 in priorities


def test_ecr_repository_name_matches_expected(ecr_client, config):
    """Test that the repository name matches the expected name."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo = response['repositories'][0]
    assert repo['repositoryName'] == repository_name


def test_ecr_repository_url_contains_region(ecr_client, config):
    """Test that the repository URL contains the AWS region."""
    repository_name = config["ecr_repository_name"]
    aws_region = config["aws_region"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    repo = response['repositories'][0]
    assert aws_region in repo['repositoryUri']
