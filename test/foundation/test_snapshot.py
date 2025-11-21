def test_terraform_plan_has_planned_values(terraform_plan_json):
    assert 'planned_values' in terraform_plan_json


def test_terraform_plan_has_resource_changes(terraform_plan_json):
    assert 'resource_changes' in terraform_plan_json


def count_resources_by_type(terraform_plan_json, resource_type):
    if 'planned_values' not in terraform_plan_json:
        return 0
    if 'root_module' not in terraform_plan_json['planned_values']:
        return 0

    count = 0
    root_module = terraform_plan_json['planned_values']['root_module']

    if 'resources' in root_module:
        count += len([r for r in root_module['resources'] if r['type'] == resource_type])

    if 'child_modules' in root_module:
        for child in root_module['child_modules']:
            if 'resources' in child:
                count += len([r for r in child['resources'] if r['type'] == resource_type])

    return count


def find_resource_by_type(terraform_plan_json, resource_type):
    resources = []
    if 'planned_values' not in terraform_plan_json:
        return resources
    if 'root_module' not in terraform_plan_json['planned_values']:
        return resources

    root_module = terraform_plan_json['planned_values']['root_module']

    if 'resources' in root_module:
        resources.extend([r for r in root_module['resources'] if r['type'] == resource_type])

    if 'child_modules' in root_module:
        for child in root_module['child_modules']:
            if 'resources' in child:
                resources.extend([r for r in child['resources'] if r['type'] == resource_type])

    return resources


def test_oidc_provider_count(terraform_plan_json):
    count = count_resources_by_type(terraform_plan_json, 'aws_iam_openid_connect_provider')
    assert count == 1


def test_iam_role_count(terraform_plan_json):
    count = count_resources_by_type(terraform_plan_json, 'aws_iam_role')
    assert count == 2


def test_cloudtrail_trail_count(terraform_plan_json):
    count = count_resources_by_type(terraform_plan_json, 'aws_cloudtrail')
    assert count == 1


def test_s3_bucket_count(terraform_plan_json):
    count = count_resources_by_type(terraform_plan_json, 'aws_s3_bucket')
    assert count == 4


def test_cloudwatch_log_group_count(terraform_plan_json):
    count = count_resources_by_type(terraform_plan_json, 'aws_cloudwatch_log_group')
    assert count == 1


def test_s3_buckets_have_versioning_disabled(terraform_plan_json):
    versioning_resources = find_resource_by_type(terraform_plan_json, 'aws_s3_bucket_versioning')
    for resource in versioning_resources:
        values = resource.get('values', {})
        versioning_config = values.get('versioning_configuration', [{}])[0]
        assert versioning_config.get('status') == 'Disabled'


def test_s3_buckets_have_encryption(terraform_plan_json):
    encryption_resources = find_resource_by_type(terraform_plan_json, 'aws_s3_bucket_server_side_encryption_configuration')
    assert len(encryption_resources) >= 3


def test_s3_buckets_have_public_access_block(terraform_plan_json):
    public_access_resources = find_resource_by_type(terraform_plan_json, 'aws_s3_bucket_public_access_block')
    assert len(public_access_resources) >= 3


def test_cloudtrail_is_multi_region(terraform_plan_json):
    trails = find_resource_by_type(terraform_plan_json, 'aws_cloudtrail')
    for trail in trails:
        values = trail.get('values', {})
        assert values.get('is_multi_region_trail') is True


def test_cloudtrail_includes_global_service_events(terraform_plan_json):
    trails = find_resource_by_type(terraform_plan_json, 'aws_cloudtrail')
    for trail in trails:
        values = trail.get('values', {})
        assert values.get('include_global_service_events') is True


def test_cloudwatch_log_group_has_retention(terraform_plan_json):
    log_groups = find_resource_by_type(terraform_plan_json, 'aws_cloudwatch_log_group')
    for log_group in log_groups:
        values = log_group.get('values', {})
        assert values.get('retention_in_days') == 365


def test_oidc_provider_has_github_url(terraform_plan_json):
    providers = find_resource_by_type(terraform_plan_json, 'aws_iam_openid_connect_provider')
    for provider in providers:
        values = provider.get('values', {})
        assert values.get('url') == 'https://token.actions.githubusercontent.com'


def test_oidc_provider_has_thumbprints(terraform_plan_json):
    providers = find_resource_by_type(terraform_plan_json, 'aws_iam_openid_connect_provider')
    for provider in providers:
        values = provider.get('values', {})
        thumbprints = values.get('thumbprint_list', [])
        assert '6938fd4d98bab03faadb97b34396831e3780aea1' in thumbprints


def test_oidc_provider_has_client_ids(terraform_plan_json):
    providers = find_resource_by_type(terraform_plan_json, 'aws_iam_openid_connect_provider')
    for provider in providers:
        values = provider.get('values', {})
        client_ids = values.get('client_id_list', [])
        assert 'sts.amazonaws.com' in client_ids


def test_github_actions_role_has_administrator_access(terraform_plan_json):
    attachments = find_resource_by_type(terraform_plan_json, 'aws_iam_role_policy_attachment')
    admin_attachments = [a for a in attachments if 'AdministratorAccess' in a.get('values', {}).get('policy_arn', '')]
    assert len(admin_attachments) >= 1


def test_no_unintended_resource_deletions(terraform_plan_json):
    if 'resource_changes' not in terraform_plan_json:
        return

    deletions = [
        r for r in terraform_plan_json['resource_changes']
        if r.get('change', {}).get('actions', []) == ['delete']
    ]

    assert len(deletions) == 0
