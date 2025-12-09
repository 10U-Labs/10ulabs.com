"""Pre-deployment tests for api/shared/ecs_runner ECR Terraform configuration."""
import re


def test_ecr_tf_defines_runners_repository(api_shared_ecs_runner_dir):
    """Test that ecr.tf defines the runners ECR repository."""
    ecr_tf = api_shared_ecs_runner_dir / "ecr.tf"
    content = ecr_tf.read_text()
    pattern = r'resource\s+"aws_ecr_repository"\s+"runners"'
    assert re.search(pattern, content) is not None


def test_ecr_repository_name_matches_shared_module(api_shared_ecs_runner_dir, shared_module_dir):
    """Test that ECR repository name matches the shared module output."""
    # Get expected name from shared module (single source of truth)
    shared_outputs = (shared_module_dir / "outputs.tf").read_text()
    match = re.search(r'output "ecr_repository_name_runners"[^}]+value\s*=\s*"([^"]+)"', shared_outputs)
    assert match, "Could not find ecr_repository_name_runners in shared module"
    expected_name = match.group(1)

    # Verify locals.tf uses the same name
    locals_tf = api_shared_ecs_runner_dir / "locals.tf"
    content = locals_tf.read_text()
    assert f'ecr_repository_name = "{expected_name}"' in content


def test_ecr_repository_has_scan_on_push(api_shared_ecs_runner_dir):
    """Test that ECR repository has scan_on_push enabled."""
    ecr_tf = api_shared_ecs_runner_dir / "ecr.tf"
    content = ecr_tf.read_text()
    assert "scan_on_push = true" in content


def test_ecr_lifecycle_policy_defined(api_shared_ecs_runner_dir):
    """Test that ECR lifecycle policy is defined."""
    ecr_tf = api_shared_ecs_runner_dir / "ecr.tf"
    content = ecr_tf.read_text()
    pattern = r'resource\s+"aws_ecr_lifecycle_policy"\s+"runners"'
    assert re.search(pattern, content) is not None


def test_ecr_lifecycle_has_latest_rule(api_shared_ecs_runner_dir):
    """Test that lifecycle policy has rule for latest tag."""
    ecr_tf = api_shared_ecs_runner_dir / "ecr.tf"
    content = ecr_tf.read_text()
    assert '"latest"' in content


def test_ecr_lifecycle_has_stable_rule(api_shared_ecs_runner_dir):
    """Test that lifecycle policy has rule for stable tag."""
    ecr_tf = api_shared_ecs_runner_dir / "ecr.tf"
    content = ecr_tf.read_text()
    assert '"stable"' in content
