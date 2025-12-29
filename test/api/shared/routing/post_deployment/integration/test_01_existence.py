"""Layer 1: Existence tests for api_shared_routing post-deployment.

These tests verify that resources were created by Terraform.
Tests are organized by resource domain for readability.
"""
import pytest

import boto3

pytestmark = pytest.mark.layer(1)


# =============================================================================
# Lambda Functions
# =============================================================================


def test_lambda_catchall_handler_exists(lambda_client, shared_config):
    """Verify Lambda catchall handler function exists."""
    function_name = shared_config['lambda_handler_names']['catchall']
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_catchall_handler_role_exists(iam_client, shared_config):
    """Verify CatchAllHandler IAM role exists."""
    role_name = f"{shared_config['resource_prefix']}CatchAllHandlerServiceRole"
    try:
        iam_client.get_role(RoleName=role_name)
    except iam_client.exceptions.NoSuchEntityException:
        pytest.fail(f"IAM role '{role_name}' does not exist")


# =============================================================================
# API Gateway Keys and Usage Plans
# =============================================================================


def test_api_gateway_api_key_exists(apigateway_client, api_gateway_id):
    """Verify API Gateway API key exists."""
    if api_gateway_id is None:
        pytest.skip("API Gateway not found")
    response = apigateway_client.get_api_keys()
    assert len(response['items']) > 0


def test_api_gateway_usage_plan_exists(apigateway_client, api_gateway_id):
    """Verify API Gateway usage plan exists."""
    if api_gateway_id is None:
        pytest.skip("API Gateway not found")
    response = apigateway_client.get_usage_plans()
    assert len(response['items']) > 0


def test_api_gateway_usage_plan_key_exists(apigateway_client, api_gateway_id):
    """Verify API Gateway usage plan key exists."""
    if api_gateway_id is None:
        pytest.skip("API Gateway not found")
    usage_plans = apigateway_client.get_usage_plans()
    if not usage_plans['items']:
        pytest.skip("No usage plans found")
    plan_id = usage_plans['items'][0]['id']
    response = apigateway_client.get_usage_plan_keys(usagePlanId=plan_id)
    assert len(response['items']) > 0


# =============================================================================
# S3 Buckets
# =============================================================================


def test_s3_docs_bucket_exists(s3_client, config):
    """Verify that the S3 docs bucket exists."""
    bucket_name = config["api_fqdn"]
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_index_html_exists_in_s3(s3_client, config):
    """Verify that index.html exists in S3 bucket."""
    bucket_name = config["api_fqdn"]
    response = s3_client.head_object(Bucket=bucket_name, Key="index.html")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_openapi_json_exists_in_s3(s3_client, config):
    """Verify that openapi.json exists in S3 bucket."""
    bucket_name = config["api_fqdn"]
    response = s3_client.head_object(Bucket=bucket_name, Key="openapi.json")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_404_html_exists_in_s3(s3_client, config):
    """Verify that 404.html exists in S3 bucket."""
    bucket_name = config["api_fqdn"]
    response = s3_client.head_object(Bucket=bucket_name, Key="404.html")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_s3_bucket_policy_exists(s3_client, config):
    """Verify that S3 bucket policy exists."""
    bucket_name = config["api_fqdn"]
    response = s3_client.get_bucket_policy(Bucket=bucket_name)
    assert 'Policy' in response


# =============================================================================
# CloudFront
# =============================================================================


def test_cloudfront_distribution_exists(cloudfront_client):
    """Verify CloudFront distribution exists."""
    distributions = cloudfront_client.list_distributions()
    distribution_list = distributions['DistributionList']
    assert distribution_list['Quantity'] > 0


def test_acm_certificate_exists(acm_client):
    """Verify ACM certificate exists for the domain."""
    certificates = acm_client.list_certificates()
    assert certificates['CertificateSummaryList']


def test_cloudfront_origin_access_control_exists(cloudfront_client):
    """Verify CloudFront origin access control exists."""
    response = cloudfront_client.list_origin_access_controls()
    oac_list = response['OriginAccessControlList'].get('Items', [])
    assert len(oac_list) > 0


# =============================================================================
# Route53
# =============================================================================


def test_route53_api_record_exists(config):
    """Verify Route53 A record for API exists."""
    route53 = boto3.client('route53')
    hosted_zones = route53.list_hosted_zones_by_name(DNSName=config['domain'])
    if not hosted_zones['HostedZones']:
        pytest.skip("Hosted zone not found")
    zone_id = hosted_zones['HostedZones'][0]['Id']
    records = route53.list_resource_record_sets(
        HostedZoneId=zone_id,
        StartRecordName=config['api_fqdn'],
        StartRecordType='A',
        MaxItems='1'
    )
    record_names = [r['Name'].rstrip('.') for r in records['ResourceRecordSets']]
    assert config['api_fqdn'] in record_names


