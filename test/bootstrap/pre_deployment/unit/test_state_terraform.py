import hcl2
import pytest


def _load_state_tf(bootstrap_dir, v7_compatible):
    with open(bootstrap_dir / "state.tf", encoding='utf-8') as f:
        return hcl2.load(f, serialization_options=v7_compatible)


def _find_resource(tf_config, resource_type, resource_name):
    for resource in tf_config.get('resource', []):
        if resource_type in resource:
            if resource_name in resource[resource_type]:
                return resource[resource_type][resource_name]
    return None


def _find_lifecycle_rule(tf_config, rule_id):
    lifecycle = _find_resource(
        tf_config,
        'aws_s3_bucket_lifecycle_configuration',
        'terraform_state'
    ) or {}
    for rule in lifecycle.get('rule', []):
        if rule['id'] == rule_id:
            return rule
    return {}


def test_terraform_state_bucket_exists_in_state_tf(bootstrap_dir, v7_compatible):
    tf_config = _load_state_tf(bootstrap_dir, v7_compatible)
    bucket = _find_resource(tf_config, 'aws_s3_bucket', 'terraform_state')
    assert bucket is not None


def test_terraform_state_bucket_versioning_is_suspended(bootstrap_dir, v7_compatible):
    tf_config = _load_state_tf(bootstrap_dir, v7_compatible)
    versioning = _find_resource(tf_config, 'aws_s3_bucket_versioning', 'terraform_state')
    assert versioning['versioning_configuration'][0]['status'] == 'Suspended'


def test_terraform_state_bucket_encryption_resource_exists(bootstrap_dir, v7_compatible):
    tf_config = _load_state_tf(bootstrap_dir, v7_compatible)
    encryption = _find_resource(
        tf_config,
        'aws_s3_bucket_server_side_encryption_configuration',
        'terraform_state'
    )
    assert encryption is not None


def test_terraform_state_bucket_public_access_block_exists(bootstrap_dir, v7_compatible):
    tf_config = _load_state_tf(bootstrap_dir, v7_compatible)
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
def test_terraform_state_bucket_public_access_block_setting(bootstrap_dir, setting, v7_compatible):
    tf_config = _load_state_tf(bootstrap_dir, v7_compatible)
    block = _find_resource(
        tf_config,
        'aws_s3_bucket_public_access_block',
        'terraform_state'
    )
    assert block[setting] is True


def test_terraform_state_bucket_logging_resource_exists(bootstrap_dir, v7_compatible):
    tf_config = _load_state_tf(bootstrap_dir, v7_compatible)
    logging = _find_resource(
        tf_config,
        'aws_s3_bucket_logging',
        'terraform_state'
    )
    assert logging is not None


def test_terraform_state_bucket_policy_resource_exists(bootstrap_dir, v7_compatible):
    tf_config = _load_state_tf(bootstrap_dir, v7_compatible)
    policy = _find_resource(tf_config, 'aws_s3_bucket_policy', 'terraform_state')
    assert policy is not None


def test_terraform_state_bucket_encryption_uses_aes256(bootstrap_dir, v7_compatible):
    tf_config = _load_state_tf(bootstrap_dir, v7_compatible)
    config = _find_resource(
        tf_config,
        'aws_s3_bucket_server_side_encryption_configuration',
        'terraform_state'
    )
    rule = config['rule'][0]
    default = rule['apply_server_side_encryption_by_default'][0]
    assert default['sse_algorithm'] == 'AES256'


def test_terraform_state_bucket_expires_delete_markers(bootstrap_dir, v7_compatible):
    tf_config = _load_state_tf(bootstrap_dir, v7_compatible)
    rule = _find_lifecycle_rule(tf_config, 'expire-delete-markers')
    expiration = (rule.get('expiration') or [{}])[0]
    assert expiration.get('expired_object_delete_marker') is True


def test_terraform_state_bucket_delete_marker_rule_sets_no_age(bootstrap_dir, v7_compatible):
    tf_config = _load_state_tf(bootstrap_dir, v7_compatible)
    rule = _find_lifecycle_rule(tf_config, 'expire-delete-markers')
    expiration = (rule.get('expiration') or [{}])[0]
    assert set(expiration) == {'expired_object_delete_marker'}


def test_terraform_state_bucket_delete_marker_rule_has_filter(bootstrap_dir, v7_compatible):
    tf_config = _load_state_tf(bootstrap_dir, v7_compatible)
    rule = _find_lifecycle_rule(tf_config, 'expire-delete-markers')
    assert rule.get('filter') is not None


def test_terraform_state_bucket_delete_marker_rule_has_one_filter(bootstrap_dir, v7_compatible):
    tf_config = _load_state_tf(bootstrap_dir, v7_compatible)
    rule = _find_lifecycle_rule(tf_config, 'expire-delete-markers')
    assert len(rule.get('filter')) == 1


def test_terraform_state_bucket_delete_marker_rule_covers_every_key(bootstrap_dir, v7_compatible):
    tf_config = _load_state_tf(bootstrap_dir, v7_compatible)
    rule = _find_lifecycle_rule(tf_config, 'expire-delete-markers')
    assert not rule.get('filter')[0]
