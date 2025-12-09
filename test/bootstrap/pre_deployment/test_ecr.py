"""Pre-deployment tests for ECR Terraform configuration."""
import re


def test_ecr_tf_defines_main_repository(bootstrap_dir):
    """Test that ecr.tf defines the main ECR repository."""
    ecr_tf = bootstrap_dir / "ecr.tf"
    content = ecr_tf.read_text()
    pattern = r'resource\s+"aws_ecr_repository"\s+"main"'
    assert re.search(pattern, content) is not None


def test_ecr_repository_has_scan_on_push(bootstrap_dir):
    """Test that ECR repository has scan_on_push enabled."""
    ecr_tf = bootstrap_dir / "ecr.tf"
    content = ecr_tf.read_text()
    assert "scan_on_push = true" in content


def test_ecr_repository_has_aes256_encryption(bootstrap_dir):
    """Test that ECR repository uses AES256 encryption."""
    ecr_tf = bootstrap_dir / "ecr.tf"
    content = ecr_tf.read_text()
    assert 'encryption_type = "AES256"' in content


def test_ecr_lifecycle_policy_defined(bootstrap_dir):
    """Test that ECR lifecycle policy is defined."""
    ecr_tf = bootstrap_dir / "ecr.tf"
    content = ecr_tf.read_text()
    pattern = r'resource\s+"aws_ecr_lifecycle_policy"\s+"main"'
    assert re.search(pattern, content) is not None


def test_outputs_contains_ecr_repository_arn(bootstrap_dir):
    """Test that outputs.tf contains ecr_repository_arn output."""
    outputs_tf = bootstrap_dir / "outputs.tf"
    content = outputs_tf.read_text()
    pattern = r'output\s+"ecr_repository_arn"'
    assert re.search(pattern, content) is not None


def test_outputs_contains_ecr_repository_name(bootstrap_dir):
    """Test that outputs.tf contains ecr_repository_name output."""
    outputs_tf = bootstrap_dir / "outputs.tf"
    content = outputs_tf.read_text()
    pattern = r'output\s+"ecr_repository_name"'
    assert re.search(pattern, content) is not None


def test_outputs_contains_ecr_repository_url(bootstrap_dir):
    """Test that outputs.tf contains ecr_repository_url output."""
    outputs_tf = bootstrap_dir / "outputs.tf"
    content = outputs_tf.read_text()
    pattern = r'output\s+"ecr_repository_url"'
    assert re.search(pattern, content) is not None
