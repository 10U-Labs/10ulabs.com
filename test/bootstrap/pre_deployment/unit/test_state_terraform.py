"""Unit tests for state.tf Terraform configuration."""
import hcl2
import pytest


def _load_state_tf(bootstrap_dir):
    """Load and parse state.tf."""
    with open(bootstrap_dir / "state.tf", encoding='utf-8') as f:
        return hcl2.load(f)


def _find_resource(tf_config, resource_type, resource_name):
    """Find a resource by type and name."""
    for resource in tf_config.get('resource', []):
        if resource_type in resource:
            if resource_name in resource[resource_type]:
                return resource[resource_type][resource_name]
    return None


def test_terraform_state_bucket_exists_in_state_tf(bootstrap_dir):
    """Test that terraform state bucket resource exists in state.tf."""
    tf_config = _load_state_tf(bootstrap_dir)
    bucket = _find_resource(tf_config, 'aws_s3_bucket', 'terraform_state')
    assert bucket is not None


def test_terraform_state_bucket_encryption_resource_exists(bootstrap_dir):
    """Test that terraform state bucket encryption resource exists."""
    tf_config = _load_state_tf(bootstrap_dir)
    encryption = _find_resource(
        tf_config,
        'aws_s3_bucket_server_side_encryption_configuration',
        'terraform_state'
    )
    assert encryption is not None


def test_terraform_state_bucket_public_access_block_exists(bootstrap_dir):
    """Test that terraform state bucket public access block exists."""
    tf_config = _load_state_tf(bootstrap_dir)
    block = _find_resource(
        tf_config,
        'aws_s3_bucket_public_access_block',
        'terraform_state'
    )
    assert block is not None


@pytest.mark.parametrize("setting", [
    "block_public_acls",
    "block_public_policy",
    "ignore_public_acls",
    "restrict_public_buckets",
])
def test_terraform_state_bucket_public_access_block_setting(bootstrap_dir, setting):
    """Test that terraform state bucket public access block has setting enabled."""
    tf_config = _load_state_tf(bootstrap_dir)
    block = _find_resource(
        tf_config,
        'aws_s3_bucket_public_access_block',
        'terraform_state'
    )
    assert block[setting] is True


def test_terraform_state_bucket_logging_resource_exists(bootstrap_dir):
    """Test that terraform state bucket logging resource exists."""
    tf_config = _load_state_tf(bootstrap_dir)
    logging = _find_resource(
        tf_config,
        'aws_s3_bucket_logging',
        'terraform_state'
    )
    assert logging is not None


def test_terraform_state_bucket_policy_resource_exists(bootstrap_dir):
    """Test that terraform state bucket policy resource exists."""
    tf_config = _load_state_tf(bootstrap_dir)
    policy = _find_resource(tf_config, 'aws_s3_bucket_policy', 'terraform_state')
    assert policy is not None


def test_terraform_state_bucket_encryption_uses_aes256(bootstrap_dir):
    """Test that terraform state bucket encryption uses AES256."""
    tf_config = _load_state_tf(bootstrap_dir)
    config = _find_resource(
        tf_config,
        'aws_s3_bucket_server_side_encryption_configuration',
        'terraform_state'
    )
    rule = config['rule'][0]
    default = rule['apply_server_side_encryption_by_default'][0]
    assert default['sse_algorithm'] == 'AES256'
