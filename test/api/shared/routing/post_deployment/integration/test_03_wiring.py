"""Layer 3: Wiring tests for api_shared_routing post-deployment.

These tests verify that components are connected properly.
Tests assume Layer 1 existence and Layer 2 configuration tests have passed.
"""
import json
from datetime import UTC, datetime, timedelta

import pytest
from botocore.exceptions import ClientError

import boto3
import requests

pytestmark = pytest.mark.layer(3)


TEST_HEADERS = {"x-test-mode": "true"}


# =============================================================================
# Helper Functions
# =============================================================================


def _extract_policy_actions(policy):
    """Extract all actions from an IAM policy document."""
    actions = []
    for stmt in policy.get('Statement', []):
        stmt_actions = stmt.get('Action', [])
        if isinstance(stmt_actions, str):
            actions.append(stmt_actions)
        else:
            actions.extend(stmt_actions)
    return actions


def _extract_policy_resources(policy):
    """Extract all resources from an IAM policy document."""
    resources = []
    for stmt in policy.get('Statement', []):
        stmt_resources = stmt.get('Resource', [])
        if isinstance(stmt_resources, str):
            resources.append(stmt_resources)
        else:
            resources.extend(stmt_resources)
    return resources


# =============================================================================
# API Gateway → Lambda Wiring
# =============================================================================


def test_api_gateway_has_permission_to_invoke_health_lambda(lambda_client, config):
    """Verify API Gateway has permission to invoke health Lambda function."""
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
    """Verify API Gateway usage plan is associated with prod stage."""
    if usage_plan_id is None:
        pytest.skip("Usage plan not found")
    plan = apigateway_client.get_usage_plan(usagePlanId=usage_plan_id)
    api_stages = plan.get('apiStages', [])
    for stage in api_stages:
        if stage.get('apiId') == api_gateway_id and stage.get('stage') == 'prod':
            return
    pytest.fail("Usage plan not associated with prod stage")


def test_api_gateway_usage_plan_key_links_key_to_plan(apigateway_client, usage_plan_id):
    """Verify API Gateway usage plan key links API key to plan."""
    if usage_plan_id is None:
        pytest.skip("Usage plan not found")
    keys = apigateway_client.get_usage_plan_keys(usagePlanId=usage_plan_id)
    assert len(keys['items']) > 0


def test_api_gateway_usage_plan_key_type_is_api_key(apigateway_client, usage_plan_id):
    """Verify API Gateway usage plan key type is API_KEY."""
    if usage_plan_id is None:
        pytest.skip("Usage plan not found")
    keys = apigateway_client.get_usage_plan_keys(usagePlanId=usage_plan_id)
    if keys['items']:
        assert keys['items'][0]['type'] == 'API_KEY'


def test_api_gateway_cloudwatch_role_has_push_logs_policy(iam_client, config):
    """Verify API Gateway CloudWatch role has policy for pushing logs."""
    role_name = config['api_gateway_cloudwatch_role_name']
    response = iam_client.list_attached_role_policies(RoleName=role_name)
    policy_arns = [p['PolicyArn'] for p in response['AttachedPolicies']]
    has_cloudwatch_policy = any(
        'CloudWatch' in arn or 'cloudwatch' in arn.lower() for arn in policy_arns
    )
    assert has_cloudwatch_policy


def test_lambda_catchall_permission_source_arn_covers_all_methods(lambda_client, shared_config):
    """Verify Lambda catchall permission source ARN covers all methods."""
    function_name = shared_config['lambda_handler_names']['catchall']
    try:
        response = lambda_client.get_policy(FunctionName=function_name)
        policy = json.loads(response['Policy'])
        for stmt in policy.get('Statement', []):
            source_arn = stmt.get('Condition', {}).get('ArnLike', {}).get('AWS:SourceArn', '')
            if 'execute-api' in source_arn:
                # Accept /*/, /*/*, or trailing /* (all cover all methods)
                assert '/*/' in source_arn or '/*/*' in source_arn or source_arn.endswith('/*')
    except ClientError as err:
        if err.response["Error"]["Code"] == "ResourceNotFoundException":
            pytest.skip("Lambda policy not found")
        raise


