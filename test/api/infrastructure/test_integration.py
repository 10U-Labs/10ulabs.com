import json
import boto3


def test_stack_deployed_successfully(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi')
    assert len(stacks['Stacks']) == 1


def test_api_gateway_has_health_resource(apigw_client, api_id):
    resources = apigw_client.get_resources(restApiId=api_id)
    resource_paths = [r['path'] for r in resources['items']]
    assert '/health' in resource_paths


def test_api_gateway_has_v1_echo_resource(apigw_client, api_id):
    resources = apigw_client.get_resources(restApiId=api_id)
    resource_paths = [r['path'] for r in resources['items']]
    assert '/v1/echo' in resource_paths


def test_api_gateway_health_has_get_method(apigw_client, api_id):
    resources = apigw_client.get_resources(restApiId=api_id)
    health_resource = None
    for r in resources['items']:
        if r['path'] == '/health':
            health_resource = r
            break
    assert 'GET' in health_resource['resourceMethods']


def test_api_gateway_echo_has_post_method(apigw_client, api_id):
    resources = apigw_client.get_resources(restApiId=api_id)
    echo_resource = None
    for r in resources['items']:
        if r['path'] == '/v1/echo':
            echo_resource = r
            break
    assert 'POST' in echo_resource['resourceMethods']


def test_health_lambda_has_memory_configured(lambda_client, health_function_name):
    function_config = lambda_client.get_function_configuration(FunctionName=health_function_name)
    assert function_config['MemorySize'] > 0


def test_echo_lambda_has_memory_configured(lambda_client, echo_function_name):
    function_config = lambda_client.get_function_configuration(FunctionName=echo_function_name)
    assert function_config['MemorySize'] > 0


def test_health_lambda_has_execution_role(lambda_client, health_function_name):
    function_config = lambda_client.get_function_configuration(FunctionName=health_function_name)
    assert 'Role' in function_config


def test_echo_lambda_has_execution_role(lambda_client, echo_function_name):
    function_config = lambda_client.get_function_configuration(FunctionName=echo_function_name)
    assert 'Role' in function_config


def test_health_lambda_has_cloudwatch_log_group(lambda_client, health_function_name):
    logs_client = boto3.client('logs', region_name=lambda_client.meta.region_name)
    log_groups = logs_client.describe_log_groups(logGroupNamePrefix=f'/aws/lambda/{health_function_name}')
    assert len(log_groups['logGroups']) > 0


def test_echo_lambda_has_cloudwatch_log_group(lambda_client, echo_function_name):
    logs_client = boto3.client('logs', region_name=lambda_client.meta.region_name)
    log_groups = logs_client.describe_log_groups(logGroupNamePrefix=f'/aws/lambda/{echo_function_name}')
    assert len(log_groups['logGroups']) > 0


def test_health_lambda_can_be_invoked(lambda_client, health_function_name):
    response = lambda_client.invoke(
        FunctionName=health_function_name,
        InvocationType='RequestResponse',
        Payload='{"path": "/health", "httpMethod": "GET"}'
    )
    assert response['StatusCode'] == 200


def test_echo_lambda_can_be_invoked(lambda_client, echo_function_name):
    response = lambda_client.invoke(
        FunctionName=echo_function_name,
        InvocationType='RequestResponse',
        Payload='{"path": "/v1/echo", "httpMethod": "POST", "body": "{\\"test\\": \\"data\\"}"}'
    )
    assert response['StatusCode'] == 200


def test_health_lambda_returns_valid_response(lambda_client, health_function_name):
    response = lambda_client.invoke(
        FunctionName=health_function_name,
        InvocationType='RequestResponse',
        Payload='{"path": "/health", "httpMethod": "GET"}'
    )
    payload = json.loads(response['Payload'].read())
    assert 'statusCode' in payload


def test_echo_lambda_returns_valid_response(lambda_client, echo_function_name):
    response = lambda_client.invoke(
        FunctionName=echo_function_name,
        InvocationType='RequestResponse',
        Payload='{"path": "/v1/echo", "httpMethod": "POST", "body": "{\\"test\\": \\"data\\"}"}'
    )
    payload = json.loads(response['Payload'].read())
    assert 'statusCode' in payload


def test_certificate_exists_for_subdomain(certificate_arn):
    assert certificate_arn is not None


def test_certificate_status_is_issued(acm_client, certificate_arn):
    cert_details = acm_client.describe_certificate(CertificateArn=certificate_arn)
    assert cert_details['Certificate']['Status'] == 'ISSUED'


def test_stack_has_api_url_output(stack_outputs):
    output_keys = [o['OutputKey'] for o in stack_outputs]
    assert 'ApiUrl' in output_keys


def test_stack_has_api_endpoint_output(stack_outputs):
    output_keys = [o['OutputKey'] for o in stack_outputs]
    assert 'ApiEndpoint' in output_keys


def test_stack_has_api_domain_name_output(stack_outputs):
    output_keys = [o['OutputKey'] for o in stack_outputs]
    assert 'ApiDomainName' in output_keys


def test_s3_bucket_exists_for_api_docs(s3_client, bucket_name):
    buckets = s3_client.list_buckets()
    bucket_names = [bucket['Name'] for bucket in buckets['Buckets']]
    assert bucket_name in bucket_names


def test_s3_bucket_contains_index_html(s3_client, bucket_name):
    objects = s3_client.list_objects_v2(Bucket=bucket_name)
    object_keys = [obj['Key'] for obj in objects.get('Contents', [])]
    assert 'index.html' in object_keys


def test_s3_bucket_contains_openapi_yaml(s3_client, bucket_name):
    objects = s3_client.list_objects_v2(Bucket=bucket_name)
    object_keys = [obj['Key'] for obj in objects.get('Contents', [])]
    assert 'openapi.yml' in object_keys


def test_s3_bucket_versioning_is_disabled(s3_client, bucket_name):
    versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
    status = versioning.get('Status', 'Disabled')
    assert status != 'Enabled'


def test_s3_bucket_has_encryption_enabled(s3_client, bucket_name):
    encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert 'ServerSideEncryptionConfiguration' in encryption


def test_cloudfront_distribution_exists(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi')
    stack_resources = cloudformation_client.list_stack_resources(StackName='TenULabsApi')
    resource_types = [r['ResourceType'] for r in stack_resources['StackResourceSummaries']]
    assert 'AWS::CloudFront::Distribution' in resource_types


def test_api_gateway_can_invoke_health_lambda(lambda_client, health_function_name):
    policy = lambda_client.get_policy(FunctionName=health_function_name)
    assert 'apigateway.amazonaws.com' in policy['Policy']


def test_api_gateway_can_invoke_echo_lambda(lambda_client, echo_function_name):
    policy = lambda_client.get_policy(FunctionName=echo_function_name)
    assert 'apigateway.amazonaws.com' in policy['Policy']
