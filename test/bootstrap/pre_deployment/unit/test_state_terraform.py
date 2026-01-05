"""Unit tests for state.tf Terraform configuration."""
import hcl2


def test_terraform_state_bucket_exists_in_state_tf(bootstrap_dir):
    """Test that terraform state bucket resource exists in state.tf."""
    with open(bootstrap_dir / "state.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    assert 'resource' in tf_config
    bucket_found = False
    for resource in tf_config['resource']:
        if 'aws_s3_bucket' in resource:
            if 'terraform_state' in resource['aws_s3_bucket']:
                bucket_found = True
                break
    assert bucket_found


def test_terraform_state_bucket_encryption_resource_exists(bootstrap_dir):
    """Test that terraform state bucket encryption resource exists."""
    with open(bootstrap_dir / "state.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    encryption_found = False
    for resource in tf_config['resource']:
        if 'aws_s3_bucket_server_side_encryption_configuration' in resource:
            if 'terraform_state' in resource['aws_s3_bucket_server_side_encryption_configuration']:
                encryption_found = True
                break
    assert encryption_found


def test_terraform_state_bucket_public_access_block_exists(bootstrap_dir):
    """Test that terraform state bucket public access block exists."""
    with open(bootstrap_dir / "state.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    block_found = False
    for resource in tf_config['resource']:
        if 'aws_s3_bucket_public_access_block' in resource:
            if 'terraform_state' in resource['aws_s3_bucket_public_access_block']:
                block_found = True
                break
    assert block_found


def test_terraform_state_bucket_public_access_block_all_true(bootstrap_dir):
    """Test that terraform state bucket public access block has all settings true."""
    with open(bootstrap_dir / "state.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    for resource in tf_config['resource']:
        if 'aws_s3_bucket_public_access_block' in resource:
            block = resource['aws_s3_bucket_public_access_block'].get('terraform_state')
            if block:
                assert block['block_public_acls'] is True
                assert block['block_public_policy'] is True
                assert block['ignore_public_acls'] is True
                assert block['restrict_public_buckets'] is True
                return
    assert False, "aws_s3_bucket_public_access_block not found"


def test_terraform_state_bucket_logging_resource_exists(bootstrap_dir):
    """Test that terraform state bucket logging resource exists."""
    with open(bootstrap_dir / "state.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    logging_found = False
    for resource in tf_config['resource']:
        if 'aws_s3_bucket_logging' in resource:
            if 'terraform_state' in resource['aws_s3_bucket_logging']:
                logging_found = True
                break
    assert logging_found


def test_terraform_state_bucket_policy_resource_exists(bootstrap_dir):
    """Test that terraform state bucket policy resource exists."""
    with open(bootstrap_dir / "state.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    policy_found = False
    for resource in tf_config['resource']:
        if 'aws_s3_bucket_policy' in resource:
            if 'terraform_state' in resource['aws_s3_bucket_policy']:
                policy_found = True
                break
    assert policy_found


def test_terraform_state_bucket_encryption_uses_aes256(bootstrap_dir):
    """Test that terraform state bucket encryption uses AES256."""
    with open(bootstrap_dir / "state.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    for resource in tf_config['resource']:
        if 'aws_s3_bucket_server_side_encryption_configuration' in resource:
            config = resource['aws_s3_bucket_server_side_encryption_configuration'].get(
                'terraform_state'
            )
            if config:
                rule = config['rule'][0]
                default = rule['apply_server_side_encryption_by_default'][0]
                assert default['sse_algorithm'] == 'AES256'
                return
    assert False, "Encryption configuration not found"