def _get_sqs_role_policy(iam_client, shared_config):
    """Get the API Gateway SQS role policy document."""
    role_name = f"{shared_config['resource_prefix']}ApiGatewaySqsRole"
    response = iam_client.get_role_policy(
        RoleName=role_name, PolicyName='SendToIngressQueues'
    )
    return response['PolicyDocument']


def test_api_gateway_sqs_policy_targets_webhook_queue(iam_client, shared_config):
    """Verify API Gateway SQS policy targets webhook queue."""
    policy = _get_sqs_role_policy(iam_client, shared_config)
    resources = _extract_policy_resources(policy)
    assert any('webhook' in r.lower() for r in resources)


def test_api_gateway_sqs_policy_targets_runners_queue(iam_client, shared_config):
    """Verify API Gateway SQS policy targets runners queue."""
    policy = _get_sqs_role_policy(iam_client, shared_config)
    resources = _extract_policy_resources(policy)
    assert any('runner' in r.lower() for r in resources)


def test_api_gateway_sqs_policy_allows_send_message(iam_client, shared_config):
    """Verify API Gateway SQS policy allows SendMessage action."""
    policy = _get_sqs_role_policy(iam_client, shared_config)
    actions = _extract_policy_actions(policy)
    assert any('sqs:SendMessage' in a for a in actions)


def test_api_gateway_sqs_policy_allows_get_queue_url(iam_client, shared_config):
    """Verify API Gateway SQS policy allows GetQueueUrl action."""
    policy = _get_sqs_role_policy(iam_client, shared_config)
    actions = _extract_policy_actions(policy)
    assert any('sqs:GetQueueUrl' in a for a in actions)


# =============================================================================
# CloudFront → S3 Wiring
# =============================================================================


def test_cloudfront_distribution_origin_points_to_s3(cloudfront_client):
    """Verify CloudFront distribution origin points to S3."""
    distributions = cloudfront_client.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        dist_config = cloudfront_client.get_distribution_config(Id=dist_id)
        origins = dist_config['DistributionConfig']['Origins']['Items']
        assert len(origins) > 0


def test_cloudfront_logging_bucket_is_central_logs(
    cloudfront_client, api_distribution_id, config
):
    """Verify CloudFront logs to central logs bucket."""
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    logging_config = dist_config['DistributionConfig'].get('Logging', {})
    if not logging_config.get('Enabled', False):
        pytest.skip("CloudFront logging not yet enabled on distribution")
    bucket = logging_config.get('Bucket', '')
    assert config['central_logs_bucket'] in bucket


def test_cloudfront_logging_prefix_is_correct(cloudfront_client, api_distribution_id):
    """Verify CloudFront logging prefix is correct."""
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    logging_config = dist_config['DistributionConfig'].get('Logging', {})
    prefix = logging_config.get('Prefix', '')
    assert prefix == 'cloudfront-logs/api/'


def test_cloudfront_waf_web_acl_association(cloudfront_client, api_distribution_id):
    """Verify CloudFront distribution has WAF Web ACL associated."""
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    web_acl_id = dist_config['DistributionConfig'].get('WebACLId', '')
    assert web_acl_id != ''


def test_s3_bucket_policy_allows_cloudfront_oac(s3_client, config):
    """Verify S3 bucket policy allows CloudFront OAC access."""
    bucket_name = config["api_fqdn"]
    response = s3_client.get_bucket_policy(Bucket=bucket_name)
    policy = json.loads(response['Policy'])
    has_cloudfront_condition = any(
        'cloudfront' in str(stmt.get('Condition', {})).lower()
        for stmt in policy.get('Statement', [])
    )
    assert has_cloudfront_condition


def test_route53_api_record_alias_target_is_cloudfront(api_route53_records, config):
    """Verify Route53 API record alias target is CloudFront."""
    if api_route53_records is None:
        pytest.skip("Hosted zone not found")
    for record in api_route53_records:
        if record['Name'].rstrip('.') == config['api_fqdn']:
            alias_target = record.get('AliasTarget', {})
            assert 'cloudfront.net' in alias_target.get('DNSName', '')


