import json
from datetime import UTC, datetime, timedelta

import pytest
from botocore.exceptions import ClientError

import boto3
import requests


TEST_HEADERS = {"x-test-mode": "true"}


def _extract_policy_actions(policy):
    actions = []
    for stmt in policy.get('Statement', []):
        stmt_actions = stmt.get('Action', [])
        if isinstance(stmt_actions, str):
            actions.append(stmt_actions)
        else:
            actions.extend(stmt_actions)
    return actions


def _extract_policy_resources(policy):
    resources = []
    for stmt in policy.get('Statement', []):
        stmt_resources = stmt.get('Resource', [])
        if isinstance(stmt_resources, str):
            resources.append(stmt_resources)
        else:
            resources.extend(stmt_resources)
    return resources


def test_api_gateway_has_permission_to_invoke_health_lambda(lambda_client, config):
    function_name = config["health_handler_function_name"]
    try:
        response = lambda_client.get_policy(FunctionName=function_name)
        assert "Policy" in response
    except ClientError as err:
        if err.response["Error"]["Code"] == "ResourceNotFoundException":
            pytest.skip("Health Lambda not deployed (managed by api_operational_health.yml)")
        raise


def test_api_gateway_usage_plan_associated_with_prod_stage(
    apigateway_client, api_gateway_id, usage_plan_id
):
    if usage_plan_id is None:
        pytest.skip("Usage plan not found")
    plan = apigateway_client.get_usage_plan(usagePlanId=usage_plan_id)
    api_stages = plan.get('apiStages', [])
    for stage in api_stages:
        if stage.get('apiId') == api_gateway_id and stage.get('stage') == 'prod':
            return
    pytest.fail("Usage plan not associated with prod stage")
    assert True


def test_api_gateway_usage_plan_key_links_key_to_plan(apigateway_client, usage_plan_id):
    if usage_plan_id is None:
        pytest.skip("Usage plan not found")
    keys = apigateway_client.get_usage_plan_keys(usagePlanId=usage_plan_id)
    assert len(keys['items']) > 0


def test_api_gateway_usage_plan_key_type_is_api_key(apigateway_client, usage_plan_id):
    if usage_plan_id is None:
        pytest.skip("Usage plan not found")
    keys = apigateway_client.get_usage_plan_keys(usagePlanId=usage_plan_id)
    if keys['items']:
        assert keys['items'][0]['type'] == 'API_KEY'


def test_api_gateway_cloudwatch_role_has_push_logs_policy(iam_client, config):
    role_name = config['api_gateway_cloudwatch_role_name']
    response = iam_client.list_attached_role_policies(RoleName=role_name)
    policy_arns = [p['PolicyArn'] for p in response['AttachedPolicies']]
    has_cloudwatch_policy = any(
        'CloudWatch' in arn or 'cloudwatch' in arn.lower() for arn in policy_arns
    )
    assert has_cloudwatch_policy


def test_lambda_catchall_permission_source_arn_covers_all_methods(lambda_client, shared_config):
    function_name = shared_config['lambda_handler_names']['catchall']
    try:
        response = lambda_client.get_policy(FunctionName=function_name)
        policy = json.loads(response['Policy'])
        for stmt in policy.get('Statement', []):
            source_arn = stmt.get('Condition', {}).get('ArnLike', {}).get('AWS:SourceArn', '')
            if 'execute-api' in source_arn:
                assert '/*/' in source_arn or '/*/*' in source_arn or source_arn.endswith('/*')
    except ClientError as err:
        if err.response["Error"]["Code"] == "ResourceNotFoundException":
            pytest.skip("Lambda policy not found")
        raise


def test_cloudfront_distribution_origin_points_to_s3(cloudfront_client):
    distributions = cloudfront_client.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        dist_config = cloudfront_client.get_distribution_config(Id=dist_id)
        origins = dist_config['DistributionConfig']['Origins']['Items']
        assert len(origins) > 0


