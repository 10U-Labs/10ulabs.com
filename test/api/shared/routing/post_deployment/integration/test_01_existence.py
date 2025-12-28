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