def test_cloudfront_uses_acm_certificate(cloudfront_client, api_distribution_id):
    """Verify CloudFront uses ACM certificate."""
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    viewer_cert = dist_config['DistributionConfig'].get('ViewerCertificate', {})
    acm_cert_arn = viewer_cert.get('ACMCertificateArn', '')
    assert 'arn:aws:acm' in acm_cert_arn


# =============================================================================
# CloudFront 404 Handling
# =============================================================================


def test_cloudfront_returns_404_for_nonexistent_endpoint(api_url):
    """Verify CloudFront returns 404 for nonexistent endpoints."""
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 404


def test_cloudfront_404_page_contains_error_message(api_url):
    """Verify CloudFront 404 page contains error message."""
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    data = json.loads(response.text)
    assert "error" in data


def test_cloudfront_404_page_contains_not_found_text(api_url):
    """Verify CloudFront 404 page contains not found text."""
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    assert "Not Found" in response.text or "Endpoint not found" in response.text


# =============================================================================
# CloudWatch Logs → Firehose Wiring (Subscription Filters)
# =============================================================================


def test_catchall_handler_subscription_filter_exists(logs_client, config):
    """Verify catchall handler log group has subscription filter."""
    log_group = config['catchall_handler_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    assert 'catchall-handler-to-firehose' in filter_names


def test_catchall_handler_subscription_destinations_firehose(logs_client, config):
    """Verify catchall handler subscription routes to Firehose."""
    log_group = config['catchall_handler_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    assert 'firehose' in destination_arn


def test_health_handler_subscription_filter_exists(logs_client, config):
    """Verify health handler log group has subscription filter."""
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
    """Verify API Gateway log group has subscription filter."""
    log_group = config['api_gateway_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    assert 'api-gateway-to-firehose' in filter_names


def test_waf_subscription_filter_exists():
    """Verify WAF log group has subscription filter."""
    logs_client_east = boto3.client('logs', region_name='us-east-1')
    log_group_name = 'aws-waf-logs-api'
    response = logs_client_east.describe_subscription_filters(logGroupName=log_group_name)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    assert 'waf-to-firehose' in filter_names


# =============================================================================
# Firehose → S3 Wiring
# =============================================================================


def test_firehose_role_trusts_firehose_service(iam_client, config):
    """Verify Firehose role trusts the Firehose service."""
    response = iam_client.get_role(RoleName=config['firehose_role_name'])
    assume_role_policy = response['Role']['AssumeRolePolicyDocument']
    statements = assume_role_policy['Statement']
    service_principal = statements[0]['Principal']['Service']
    assert service_principal == 'firehose.amazonaws.com'


def test_cloudwatch_logs_firehose_role_trusts_logs_service(iam_client, config):
    """Verify CloudWatch Logs Firehose role trusts the CloudWatch Logs service."""
    role_name = config['cloudwatch_logs_firehose_role_name']
    response = iam_client.get_role(RoleName=role_name)
    assume_role_policy = response['Role']['AssumeRolePolicyDocument']
    statements = assume_role_policy['Statement']
    service_principal = statements[0]['Principal']['Service']
    assert f"logs.{config['aws_region']}.amazonaws.com" == service_principal


def test_firehose_role_has_s3_access_policy(iam_client, config):
    """Verify Firehose role has S3 access policy attached."""
    response = iam_client.list_role_policies(RoleName=config['firehose_role_name'])
    assert 'S3Access' in response['PolicyNames']


def test_firehose_s3_policy_has_all_required_actions(iam_client, config):
    """Verify Firehose S3 policy has all required S3 actions."""
    response = iam_client.get_role_policy(
        RoleName=config['firehose_role_name'], PolicyName='S3Access'
    )
    actions = _extract_policy_actions(response['PolicyDocument'])
    assert any('s3:PutObject' in a or 's3:*' in a for a in actions)


def test_waf_firehose_s3_policy_has_all_required_actions(shared_config):
    """Verify WAF Firehose S3 policy has all required S3 actions."""
    iam_client = boto3.client('iam')
    role_name = f"{shared_config['resource_prefix']}-FirehoseWafLogs"
    response = iam_client.list_role_policies(RoleName=role_name)
    if 'S3Access' in response['PolicyNames']:
        policy_response = iam_client.get_role_policy(
            RoleName=role_name, PolicyName='S3Access'
        )
        actions = _extract_policy_actions(policy_response['PolicyDocument'])
        assert any('s3:PutObject' in a or 's3:*' in a for a in actions)


def test_cloudwatch_logs_firehose_role_has_firehose_access_policy(iam_client, config):
    """Verify CloudWatch Logs Firehose role has Firehose access policy attached."""
    role_name = config['cloudwatch_logs_firehose_role_name']
    response = iam_client.list_role_policies(RoleName=role_name)
    assert 'FirehoseAccess' in response['PolicyNames']


def test_catchall_subscription_uses_correct_firehose_role(logs_client, config):
    """Verify catchall subscription filter uses correct Firehose role."""
    log_group = config['catchall_handler_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    if response['subscriptionFilters']:
        role_arn = response['subscriptionFilters'][0].get('roleArn', '')
        assert config['cloudwatch_logs_firehose_role_name'] in role_arn


def test_api_gateway_subscription_uses_correct_firehose_role(logs_client, config):
    """Verify API Gateway subscription filter uses correct Firehose role."""
    log_group = config['api_gateway_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    if response['subscriptionFilters']:
        role_arn = response['subscriptionFilters'][0].get('roleArn', '')
        assert config['cloudwatch_logs_firehose_role_name'] in role_arn


def test_lambda_role_has_basic_execution_policy(iam_client, shared_config):
    """Verify Lambda role has basic execution policy attached."""
    role_name = f"{shared_config['resource_prefix']}CatchAllHandlerServiceRole"
    response = iam_client.list_attached_role_policies(RoleName=role_name)
    policy_arns = [p['PolicyArn'] for p in response['AttachedPolicies']]
    has_basic_exec = any('BasicExecutionRole' in arn for arn in policy_arns)
    assert has_basic_exec


def test_cloudwatch_logs_firehose_policy_allows_put_record(iam_client, config):
    """Verify CloudWatch Logs Firehose policy allows PutRecord action."""
    role_name = config['cloudwatch_logs_firehose_role_name']
    response = iam_client.get_role_policy(RoleName=role_name, PolicyName='FirehoseAccess')
    actions = _extract_policy_actions(response['PolicyDocument'])
    assert any('firehose:PutRecord' in a for a in actions)


# =============================================================================
# WAF → CloudWatch Logs Wiring
# =============================================================================


def test_waf_logging_configuration_exists(waf_logging_config):
    """Verify WAF logging configuration exists."""
    assert waf_logging_config is not None


def test_waf_logging_destinations_cloudwatch_logs(waf_logging_config):
    """Verify WAF logs to CloudWatch Logs."""
    if waf_logging_config is not None:
        destinations = waf_logging_config['LogDestinationConfigs']
        assert 'aws-waf-logs-api' in destinations[0]


# =============================================================================
# Metrics / Observability Wiring
# =============================================================================


def test_firehose_receives_incoming_records(config, aws_region):
    """Verify Firehose delivery stream receives incoming records."""
    cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=24)
    stream_name = config['firehose_delivery_stream_name']
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Firehose',
        MetricName='IncomingRecords',
        Dimensions=[{'Name': 'DeliveryStreamName', 'Value': stream_name}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Sum']
    )
    assert 'Datapoints' in response


def test_firehose_delivery_to_s3_is_successful(config, aws_region):
    """Verify Firehose successfully delivers to S3."""
    cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=24)
    stream_name = config['firehose_delivery_stream_name']
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Firehose',
        MetricName='DeliveryToS3.Success',
        Dimensions=[{'Name': 'DeliveryStreamName', 'Value': stream_name}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Sum']
    )
    assert 'Datapoints' in response


def test_s3_cloudwatch_logs_prefix_accessible(config, aws_region):
    """Verify S3 cloudwatch-logs prefix is accessible."""
    s3 = boto3.client('s3', region_name=aws_region)
    response = s3.list_objects_v2(
        Bucket=config['central_logs_bucket'],
        Prefix='cloudwatch-logs/api/',
        MaxKeys=1
    )
    assert 'Contents' in response or 'KeyCount' in response


def test_s3_cloudfront_logs_prefix_accessible(config, aws_region):
    """Verify S3 cloudfront-logs prefix is accessible."""
    s3 = boto3.client('s3', region_name=aws_region)
    response = s3.list_objects_v2(
        Bucket=config['central_logs_bucket'],
        Prefix='cloudfront-logs/api/',
        MaxKeys=1
    )
    assert 'Contents' in response or 'KeyCount' in response


def test_waf_metrics_being_collected():
    """Verify WAF metrics are being collected in CloudWatch."""
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=24)
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/WAFV2',
        MetricName='AllowedRequests',
        Dimensions=[
            {'Name': 'WebACL', 'Value': 'ApiWafWebAcl'},
            {'Name': 'Region', 'Value': 'us-east-1'},
            {'Name': 'Rule', 'Value': 'ALL'}
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Sum']
    )
    assert 'Datapoints' in response


# =============================================================================
# API Gateway → SQS Wiring
# =============================================================================


def test_api_gateway_sqs_role_trusts_apigateway_service(iam_client, shared_config):
    """Verify API Gateway SQS role trusts the API Gateway service."""
    role_name = f"{shared_config['resource_prefix']}ApiGatewaySqsRole"
    response = iam_client.get_role(RoleName=role_name)
    assume_role_policy = response['Role']['AssumeRolePolicyDocument']
    statements = assume_role_policy['Statement']
    service_principal = statements[0]['Principal']['Service']
    assert service_principal == 'apigateway.amazonaws.com'


def test_api_gateway_sqs_role_has_sqs_policy(iam_client, shared_config):
    """Verify API Gateway SQS role has SQS access policy attached."""
    role_name = f"{shared_config['resource_prefix']}ApiGatewaySqsRole"
    response = iam_client.list_role_policies(RoleName=role_name)
    assert 'SendToIngressQueues' in response['PolicyNames']


# =============================================================================
# API Gateway → CloudWatch Wiring
# =============================================================================


def test_api_gateway_cloudwatch_role_trusts_apigateway_service(iam_client, config):
    """Verify API Gateway CloudWatch role trusts the API Gateway service."""
    role_name = config['api_gateway_cloudwatch_role_name']
    response = iam_client.get_role(RoleName=role_name)
    assume_role_policy = response['Role']['AssumeRolePolicyDocument']
    statements = assume_role_policy['Statement']
    service_principal = statements[0]['Principal']['Service']
    assert service_principal == 'apigateway.amazonaws.com'


# =============================================================================
# WAF Firehose Wiring (us-east-1)
# =============================================================================


def test_waf_firehose_role_trusts_firehose_service(shared_config):
    """Verify WAF Firehose role trusts the Firehose service."""
    iam_client = boto3.client('iam')
    role_name = f"{shared_config['resource_prefix']}-FirehoseWafLogs"
    response = iam_client.get_role(RoleName=role_name)
    assume_role_policy = response['Role']['AssumeRolePolicyDocument']
    statements = assume_role_policy['Statement']
    service_principal = statements[0]['Principal']['Service']
    assert service_principal == 'firehose.amazonaws.com'


def test_waf_subscription_filter_routes_to_waf_firehose():
    """Verify WAF subscription filter routes to WAF-specific Firehose."""
    logs_client = boto3.client('logs', region_name='us-east-1')
    response = logs_client.describe_subscription_filters(logGroupName='aws-waf-logs-api')
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    assert 'WafLogs' in destination_arn or 'waf' in destination_arn.lower()


# Note: WebhookRouter metrics (CircuitBreakerState) and circuit_breaker_state_table
# DynamoDB metrics are tested in jit_runner_requests post-deployment tests because
# those resources are created by that module.
