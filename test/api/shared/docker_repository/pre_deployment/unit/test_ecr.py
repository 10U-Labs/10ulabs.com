"""Pre-deployment unit tests for api/shared/docker_repository ECR Terraform configuration."""
import re


def test_ecr_tf_defines_runners_repository(api_shared_docker_repository_dir):
    """Test that ecr.tf defines the runners ECR repository."""
    ecr_tf = api_shared_docker_repository_dir / "ecr.tf"
    content = ecr_tf.read_text()
    pattern = r'resource\s+"aws_ecr_repository"\s+"runners"'
    assert re.search(pattern, content) is not None


def test_shared_module_defines_ecr_repository_name_runners(shared_module_dir):
    """Test that shared module defines ecr_repository_name_runners output."""
    shared_outputs = (shared_module_dir / "outputs.tf").read_text()
    pattern = r'output "ecr_repository_name_runners"[^}]+value\s*=\s*"([^"]+)"'
    match = re.search(pattern, shared_outputs)
    assert match, "Could not find ecr_repository_name_runners in shared module"


def test_ecr_repository_name_matches_shared_module(
    api_shared_docker_repository_dir, shared_module_dir
):
    """Test that ECR repository name matches the shared module output."""
    shared_outputs = (shared_module_dir / "outputs.tf").read_text()
    pattern = r'output "ecr_repository_name_runners"[^}]+value\s*=\s*"([^"]+)"'
    match = re.search(pattern, shared_outputs)
    expected_name = match.group(1)

    locals_tf = api_shared_docker_repository_dir / "locals.tf"
    content = locals_tf.read_text()
    assert f'ecr_repository_name = "{expected_name}"' in content


def test_ecr_repository_has_scan_on_push_disabled(api_shared_docker_repository_dir):
    """Test that ECR repository has scan_on_push disabled (ARM64 not supported)."""
    ecr_tf = api_shared_docker_repository_dir / "ecr.tf"
    content = ecr_tf.read_text()
    assert "scan_on_push = false" in content


def test_ecr_repository_has_aes256_encryption(api_shared_docker_repository_dir):
    """Test that ECR repository uses AES256 encryption."""
    ecr_tf = api_shared_docker_repository_dir / "ecr.tf"
    content = ecr_tf.read_text()
    assert 'encryption_type = "AES256"' in content


def test_ecr_repository_has_mutable_image_tags(api_shared_docker_repository_dir):
    """Test that ECR repository has MUTABLE image tag mutability."""
    ecr_tf = api_shared_docker_repository_dir / "ecr.tf"
    content = ecr_tf.read_text()
    assert 'image_tag_mutability = "MUTABLE"' in content


def test_ecr_repository_uses_common_tags(api_shared_docker_repository_dir):
    """Test that ECR repository uses common_tags for tagging."""
    ecr_tf = api_shared_docker_repository_dir / "ecr.tf"
    content = ecr_tf.read_text()
    assert "local.common_tags" in content


def test_common_tags_has_managed_by_terraform(api_shared_docker_repository_dir):
    """Test that common_tags includes ManagedBy = terraform."""
    locals_tf = api_shared_docker_repository_dir / "locals.tf"
    content = locals_tf.read_text()
    assert 'ManagedBy   = "terraform"' in content


def test_ecr_lifecycle_policy_defined(api_shared_docker_repository_dir):
    """Test that ECR lifecycle policy is defined."""
    ecr_tf = api_shared_docker_repository_dir / "ecr.tf"
    content = ecr_tf.read_text()
    pattern = r'resource\s+"aws_ecr_lifecycle_policy"\s+"runners"'
    assert re.search(pattern, content) is not None


def test_ecr_lifecycle_has_latest_rule(api_shared_docker_repository_dir):
    """Test that lifecycle policy has rule for latest tag."""
    ecr_tf = api_shared_docker_repository_dir / "ecr.tf"
    content = ecr_tf.read_text()
    assert '"latest"' in content


def test_ecr_lifecycle_has_stable_rule(api_shared_docker_repository_dir):
    """Test that lifecycle policy has rule for stable tag."""
    ecr_tf = api_shared_docker_repository_dir / "ecr.tf"
    content = ecr_tf.read_text()
    assert '"stable"' in content