# Note: CloudWatch/EventBridge resources (circuit breaker rules, alarms, WebhookRouter
# metrics namespace) are tested in jit_runner_requests post-deployment tests because
# they are created by that module, which deploys after routing.


# =============================================================================
# WAF
# =============================================================================


def test_waf_web_acl_exists():
    """Verify WAF Web ACL exists."""
    waf_client = boto3.client('wafv2', region_name='us-east-1')
    response = waf_client.list_web_acls(Scope='CLOUDFRONT')
    acl_names = [acl['Name'] for acl in response['WebACLs']]
    assert 'ApiWafWebAcl' in acl_names


def test_waf_log_group_exists():
    """Verify WAF log group exists."""
    logs_client = boto3.client('logs', region_name='us-east-1')
    response = logs_client.describe_log_groups(logGroupNamePrefix='aws-waf-logs-api')
    log_groups = [lg['logGroupName'] for lg in response['logGroups']]
    assert 'aws-waf-logs-api' in log_groups


# =============================================================================
# Firehose
# =============================================================================


def test_firehose_delivery_stream_exists(firehose_client, config):
    """Verify Firehose delivery stream exists."""
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    assert response['DeliveryStreamDescription']['DeliveryStreamName'] == stream_name


def test_firehose_role_exists(iam_client, config):
    """Verify Firehose IAM role exists."""
    response = iam_client.get_role(RoleName=config['firehose_role_name'])
    assert response['Role']['RoleName'] == config['firehose_role_name']


def test_cloudwatch_logs_firehose_role_exists(iam_client, config):
    """Verify CloudWatch Logs Firehose IAM role exists."""
    role_name = config['cloudwatch_logs_firehose_role_name']
    response = iam_client.get_role(RoleName=role_name)
    assert response['Role']['RoleName'] == role_name


# =============================================================================
# DynamoDB
# =============================================================================


def test_api_audit_log_table_exists(dynamodb_client, shared_config):
    """Verify API audit log DynamoDB table exists."""
    table_name = f"{shared_config['resource_prefix']}ApiAuditLog"
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response['Table']['TableName'] == table_name


# =============================================================================
# SSM Parameter Store
# =============================================================================


def test_api_key_ssm_parameter_exists(ssm_client, config):
    """Verify API key SSM parameter exists."""
    param_name = config['ssm_parameter_name_for_api_key']
    response = ssm_client.get_parameter(Name=param_name, WithDecryption=False)
    assert response['Parameter']['Name'] == param_name


# =============================================================================
# API Gateway
# =============================================================================


def test_api_gateway_rest_api_exists(apigateway_client, config):
    """Verify API Gateway REST API exists."""
    apis = apigateway_client.get_rest_apis()
    api_names = [api['name'] for api in apis['items']]
    assert config['api_gateway_name'] in api_names


def test_api_gateway_stage_exists(apigateway_client, api_gateway_id):
    """Verify API Gateway prod stage exists."""
    if api_gateway_id is None:
        pytest.skip("API Gateway not found")
    response = apigateway_client.get_stage(restApiId=api_gateway_id, stageName='prod')
    assert response['stageName'] == 'prod'


def test_api_gateway_cloudwatch_role_exists(iam_client, shared_config):
    """Verify API Gateway CloudWatch IAM role exists."""
    role_name = f"{shared_config['resource_prefix']}ApiGatewayCloudWatch"
    response = iam_client.get_role(RoleName=role_name)
    assert response['Role']['RoleName'] == role_name


def test_api_gateway_sqs_role_exists(iam_client, shared_config):
    """Verify API Gateway SQS IAM role exists."""
    role_name = f"{shared_config['resource_prefix']}ApiGatewaySqsRole"
    response = iam_client.get_role(RoleName=role_name)
    assert response['Role']['RoleName'] == role_name


# =============================================================================
# CloudFront Function
# =============================================================================


def test_cloudfront_url_rewrite_function_exists(cloudfront_client):
    """Verify CloudFront URL rewrite function exists."""
    response = cloudfront_client.list_functions()
    function_names = [f['Name'] for f in response['FunctionList'].get('Items', [])]
    assert 'url-rewrite' in function_names


# =============================================================================
# WAF Firehose (us-east-1)
# =============================================================================


def test_waf_firehose_delivery_stream_exists(shared_config):
    """Verify WAF Firehose delivery stream exists in us-east-1."""
    firehose_client = boto3.client('firehose', region_name='us-east-1')
    stream_name = f"{shared_config['resource_prefix']}-WafLogs"
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    assert response['DeliveryStreamDescription']['DeliveryStreamName'] == stream_name