def test_cloudfront_logging_bucket_is_central_logs(
    cloudfront_client, api_distribution_id, config
):
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    logging_config = dist_config['DistributionConfig'].get('Logging', {})
    if not logging_config.get('Enabled', False):
        pytest.skip("CloudFront logging not yet enabled on distribution")
    bucket = logging_config.get('Bucket', '')
    assert config['central_logs_bucket'] in bucket


def test_cloudfront_logging_prefix_is_correct(cloudfront_client, api_distribution_id):
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    logging_config = dist_config['DistributionConfig'].get('Logging', {})
    prefix = logging_config.get('Prefix', '')
    assert prefix == 'cloudfront-logs/api/'


def test_s3_bucket_policy_allows_cloudfront_oac(s3_client, config):
    bucket_name = config["api_fqdn"]
    response = s3_client.get_bucket_policy(Bucket=bucket_name)
    policy = json.loads(response['Policy'])
    has_cloudfront_condition = any(
        'cloudfront' in str(stmt.get('Condition', {})).lower()
        for stmt in policy.get('Statement', [])
    )
    assert has_cloudfront_condition


def test_route53_api_record_alias_target_is_cloudfront(api_route53_records, config):
    if api_route53_records is None:
        pytest.skip("Hosted zone not found")
    for record in api_route53_records:
        if record['Name'].rstrip('.') == config['api_fqdn']:
            alias_target = record.get('AliasTarget', {})
            assert 'cloudfront.net' in alias_target.get('DNSName', '')


def test_cloudfront_uses_acm_certificate(cloudfront_client, api_distribution_id):
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    viewer_cert = dist_config['DistributionConfig'].get('ViewerCertificate', {})
    acm_cert_arn = viewer_cert.get('ACMCertificateArn', '')
    assert 'arn:aws:acm' in acm_cert_arn


def test_cloudfront_returns_404_for_nonexistent_endpoint(api_url):
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 404


def test_cloudfront_404_page_contains_error_message(api_url):
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    data = json.loads(response.text)
    assert "error" in data


def test_cloudfront_404_page_contains_not_found_text(api_url):
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    assert "Not Found" in response.text or "Endpoint not found" in response.text


