import hcl2


def test_central_logs_module_main_tf_exists(bootstrap_dir):
    assert (bootstrap_dir / "modules" / "central_logs" / "main.tf").exists()


def test_central_logs_bucket_policy_exists(bootstrap_dir):
    with open(bootstrap_dir / "modules" / "central_logs" / "main.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    resources = tf_config.get('resource', [])
    bucket_policy_found = False
    for resource in resources:
        if 'aws_s3_bucket_policy' in resource:
            bucket_policy_found = True
            break
    assert bucket_policy_found


def test_central_logs_bucket_policy_has_firehose_statement(bootstrap_dir):
    with open(bootstrap_dir / "modules" / "central_logs" / "main.tf", encoding='utf-8') as f:
        content = f.read()
    assert 'AllowFirehoseWrite' in content


def test_central_logs_bucket_policy_firehose_has_put_object(bootstrap_dir):
    with open(bootstrap_dir / "modules" / "central_logs" / "main.tf", encoding='utf-8') as f:
        content = f.read()
    assert 's3:PutObject' in content


def test_central_logs_bucket_policy_firehose_has_abort_multipart(bootstrap_dir):
    with open(bootstrap_dir / "modules" / "central_logs" / "main.tf", encoding='utf-8') as f:
        content = f.read()
    assert 's3:AbortMultipartUpload' in content


def test_central_logs_bucket_policy_firehose_has_get_bucket_location(bootstrap_dir):
    with open(bootstrap_dir / "modules" / "central_logs" / "main.tf", encoding='utf-8') as f:
        content = f.read()
    assert 's3:GetBucketLocation' in content


def test_central_logs_bucket_policy_firehose_has_list_bucket(bootstrap_dir):
    with open(bootstrap_dir / "modules" / "central_logs" / "main.tf", encoding='utf-8') as f:
        content = f.read()
    assert 's3:ListBucket' in content


def test_central_logs_bucket_policy_firehose_has_list_multipart_uploads(bootstrap_dir):
    with open(bootstrap_dir / "modules" / "central_logs" / "main.tf", encoding='utf-8') as f:
        content = f.read()
    assert 's3:ListBucketMultipartUploads' in content


def test_central_logs_bucket_policy_firehose_targets_cloudwatch_logs_prefix(bootstrap_dir):
    with open(bootstrap_dir / "modules" / "central_logs" / "main.tf", encoding='utf-8') as f:
        content = f.read()
    assert 'cloudwatch-logs/*' in content


def test_central_logs_bucket_policy_firehose_has_service_condition(bootstrap_dir):
    with open(bootstrap_dir / "modules" / "central_logs" / "main.tf", encoding='utf-8') as f:
        content = f.read()
    assert 'firehose.amazonaws.com' in content


def test_central_logs_bucket_policy_firehose_uses_principal_service_condition(bootstrap_dir):
    with open(bootstrap_dir / "modules" / "central_logs" / "main.tf", encoding='utf-8') as f:
        content = f.read()
    assert 'aws:PrincipalService' in content


def test_central_logs_bucket_policy_firehose_uses_account_principal(bootstrap_dir):
    with open(bootstrap_dir / "modules" / "central_logs" / "main.tf", encoding='utf-8') as f:
        content = f.read()
    assert 'var.aws_account_id' in content


def test_central_logs_write_policy_exists(bootstrap_dir):
    with open(bootstrap_dir / "modules" / "central_logs" / "main.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    resources = tf_config.get('resource', [])
    policy_found = False
    for resource in resources:
        if 'aws_iam_policy' in resource:
            policy_found = True
            break
    assert policy_found


def test_central_logs_outputs_bucket_arn(bootstrap_dir):
    with open(bootstrap_dir / "modules" / "central_logs" / "outputs.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    outputs = tf_config.get('output', [])
    output_names = [list(o.keys())[0] for o in outputs]
    assert 'bucket_arn' in output_names


def test_central_logs_outputs_write_policy_arn(bootstrap_dir):
    with open(bootstrap_dir / "modules" / "central_logs" / "outputs.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    outputs = tf_config.get('output', [])
    output_names = [list(o.keys())[0] for o in outputs]
    assert 'write_policy_arn' in output_names