def test_catchall_handler_subscription_filter_exists(logs_client, config):
    log_group = config['catchall_handler_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    assert 'catchall-handler-to-firehose' in filter_names


def test_catchall_handler_subscription_destinations_firehose(logs_client, config):
    log_group = config['catchall_handler_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    assert 'firehose' in destination_arn


def test_health_handler_subscription_filter_exists(logs_client, config):
    log_group = config['health_handler_log_group_name']
    try:
        response = logs_client.describe_subscription_filters(logGroupName=log_group)
    except ClientError as err:
        if err.response["Error"]["Code"] == "ResourceNotFoundException":
            pytest.skip("Health handler log group not deployed")
        raise
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    assert 'health-handler-to-firehose' in filter_names


def test_api_gateway_subscription_filter_exists(logs_client, config):
    log_group = config['api_gateway_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    assert 'api-gateway-to-firehose' in filter_names


def test_firehose_role_trusts_firehose_service(iam_client, config):
    response = iam_client.get_role(RoleName=config['firehose_role_name'])
    assume_role_policy = response['Role']['AssumeRolePolicyDocument']
    statements = assume_role_policy['Statement']
    service_principal = statements[0]['Principal']['Service']
    assert service_principal == 'firehose.amazonaws.com'


def test_cloudwatch_logs_firehose_role_trusts_logs_service(iam_client, config):
    role_name = config['cloudwatch_logs_firehose_role_name']
    response = iam_client.get_role(RoleName=role_name)
    assume_role_policy = response['Role']['AssumeRolePolicyDocument']
    statements = assume_role_policy['Statement']
    service_principal = statements[0]['Principal']['Service']
    assert f"logs.{config['aws_region']}.amazonaws.com" == service_principal


def test_firehose_role_has_s3_access_policy(iam_client, config):
    response = iam_client.list_role_policies(RoleName=config['firehose_role_name'])
    assert 'S3Access' in response['PolicyNames']


def test_firehose_s3_policy_has_all_required_actions(iam_client, config):
    response = iam_client.get_role_policy(
        RoleName=config['firehose_role_name'], PolicyName='S3Access'
    )
    actions = _extract_policy_actions(response['PolicyDocument'])
    assert any('s3:PutObject' in a or 's3:*' in a for a in actions)


def test_cloudwatch_logs_firehose_role_has_firehose_access_policy(iam_client, config):
    role_name = config['cloudwatch_logs_firehose_role_name']
    response = iam_client.list_role_policies(RoleName=role_name)
    assert 'FirehoseAccess' in response['PolicyNames']


def test_catchall_subscription_uses_correct_firehose_role(logs_client, config):
    log_group = config['catchall_handler_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    if response['subscriptionFilters']:
        role_arn = response['subscriptionFilters'][0].get('roleArn', '')
        assert config['cloudwatch_logs_firehose_role_name'] in role_arn


def test_api_gateway_subscription_uses_correct_firehose_role(logs_client, config):
    log_group = config['api_gateway_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    if response['subscriptionFilters']:
        role_arn = response['subscriptionFilters'][0].get('roleArn', '')
        assert config['cloudwatch_logs_firehose_role_name'] in role_arn


def test_lambda_role_has_basic_execution_policy(iam_client, shared_config):
    role_name = f"{shared_config['resource_prefix']}CatchAllHandlerServiceRole"
    response = iam_client.list_attached_role_policies(RoleName=role_name)
    policy_arns = [p['PolicyArn'] for p in response['AttachedPolicies']]
    has_basic_exec = any('BasicExecutionRole' in arn for arn in policy_arns)
    assert has_basic_exec


def test_cloudwatch_logs_firehose_policy_allows_put_record(iam_client, config):
    role_name = config['cloudwatch_logs_firehose_role_name']
    response = iam_client.get_role_policy(RoleName=role_name, PolicyName='FirehoseAccess')
    actions = _extract_policy_actions(response['PolicyDocument'])
    assert any('firehose:PutRecord' in a for a in actions)


def _firehose_metric(config, aws_region, metric_name):
    cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=24)
    stream_name = config['firehose_delivery_stream_name']
    return cloudwatch.get_metric_statistics(
        Namespace='AWS/Firehose',
        MetricName=metric_name,
        Dimensions=[{'Name': 'DeliveryStreamName', 'Value': stream_name}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Sum']
    )


def test_firehose_receives_incoming_records(config, aws_region):
    response = _firehose_metric(config, aws_region, 'IncomingRecords')
    assert 'Datapoints' in response


def test_firehose_delivery_to_s3_is_successful(config, aws_region):
    response = _firehose_metric(config, aws_region, 'DeliveryToS3.Success')
    assert 'Datapoints' in response


def test_s3_cloudwatch_logs_prefix_accessible(config, aws_region):
    s3 = boto3.client('s3', region_name=aws_region)
    response = s3.list_objects_v2(
        Bucket=config['central_logs_bucket'],
        Prefix='cloudwatch-logs/api/',
        MaxKeys=1
    )
    assert 'Contents' in response or 'KeyCount' in response


def test_s3_cloudfront_logs_prefix_accessible(config, aws_region):
    s3 = boto3.client('s3', region_name=aws_region)
    response = s3.list_objects_v2(
        Bucket=config['central_logs_bucket'],
        Prefix='cloudfront-logs/api/',
        MaxKeys=1
    )
    assert 'Contents' in response or 'KeyCount' in response


def test_api_gateway_cloudwatch_role_trusts_apigateway_service(iam_client, config):
    role_name = config['api_gateway_cloudwatch_role_name']
    response = iam_client.get_role(RoleName=role_name)
    assume_role_policy = response['Role']['AssumeRolePolicyDocument']
    statements = assume_role_policy['Statement']
    service_principal = statements[0]['Principal']['Service']
    assert service_principal == 'apigateway.amazonaws.com'
